# Git 从零入门｜跟着视频敲一遍

我是武辰。这页用的还是视频里的两个例子：把我的概率论仓库下载到电脑，再给自己的 `test.txt` 存两版。命令可以在 Windows 的 Git Bash 里运行。

## 把仓库下载到电脑

打开 Git Bash，先进入你想放项目的位置，然后运行下面三行。

```bash
git clone https://github.com/wuchen2018/probability-book.git
cd probability-book
git status
```

第一行会新建一个 `probability-book` 文件夹。资源管理器里点开它以后，Git Bash 的位置还在原地，所以第二行要单独敲。看到 `working tree clean`，意思是你现在没有尚未提交的改动。以后远端有新提交，进入同一个文件夹后运行 `git pull`。

## 把自己的改动推上 GitHub

先在 GitHub 建一个自己的空仓库，名字叫 `git-practice`，创建时先跳过 README 等初始化选项。接下来回到 Git Bash，在你放练习文件的位置运行下列命令。把网址里的 `YOUR-NAME` 换成你自己的 GitHub 用户名。

```bash
mkdir git-practice
cd git-practice
git init -b main
echo '1+1=3' > test.txt
git status
git add test.txt
git commit -m "Save the first version"
git remote add origin https://github.com/YOUR-NAME/git-practice.git
git push -u origin main
```

`add` 选出这次要保存的改动，`commit` 在本地保存一版，`push` 才把这版传上去。`origin` 是你给远端仓库起的名字。`-u` 会记住本地这条分支对应哪个远端分支，以后在 `main` 上直接敲 `git push` 就行。

如果第一次 `commit` 提示没配置名字和邮箱，在这个练习目录执行下面两行，把示例值换成自己的提交署名和邮箱，再重试 `commit`。

```bash
git config user.name "Your Name"
git config user.email "you@example.com"
```

## 看看以前写的是什么

还在 `git-practice` 里。把刚才的 `1+1=3` 改成 `1+1=2`，再存一版。

```bash
echo '1+1=2' > test.txt
git add test.txt
git commit -m "Change the answer to 2"
git log --oneline
```

从日志里找到 `Save the first version` 那一行，复制行首的提交编号。把下面的 `COMMIT_ID` 换成这个编号，就能看到旧版文件。看完用最后两行回到 `main`，确认文件里又是 `1+1=2`。

```bash
git checkout COMMIT_ID
cat test.txt
git switch main
cat test.txt
```

想接着学分支、合并冲突和 `.gitignore`，可以看《一个大模型工程师的诞生》第 1.7 节的[完整 Git 生存手册（PDF）](../../samples/git-handbook.pdf)。
