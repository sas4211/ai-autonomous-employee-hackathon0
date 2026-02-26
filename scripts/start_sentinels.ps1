# AI Employee — Start All Sentinels
# Launches the master scheduler as a background process.
# Run this at the start of each work session, or register via setup_scheduler.ps1.
#
# Usage (PowerShell):
#   .\scripts\start_sentinels.ps1

$VaultPath = "C:\Users\Amena\Desktop\ai-empolyee"
$PythonExe = (Get-Command python -ErrorAction SilentlyContinue)?.Source

if (-not $PythonExe) {
    Write-Error "Python not found. Install Python 3.13+ and add to PATH."
    exit 1
}

Write-Host "`n=== AI Employee Sentinel Startup ===" -ForegroundColor Cyan
Write-Host "Vault: $VaultPath"
Write-Host "Python: $PythonExe`n"

# Check .env exists
if (-not (Test-Path "$VaultPath\.env")) {
    Write-Warning ".env file not found. Copy .env.example to .env and fill in credentials."
    Write-Warning "Sentinels will run but Gmail/Odoo/social features will be inactive."
}

# Start master scheduler (runs all watchers on schedule)
$schedulerProcess = Start-Process -FilePath $PythonExe `
    -ArgumentList "sentinels\scheduler.py" `
    -WorkingDirectory $VaultPath `
    -PassThru -WindowStyle Minimized

Write-Host "Master Scheduler started. PID: $($schedulerProcess.Id)" -ForegroundColor Green
Write-Host "  Schedule: Gmail (5 min), Social (15 min), Odoo (30 min), Heartbeat (1 min)"

# Save PID for later management
$pidFile = "$VaultPath\.claude\sentinel_pid.txt"
$schedulerProcess.Id | Out-File -FilePath $pidFile -Force
Write-Host "  PID saved to: $pidFile`n"

Write-Host "Sentinels running in background." -ForegroundColor Green
Write-Host "To stop: Stop-Process -Id (Get-Content '$pidFile')"
Write-Host "To view logs: Get-Content '$VaultPath\Logs\*.md' | Select-String 'ERROR|WARNING'"
Write-Host ""
Write-Host "Claude Code will process tasks as the sentinels drop them into /Inbox."
Write-Host "Run 'claude' in $VaultPath to start the autonomy loop."
