"""
文件名: lora_core_demo.py
功能: 用几个可观察的小实验理解 LoRA 的低秩分解、前向传播和参数量压缩。

【这是什么？】
这段代码用 numpy 构造几个小矩阵实验，展示 LoRA 为什么能用低秩矩阵近似权重更新、
前向传播里 LoRA 分支如何和原模型分支相加，以及不同 rank 会带来多少参数量差异。

【怎么用？】
直接运行即可。脚本会打印每个实验的中间结果，并在脚本同目录保存多张 PNG 图。
你可以修改 RANK_LIST、LORA_R、DIM_RANGE 等参数，观察图像和参数量如何变化。

【运行条件】
- 是否需要 GPU：不需要。
- 是否需要联网：不需要。
- 是否下载模型：不会下载模型。
- 预计耗时：几秒钟。

【额外安装】
pip install numpy matplotlib
"""

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


OUTPUT_DIR = Path(__file__).resolve().parent
np.random.seed(42)

MATRIX_SIZE = 8
RANK_LIST = [1, 2, 4, 8]
ORIGINAL_DIM = 64
TRUE_RANK = 4
APPROX_RANK_LIST = [1, 2, 4, 8, 16]
D_IN = 6
D_OUT = 6
LORA_R = 2
DIM_RANGE = [512, 1024, 2048, 4096, 8192]
R_VALUES = [4, 8, 16, 32, 64]


def save(name):
    path = OUTPUT_DIR / name
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"已保存: {path}")


def experiment_rank_visualization():
    print("=" * 60)
    print("实验1：不同秩的矩阵长什么样")
    print("=" * 60)

    fig, axes = plt.subplots(1, len(RANK_LIST), figsize=(12, 3))
    fig.suptitle("Matrices of Different Ranks", fontsize=12, y=1.02)

    for idx, rank in enumerate(RANK_LIST):
        left = np.random.randn(MATRIX_SIZE, rank)
        right = np.random.randn(rank, MATRIX_SIZE)
        matrix = left @ right

        ax = axes[idx]
        im = ax.imshow(matrix, cmap="coolwarm", aspect="equal", vmin=-5, vmax=5)
        ax.set_title(f"rank = {rank}", fontsize=10)
        ax.set_xticks([])
        ax.set_yticks([])

        actual_rank = np.linalg.matrix_rank(matrix, tol=1e-6)
        print(
            f"设定秩 {rank}, 实际计算秩 {actual_rank}, "
            f"矩阵形状 {matrix.shape}, 参数量 {matrix.size}"
        )

    fig.colorbar(im, ax=axes, shrink=0.8, label="value")
    save("exp1_rank_visualization.png")


def experiment_low_rank_approximation():
    print("=" * 60)
    print(f"实验2：低秩分解的还原精度，真实秩={TRUE_RANK}")
    print("=" * 60)

    true_b = np.random.randn(ORIGINAL_DIM, TRUE_RANK)
    true_a = np.random.randn(TRUE_RANK, ORIGINAL_DIM)
    delta_w = true_b @ true_a
    print(f"原始 Delta W 参数量: {delta_w.size}")

    errors = []
    param_counts = []
    for r in APPROX_RANK_LIST:
        u, s, vt = np.linalg.svd(delta_w, full_matrices=False)
        b_approx = u[:, :r] * s[:r]
        a_approx = vt[:r, :]
        reconstructed = b_approx @ a_approx

        error = np.linalg.norm(delta_w - reconstructed) / np.linalg.norm(delta_w)
        param_count = ORIGINAL_DIM * r + r * ORIGINAL_DIM
        errors.append(error)
        param_counts.append(param_count)
        print(
            f"r={r:>2d} | B+A 参数量 {param_count:>6d} "
            f"({param_count / delta_w.size * 100:.1f}%) | 还原误差 {error:.6f}"
        )

    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(APPROX_RANK_LIST, errors, "o-", color="#1F77B4", linewidth=1.5)
    ax1.set_xlabel("Approximation Rank (r)")
    ax1.set_ylabel("Relative Error", color="#1F77B4")
    ax1.tick_params(axis="y", labelcolor="#1F77B4")
    ax1.set_xticks(APPROX_RANK_LIST)
    ax1.axvline(x=TRUE_RANK, color="gray", linestyle="--", linewidth=0.8)

    ax2 = ax1.twinx()
    compression = [p / delta_w.size * 100 for p in param_counts]
    ax2.bar(APPROX_RANK_LIST, compression, width=1.5, alpha=0.2, color="#1F77B4")
    ax2.set_ylabel("Parameters (% of original)", color="gray")
    ax2.tick_params(axis="y", labelcolor="gray")

    fig.suptitle("Low-Rank Approximation: Error vs. Rank", fontsize=12)
    save("exp2_low_rank_approximation.png")


