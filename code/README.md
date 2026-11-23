# Python 交互实验室

这里收录已公开样章对应的实验代码，按书中小节查找。本书正式出版后，这里会更新全部配套代码。

| 小节 | 实验 | 代码 |
| --- | --- | --- |
| 1.7 Git 生存指南 | 自动演示提交、分支、合并冲突与忽略文件 | [git_workflow_lab.py](git/git_workflow_lab.py) |
| 1.8 浮点数常识 | 小数的二进制表示、精度、溢出与小数更新 | [float_precision_demo.py](floating-point/float_precision_demo.py) |
| 8.1 注意力的直觉 | 比较同一个词在不同语境下的注意力和向量 | [attention_intuition_demo.py](attention-intuition/attention_intuition_demo.py) |
| 8.2 Q、K、V | 手算投影、注意力分数与缩放因子的影响 | [qkv_attention_demo.py](qkv/qkv_attention_demo.py) |
| 13.3 结构化输出 | 解析、校验和修复典型的 JSON 输出 | [structured_json_demo.py](structured-output/structured_json_demo.py) |
| 15.1 LoRA 的核心思想 | 观察矩阵秩、低秩近似和参数量 | [lora_core_demo.py](lora/lora_core_demo.py) |
| 19.1 Function Calling | 模拟计算、天气查询和闲聊中的工具调用流程 | [function_calling_demo.py](function-calling/function_calling_demo.py) |

## 怎么运行

先安装 Python 3。从[仓库首页](../)点击绿色的 **Code → Download ZIP**，解压后，在 `code` 文件夹里打开终端，安装依赖：

```bash
python -m pip install -r requirements.txt
```

然后选择一份脚本运行。例如浮点数实验：

```bash
python floating-point/float_precision_demo.py
```

这些实验不需要 GPU、不下载模型，也不调用付费 API。有些实验会在终端里请你输入参数，有些会生成图片。Git 实验还需要电脑已经安装 Git；它会在系统临时目录建立一个练习仓库，结束后保留，方便你继续探索。
