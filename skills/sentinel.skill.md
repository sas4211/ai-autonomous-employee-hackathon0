# Skill: Sentinel / Watcher Pattern

> Skill Name: `sentinel.watch`
> Category: Integration / Event-Driven
> Type: Core System
> Trigger: Scheduled (via `scheduler.py` or Windows Task Scheduler)
> Output: Task files in `/Inbox` + event JSON in `/Logs/events/`
> Implementation: `sentinels/` directory

---

## Purpose

Sentinels are the "Senses" of the AI Employee. They monitor external systems and the filesystem for events, then translate those events into vault task files. This wakes Claude up without requiring a human to type anything.

```
External World          Sentinels             Vault
─────────────   ──────────────────────   ──────────────
Gmail inbox  →  gmail_watcher.py      →  /Inbox task
New Odoo order  odoo_watcher.py          /Inbox task
FB comment   →  social_media_watcher  →  /Inbox task
New file     →  file_watcher.py       →  /Logs/events
```

---

## Active Sentinels

| Sentinel | Extends | What It Watches | Poll Interval | Output |
|----------|---------|----------------|---------------|--------|
| `file_watcher.py` | watchdog (event-driven) | `/Inbox` filesystem changes | Real-time | `/Logs/events/*.json` |
| `gmail_watcher.py` | BaseWatcher | Gmail IMAP (unread emails) | 5 minutes | `/Inbox/` task |
| `whatsapp_watcher.py` | BaseWatcher | WhatsApp via Twilio API | 5 minutes | `/Needs_Action/` task |
| `linkedin_poster.py` | standalone | `/Approved/` for LinkedIn posts | 10 minutes | Publishes post + `/Done/` |
| `social_media_watcher.py` | BaseWatcher | FB comments, Twitter mentions | 15 minutes | `/Inbox/` task |
| `odoo_watcher.py` | BaseWatcher | Odoo: overdue invoices, new orders | 30 minutes | `/Inbox/` task |
| `finance_watcher.py` | BaseWatcher | Bank CSV files or Plaid API | 1 hour | `/Accounting/Current_Month.md` + `/Inbox/` alert |
| `scheduler.py` | master | Runs all sentinels on schedule | Continuous | Orchestrates all |
| `check_work_remaining.py` | standalone | Vault folder state | Per Claude stop | Stop hook output |

**Note:** `file_watcher.py` uses `watchdog.FileSystemEventHandler` (event-driven) rather than
BaseWatcher (polling). `linkedin_poster.py` and `check_work_remaining.py` are action scripts,
not monitors — they also do not extend BaseWatcher.

---

## BaseWatcher (Abstract Base Class)

All polling sentinels extend `sentinels/base_watcher.py`:

```python
from base_watcher import BaseWatcher

class MyWatcher(BaseWatcher):
    def check_for_updates(self) -> list:
        # Poll external service; return [] if not configured
        ...

    def create_action_file(self, item) -> Path:
        # Write .md task file; return Path
        ...
```

`BaseWatcher` provides:
- `self.inbox` — `/Inbox` path
- `self.needs_action` — `/Needs_Action` path
- `self.logs_events` — `/Logs/events/` path
- `self.now()`, `self.datestamp()` — timestamps
- `self.log_event(event_type, payload)` — writes JSON event
- `self.task_exists(slug)` — idempotency check
- `self.write_task(folder, filename, content)` — atomic file write
- `self.run()` — blocking polling loop
- `self.run_once()` — single cycle (used by scheduler)

---

## Sentinel Design Contract

Every sentinel must follow this contract:

### 1. Graceful Degradation

If credentials are missing or a service is offline, the sentinel **skips** that service and exits cleanly. It never crashes the scheduler.

```python
if not os.getenv("GMAIL_ADDRESS"):
    print(f"[{now()}] Gmail not configured — skipping.")
    return
```

### 2. Idempotency

Before creating a task file, check if one already exists for today's slug. Never create duplicate tasks.

```python
def _task_exists(slug: str) -> bool:
    for folder in ["Inbox", "Active", "Done"]:
        if list((VAULT_ROOT / folder).glob(f"*{slug}*")):
            return True
    return False
```

### 3. Structured Event Logging

Every sentinel event writes a JSON file to `/Logs/events/`:

```json
{
  "event_id": "unix_timestamp",
  "event_type": "email.inbound | odoo.overdue_invoices | ...",
  "timestamp": "ISO8601",
  "source": "sentinel_name",
  "payload": { ... }
}
```

### 4. State Persistence

Sentinels that track "what have I seen" use a state file in `.claude/`:
- `social_watcher_state.json` — last seen Twitter mention ID, last FB comment time
- This prevents re-processing old events on each run

### 5. Task File Format

Every Inbox task created by a sentinel must include:

```markdown
> Type: email_response | odoo_followup | social_reply | ...
> Source: gmail_watcher | odoo_watcher | social_media_watcher
```

This tells Claude which skill to use when it claims the task.

---

## Adding a New Sentinel

To add a new watcher (e.g., WhatsApp, Slack, bank transactions):

### Step 1 — Create `sentinels/<name>_watcher.py`

```python
VAULT_ROOT = Path(__file__).parent.parent
INBOX = VAULT_ROOT / "Inbox"

def run_once():
    load_dotenv(VAULT_ROOT / ".env")
    if not os.getenv("SERVICE_API_KEY"):
        print("Not configured — skipping.")
        return
    # ... poll the service ...
    # ... call _write_task() for each new event ...

def main():
    if "--loop" in sys.argv:
        while True:
            run_once()
            time.sleep(POLL_INTERVAL)
    else:
        run_once()
```

### Step 2 — Add credentials to `.env.example`

```
SERVICE_API_KEY=your_key_here
```

### Step 3 — Add to `sentinels/scheduler.py`

```python
def job_check_service():
    _run_script("service_watcher.py")

# In setup_schedule():
schedule.every(15).minutes.do(job_check_service)
```

### Step 4 — Create a skill for the event type

Add `skills/<service>_skill.md` that describes what Claude should do when it sees a task with `Type: <service>_event`.

### Step 5 — Add to `pyproject.toml` scripts

```toml
watch-service = "sentinels.service_watcher:main"
```

### Step 6 — Document in this file and `Company_Handbook.md`

---

## Scheduler Integration

The master scheduler (`sentinels/scheduler.py`) runs all sentinels as subprocesses using `schedule` library. Each job is isolated — one sentinel crashing does not affect others.

```
Every  1 min  — Heartbeat (vault state)
Every  5 min  — Gmail
Every 10 min  — LinkedIn publisher
Every 15 min  — Social media (FB + Twitter)
Every 30 min  — Odoo
Every  1 hr   — Ralph Wiggum (work remaining check)
Monday 09:00  — Weekly briefing + audit queue
Monday 09:05  — LinkedIn post draft queue
```

Start the scheduler:
```bash
python sentinels/scheduler.py          # blocking
python sentinels/scheduler.py --once   # run all once and exit
```

Or register with Windows Task Scheduler:
```powershell
.\scripts\setup_scheduler.ps1
```

---

## Rules

- Sentinels are read-only from external services — they observe, not act
- Only Claude Code (via MCP tools) takes external actions
- All sentinel-created tasks go through the approval gate before any action is taken
- Never hard-code credentials in sentinel scripts — always use `.env`
- Test each sentinel with `--once` before enabling `--loop`
