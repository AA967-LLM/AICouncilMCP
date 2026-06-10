$ErrorActionPreference = "Stop"

Write-Host "Starting LiteLLM Proxy in the background..." -ForegroundColor Cyan

# Check if LiteLLM is already running on port 8000
$tcpConns = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($null -eq $tcpConns) {
    Start-Process -WindowStyle Hidden -FilePath "litellm" -ArgumentList "--config C:\Users\AA_p\litellm_config.yaml --port 8000"
    Start-Sleep -Seconds 3
    Write-Host "LiteLLM Proxy started!" -ForegroundColor Green
} else {
    Write-Host "LiteLLM Proxy is already running on port 8000." -ForegroundColor Yellow
}

Write-Host "Configuring Claude Code environment..." -ForegroundColor Cyan
$env:ANTHROPIC_BASE_URL = "http://localhost:8000"
$env:ANTHROPIC_API_KEY = "sk-lite-any-key"

Write-Host "Launching Claude Code..." -ForegroundColor Cyan
claude --model claude-3-5-sonnet-20241022
