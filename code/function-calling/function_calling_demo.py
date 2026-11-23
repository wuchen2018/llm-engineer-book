"""
文件名: function_calling_demo.py
功能: 模拟 Function Calling 的完整五步流程，逐步展示每一步的消息内容和流向

【这是什么？】
Function Calling 的核心是模型与程序之间的一套通信协议。这段代码用一个简化
模拟器，走完这套协议的每一步，让你看清：每一步谁在对谁说话、消息长什么样、
模型的两次输出分别是给谁看的。附带一个真正能算数的计算器工具。

【怎么用？】
直接运行。程序会演示三个场景：
  场景一：数学计算 -> 模型调用计算器工具
  场景二：天气查询 -> 模型调用天气工具
  场景三：闲聊问题 -> 模型不调用任何工具，直接回答
每个场景会逐步打印五步流程中每一步的消息。运行后修改参数配置区的数学表达式
或城市名，重新运行，可以看到工具执行结果的实时变化。

【运行条件】
这段代码不调用真实大模型，不联网，不下载模型，也不需要 GPU。它只用 Python
标准库模拟 Function Calling 的消息流，所以装好 Python 就能运行。
"""

import json

# --- 可调整参数配置区 ---

# 场景一：数学计算
# -> 改成其他表达式试试，比如 "(2**10 - 24) * 3" 或 "355 / 113"
# -> 计算器会用 Python 真正算出结果，不是预设的假数据
MATH_EXPRESSION = "387 * 529"

# 场景二：天气查询
# -> 可选：北京、上海、广州（其他城市会返回默认值）
WEATHER_CITY = "北京"

# 场景三：闲聊（这个问题不需要任何工具）
CHAT_QUESTION = "你觉得秋天适合去北京玩吗？"


# ============================================================
# 工具描述（和真实 API 传给模型的格式一致）
# ============================================================
# 试试把 description 改短改模糊，比如把 calculate 的描述改成
# "计算工具"两个字，想想模型看到这样的描述还能不能做出正确判断

TOOLS = [
    {
        "name": "calculate",
        "description": "计算数学表达式的精确结果，支持加减乘除和乘方。"
                       "当用户提出需要精确数值计算的数学问题时使用。",
        "parameters": {
            "expression": {
                "type": "string",
                "required": True,
                "description": "数学表达式，如 '387 * 529' 或 '(100 - 37) ** 2'"
            }
        }
    },
    {
        "name": "get_weather",
        "description": "查询指定城市的实时天气信息，包括温度、天气状况和风力。"
                       "当用户询问某个城市当前或今天的天气、气温时使用。",
        "parameters": {
            "city": {
                "type": "string",
                "required": True,
                "description": "城市名称，如 北京、上海"
            }
        }
    }
]


# ============================================================
# 工具的真实实现——这就是五步流程中"外部服务"那一层
# ============================================================

def calculate(expression):
    """一个真正能算数的计算器。真实项目中的工具可以就是这么简单的一个函数。
    注意：这里用 eval() 纯粹是为了演示方便。生产环境中绝不能用 eval()
    执行用户输入的内容，因为用户可以注入恶意代码。"""
    try:
        result = eval(expression)
        return {"result": result, "expression": expression}
    except Exception as e:
        return {"error": f"计算失败: {str(e)}"}


def get_weather(city):
    """模拟的天气查询。真实项目中，这个函数里会发网络请求到天气服务商
    （比如和风天气、OpenWeatherMap）的 API，拿到实时数据。
    这里用固定数据模拟，只是为了演示消息流程。"""
    mock_data = {
        "北京": {"temperature": 22, "condition": "晴", "wind": "北风3级"},
        "上海": {"temperature": 26, "condition": "多云", "wind": "东南风2级"},
        "广州": {"temperature": 31, "condition": "雷阵雨", "wind": "南风4级"},
    }
    return mock_data.get(city, {"temperature": 25, "condition": "晴", "wind": "微风"})


