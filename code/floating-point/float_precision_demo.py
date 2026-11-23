"""
文件名: float_precision_demo.py
功能: 交互式探索浮点数存储原理、精度损失、格点分布及溢出/NaN行为

【这是什么？】
计算机存小数用 IEEE 754 二进制科学计数法，受限于位数，十进制小数往往只能近似。
本程序是一个交互式实验台：你可以输入任意十进制小数，查看它的二进制表示、存储误差；
也可以输入大数观察格点间距如何膨胀，亲眼看到“大数吞小数”；还可以触发溢出和 NaN 传染。
所有实验都基于 numpy 和标准库，不依赖深度学习框架。

【怎么用？】
直接运行本脚本。程序会依次进入 5 个实验模块，每个模块内你可以反复输入不同的数值，
观察输出变化。每个实验结束后会询问：按回车继续尝试新数值，输入 n 进入下一个实验，
输入 q 退出程序。强烈建议：在每个实验中都尝试多个数值，建立直觉。

【运行条件】
不需要真实模型，不需要联网，不需要下载数据集，也不需要GPU。脚本是交互式程序，
运行后会等待你在终端输入数字。

【额外安装】
需要 numpy。如果本机还没有安装，可以先运行：
pip install numpy
"""

import numpy as np
import struct
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ==================== 工具函数 ====================
def float32_bits(x: float):
    """返回 float32 的 32 位二进制字符串，以及符号、指数、尾数分段"""
    f32 = np.float32(x)
    bits = struct.unpack('I', struct.pack('f', f32))[0]
    bin_str = f"{bits:032b}"
    return bin_str, bin_str[0], bin_str[1:9], bin_str[9:]

def spacing_at(x: float):
    """返回 float32 中 x 与其下一个可表示数的间距"""
    x32 = np.float32(x)
    next_x = np.nextafter(x32, np.float32(np.inf))
    return float(next_x - x32)

def prompt_continue(exp_name):
    """
    每个实验结束后询问用户：
    回车 -> 继续本实验（重新输入数值）
    n   -> 进入下一个实验
    q   -> 退出程序
    """
    while True:
        choice = input(f"\n[{exp_name}] 按 Enter 重新尝试本实验，输入 n 进入下一步，输入 q 退出: ")
        if choice == '':
            return 'retry'
        elif choice.lower() == 'n':
            return 'next'
        elif choice.lower() == 'q':
            print("已退出程序。")
            sys.exit(0)
        else:
            print("无效输入，请按 Enter、n 或 q。")

# ==================== 实验 1：十进制小数转二进制 ====================
def experiment1():
    print("\n" + "="*70)
    print("【实验 1】十进制小数的二进制真相")
    print("="*70)
    print("说明：输入一个十进制小数，查看它存为 float32 后的实际值和二进制表示。")
    
    while True:
        s = input("\n请输入一个十进制小数（例如 0.1, 0.2, 0.3, 0.5）: ")
        try:
            val = float(s)
        except:
            print("输入无效，请重新输入数字。")
            continue
        
        val32 = np.float32(val)
        bin_str, sign, exp, mant = float32_bits(val)
        
        print(f"\n你输入的数字: {val}")
        print(f"存储为 float32 后的实际值: {val32:.10f}")
        print(f"相对误差: {abs(val32 - val) / max(abs(val), 1e-8):.2e}")
        print(f"32位二进制: {bin_str}")
        print(f"  符号位(1): {sign} ({'负' if sign=='1' else '正'})")
        print(f"  指数位(8): {exp} = 十进制 {int(exp,2)}，实际指数 = {int(exp,2) - 127}")
        print(f"  尾数位(23): {mant} (隐含前导 1)")
        print("\n【思考】有些小数（如 0.5）二进制是有限的，存储无误差；")
        print("        有些（如 0.1）是无限循环，只能近似。")
        
        action = prompt_continue("实验1")
        if action == 'next':
            break
        # 否则 retry，继续循环

# ==================== 实验 2：格点密度探测器 ====================
def experiment2():
    print("\n" + "="*70)
    print("【实验 2】格点密度探测器 — 数字越大，邻居越远")
    print("="*70)
    print("说明：输入一个数字，查看它在 float32 中与下一个可表示数的间距。")
    
    while True:
        s = input("\n请输入一个数字（例如 6.75, 1e7, 1e8, 123456789）: ")
        try:
            val = float(s)
        except:
            print("输入无效，请重新输入数字。")
            continue
        
        next_val = np.nextafter(np.float32(val), np.float32(np.inf))
        space = spacing_at(val)
        print(f"\n数字: {val}")
        print(f"下一个可表示的 float32: {next_val}")
        print(f"相邻间距: {space:.6g}")
        if space >= 0.5:
            print(f"  → 在此量级，float32 连整数都区分不了，间距达到 {space:.0f}")
        elif space > 0.001:
            print(f"  → 间距约 {space:.4f}，小数精度开始丢失")
        else:
            print(f"  → 间距很小，精度较高")
        
        print(f"\n【直观感受】如果你把 {val} 加上 {space/2:.4g}，数值不会变化，")
        print(f"            因为格点间距是 {space:.4g}，小于一半的变化会被舍入。")
        
        action = prompt_continue("实验2")
        if action == 'next':
            break

