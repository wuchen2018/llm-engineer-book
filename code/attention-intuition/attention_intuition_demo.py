"""
文件名: attention_intuition_demo.py
功能: 可视化自注意力机制的打分与加权平均过程，观察同一个词在不同上下文中如何获得不同的向量表示。

【这是什么？】
这段代码模拟了注意力机制最核心的三步操作：点积打分、Softmax归一化、加权平均。
你可以亲眼看到"苹果"这个词在"我喜欢吃苹果"和"苹果发布新手机"两个语境下，
注意力权重分布完全不同，最终得到的新向量也指向了截然不同的方向。

【怎么用？】
直接运行即可。程序会输出两个语境下的完整计算过程，并在当前运行目录生成 attention_intuition_result.png：
左图和中图分别展示两个句子中"苹果"的注意力权重分布，右图在二维坐标系中画出
"苹果"的原始向量和两个语境下更新后的向量，让你直观看到向量的分叉。
你可以修改下方参数区里的向量数值，观察注意力分布如何随之变化。

【运行条件】
- 是否需要 GPU：不需要。
- 是否需要联网：不需要。
- 是否下载模型：不会下载模型。
- 预计耗时：几秒钟。

【额外安装】
pip install numpy matplotlib
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# --- 可调整参数配置区 ---

# 句子1："我喜欢吃苹果"——四个词的二维向量
# 试试把"吃"的向量改成 [0, 1]（和"苹果"不那么相似），看"吃"的注意力权重会下降多少
SENTENCE_1_WORDS = ["我", "喜欢", "吃", "苹果"]
SENTENCE_1_VECTORS = np.array([
    [0, 1],    # 我
    [1, 0],    # 喜欢
    [1, 2],    # 吃
    [1, 1],    # 苹果
], dtype=float)
SENTENCE_1_TARGET = 3  # 我们关注第几个词（从0开始），3代表"苹果"

# 句子2："苹果发布新手机"——三个词的二维向量
# 试试把"发布"的向量改成 [0.5, 0.5]（和"苹果"更接近），看权重分布会怎么变
SENTENCE_2_WORDS = ["苹果", "发布", "新手机"]
SENTENCE_2_VECTORS = np.array([
    [1, 1],    # 苹果（和句子1中完全相同——这是关键！）
    [2, 1],    # 发布
    [2, 0],    # 新手机
], dtype=float)
SENTENCE_2_TARGET = 0  # 关注第0个词，即"苹果"

# 可视化标题中"苹果"用哪种颜色高亮
FOCUS_COLOR = '#1F77B4'
BASE_COLOR = '#000000'


# ======================================================================
# 核心函数
# ======================================================================

def softmax(scores):
    """
    Softmax函数：把一组任意大小的数字变成一组加起来等于1的正数权重。
    先减去最大值再取指数，是为了防止指数爆炸导致数值溢出——
    这个技巧在损失函数那一节讲过，叫做"平移不变性"。
    """
    shifted = scores - np.max(scores)
    exp_scores = np.exp(shifted)
    return exp_scores / np.sum(exp_scores)


def compute_attention(vectors, target_idx, word_labels):
    """
    对目标词执行一轮完整的注意力计算。

    参数:
        vectors: 所有词的向量矩阵，每一行是一个词的向量
        target_idx: 目标词的索引（我们要为这个词计算新向量）
        word_labels: 每个词的文字标签，用于打印

    返回:
        weights: Softmax之后的注意力权重
        new_vector: 加权平均得到的新向量
    """
    target_vector = vectors[target_idx]
    target_word = word_labels[target_idx]
    n = len(vectors)

    # --- 第一步：打分（点积） ---
    # 目标词和每个词（包括自己）做点积，得到原始分数
    raw_scores = np.array([np.dot(target_vector, vectors[i]) for i in range(n)])

    print(f"\n{'='*50}")
    print(f"目标词：「{target_word}」  向量：{target_vector}")
    print(f"{'='*50}")
    print(f"\n第一步：点积打分")
    for i in range(n):
        dot_detail = " + ".join(
            f"{target_vector[d]:.0f}×{vectors[i][d]:.0f}" for d in range(vectors.shape[1])
        )
        print(f"  「{target_word}」·「{word_labels[i]}」= {dot_detail} = {raw_scores[i]:.1f}")

    # --- 第二步：Softmax归一化 ---
    # 把原始分数变成一组加起来等于1的权重
    weights = softmax(raw_scores)

    print(f"\n第二步：Softmax归一化")
    print(f"  原始分数：{[f'{s:.1f}' for s in raw_scores]}")
    print(f"  注意力权重：{[f'{w:.4f}' for w in weights]}")
    print(f"  权重之和：{np.sum(weights):.4f}（应该等于1）")

    # 找出权重最大的词
    max_idx = np.argmax(weights)
    print(f"  →「{target_word}」最关注的词：「{word_labels[max_idx]}」（权重 {weights[max_idx]:.4f}）")

    # --- 第三步：加权平均 ---
    # 用注意力权重对所有词的向量做加权求和，得到目标词的新向量
    new_vector = np.zeros(vectors.shape[1])
    print(f"\n第三步：加权平均")
    terms = []
    for i in range(n):
        contribution = weights[i] * vectors[i]
        new_vector += contribution
        terms.append(f"{weights[i]:.2f}×{vectors[i]}")
    print(f"  新向量 = {' + '.join(terms)}")
    print(f"         = [{', '.join(f'{v:.4f}' for v in new_vector)}]")

    # --- 对比原始向量和新向量 ---
    print(f"\n对比：")
    print(f"  原始向量：{target_vector}")
    print(f"  新向量：  [{', '.join(f'{v:.4f}' for v in new_vector)}]")
    diff = new_vector - target_vector
    print(f"  变化量：  [{', '.join(f'{v:+.4f}' for v in diff)}]")

    return weights, new_vector


def visualize_comparison(
    words_1, weights_1, words_2, weights_2,
    original_vec, new_vec_1, new_vec_2,
    target_word, label_1, label_2
):
    """
    生成三张子图的对比可视化：
    左图：句子1中目标词的注意力权重分布
    中图：句子2中目标词的注意力权重分布
    右图：二维坐标系中原始向量与两个新向量的分叉
    """

    # 尝试加载中文字体，如果系统没有则回退到默认字体
    chinese_font = None
    for font_name in ['SimSun', 'SimHei', 'STSong', 'Microsoft YaHei',
                       'WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'PingFang SC']:
        try:
            chinese_font = fm.FontProperties(family=font_name, size=9)
            # 测试字体是否真的可用
            fig_test = plt.figure()
            fig_test.text(0.5, 0.5, '测试', fontproperties=chinese_font)
            plt.close(fig_test)
            break
        except:
            chinese_font = None

    if chinese_font is None:
        print("\n[提示] 未找到中文字体，图表中的中文可能显示为方块。")
        print("  如果你在Linux上，可以安装: sudo apt install fonts-wqy-microhei")
        chinese_font = fm.FontProperties(size=9)

    font_small = fm.FontProperties(fname=chinese_font.get_file(), size=8) if chinese_font.get_file() else fm.FontProperties(size=8)

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12, 4))

    # ========== 左图：句子1的注意力权重 ==========
    max_idx_1 = np.argmax(weights_1)
    bars1 = ax1.bar(range(len(words_1)), weights_1, color=FOCUS_COLOR, width=0.55)
    for i, bar in enumerate(bars1):
        bar.set_alpha(1.0 if i == max_idx_1 else 0.3)
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                 f'{weights_1[i]:.2f}', ha='center', va='bottom', fontsize=8)
    ax1.set_xticks(range(len(words_1)))
    ax1.set_xticklabels(words_1, fontproperties=chinese_font)
    ax1.set_title(f'{label_1}', fontproperties=chinese_font, fontsize=10)
    ax1.set_ylabel('注意力权重', fontproperties=chinese_font)
    ax1.set_ylim(0, max(weights_1) + 0.15)

    # ========== 中图：句子2的注意力权重 ==========
    max_idx_2 = np.argmax(weights_2)
    bars2 = ax2.bar(range(len(words_2)), weights_2, color=FOCUS_COLOR, width=0.55)
    for i, bar in enumerate(bars2):
        bar.set_alpha(1.0 if i == max_idx_2 else 0.3)
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                 f'{weights_2[i]:.2f}', ha='center', va='bottom', fontsize=8)
    ax2.set_xticks(range(len(words_2)))
    ax2.set_xticklabels(words_2, fontproperties=chinese_font)
    ax2.set_title(f'{label_2}', fontproperties=chinese_font, fontsize=10)
    ax2.set_ylim(0, max(weights_2) + 0.15)

    # ========== 右图：向量分叉 ==========
    arrow_kw = dict(arrowstyle='->', mutation_scale=12, shrinkA=0, shrinkB=0)

    ax3.annotate('', xy=original_vec, xytext=(0, 0),
                 arrowprops=dict(**arrow_kw, color=BASE_COLOR, lw=1.2))
    ax3.annotate('', xy=new_vec_1, xytext=(0, 0),
                 arrowprops=dict(**arrow_kw, color=FOCUS_COLOR, lw=1.2))
    ax3.annotate('', xy=new_vec_2, xytext=(0, 0),
                 arrowprops=dict(**arrow_kw, color=FOCUS_COLOR, lw=1.2, linestyle='--'))

    ax3.plot(0, 0, 'o', color=BASE_COLOR, markersize=3, zorder=5)

    # 标注坐标
    ax3.annotate(f'[{original_vec[0]:.1f}, {original_vec[1]:.1f}]',
                 xy=original_vec, xytext=(8, -14), textcoords='offset points',
                 fontsize=8, ha='left', color=BASE_COLOR)
    ax3.annotate(f'[{new_vec_1[0]:.2f}, {new_vec_1[1]:.2f}]',
                 xy=new_vec_1, xytext=(-8, 8), textcoords='offset points',
                 fontsize=8, ha='right', color=FOCUS_COLOR)
    ax3.annotate(f'[{new_vec_2[0]:.2f}, {new_vec_2[1]:.2f}]',
                 xy=new_vec_2, xytext=(8, -14), textcoords='offset points',
                 fontsize=8, ha='left', color=FOCUS_COLOR)

    # 图例
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color=BASE_COLOR, lw=1.2, label=f'原始向量'),
        Line2D([0], [0], color=FOCUS_COLOR, lw=1.2, label=label_1),
        Line2D([0], [0], color=FOCUS_COLOR, lw=1.2, linestyle='--', label=label_2),
    ]
    ax3.legend(handles=legend_elements, prop=chinese_font, loc='upper left',
               framealpha=0.9, edgecolor=BASE_COLOR)

    ax3.set_title(f'「{target_word}」的向量分叉', fontproperties=chinese_font, fontsize=10)

    # 坐标轴范围：自动适配所有向量
    all_points = np.array([original_vec, new_vec_1, new_vec_2, [0, 0]])
    x_min, x_max = all_points[:, 0].min() - 0.3, all_points[:, 0].max() + 0.5
    y_min, y_max = all_points[:, 1].min() - 0.3, all_points[:, 1].max() + 0.3
    ax3.set_xlim(x_min, x_max)
    ax3.set_ylim(y_min, y_max)
    ax3.set_aspect('equal')
    ax3.grid(True, alpha=0.3, linestyle=':')

    # 统一清理边框
    for ax in [ax1, ax2, ax3]:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig('attention_intuition_result.png', dpi=150, bbox_inches='tight')
    print(f"\n[可视化已保存为 attention_intuition_result.png]")
    plt.show()


# ======================================================================
# 主程序
# ======================================================================

if __name__ == "__main__":

    print("=" * 60)
    print(f" 语境一：「{''.join(SENTENCE_1_WORDS)}」")
    print("=" * 60)

    target_word = SENTENCE_1_WORDS[SENTENCE_1_TARGET]
    weights_1, new_vec_1 = compute_attention(
        SENTENCE_1_VECTORS, SENTENCE_1_TARGET, SENTENCE_1_WORDS
    )
    original_vec = SENTENCE_1_VECTORS[SENTENCE_1_TARGET].copy()

    print("\n\n")
    print("=" * 60)
    print(f" 语境二：「{''.join(SENTENCE_2_WORDS)}」")
    print("=" * 60)

    weights_2, new_vec_2 = compute_attention(
        SENTENCE_2_VECTORS, SENTENCE_2_TARGET, SENTENCE_2_WORDS
    )

    # --- 最终对比 ---
    print("\n\n")
    print("=" * 60)
    print(f" 最终对比：同一个「{target_word}」在两个语境下的向量")
    print("=" * 60)
    print(f"\n  Embedding原始向量（两个语境完全相同）：{original_vec}")
    print(f"  语境一更新后：[{', '.join(f'{v:.4f}' for v in new_vec_1)}]")
    print(f"  语境二更新后：[{', '.join(f'{v:.4f}' for v in new_vec_2)}]")

    vec_distance = np.linalg.norm(new_vec_1 - new_vec_2)
    print(f"\n  两个新向量之间的距离：{vec_distance:.4f}")
    print(f"  （距离越大，说明两个语境把「{target_word}」拉得越远）")

    # --- 可视化 ---
    visualize_comparison(
        SENTENCE_1_WORDS, weights_1,
        SENTENCE_2_WORDS, weights_2,
        original_vec, new_vec_1, new_vec_2,
        target_word,
        label_1=f"「{''.join(SENTENCE_1_WORDS)}」",
        label_2=f"「{''.join(SENTENCE_2_WORDS)}」"
    )