# 工具名 -> 工具函数的映射，方便按名字查找
TOOL_MAP = {"calculate": calculate, "get_weather": get_weather}


# ============================================================
# 辅助函数：格式化输出
# ============================================================

def divider(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def step_header(num, who_to_whom, note=""):
    print(f"\n  -- 第{num}步：{who_to_whom} --")
    if note:
        print(f"     ({note})")


def show_model_view(sections):
    """用缩进文本展示"模型看到的完整上下文"，每个 section 是 (标签, 内容) 元组"""
    print("\n     模型看到的完整上下文：")
    print("     +----------------------------------------+")
    for label, content in sections:
        print(f"     | 【{label}】")
        # 内容可能是多行的，逐行打印
        for line in content.split("\n"):
            print(f"     |   {line}")
    print("     +----------------------------------------+")


# ============================================================
# 场景演示：需要调用工具
# ============================================================

def run_tool_scenario(title, user_question, tool_name, tool_args):
    divider(f"场景：{title}")
    print(f'  用户说："{user_question}"')

    # ---- 第1步 ----
    step_header(1, "你的代码 -> 大模型",
                "把工具清单和用户消息打包，发给模型")

    # 拼接工具清单的文字描述
    tools_text = ""
    for t in TOOLS:
        params = ", ".join(
            f'{k}({"必填" if v.get("required") else "可选"})'
            for k, v in t["parameters"].items()
        )
        tools_text += f"  {t['name']}({params}): {t['description'][:30]}...\n"

    show_model_view([
        ("系统提示 + 工具清单", f"你可以使用以下工具：\n{tools_text.rstrip()}"),
        ("用户消息", user_question),
    ])

    # ---- 第2步 ----
    step_header(2, "大模型 -> 你的程序",
                "[注意] 这段输出是给程序看的，用户看不到")

    args_str = json.dumps(tool_args, ensure_ascii=False)
    print(f"\n     模型的输出（结构化的调用意图，不是自然语言）：")
    print(f"       tool_name: {tool_name}")
    print(f"       arguments: {args_str}")
    print(f"\n     此时用户的屏幕上显示的是：[处理中] 正在处理中...")

    # ---- 第3步 ----
    step_header(3, "你的程序 -> 外部工具",
                "程序解析意图，替模型去执行")

    # 真正执行工具函数
    func = TOOL_MAP[tool_name]
    first_arg_value = list(tool_args.values())[0]
    tool_result = func(first_arg_value)

    result_str = json.dumps(tool_result, ensure_ascii=False)
    print(f"\n     执行: {tool_name}({args_str})")
    print(f"     返回: {result_str}")
    print(f"\n     这一步和大模型没有任何关系。模型不知道你调了什么、结果是什么。")

    # ---- 第4步 ----
    step_header(4, "你的程序 -> 大模型（第二次调用）",
                "把工具结果塞进对话历史，再发给模型")

    show_model_view([
        ("系统提示 + 工具清单", "（和第1步一样，省略）"),
        ("用户消息", user_question),
        ("助手上一轮的决定", f"调用 {tool_name}，参数 {args_str}"),
        ("工具返回的结果", result_str),
    ])

    print(f"\n     注意：模型到这里已经被调用了第二次。")

    # ---- 第5步 ----
    step_header(5, "大模型 -> 用户",
                "[完成] 这次的输出是给用户看的")

    # 根据工具类型生成模拟的最终回答
    if tool_name == "calculate":
        r = tool_result
        if "error" in r:
            answer = f"抱歉，计算出错了：{r['error']}"
        else:
            answer = f"{r['expression']} = {r['result']:,}"
    elif tool_name == "get_weather":
        r = tool_result
        answer = (f"{tool_args['city']}今天{r['condition']}，"
                  f"气温{r['temperature']}摄氏度，{r['wind']}。")
    else:
        answer = f"查询结果：{result_str}"

    print(f'\n     模型的回答："{answer}"')
    print(f"     用户在屏幕上看到了这句话。一次完整的工具调用结束。")
    print(f"\n     回顾：模型被调用了 2 次，中间由你的程序代劳执行工具。")


# ============================================================
# 场景演示：不需要调用工具
# ============================================================

def run_no_tool_scenario(user_question):
    divider("场景：闲聊（不需要工具）")
    print(f'  用户说："{user_question}"')

    step_header(1, "你的代码 -> 大模型",
                "同样传了工具清单和用户消息")

    print(f"\n     模型看到了工具清单，也看到了用户问题。")
    print(f"     但这是一个常识问题，不需要实时数据，不需要计算。")
    print(f"     模型判断：不需要调用任何工具，直接回答。")

    step_header(2, "大模型 -> 用户",
                "直接输出自然语言回答，跳过工具调用")

    answer = "秋天是去北京非常好的季节。九月底到十月气温凉爽，香山红叶也很值得一看。"
    print(f'\n     模型的回答："{answer}"')

    print(f"\n     注意：这个场景里模型只被调用了 1 次（不是2次），")
    print(f"     因为它判断不需要工具，直接回答了用户。")
    print(f"     工具清单虽然传了，但模型选择忽略它——这完全没问题。")


# ============================================================
# 附加实验：工具描述好坏对比
# ============================================================

def run_description_comparison():
    divider("附加实验：工具描述的好坏直接影响模型的决策")

    question = "有没有500块以内的蓝牙降噪耳机？"
    print(f'  假设用户问："{question}"\n')

    print("  [不推荐] 描述A（模糊）：")
    print('     name: search_product')
    print('     description: "搜索商品"')
    print()
    print('     模型的反应：犹豫。"搜索商品"？用户说的是"有没有"，这算搜索吗？')
    print('     可能结果：模型跳过工具，自己编了一个推荐清单，里面的耳机型号不存在。')

    print()

    print("  [推荐] 描述B（精确）：")
    print('     name: search_product')
    print('     description: "根据用户的购物需求搜索匹配商品。')
    print('      支持按品类、品牌、价格范围筛选。')
    print('      当用户询问某类商品是否有售、或寻找特定条件的商品时使用。"')
    print()
    print('     模型的反应：看到"询问某类商品是否有售"和"价格范围筛选"，')
    print('     和用户问题完美匹配。果断调用工具，传入品类和价格参数。')

    print(f"\n  结论：同样的用户问题，工具描述的质量直接决定模型的行为。")
    print(f"  写工具描述和写 Prompt 是同一项技能，值得花时间打磨。")


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("  Function Calling 完整流程演示")
    print("  （三个场景 + 一个附加实验）")
    print("=" * 60)

    # 场景一：数学计算 -- 调用 calculate 工具
    # 这里的计算器是真正在算的，不是预设的假数据
    run_tool_scenario(
        title=f"数学计算（{MATH_EXPRESSION}）",
        user_question=f"{MATH_EXPRESSION} 等于多少？",
        tool_name="calculate",
        tool_args={"expression": MATH_EXPRESSION},
    )

    # 场景二：天气查询 -- 调用 get_weather 工具
    run_tool_scenario(
        title=f"天气查询（{WEATHER_CITY}）",
        user_question=f"{WEATHER_CITY}今天多少度？",
        tool_name="get_weather",
        tool_args={"city": WEATHER_CITY},
    )

    # 场景三：闲聊 -- 不调用任何工具
    run_no_tool_scenario(CHAT_QUESTION)

    # 附加实验：工具描述好坏对比
    run_description_comparison()

    print("\n" + "=" * 60)
    print("  演示结束。")
    print("  建议尝试：")
    print("    1. 把 MATH_EXPRESSION 改成 '(2**10 - 24) * 3'，重新运行")
    print("    2. 把 WEATHER_CITY 改成 '广州'，看看天气数据的变化")
    print("    3. 把 TOOLS 里 calculate 的 description 改成 '工具'")
    print("       两个字，想想模型还能不能做出正确判断")
    print("=" * 60)