def experiment_lora_forward():
    print("=" * 60)
    print(f"实验3：LoRA 前向传播模拟，d_in={D_IN}, d_out={D_OUT}, r={LORA_R}")
    print("=" * 60)

    w = np.random.randn(D_OUT, D_IN) * 0.5
    x = np.random.randn(D_IN)
    h_original = w @ x
    print(f"原始输出 Wx: {np.round(h_original, 4)}")

    a_lora = np.random.randn(LORA_R, D_IN) * 0.01
    b_zero = np.zeros((D_OUT, LORA_R))
    bypass_zero = b_zero @ (a_lora @ x)
    h_with_zero_b = h_original + bypass_zero
    print(f"B=0 的旁路输出: {np.round(bypass_zero, 4)}")
    print(f"B=0 时的最终输出: {np.round(h_with_zero_b, 4)}")

    b_random = np.random.randn(D_OUT, LORA_R) * 0.01
    bypass_random = b_random @ (a_lora @ x)
    h_with_random_b = h_original + bypass_random
    print(f"B=随机的旁路输出: {np.round(bypass_random, 4)}")
    print(f"B=随机时的最终输出: {np.round(h_with_random_b, 4)}")

    b_trained = np.random.randn(D_OUT, LORA_R) * 0.1
    bypass_trained = b_trained @ (a_lora @ x)
    h_trained = h_original + bypass_trained
    print(f"训练后的旁路输出: {np.round(bypass_trained, 4)}")
    print(f"训练后的最终输出: {np.round(h_trained, 4)}")

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))
    titles = ["Original Output", "B=0", "B=random"]
    outputs = [h_original, h_with_zero_b, h_with_random_b]
    colors = ["#333333", "#1F77B4", "#D62728"]

    for ax, title, output, color in zip(axes, titles, outputs, colors):
        ax.bar(range(D_OUT), output, color=color, alpha=0.7, width=0.6)
        if title != titles[0]:
            ax.bar(
                range(D_OUT),
                h_original,
                color="none",
                edgecolor="#333333",
                linewidth=0.8,
                linestyle="--",
                width=0.6,
                label="original",
            )
            ax.legend(fontsize=7, loc="upper right")
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("dimension", fontsize=8)
        ax.set_ylabel("value", fontsize=8)
        ax.set_xticks(range(D_OUT))

    plt.suptitle("LoRA Forward Pass: Effect of B Initialization", fontsize=11, y=1.02)
    save("exp3_lora_initialization.png")


def experiment_compression_ratio():
    print("=" * 60)
    print("实验4：参数压缩比")
    print("=" * 60)

    print(f"{'维度d':>8s}", end="")
    for r in R_VALUES:
        print(f" | r={r:>2d}", end="")
    print(f" | {'全量参数':>10s}")
    print("-" * 70)

    fig, ax = plt.subplots(figsize=(8, 4))
    for d in DIM_RANGE:
        full_params = d * d
        ratios = []
        print(f"{d:>8d}", end="")
        for r in R_VALUES:
            lora_params = d * r + r * d
            ratio = lora_params / full_params * 100
            ratios.append(ratio)
            print(f" | {ratio:>5.2f}%", end="")
        print(f" | {full_params:>10,d}")
        ax.plot(R_VALUES, ratios, "o-", linewidth=1, markersize=4, label=f"d = {d}")

    ax.set_xlabel("LoRA Rank (r)")
    ax.set_ylabel("LoRA Params / Full Params (%)")
    ax.set_title("Parameter Compression Ratio")
    ax.set_xticks(R_VALUES)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, linestyle=":")
    ax.axhline(y=1.0, color="gray", linestyle="--", linewidth=0.8, alpha=0.7)
    ax.text(R_VALUES[-1] + 2, 1.0, "1%", fontsize=8, color="gray", va="center")
    save("exp4_compression_ratio.png")


if __name__ == "__main__":
    experiment_rank_visualization()
    experiment_low_rank_approximation()
    experiment_lora_forward()
    experiment_compression_ratio()
    print("=" * 60)
    print("全部实验完成。")
