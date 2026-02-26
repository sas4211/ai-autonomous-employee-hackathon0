# Skill: error_handling

> Type: Core System
> Trigger: When any action fails during task execution
> Output: Error logs, escalation files, retry attempts

---

## Purpose

Define how Claude Code handles failures so errors never disappear silently. Every failure is logged, categorized, and either retried or escalated.

## Error Categories

| Category | Examples | Recovery Strategy |
|----------|----------|-------------------|
| Transient | Network timeout, file locked, API rate limit | Exponential backoff retry (max 3x via `retry_handler.py`) |
| Authentication | Expired token, revoked access | Alert human, pause all operations for that integration |
| Logic | Claude misinterprets message, invalid state | Log + human review queue (`/Review`) |
| Data | Corrupted file, missing required field | Quarantine file + alert human |
| System | Orchestrator crash, disk full | `watchdog.py` auto-restart + `/Needs_Action` notification |
| Permission | Access denied, scope violation | Log + escalate to `/Review` |
| Unknown | Unexpected exception, unrecognised output | Log + escalate to `/Review` |

## Response Protocol

### 1. Catch

- Detect the failure (command exit code, missing expected output, exception)
- Do NOT continue the task as if it succeeded

### 2. Log

Create an error log in `/Logs`:

```markdown
# Error Log

- **Timestamp**: YYYY-MM-DD
- **Task**: {{task_file}}
- **Step**: {{which step failed}}
- **Category**: Transient | Logical | Permission | Unknown
- **Error**: {{error message or output}}
- **Action Taken**: Retry | Escalate | Halt
```

### 3. Retry (Transient only)

- Use `sentinels/retry_handler.py` — exponential backoff (1s → 2s → 4s, capped at 60s)
- Maximum 3 attempts
- Only `TransientError` class is retried — authentication, data, and logic errors are never retried
- If still failing after retries, escalate

### 3a. Graceful Degradation

When a component is persistently unavailable, degrade gracefully:

| Component Down | Behaviour |
|---------------|-----------|
| Gmail API | Queue outgoing emails locally; process when restored |
| Banking API | Never auto-retry payments — always require fresh human approval |
| Claude Code | Watchers continue collecting; inbox queue grows for later processing |
| Vault locked | Write to temp folder; sync when available |

### 4. Escalate

- Keep task in `/Active` (do not move to `/Done`)
- Create an escalation file in `/Review`:

```markdown
# Escalation: {{task_name}}

> Source Task: {{task_file}}
> Error Category: {{category}}
> Failed Step: {{step}}
> Date: YYYY-MM-DD

---

## What Happened

{{plain-language description of the failure}}

## What Was Tried

{{retry attempts or why retry was not applicable}}

## What's Needed

{{what the human should do — fix config, grant access, clarify requirement}}

## Original Error

```
{{raw error output}}
```
```

### 5. Resume After Fix

When human moves the escalation file to `/Approved` or adds notes:
1. Read the human's notes
2. Re-attempt the failed step
3. If success, continue task normally
4. If failure, re-escalate (do not loop forever)

## Rules

- Never mark a task as complete if any step failed
- Never swallow an error silently
- Never retry more than 2 times
- Never retry non-transient errors
- Always log before escalating
- Always tell the human what you need from them
