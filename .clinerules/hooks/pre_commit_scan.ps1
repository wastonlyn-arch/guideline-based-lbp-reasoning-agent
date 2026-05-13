# Pre-commit Hook: 敏感文件扫描
# 在 git commit 前执行，检测并阻止敏感文件被提交
param()

$sensitive_patterns = @(
    '\.env$',
    '\.env\.local$',
    '\.sqlite$',
    '\.db$',
    '__pycache__',
    '\.pytest_cache',
    'node_modules'
)

$changes = git diff --cached --name-only 2>$null
if (-not $changes) {
    Write-Host "✅ 无暂存文件更改"
    exit 0
}

$issues = @()

foreach ($file in $changes) {
    foreach ($pattern in $sensitive_patterns) {
        if ($file -match $pattern) {
            $issues += "⚠️  敏感文件将被提交: $file"
        }
    }
}

if ($issues.Count -gt 0) {
    Write-Host "`n❌ 提交被拒绝:"
    $issues | ForEach-Object { Write-Host $_ }
    exit 1
}

Write-Host "✅ 敏感文件检查通过"