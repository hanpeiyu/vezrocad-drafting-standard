# GitHub 仓库初始化与持续迭代

仓库推荐名称：`hanpeiyu/vezrocad-drafting-standard`，**Private（私有）**。本规范单独管理，不直接向现有 VezroCAD 源代码仓库写入。

## 创建仓库并推送

1. 打开 https://github.com/new ；Owner 为 `hanpeiyu`；Repository name 为 `vezrocad-drafting-standard`；Visibility 选 **Private**。
2. 不勾选“Add a README file”“Add .gitignore”“Choose a license”，建立**空仓库**。
3. 将本压缩包解压，打开 `vezrocad-drafting-standard` 文件夹；Git for Windows 已安装时，运行 `推送到GitHub.ps1`。如果 PowerShell 脚本执行受系统策略阻止，使用下面的手动命令。

```powershell
git init -b main
git add .
git commit -m "docs: initial VezroCAD drafting standard v2 proposal"
git remote add origin https://github.com/hanpeiyu/vezrocad-drafting-standard.git
git push -u origin main
```

执行前请确认你已经登录 GitHub。**如远程非空、或 origin 已存在指向其他仓库，停止并检查，不要强制推送。**

## 版本迭代

- Issue：提出方案、记录打印故障、讨论新图层；不要直接改生产 DWT。
- ADR：记录已确认决策及其代价，保留被否决的替代方案。
- PR：提交 JSON/规范/样张改变，自动执行数据与二进制结构检查。
- Release：只有在 AutoCAD 实机完成 A3 黑白/彩色及遮罩验收之后才能标记为“可生产使用”。
- 与 `VezroCAD` 插件仓库的关系：通过固定版本的 JSON 契约消费，不直接复制修改历史项目图纸。

本目录不包含原统帅 DWT/CTB 或客户项目图纸，避免无关商业数据进入远程仓库。
