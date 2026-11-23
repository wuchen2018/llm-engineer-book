"""
文件名: structured_json_demo.py
功能: 演示结构化输出的完整防御链——从各种翻车输出到逐步修复与校验

【这是什么？】
大模型输出 JSON 时会以各种方式翻车：加废话、少括号、多逗号、字段名乱跑……
这段代码准备了 8 种典型的翻车样本，带你走一遍“提取→解析→修复→校验”的
完整防御流程，让你亲眼看到每种翻车的报错长什么样、每一步修复做了什么。

【怎么用？】
直接运行 python structured_json_demo.py，终端会逐条处理 8 个翻车样本，
打印每一步的处理过程和最终结果。你可以修改 SIMULATED_OUTPUTS 列表，
加入自己在实际项目中遇到的翻车输出，测试防御链能不能接住。

【运行条件】
- 是否需要 GPU：不需要。
- 是否需要联网：不需要，本脚本只使用预设样本。
- 是否下载模型：不会下载模型。
- 预计耗时：几秒钟。

【额外安装】
只使用 Python 标准库，不需要额外安装第三方库。
"""

import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


SIMULATED_OUTPUTS = [
    '好的，以下是提取结果：\n{"product": "蓝色运动外套", "order_id": "20250415123", "reason": "尺码偏大"}',
    '{"product": "红色连衣裙", "order_id": "20250416789", "reason": "颜色不符"}',
    '{"product": "黑色皮鞋", "order_id": "20250417456", "reason": "质量问题",}',
    '```json\n{"product": "白色T恤", "order_id": "20250418111", "reason": "发错货"}\n```',
    '{"product_name": "灰色背包", "orderID": "20250419222", "退货原因": "不喜欢"}',
    '{"product": "绿色卫衣", "order_id": 20250420333, "reason": "尺码偏大"}',
    '{"product": "棕色大衣", "order_id": "20250421444", "reason": "面料起',
    "{'product': '紫色围巾', 'order_id': '20250422555', 'reason': '有污渍'}",
]

EXPECTED_SCHEMA = {
    "product": str,
    "order_id": str,
    "reason": str,
}


def extract_json(raw_text):
    """
    从原始文本中提取 JSON 子串。
    返回 (提取结果字符串, 使用了哪种策略的说明)。
    提取失败返回 (None, 失败原因)。
    """
    fence_pattern = r'```(?:json)?\s*\n?(.*?)\n?\s*```'
    match = re.search(fence_pattern, raw_text, re.DOTALL)
    if match:
        return match.group(1).strip(), "从 Markdown 代码栅栏中提取"

    start = raw_text.find('{')
    end = raw_text.rfind('}')
    if start != -1 and end != -1 and end > start:
        return raw_text[start:end + 1], "用 find/rfind 定位花括号"

    return None, "未找到任何 JSON 结构"


def try_parse_json(json_str):
    """
    尝试解析 JSON 字符串。
    如果直接解析失败，会依次尝试几种常见的自动修复。
    返回 (解析结果字典或None, 状态说明)。
    """
    try:
        return json.loads(json_str), "直接解析成功"
    except json.JSONDecodeError as e:
        original_error = str(e)

    fixed = re.sub(r',(\s*[}\]])', r'\1', json_str)
    if fixed != json_str:
        try:
            return json.loads(fixed), "修复尾逗号后解析成功"
        except json.JSONDecodeError:
            pass

    fixed = json_str.replace("'", '"')
    try:
        return json.loads(fixed), "修复单引号后解析成功"
    except json.JSONDecodeError:
        pass

    return None, f"所有修复尝试均失败。原始错误: {original_error}"


def validate_fields(data, schema):
    """
    根据 schema 定义检查字段是否完整、类型是否正确。
    返回一个错误列表，空列表表示全部通过。
    """
    errors = []

    for field_name, expected_type in schema.items():
        if field_name not in data:
            errors.append(f"缺少字段 '{field_name}'")
        elif not isinstance(data[field_name], expected_type):
            actual = type(data[field_name]).__name__
            errors.append(
                f"字段 '{field_name}' 类型错误: "
                f"期望 {expected_type.__name__}, 实际 {actual}, "
                f"值为 {data[field_name]!r}"
            )

    extra_fields = set(data.keys()) - set(schema.keys())
    if extra_fields:
        errors.append(f"多余字段: {extra_fields}")

    return errors


