# Skill: Git Vault Sync

> Skill Name: `git_sync.protocol`
> Category: Infrastructure / Coordination
> Type: Operational — called by autonomy loop and scheduler

---

## Purpose

Keeps the shared vault in sync between Local and Cloud agents via Git.
Markdown files are the communication channel. Secrets never sync.

---

## Sync Rules

### Pull (always before acting)
```bash
git pull --rebase origin main
```
- Run at the start of every autonomy loop iteration
- Run every 30 seconds by the scheduler heartbeat
- If rebase conflict → log to /Review → keep local version → notify human

### Push (immediately after any file move)
```bash
git add <changed_files>
git commit -m "agent/<id>: <action> <task_slug>"
git push origin main
```
- Push MUST happen within 5 seconds of a file move (claim or completion)
- Never batch multiple task moves into one push (breaks atomicity)
- If push fails → retry once → if still fails → log WARNING → scheduler will retry on next cycle

---

## Commit Message Convention

| Action | Format |
|--------|--------|
| Claim task | `agent/cloud: claim 2026-02-26_email-reply-client-a` |
| Complete task | `agent/cloud: complete 2026-02-26_email-reply-client-a` |
| Write draft | `agent/cloud: draft /Pending_Approval/cloud/...` |
| Merge update | `agent/local: merge cloud update 2026-02-26_health-check` |
| Scheduler sync | `sync: heartbeat 2026-02-26T13:00:00Z` |

---

## What Syncs (Markdown + State)

✅ Synced via Git:
- All `.md` files (tasks, plans, logs, briefings, skills)
- `/Updates/`, `/Signals/` (cloud→local signals)
- `pyproject.toml`, `pm2.config.js`, `*.py`, `*.sh` (source code)
- `.env.cloud.template` (no real values)

❌ Never synced (.gitignore):
- `.env` (real credentials)
- `.claude/gmail_token.json`
- `.claude/whatsapp_session/`
- `.venv/`, `__pycache__/`
- `logs/scheduler.log` (high-churn, not useful across agents)

---

## Scheduler Integration

```python
# Every 30 seconds (both agents):
schedule.every(30).seconds.do(job_git_pull)

# After every file move:
def job_git_pull():
    result = subprocess.run(["git", "pull", "--rebase", "origin", "main"], ...)
    if result.returncode != 0:
        log_warning("git pull failed — will retry in 30s")

def git_push(message: str):
    subprocess.run(["git", "add", "-A"])
    subprocess.run(["git", "commit", "-m", message])
    result = subprocess.run(["git", "push", "origin", "main"])
    if result.returncode != 0:
        log_warning(f"git push failed: {message}")
```

---

## Error Handling

| Error | Action |
|-------|--------|
| `git pull` conflict | Keep local, log to /Review, continue |
| `git push` rejected | Retry once after 5s; if fails, log WARNING |
| Network offline | Skip sync, log DEGRADED, retry next cycle |
| Repo not initialized | Log ERROR, move task to /Review |
| Diverged branches | Never force-push; escalate to /Review |

---

## First-Time Setup (Cloud VM)

```bash
git clone https://github.com/<user>/ai-employee-vault.git /opt/ai-employee
cd /opt/ai-employee
git config user.email "cloud-agent@ai-employee"
git config user.name "AI Employee Cloud"
# Use SSH deploy key or GitHub Personal Access Token for auth
```

---

## Security Rule

The Git remote is the single source of truth for vault state.
**Secrets are never in the repo.** Each agent maintains its own `.env` locally.
The `.env.cloud.template` file (committed) contains only placeholder keys — no values.
