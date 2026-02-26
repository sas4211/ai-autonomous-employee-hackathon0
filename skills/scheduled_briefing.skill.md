# Skill: Scheduled Briefing

> Skill Name: `scheduled_briefing`
> Category: Automation / Scheduling
> Type: Trigger / Cron
> Trigger: Time-based (daily or weekly) OR file-based sentinel event
> Output: CEO Briefing in `/Briefings/`

---

## Purpose

Automate the generation of CEO briefings on a schedule so the agent proactively reports status without waiting to be asked. This closes the Level 2 maturity gap ("Scheduled briefing generation") and demonstrates proactive behaviour.

---

## Scheduling Options

### Option A — Windows Task Scheduler (Native)

Create a scheduled task that runs `claude` at 9 AM Monday:

```powershell
# Run once to register (in PowerShell as Admin):
$action = New-ScheduledTaskAction -Execute "claude" -Argument "--print `"Generate the weekly CEO briefing`"" -WorkingDirectory "C:\Users\Amena\Desktop\ai-empolyee"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9am
Register-ScheduledTask -TaskName "AIEmployee-WeeklyBriefing" -Action $action -Trigger $trigger -RunLevel Highest
```

### Option B — Sentinel Heartbeat (Python)

Add a heartbeat to `sentinels/file_watcher.py` that drops a briefing task into `/Inbox` every Monday:

```python
# In file_watcher.py, add to the main loop:
from datetime import datetime

def check_weekly_briefing(inbox: Path):
    today = datetime.now()
    if today.weekday() == 0:  # Monday
        briefing_task = inbox / f"{today.strftime('%Y-%m-%d')}_weekly-ceo-briefing.md"
        if not briefing_task.exists():
            briefing_task.write_text(BRIEFING_TASK_TEMPLATE.format(date=today.strftime('%Y-%m-%d')))
            print(f"[Sentinel] Dropped weekly briefing task: {briefing_task.name}")
```

### Option C — Git Commit Hook (On-Change)

Trigger a briefing whenever the vault changes significantly (10+ file moves in a session):

- Use `post-commit` hook in the vault's git repo
- Run `claude --print "Check if a CEO briefing is due and generate one if so"`

---

## Briefing Task Template

When the scheduler drops a task into `/Inbox`, it uses this template:

```markdown
# Task: Weekly CEO Briefing

> Status: **New**
> Created: {{date}}
> Priority: High
> Owner: --
> Type: scheduled_briefing

---

## Description

Generate the weekly CEO briefing using `ceo_briefing.generate` skill.
Cover the period from the last briefing date to today.

## Acceptance Criteria

- [ ] Briefing file created in `/Briefings/`
- [ ] Trust ledger updated (briefing dates counter +1)
- [ ] Dashboard.md refreshed
- [ ] Log entry created in `/Logs/`
```

---

## Execution Steps

1. Sentinel (or scheduler) drops briefing task into `/Inbox`
2. Autonomy loop picks it up (priority: Inbox → Active)
3. Claude executes `ceo_briefing.generate` skill
4. Briefing written to `/Briefings/YYYY-MM-DD_ceo_briefing.md`
5. Trust ledger updated
6. Dashboard refreshed
7. Task moved to `/Done`

---

## Rules

- Never generate more than one briefing per date
- If a briefing already exists for today, skip and log "already generated"
- Always use the `ceo_briefing.generate` skill — do not freestyle the format
- Log every scheduled trigger, even if skipped