def build_retry_prompt(raw_output, error_description):
    """
    根据上一次的翻车输出和具体的错误描述，
    拼出一段用于重试的 prompt。
    在真实项目中，你会把这段文字发给模型，让它修正后重新输出。
    """
    retry_prompt = (
        "你上一次的输出存在格式问题，无法被程序解析。\n"
        f"你上次的原始输出:\n{raw_output}\n\n"
        f"具体问题:\n{error_description}\n\n"
        "请严格只输出一个合法的 JSON 对象，不要包含任何其他文字、"
        "不要用代码块包裹、不要加任何解释。"
    )
    return retry_prompt


def check_truncation(json_str):
    """
    检查 JSON 字符串是否疑似被截断。
    截断的典型特征：最后一个非空白字符不是 } 或 ]。
    如果是截断，修复几乎不可能成功，应该直接走重试。
    """
    stripped = json_str.rstrip()
    if stripped and stripped[-1] not in ('}', ']'):
        return True
    return False


def process_one(raw_output, case_id):
    """对一条模型输出执行完整的防御链，打印每一步的过程。"""
    print(f"\n{'-' * 60}")
    print(f"  案例 {case_id}")
    print(f"{'-' * 60}")

    display = raw_output if len(raw_output) <= 80 else raw_output[:77] + "..."
    print(f"原始输出: {display!r}")

    json_str, extract_msg = extract_json(raw_output)
    print(f"[提取] {extract_msg}")
    if json_str is None:
        print("  >>> 结果: 提取失败，需要重试")
        return False, "提取阶段失败"

    if check_truncation(json_str):
        print(f"[截断检测] 输出疑似被截断（末尾字符: {json_str.rstrip()[-1]!r}）")
        print("  >>> 结果: 截断的 JSON 无法修复，需要增大 max_tokens 后重试")
        return False, "输出被截断"

    data, parse_msg = try_parse_json(json_str)
    print(f"[解析] {parse_msg}")
    if data is None:
        print("  >>> 结果: 解析失败，需要重试")
        return False, parse_msg

    errors = validate_fields(data, EXPECTED_SCHEMA)
    if errors:
        print(f"[校验] 发现 {len(errors)} 个问题:")
        for err in errors:
            print(f"       - {err}")
        print("  >>> 结果: 校验未通过，需要重试或人工处理")
        return False, "; ".join(errors)

    print(f"[校验] 全部通过")
    print(f"  >>> 最终结果: {data}")
    return True, ""


if __name__ == "__main__":
    print("=" * 60)
    print("  结构化输出防御链演示")
    print("  8 种翻车样本 x 完整处理流程")
    print("=" * 60)

    results = []
    for i, output in enumerate(SIMULATED_OUTPUTS, 1):
        success, error_msg = process_one(output, i)
        results.append((i, success, error_msg))

    total = len(results)
    passed = sum(1 for _, s, _ in results if s)
    failed = total - passed

    print(f"\n{'=' * 60}")
    print(f"  汇总")
    print(f"{'=' * 60}")
    print(f"总计: {total} 条  |  通过: {passed} 条  |  失败: {failed} 条")
    print(f"通过率: {passed / total * 100:.0f}%")

    if failed > 0:
        print(f"\n失败案例的重试 prompt 示例（以第一个失败案例为例）:")
        print("-" * 40)
        for case_id, success, error_msg in results:
            if not success:
                retry = build_retry_prompt(
                    SIMULATED_OUTPUTS[case_id - 1], error_msg
                )
                print(retry)
                break

    print(f"\n{'=' * 60}")
    print("提示: 修改代码开头的 SIMULATED_OUTPUTS 列表，")
    print("加入你自己遇到的翻车输出，看看防御链能不能接住。")
    print("试试往 EXPECTED_SCHEMA 里加一个 'price': float，")
    print("看看哪些案例会多报一个字段缺失。")
