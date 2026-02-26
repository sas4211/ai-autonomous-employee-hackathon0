# AI Employee — Windows Task Scheduler Setup
# Run this script ONCE (as Administrator) to register all scheduled tasks.
#
# Usage (in PowerShell as Admin):
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\scripts\setup_scheduler.ps1

$VaultPath   = "C:\Users\Amena\Desktop\ai-empolyee"
$PythonExe   = (Get-Command python).Source
$TaskPrefix  = "AIEmployee"

Write-Host "`n=== AI Employee Task Scheduler Setup ===" -ForegroundColor Cyan
Write-Host "Vault: $VaultPath"
Write-Host "Python: $PythonExe`n"

# ── Helper ────────────────────────────────────────────────────────────────────
function Register-AITask {
    param(
        [string]$Name,
        [string]$Description,
        [string]$Arguments,
        [object]$Trigger
    )
    $fullName = "$TaskPrefix-$Name"
    # Remove if exists
    if (Get-ScheduledTask -TaskName $fullName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $fullName -Confirm:$false
        Write-Host "  Replaced: $fullName"
    }

    $action  = New-ScheduledTaskAction -Execute $PythonExe -Argument $Arguments -WorkingDirectory $VaultPath
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -StartWhenAvailable
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Limited

    Register-ScheduledTask `
        -TaskName   $fullName `
        -Description $Description `
        -Action     $action `
        -Trigger    $Trigger `
        -Settings   $settings `
        -Principal  $principal `
        | Out-Null

    Write-Host "  Registered: $fullName" -ForegroundColor Green
}

# ── 0. Wake-on-Logon (runs all sentinels once when laptop opens) ──────────────
$triggerLogon = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
Register-AITask `
    -Name        "WakeOnLogon" `
    -Description "Runs all sentinels once when you log in (wake-up on laptop start)" `
    -Arguments   "sentinels\scheduler.py --once" `
    -Trigger     $triggerLogon

# ── 1. Master Scheduler (every 5 min, always-on) ─────────────────────────────
$triggerRepeat = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) -Once -At (Get-Date)
Register-AITask `
    -Name        "MasterScheduler" `
    -Description "Runs Gmail, WhatsApp, Finance, LinkedIn, social watchers on schedule" `
    -Arguments   "sentinels\scheduler.py" `
    -Trigger     $triggerRepeat

# ── 2. Weekly CEO Briefing (Monday 09:00) ─────────────────────────────────────
$triggerMonday = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "09:00"
Register-AITask `
    -Name        "WeeklyBriefing" `
    -Description "Drops weekly CEO briefing task into /Inbox" `
    -Arguments   "sentinels\scheduler.py --once" `
    -Trigger     $triggerMonday

# ── 3. Daily Gmail Check (every day 08:00) ────────────────────────────────────
$triggerDaily = New-ScheduledTaskTrigger -Daily -At "08:00"
Register-AITask `
    -Name        "DailyGmailCheck" `
    -Description "Morning Gmail poll — drops new emails into /Inbox" `
    -Arguments   "sentinels\gmail_watcher.py" `
    -Trigger     $triggerDaily

# ── 4. LinkedIn Post Queue (Monday 09:05) ─────────────────────────────────────
$triggerLinkedIn = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "09:05"
Register-AITask `
    -Name        "WeeklyLinkedInPost" `
    -Description "Queues a LinkedIn post draft task into /Inbox" `
    -Arguments   "sentinels\linkedin_poster.py --draft" `
    -Trigger     $triggerLinkedIn

# ── 5. LinkedIn Publisher (every 30 min) ──────────────────────────────────────
$triggerPublish = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 30) -Once -At (Get-Date)
Register-AITask `
    -Name        "LinkedInPublisher" `
    -Description "Publishes approved LinkedIn posts from /Approved" `
    -Arguments   "sentinels\linkedin_poster.py --watch" `
    -Trigger     $triggerPublish

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host "`n=== Registered Tasks ===" -ForegroundColor Cyan
Get-ScheduledTask -TaskPath "\" | Where-Object { $_.TaskName -like "$TaskPrefix-*" } |
    Format-Table TaskName, State -AutoSize

Write-Host "`nDone. All AI Employee tasks are registered.`n" -ForegroundColor Green
Write-Host "To verify: Open Task Scheduler → Task Scheduler Library → look for AIEmployee-*"
Write-Host "To remove: Run Unregister-ScheduledTask -TaskName 'AIEmployee-*' -Confirm:`$false"
