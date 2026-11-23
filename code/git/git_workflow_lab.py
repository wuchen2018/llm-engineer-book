"""
文件名: git_workflow_lab.py
功能: 自动编排一套完整的 Git 操作流程，在终端里逐步演示并解说每一步的效果

【这是什么？】
这个脚本会在你的机器上创建一个临时文件夹，然后自动执行一连串 Git 操作：
初始化仓库、添加文件、提交快照、查看历史、创建分支、制造合并冲突并手动解决、
以及演示 .gitignore 的行为。每一步操作前会打印解说，操作后展示 Git 的真实输出。

【怎么用？】
确保你的机器上已安装 Git（终端里敲 git --version 能看到版本号即可）。
直接运行: python git_workflow_lab.py
脚本会在临时目录中完成所有操作，不会影响你电脑上的任何文件。
运行结束后会打印临时仓库的路径，你可以 cd 进去自己用 git log 等命令探索。

【运行条件】
不需要真实模型，不需要联网，不需要下载数据集，也不需要GPU。需要本机已经安装 Git。
脚本会创建一个临时实验仓库，并在结束后保留这个目录，方便你继续探索；不需要时手动删除即可。
"""

import subprocess
import os
import sys
import tempfile
import shutil
import textwrap

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# --- 可调整参数配置区 ---
# 实验仓库的位置。设为 None 使用系统临时目录，也可以改成你想要的路径
# 例如: CUSTOM_WORK_DIR = "/home/yourname/git-lab"
CUSTOM_WORK_DIR = None

# 模拟的 Git 用户名和邮箱（仅在本次实验仓库内生效，不影响你的全局 Git 配置）
GIT_USER_NAME = "Lab User"
GIT_USER_EMAIL = "lab@example.com"


# ============================================================
# 工具函数（不需要阅读，直接跳到下面的实验步骤）
# ============================================================

# 实验仓库的工作目录，后面会在 main 里赋值
REPO_DIR = ""

# 步骤计数器
_step_counter = 0


def banner(title):
    """打印一个醒目的步骤标题，方便在终端输出中定位每一步"""
    global _step_counter
    _step_counter += 1
    width = 60
    print("\n" + "=" * width)
    print(f"  步骤 {_step_counter}: {title}")
    print("=" * width)


def explain(text):
    """打印解说文字，帮助理解接下来要做什么、为什么这么做"""
    wrapped = textwrap.fill(text, width=70, initial_indent="  💡 ", subsequent_indent="     ")
    print(wrapped)


def run_git(*args, check=True, capture=False):
    """在实验仓库中执行一条 git 命令，并打印命令本身和输出结果"""
    cmd = ["git"] + list(args)
    cmd_str = " ".join(cmd)
    print(f"\n  $ {cmd_str}")
    print("  " + "-" * 40)

    result = subprocess.run(
        cmd,
        cwd=REPO_DIR,
        capture_output=True,
        text=True,
        # 有些 git 命令在特定情况下会返回非零退出码（如 diff 发现有差异时），
        # 这不是报错，所以这里不总是 check=True
    )
    output = result.stdout.strip()
    err_output = result.stderr.strip()

    # git 的很多正常信息（如 init、checkout 的提示）走的是 stderr 而非 stdout，
    # 这是 git 的设计，不代表出错了
    display = output if output else err_output
    if display:
        for line in display.split("\n"):
            print(f"  {line}")
    else:
        print("  (无输出)")

    if check and result.returncode != 0 and not output:
        print(f"  ⚠️  命令返回了非零状态码: {result.returncode}")

    return result


def write_file(filename, content):
    """在实验仓库中创建或覆盖一个文件"""
    filepath = os.path.join(REPO_DIR, filename)
    # 如果文件在子目录里，先确保目录存在
    os.makedirs(os.path.dirname(filepath), exist_ok=True) if os.path.dirname(filepath) else None
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def read_file(filename):
    """读取实验仓库中某个文件的内容并打印"""
    filepath = os.path.join(REPO_DIR, filename)
    print(f"\n  📄 文件内容 [{filename}]:")
    print("  " + "-" * 40)
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            print(f"  {line}", end="")
    print()


