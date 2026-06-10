$ErrorActionPreference = "Stop"

Write-Host "Cleaning up zombie processes on port 8000..." -ForegroundColor Yellow
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }

Write-Host "Starting LiteLLM Proxy in the background..." -ForegroundColor Cyan
Start-Process -WindowStyle Hidden -FilePath "litellm" -ArgumentList "--config C:\Users\AA_p\litellm_config.yaml --port 8000"
Start-Sleep -Seconds 3
Write-Host "LiteLLM Proxy started!" -ForegroundColor Green

Write-Host "Configuring Claude Code environment..." -ForegroundColor Cyan
$env:ANTHROPIC_BASE_URL = "http://localhost:8000"
$env:ANTHROPIC_API_KEY = "sk-lite-any-key"

Write-Host "Launching Claude Code..." -ForegroundColor Cyan
claude --model claude-3-5-sonnet-20241022
