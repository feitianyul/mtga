param(
  [string]$MainBranch = "tauri",
  [string]$DevBranch  = "dev"
)

$repoRoot = (git rev-parse --show-toplevel 2>$null)
if (-not $repoRoot) { throw "当前目录不在 git 仓库里。" }

$hooksDir = Join-Path $repoRoot ".git\hooks"
New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null

$hookPath = Join-Path $hooksDir "post-flow-release-finish"

# 单引号 here-string：避免 PowerShell 把 bash 里的 $ / $(...) / ${...} 提前展开
$hookTemplate = @'
#!/usr/bin/env bash
set -euo pipefail

remote="${GITFLOW_ORIGIN:-origin}"
main_branch="{{MAIN}}"
dev_branch="{{DEV}}"

gitdir="$(git rev-parse --git-dir)"
log="$gitdir/flow-hook.log"

{
  echo "----"
  echo "post-flow-release-finish @ $(date)"
  echo "remote=$remote"
  echo "branch=$(git rev-parse --abbrev-ref HEAD)"
  echo "GITFLOW_VERSION=${GITFLOW_VERSION-}"
} >>"$log" 2>&1

# 推分支
git push "$remote" "$main_branch" "$dev_branch" >>"$log" 2>&1

# 推 tag：直接取 HEAD 上的 tag（finish 刚创建的 tag 一定在 HEAD）
tag="$(git describe --tags --exact-match 2>/dev/null || true)"
if [[ -n "$tag" ]]; then
  git push "$remote" "refs/tags/$tag" >>"$log" 2>&1
else
  echo "no tag on HEAD, skip tag push" >>"$log" 2>&1
fi
'@

$hook = $hookTemplate.Replace("{{MAIN}}", $MainBranch).Replace("{{DEV}}", $DevBranch)

# 写入时强制 LF + UTF-8 no BOM，避免 Windows 换行/编码坑
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText(
  $hookPath,
  ($hook -replace "`r`n","`n" -replace "`r","`n"),
  $utf8NoBom
)

# 尝试 chmod +x（有 bash 的话就设一下；没有也不报错）
$bash = (Get-Command bash.exe -ErrorAction SilentlyContinue).Source
if ($bash) { & $bash -lc "chmod +x '$hookPath'" }

Write-Host "✅ 已写入 flow hook: $hookPath"
Write-Host "📄 hook 运行日志: $repoRoot\.git\flow-hook.log"