def show_file_list():
    """展示当前仓库里有哪些文件（不含 .git 目录）"""
    print("\n  📁 当前文件列表:")
    for root, dirs, files in os.walk(REPO_DIR):
        # 跳过 .git 目录内部
        dirs[:] = [d for d in dirs if d != ".git"]
        level = root.replace(REPO_DIR, "").count(os.sep)
        indent = "     " + "  " * level
        if root != REPO_DIR:
            print(f"{indent}{os.path.basename(root)}/")
        for f in files:
            print(f"{indent}  {f}")


def pause():
    """在关键步骤之间暂停，让读者有时间消化输出"""
    print("\n  ⏸  按 Enter 继续下一步...")
    try:
        input()
    except EOFError:
        # 如果是在非交互环境中运行（如 CI），直接跳过
        pass


# ============================================================
# 正式实验开始
# ============================================================

def main():
    global REPO_DIR

    # 创建实验用的临时目录
    if CUSTOM_WORK_DIR:
        REPO_DIR = CUSTOM_WORK_DIR
        os.makedirs(REPO_DIR, exist_ok=True)
    else:
        REPO_DIR = tempfile.mkdtemp(prefix="git_lab_")

    print("🔬 Git 实战实验室")
    print(f"   实验仓库位置: {REPO_DIR}")
    print("   实验结束后你可以 cd 进去自己探索。")
    print("   每个步骤之间会暂停，按 Enter 继续。")

    # ----------------------------------------------------------
    # 第一部分：最基本的 init / add / commit 流程
    # ----------------------------------------------------------

    banner("初始化一个 Git 仓库")
    explain(
        "git init 会在当前文件夹里创建一个隐藏的 .git 目录，"
        "从这一刻起，Git 开始追踪这个文件夹里的变化。"
    )
    run_git("init", "-b", "main")

    # 在仓库内部设置用户名和邮箱，这样实验不会污染你的全局配置
    run_git("config", "user.name", GIT_USER_NAME)
    run_git("config", "user.email", GIT_USER_EMAIL)

    pause()

    # ----------------------------------------------------------
    banner("创建第一个文件，观察 git status 的变化")
    explain(
        "我们创建一个 Python 脚本文件。此时这个文件对 Git 来说是 "
        "'untracked'（未追踪）的——Git 看到了它，但还没开始管理它。"
    )
    write_file("train.py", textwrap.dedent("""\
        import torch

        learning_rate = 1e-4
        batch_size = 32
        epochs = 10

        print(f"lr={learning_rate}, bs={batch_size}, epochs={epochs}")
    """))

    read_file("train.py")
    run_git("status")

    explain(
        "注意看输出里的 'Untracked files' 部分——train.py 显示为红色（如果你的终端支持彩色），"
        "表示它还不在 Git 的管理范围内。"
    )
    pause()

    # ----------------------------------------------------------
    banner("用 git add 将文件放入暂存区")
    explain(
        "git add 的作用是把文件的改动放进'暂存区'，相当于在这个文件上打个勾，"
        "意思是'这个改动我确认了，准备存档'。"
    )
    run_git("add", "train.py")
    run_git("status")

    explain(
        "再看 git status 的输出：train.py 现在出现在 'Changes to be committed' 下面，"
        "如果终端支持彩色，它会变成绿色。这说明它已经进了暂存区，等待提交。"
    )
    pause()

    # ----------------------------------------------------------
    banner("用 git commit 生成第一张快照")
    explain(
        "git commit 会把暂存区里的内容永久保存为一张快照。"
        "-m 后面的引号里是这次提交的说明，写给未来的自己和同事看的。"
    )
    run_git("commit", "-m", "创建训练脚本，设置基本超参数")
    run_git("status")

    explain(
        "提交之后再看 status，会显示 'nothing to commit, working tree clean'。"
        "这意味着工作区的状态和最新的快照完全一致，没有未保存的改动。"
    )
    pause()

    # ----------------------------------------------------------
    banner("修改文件，用 git diff 查看改了什么")
    explain(
        "现在我们修改 train.py，把学习率从 1e-4 改成 5e-5。"
        "改完之后用 git diff 看看 Git 是怎么记录这个变化的。"
    )

    write_file("train.py", textwrap.dedent("""\
        import torch

        learning_rate = 5e-5
        batch_size = 32
        epochs = 10

        print(f"lr={learning_rate}, bs={batch_size}, epochs={epochs}")
    """))

    run_git("diff")

    explain(
        "diff 的输出里，以 - 开头的行是被删掉的旧内容，以 + 开头的行是新加的内容。"
        "你可以清楚地看到 learning_rate 从 1e-4 变成了 5e-5。"
        "这个命令在你提交之前做最后确认时非常有用。"
    )
    pause()

    # ----------------------------------------------------------
    banner("提交这次修改，然后用 git log 查看历史")
    run_git("add", "train.py")
    run_git("commit", "-m", "将学习率从1e-4调整为5e-5")
    run_git("log", "--oneline")

    explain(
        "git log --oneline 用紧凑的格式展示提交历史。"
        "每一行是一次提交：左边那串短字符是这次提交的唯一标识（哈希值的前几位），"
        "右边是你写的提交说明。最新的提交在最上面。"
    )
    pause()

    # ----------------------------------------------------------
    # 第二部分：分支操作
    # ----------------------------------------------------------

    banner("创建并切换到一条实验分支")
    explain(
        "假设你想试一下把 batch_size 从 32 改成 64，但不确定效果好不好。"
        "直接在 main 上改不太安全——万一改坏了不好恢复。"
        "更好的做法是开一条新分支，在上面随便折腾。"
    )

    # git checkout -b 是 "创建并切换" 的快捷写法
    run_git("checkout", "-b", "exp/bs-64")
    run_git("branch")

    explain(
        "git branch 列出所有分支，带 * 号的是你当前所在的分支。"
        "可以看到我们已经站在 exp/bs-64 上了。"
    )
    pause()

    # ----------------------------------------------------------
    banner("在实验分支上修改并提交")
    explain(
        "现在我们在实验分支上把 batch_size 改成 64，然后提交。"
        "这个改动只属于 exp/bs-64 分支，main 分支完全不受影响。"
    )

    write_file("train.py", textwrap.dedent("""\
        import torch

        learning_rate = 5e-5
        batch_size = 64
        epochs = 10

        print(f"lr={learning_rate}, bs={batch_size}, epochs={epochs}")
    """))

    run_git("add", "train.py")
    run_git("commit", "-m", "实验：将batch_size从32增大到64")
    pause()

    # ----------------------------------------------------------
    banner("切回 main 分支，观察文件内容的变化")
    explain(
        "现在切回 main 分支，然后看 train.py 的内容。"
        "你会发现 batch_size 还是 32——因为刚才的修改只在 exp/bs-64 分支上。"
        "这就是分支'互不干扰'的效果。"
    )

    run_git("checkout", "main")
    read_file("train.py")

    explain(
        "看到了吗？batch_size 仍然是 32。"
        "你在实验分支上做的所有改动，main 分支上一行都看不到。"
    )
    pause()

    # ----------------------------------------------------------
    banner("合并实验分支到 main（无冲突的情况）")
    explain(
        "假设你对 batch_size=64 的实验效果很满意，想把这个改动正式纳入 main 分支。"
        "用 git merge 把实验分支的改动合并过来。"
    )

    run_git("merge", "exp/bs-64")
    read_file("train.py")

    explain(
        "合并成功后，main 分支上的 train.py 里 batch_size 也变成 64 了。"
        "这次合并很顺利，因为 main 分支上没有人改过同一个文件。"
        "下一步我们来看不那么顺利的情况——合并冲突。"
    )
    pause()

    # ----------------------------------------------------------
    # 第三部分：合并冲突的制造与解决
    # ----------------------------------------------------------

    banner("制造一次合并冲突（两个分支改了同一行）")
    explain(
        "现在我们故意制造一个冲突：在 main 上把 epochs 改成 20，"
        "同时创建另一条分支把 epochs 改成 5。"
        "当两条分支修改了同一个文件的同一个位置时，Git 无法自动决定该保留谁的版本。"
    )

    # 先在 main 上修改 epochs 为 20 并提交
    write_file("train.py", textwrap.dedent("""\
        import torch

        learning_rate = 5e-5
        batch_size = 64
        epochs = 20

        print(f"lr={learning_rate}, bs={batch_size}, epochs={epochs}")
    """))
    run_git("add", "train.py")
    run_git("commit", "-m", "main分支：将epochs增加到20")

    # 创建一条新分支（从 main 的上一次提交分叉）
    # 先回退到合并后、修改 epochs 之前的那个状态来创建分支
    # 更简单的做法：直接创建分支然后在上面做不同的修改
    run_git("checkout", "-b", "exp/fewer-epochs", "HEAD~1")

    write_file("train.py", textwrap.dedent("""\
        import torch

        learning_rate = 5e-5
        batch_size = 64
        epochs = 5

        print(f"lr={learning_rate}, bs={batch_size}, epochs={epochs}")
    """))
    run_git("add", "train.py")
    run_git("commit", "-m", "实验分支：将epochs减少到5看看效果")

    explain(
        "现在 main 上 epochs=20，exp/fewer-epochs 上 epochs=5。"
        "两条分支改了同一个文件的同一行。接下来切回 main 并尝试合并。"
    )
    pause()

    # ----------------------------------------------------------
    banner("尝试合并——观察冲突的样子")

    run_git("checkout", "main")

    # merge 会返回非零退出码（因为有冲突），这不是报错
    result = run_git("merge", "exp/fewer-epochs", check=False)

    explain(
        "Git 告诉你合并失败了——出现了冲突（CONFLICT）。"
        "别慌，我们来看看冲突在文件里长什么样。"
    )

    read_file("train.py")

    explain(
        "看到文件里的 <<<<<<< HEAD 和 >>>>>>> 标记了吗？"
        "<<<<<<< HEAD 到 ======= 之间是 main 分支的版本（epochs = 20）。"
        "======= 到 >>>>>>> 之间是要合并进来的分支的版本（epochs = 5）。"
        "Git 在说：'这个地方我不知道该保留谁的，你来决定。'"
    )
    pause()

    # ----------------------------------------------------------
    banner("手动解决冲突")
    explain(
        "解决冲突的方法很机械：打开文件，删掉所有冲突标记（<<<、===、>>>），"
        "只保留你最终想要的内容。假设你决定用 epochs=15 作为折中方案。"
    )

    # 模拟手动解决冲突：写入最终想要的版本
    write_file("train.py", textwrap.dedent("""\
        import torch

        learning_rate = 5e-5
        batch_size = 64
        epochs = 15

        print(f"lr={learning_rate}, bs={batch_size}, epochs={epochs}")
    """))

    read_file("train.py")
    explain("冲突标记已经被删除，文件内容是我们想要的最终版本。")

    run_git("add", "train.py")
    run_git("commit", "-m", "解决epochs冲突：折中选择15")

    run_git("log", "--oneline")

    explain(
        "冲突解决了。在 git log 中可以看到完整的历史："
        "最开始的提交、分支上的实验、以及最后这次解决冲突的合并提交。"
    )
    pause()

    # ----------------------------------------------------------
    # 第四部分：.gitignore 的行为演示
    # ----------------------------------------------------------

    banner("演示 .gitignore 的效果")
    explain(
        "在大模型项目中，有很多文件是不应该被 Git 追踪的："
        "模型权重文件（体积巨大）、Python 缓存、日志文件、密钥等。"
        ".gitignore 文件就是告诉 Git '请假装看不见这些东西'。"
    )

    # 创建一些"不该进仓库"的文件
    write_file("model_weights.pt", "（假装这是一个 2GB 的模型权重文件）")
    write_file("__pycache__/train.cpython-310.pyc", "（Python自动生成的缓存）")
    write_file("logs/train_2024.log", "epoch 1, loss=2.35\nepoch 2, loss=1.98\n")
    write_file(".env", "WANDB_API_KEY=sk-abc123-这是一个不该泄露的密钥")

    explain("我们创建了几个文件：模型权重、Python缓存、日志、密钥文件。"
            "先看看没有 .gitignore 时 git status 会显示什么。")

    run_git("status")

    explain(
        "所有文件都出现在了 'Untracked files' 里。"
        "如果你此时 git add . 然后 commit，这些文件全都会进入仓库——"
        "包括那个写着 API 密钥的 .env 文件。这就是事故的开始。"
        "现在我们创建一个 .gitignore 文件来阻止这件事。"
    )
    pause()

    # ----------------------------------------------------------
    banner("创建 .gitignore 并观察效果")

    gitignore_content = textwrap.dedent("""\
        # 模型权重文件（通常非常大，不应该进入 Git 仓库）
        *.pt
        *.bin
        *.ckpt

        # Python 运行时自动生成的缓存
        __pycache__/
        *.pyc

        # 训练日志（每次运行都会变，没必要追踪）
        logs/

        # 包含密钥、密码等敏感信息的环境变量文件
        .env
    """)

    write_file(".gitignore", gitignore_content)
    read_file(".gitignore")

    run_git("status")

    explain(
        "对比一下前后两次 git status 的输出。"
        "现在只剩下 .gitignore 本身出现在 untracked files 里了。"
        "model_weights.pt、__pycache__、logs/、.env 全部消失了——"
        "Git 真的在'假装看不见'它们。"
        "接下来把 .gitignore 本身提交到仓库（它是项目配置的一部分，"
        "应该和代码一起管理，这样团队所有人都使用同一套忽略规则）。"
    )

    run_git("add", ".gitignore")
    run_git("commit", "-m", "添加.gitignore：忽略模型权重、缓存、日志和密钥文件")

    pause()

    # ----------------------------------------------------------
    banner("验证：git add . 不会把被忽略的文件加进来")
    explain(
        "最后验证一下：即使你用 git add .（添加所有文件），"
        "那些在 .gitignore 里列出的文件也不会被添加到暂存区。"
    )

    run_git("add", ".")
    run_git("status")

    explain(
        "看到了吗？nothing to commit。"
        "那些被忽略的文件安安静静地躺在文件夹里，"
        "但 Git 完全无视它们，不会追踪、不会提交。"
    )

    show_file_list()
    explain(
        "虽然这些文件在文件夹里真实存在（上面的文件列表可以看到），"
        "但 Git 的世界里它们是'隐身'的。"
    )
    pause()

    # ----------------------------------------------------------
    # 实验结束
    # ----------------------------------------------------------

    print("\n" + "=" * 60)
    print("  🎉 实验结束！")
    print("=" * 60)
    print(f"\n  你的实验仓库还在这里: {REPO_DIR}")
    print("  你可以自己 cd 进去继续探索：")
    print("    - git log --oneline --graph --all  (查看完整的分支图)")
    print("    - git branch                       (查看所有分支)")
    print("    - git diff HEAD~1                  (对比最近两次提交)")
    print(f"\n  如果不需要了，直接删除文件夹即可: rm -rf {REPO_DIR}")


if __name__ == "__main__":
    # 先检查 git 是否可用
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True, text=True, check=True
        )
        print(f"✅ 检测到 Git: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ 未检测到 Git。请先安装 Git，然后再运行此脚本。")
        print("   Mac 用户: 打开终端输入 git，系统会提示安装。")
        print("   Linux 用户: sudo apt install git 或 sudo yum install git")
        print("   Windows 用户: 从 https://git-scm.com 下载安装。")
        sys.exit(1)

    main()