# ==================== 实验 3：大数吞小数 ====================
def experiment3():
    print("\n" + "="*70)
    print("【实验 3】大数吞小数 — 加法可能无效")
    print("="*70)
    print("说明：输入一个大数和一个小数，判断加法在 float32 下是否有效。")
    
    while True:
        big_s = input("\n请输入一个较大的数（例如 1e8, 1e9）: ")
        small_s = input("请输入一个较小的数（例如 1, 0.5, 0.1）: ")
        try:
            big = float(big_s)
            small = float(small_s)
        except:
            print("输入无效，请重新输入数字。")
            continue
        
        big32 = np.float32(big)
        small32 = np.float32(small)
        result = big32 + small32
        
        print(f"\n{big} (float32) + {small} (float32) = {result}")
        if result == big32:
            space = spacing_at(big)
            print(f"结果等于原大数 → 加法无效！")
            print(f"原因：当前量级下，float32 的格点间距是 {space:.4g}，")
            print(f"      而 {small} 小于间距的一半，无法跨越到下一个格点。")
            critical = space / 2
            print(f"【临界值】要使加法有效，小数至少需要大于 {critical:.4g}。")
        else:
            print(f"结果大于原大数 → 加法有效。")
            space = spacing_at(big)
            print(f"当前格点间距是 {space:.4g}，{small} 足够让数值跳到下一个格点。")
        
        print("\n【探索建议】固定大数为 1e8，把小数从 1 逐渐减小到 0.1，观察何时加法失效。")
        
        action = prompt_continue("实验3")
        if action == 'next':
            break

# ==================== 实验 4：溢出与 NaN 传染 ====================
def experiment4():
    print("\n" + "="*70)
    print("【实验 4】溢出（inf）与 NaN 的传染性")
    print("="*70)
    print("说明：输入一个数值，观察它在 float16 下是否溢出；然后展示 inf 到 nan 的传染链。")
    
    while True:
        s = input("\n请输入一个数值，尝试让它溢出 float16（上限约 65504）: ")
        try:
            val = float(s)
        except:
            print("输入无效，请重新输入数字。")
            continue
        
        f16 = np.float16(val)
        if np.isinf(f16):
            print(f"\n{val} 转为 float16 后变成 {f16} (inf) → 上溢了！")
        else:
            print(f"\n{val} 转为 float16 后是 {f16}，未溢出，但可能接近上限。")
        
        # 演示 inf 传染链（使用 float32）
        print("\n现在模拟 inf 的传染过程（使用 float32）：")
        huge = np.float32(1e38) * 10   # 超出 float32 范围
        print(f"1e38 * 10 = {huge}  (inf)")
        nan_val = huge * np.float32(0.0)
        print(f"inf × 0 = {nan_val}  (nan)")
        result = nan_val + np.float32(100.0)
        print(f"nan + 100 = {result}  (nan)")
        
        print("\n【结论】一旦某步运算产生 inf，后续运算很快变成 nan，")
        print("        并且 nan 会污染所有后续结果。训练中遇到 nan，")
        print("        往往是因为某层输出溢出了。")
        
        action = prompt_continue("实验4")
        if action == 'next':
            break

# ==================== 实验 5：低精度参数更新丢失 ====================
def experiment5():
    print("\n" + "="*70)
    print("【实验 5】为什么参数更新需要高精度 — 小更新被吞掉")
    print("="*70)
    print("说明：模拟一个参数值 1.0，每步更新量很小，对比 float32 和 float16 的行为。")
    
    while True:
        s = input("\n请输入一个更新量（例如 1e-5, 1e-4, 1e-3）: ")
        try:
            update_val = float(s)
        except:
            print("输入无效，请重新输入数字。")
            continue
        
        param_f32 = np.float32(1.0)
        update_f32 = np.float32(update_val)
        new_f32 = param_f32 + update_f32
        
        param_f16 = np.float16(1.0)
        update_f16 = np.float16(update_val)
        new_f16 = param_f16 + update_f16
        
        print(f"\n更新量 = {update_val}")
        print(f"float32 下: 1.0 + {update_val} = {new_f32:.10f}  → {'更新成功' if new_f32 != 1.0 else '未变化'}")
        print(f"float16 下: 1.0 + {update_val} = {new_f16:.10f}  → {'更新成功' if new_f16 != 1.0 else '被吞掉了'}")
        
        eps_f16 = np.finfo(np.float16).resolution
        print(f"\nfloat16 的有效十进制位数约 3~4 位，它能分辨的最小相对变化约 {eps_f16:.2e}")
        print("小于此阈值的变化会被舍入为 0。")
        print("\n【混合精度训练的思想】前向/反向用低精度（快省显存），")
        print("  但参数更新用 FP32 副本，保证小更新不被丢失。")
        
        action = prompt_continue("实验5")
        if action == 'next':
            break

# ==================== 主入口 ====================
def main():
    print("\n" + "="*70)
    print("           浮点数探索实验室 — IEEE 754 直观演示")
    print("="*70)
    print("本程序会带你做 5 个实验。每个实验内你可以反复输入不同数值，")
    print("观察输出变化。实验结束后按 Enter 重试本实验，输入 n 进入下一步，")
    print("输入 q 退出程序。\n")
    
    experiment1()
    experiment2()
    experiment3()
    experiment4()
    experiment5()
    
    print("\n" + "="*70)
    print("所有实验结束。感谢探索！你可以再次运行本程序，尝试更多数值。")
    print("="*70)

if __name__ == "__main__":
    main()
