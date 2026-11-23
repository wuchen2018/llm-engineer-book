"""
文件名: qkv_attention_demo.py
功能: 完整演示Q、K、V投影如何改变注意力打分，以及缩放因子的关键作用

【这是什么？】
这段代码用一个四词句子手算 Q、K、V 投影之后的注意力过程。
它会展示原始点积、QK 投影后的分数矩阵、Value 如何参与加权求和，
以及为什么缩放因子能防止 Softmax 过早变成“赢家通吃”。

【怎么用？】
直接运行即可。程序会逐步打印每一步的计算过程，并在脚本同目录生成两张对比图。
最值得尝试：把 W_Q 改成和 W_K 相同，观察分数矩阵是否变成对称矩阵。
另一个值得尝试的操作是把 W_V 改成单位矩阵，对比“苹果”最终的新向量发生了什么变化。

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

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


if sys.platform == "win32":
    matplotlib.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "SimSun"]
elif sys.platform == "darwin":
    matplotlib.rcParams["font.sans-serif"] = ["Arial Unicode MS", "PingFang SC"]
else:
    matplotlib.rcParams["font.sans-serif"] = ["WenQuanYi Micro Hei", "Noto Sans CJK SC"]
matplotlib.rcParams["axes.unicode_minus"] = False


EMBEDDINGS = {
    "我": np.array([0.0, 1.0]),
    "喜欢": np.array([1.0, 0.0]),
    "吃": np.array([1.0, 2.0]),
    "苹果": np.array([1.0, 1.0]),
}

W_Q = np.array([[1.0, 1.0], [0.0, 1.0]])
W_K = np.array([[1.0, 0.0], [1.0, 1.0]])
W_V = np.array([[1.0, -1.0], [0.0, 1.0]])

SCALE_DEMO_SCORES = np.array([10.0, 3.0, 2.0])
SCALE_DEMO_DK = 64


def softmax(x):
    shifted = x - np.max(x)
    exp_vals = np.exp(shifted)
    return exp_vals / exp_vals.sum()


def section(title):
    print(f"\n{'=' * 62}")
    print(f"  {title}")
    print(f"{'=' * 62}\n")


def print_matrix(title, words, matrix):
    print(f"{title}\n")
    header = "        " + "".join(f"{w:>8s}" for w in words)
    print(header)
    for i, w in enumerate(words):
        row = "".join(f"{matrix[i][j]:8.1f}" for j in range(len(words)))
        print(f"  {w:4s} |{row}")


def draw_score_comparison(words, direct_scores, qk_scores, apple_i, output_dir):
    blue = "#1F77B4"
    blue_dim = (0.122, 0.467, 0.706, 0.3)
    x = np.arange(len(words))
    colors = [blue if w == "吃" else blue_dim for w in words]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.2), sharey=True)
    ax1.bar(x, direct_scores[apple_i], width=0.55, color=colors, edgecolor="black", linewidth=0.5)
    ax1.set_title("直接点积打分", fontsize=11)
    ax1.set_xticks(x)
    ax1.set_xticklabels(words, fontsize=10)
    ax1.set_ylabel("分数", fontsize=10)
    ax1.set_ylim(0, max(qk_scores[apple_i]) * 1.2)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    for i, value in enumerate(direct_scores[apple_i]):
        ax1.text(i, value + 0.15, f"{value:.0f}", ha="center", fontsize=9)

    ax2.bar(x, qk_scores[apple_i], width=0.55, color=colors, edgecolor="black", linewidth=0.5)
    ax2.set_title("QKV投影后打分", fontsize=11)
    ax2.set_xticks(x)
    ax2.set_xticklabels(words, fontsize=10)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    for i, value in enumerate(qk_scores[apple_i]):
        ax2.text(i, value + 0.15, f"{value:.0f}", ha="center", fontsize=9)

    fig.suptitle("“苹果”对各词的注意力分数对比", fontsize=12, y=1.02)
    fig.tight_layout()
    out = output_dir / "qkv_score_comparison.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\n[图1已保存: {out}]")


def draw_scaling_comparison(weights_no_scale, weights_scaled, dk, output_dir):
    blue = "#1F77B4"
    blue_dim = (0.122, 0.467, 0.706, 0.3)
    blue_mid = (0.122, 0.467, 0.706, 0.6)
    labels = ["词1", "词2", "词3"]
    x = np.arange(len(labels))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.2), sharey=True)
    ax1.bar(x, weights_no_scale, width=0.5, color=[blue, blue_dim, blue_dim], edgecolor="black", linewidth=0.5)
    ax1.set_title("不缩放", fontsize=11)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=10)
    ax1.set_ylabel("注意力权重", fontsize=10)
    ax1.set_ylim(0, 1.12)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    for i, value in enumerate(weights_no_scale):
        ax1.text(i, value + 0.02, f"{value:.3f}", ha="center", fontsize=9)

    ax2.bar(x, weights_scaled, width=0.5, color=[blue, blue_mid, blue_mid], edgecolor="black", linewidth=0.5)
    ax2.set_title(f"除以 √{dk} 后", fontsize=11)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=10)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    for i, value in enumerate(weights_scaled):
        ax2.text(i, value + 0.02, f"{value:.2f}", ha="center", fontsize=9)

    fig.suptitle("Softmax缩放效果对比", fontsize=12, y=1.02)
    fig.tight_layout()
    out = output_dir / "qkv_scaling_comparison.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[图2已保存: {out}]")


def main():
    output_dir = Path(__file__).resolve().parent
    words = list(EMBEDDINGS.keys())
    vecs = np.array([EMBEDDINGS[w] for w in words])

    section("第一部分：直接用原始向量做点积打分")
    print("各词的Embedding向量:")
    for word in words:
        print(f"  {word:4s} -> {EMBEDDINGS[word].tolist()}")

    direct_scores = vecs @ vecs.T
    print_matrix("直接点积分数矩阵（每一行 = 这个词对所有词的打分）:", words, direct_scores)

    apple_i = words.index("苹果")
    chi_i = words.index("吃")
    wo_i = words.index("我")
    xihuan_i = words.index("喜欢")

    print('\n以“苹果”的视角看（最后一行）:')
    for j, word in enumerate(words):
        print(f"  苹果->{word}: {direct_scores[apple_i][j]:.0f}")
    print(f"  最高分给了: “{words[np.argmax(direct_scores[apple_i])]}”")

    print("\n两个值得注意的问题:")
    print(f"  ① “我”->“喜欢” = {direct_scores[wo_i][xihuan_i]:.0f} 分")
    print("     明明是紧密的主谓结构，分数却是0（两个向量恰好垂直）")
    print(
        f"  ② “吃”->“吃”自己 = {direct_scores[chi_i][chi_i]:.0f} 分 > "
        f"“吃”->“苹果” = {direct_scores[chi_i][apple_i]:.0f} 分"
    )
    print("     “吃”最关注的不是宾语，而是自己")

    section("第二部分：Q、K、V 投影 —— 同一个词的三副面孔")
    print("三个投影矩阵:")
    print(f"  W_Q = {W_Q.tolist()}")
    print(f"  W_K = {W_K.tolist()}")
    print(f"  W_V = {W_V.tolist()}")

    Q = vecs @ W_Q
    K = vecs @ W_K
    V = vecs @ W_V

    print("\n投影结果:\n")
    print(f"  {'词':4s}   {'原始':>10s}  ->  {'Query':>10s}  {'Key':>10s}  {'Value':>10s}")
    print(f"  {'-' * 50}")
    for i, word in enumerate(words):
        print(
            f"  {word:4s}   {str(vecs[i].tolist()):>10s}  ->  "
            f"{str(Q[i].tolist()):>10s}  {str(K[i].tolist()):>10s}  {str(V[i].tolist()):>10s}"
        )

    print(f'\n同一个原始向量，乘以三个不同矩阵，变成了三个不同向量。')
    print(f'以“苹果”为例，原始向量 {vecs[apple_i].tolist()} 变成:')
    print(f"  Query（在找什么）:       {Q[apple_i].tolist()}")
    print(f"  Key  （能提供什么）:     {K[apple_i].tolist()}")
    print(f"  Value（被选中后给什么）: {V[apple_i].tolist()}")

    section("第三部分：用Query和Key重新打分")
    qk_scores = Q @ K.T
    print_matrix("QK分数矩阵（行=Query，列=Key）:", words, qk_scores)

    print('\n以“苹果”的视角看（最后一行）:')
    for j, word in enumerate(words):
        print(f"  苹果->{word}: {qk_scores[apple_i][j]:.0f}")
    print(f"  最高分给了: “{words[np.argmax(qk_scores[apple_i])]}”")

    direct_gap = direct_scores[apple_i][chi_i] - sorted(direct_scores[apple_i])[-2]
    qk_gap = qk_scores[apple_i][chi_i] - sorted(qk_scores[apple_i])[-2]
    print(f"\n{'-' * 50}")
    print("【核心对比】苹果对“吃”的分数:")
    print(f"  直接点积:  {direct_scores[apple_i][chi_i]:.0f} 分（领先第二名 {direct_gap:.0f} 分）")
    print(f"  QKV投影后: {qk_scores[apple_i][chi_i]:.0f} 分（领先第二名 {qk_gap:.0f} 分）")
    print("  -> 投影把“吃”的优势从微弱领先变成了遥遥领先")
    print(f"{'-' * 50}")

    is_sym = np.allclose(qk_scores, qk_scores.T)
    print(f"\nQK分数矩阵是否对称？ {'是' if is_sym else '不是'}")
    if not is_sym:
        print(f"  苹果->吃 = {qk_scores[apple_i][chi_i]:.0f}，吃->苹果 = {qk_scores[chi_i][apple_i]:.0f}")
        print("  注意力有方向性：“我关注你”不等于“你关注我”")
    else:
        print("  当前 W_Q == W_K，分数矩阵是对称的，注意力失去了方向性。")

    section("第四部分：苹果的完整注意力计算")
    d_k = Q.shape[1]
    raw = qk_scores[apple_i]
    scaled = raw / np.sqrt(d_k)
    attn_w = softmax(scaled)
    new_apple = attn_w @ V

    print(f"d_k = {d_k}，sqrt(d_k) = {np.sqrt(d_k):.4f}\n")
    print(f"步骤1 — QK点积原始分数: {raw.tolist()}")
    print(f"步骤2 — 除以sqrt({d_k}): [{', '.join(f'{s:.2f}' for s in scaled)}]")
    print(f"步骤3 — Softmax归一化: [{', '.join(f'{w:.2f}' for w in attn_w)}]  (和={attn_w.sum():.2f})")

    print("\n各词的注意力权重和Value向量:")
    for i, word in enumerate(words):
        print(f"  {word}: 权重={attn_w[i]:.2f}, Value={V[i].tolist()}")

    print("\n步骤4 — 用权重对Value加权求和:")
    for i, word in enumerate(words):
        contrib = attn_w[i] * V[i]
        print(f"  {attn_w[i]:.2f} x {str(V[i].tolist()):>10s} = [{', '.join(f'{c:.2f}' for c in contrib)}]")

    print(f"\n苹果的新向量 = [{', '.join(f'{value:.2f}' for value in new_apple)}]")
    print(f'“吃”以 {attn_w[chi_i] * 100:.0f}% 的权重主导了加权求和。')

    section("第五部分：缩放因子的威力（高维场景）")
    scores = SCALE_DEMO_SCORES
    dk = SCALE_DEMO_DK
    weights_no_scale = softmax(scores)
    factor = np.sqrt(dk)
    scaled_scores = scores / factor
    weights_scaled = softmax(scaled_scores)

    print(f"模拟场景: d_k = {dk}，三个词的原始QK分数 = {scores.tolist()}\n")
    print("【不缩放】直接对原始分数做Softmax:")
    print(f"  权重: [{', '.join(f'{w:.4f}' for w in weights_no_scale)}]")
    print(f"  -> 第一个词独占 {weights_no_scale[0] * 100:.1f}% 的权重\n")

    print(f"【除以 sqrt({dk}) = {factor:.0f}】缩放后再做Softmax:")
    print(f"  缩放后分数: [{', '.join(f'{s:.3f}' for s in scaled_scores)}]")
    print(f"  权重: [{', '.join(f'{w:.2f}' for w in weights_scaled)}]")
    print(f"  -> 第一个词仍然最高（{weights_scaled[0] * 100:.0f}%），但其他词也有可观权重")

    print('\n--- 额外实验：不同d_k下“词1”拿到的权重 ---')
    for test_dk in [4, 16, 64, 128, 256]:
        test_weights = softmax(scores / np.sqrt(test_dk))
        bar = "█" * int(test_weights[0] * 40)
        print(f"  d_k={test_dk:>4d}  ->  词1权重={test_weights[0]:.4f}  {bar}")

    draw_score_comparison(words, direct_scores, qk_scores, apple_i, output_dir)
    draw_scaling_comparison(weights_no_scale, weights_scaled, dk, output_dir)


if __name__ == "__main__":
    main()
