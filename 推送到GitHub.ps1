# 使用前先在 https://github.com/new 创建 EMPTY PRIVATE 仓库：
# Owner: hanpeiyu  Name: vezrocad-drafting-standard
# 不勾选 Initialize with README、LICENSE 或 .gitignore（本地已经包含）。
# 在解压后的 vezrocad-drafting-standard 文件夹中右键打开 PowerShell 执行。
$ErrorActionPreference = 'Stop'
$RepoUrl = 'https://github.com/hanpeiyu/vezrocad-drafting-standard.git'
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw '没有找到 git。请先安装 Git for Windows。' }
if (-not (Test-Path '.git')) {
    git init -b main
    if ($LASTEXITCODE -ne 0) { throw 'git init 失败' }
}
git add .
if ($LASTEXITCODE -ne 0) { throw 'git add 失败' }
git diff --cached --quiet
if ($LASTEXITCODE -eq 1) {
    git commit -m 'docs: initial VezroCAD drafting standard v2 proposal'
    if ($LASTEXITCODE -ne 0) { throw 'git commit 失败；请检查 git user.name 与 user.email。' }
}
$origin = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0 -or -not $origin) {
    git remote add origin $RepoUrl
    if ($LASTEXITCODE -ne 0) { throw 'git remote add 失败' }
} elseif ($origin -ne $RepoUrl) {
    throw "当前 origin 已指向 $origin 。为避免误推送，脚本已停止。"
}
git push -u origin main
if ($LASTEXITCODE -ne 0) { throw 'GitHub 推送失败：请检查仓库是否已创建、账号权限和登录认证。' }
Write-Host "推送完成： https://github.com/hanpeiyu/vezrocad-drafting-standard"
