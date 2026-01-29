# 1) 可选：清掉旧 gitflow.*（相当于 reset）
git config --local --get-regexp "^gitflow\." `
  | ForEach-Object { ($_ -split "\s+")[0] } `
  | Sort-Object -Unique `
  | ForEach-Object { git config --local --unset-all $_ }

# 2) 重新 init（不创建分支）
git-flow init --preset=classic --defaults --main=tauri --develop=dev --no-create-branches

# 3) release finish 默认打 tag
git-flow config add topic release tauri --starting-point=dev --tag=true
