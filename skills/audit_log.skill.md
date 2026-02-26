# Skill: Comprehensive Audit Logging

> Skill Name: `audit_log.write`
> Category: Observability / Compliance
> Type: Core System
> Trigger: After EVERY action (internal or external)
> Output: `/Logs/YYYY-MM-DD_<category>.md` and `/Logs/events/<timestamp>_<type>.json`

---

## Purpose

Every action Claude takes — reading data, moving files, calling APIs, generating content — is logged with enough detail to reconstruct exactly what happened, when, and why. No silent actions.

Gold Tier audit logging goes beyond basic task logs to include:
- Structured JSON events for machine-readable audit trails
- Human-readable markdown summaries
- Error and degradation events
- External API call records
- Cross-domain activity separation

---

## Log Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| `INFO` | Routine actions completed successfully | Task claimed, file moved |
| `ACTION` | External action taken (email sent, post published) | Email sent to customer |
| `APPROVAL` | Human approval decision recorded | Approval granted / rejected |
| `WARNING` | Unexpected state, non-fatal issue | Odoo offline, API rate limit |
| `ERROR` | Failure requiring attention | Email send failed |
| `DEGRADED` | Service unavailable, partial completion | Social data missing from audit |
| `SECURITY` | Sensitive operation, credential use | LinkedIn token used |

---

## Markdown Log Format

Every action gets a markdown entry in `/Logs/YYYY-MM-DD_<category>.md`:

```markdown
## [LEVEL] action_name — YYYY-MM-DDTHH:MM:SSZ

**Task:** task_filename.md
**Domain:** business | personal | system
**Actor:** Claude Code | gmail_watcher | odoo_watcher | human
**Action:** Plain-language description of what happened

**Inputs:**
- input_key: input_value

**Outputs:**
- output_key: output_value

**Result:** Success | Failed | Degraded | Pending
**Notes:** Any relevant context, error messages, or follow-up needed
```

---

## JSON Event Format

Every state transition also writes a structured JSON file to `/Logs/events/`:

```json
{
  "event_id": "unix_timestamp",
  "event_type": "task.completed | email.sent | approval.granted | error.logged | ...",
  "timestamp": "ISO8601",
  "level": "INFO | ACTION | WARNING | ERROR | DEGRADED | SECURITY",
  "source": "claude_code | sentinel_name | mcp_server_name",
  "domain": "business | personal | system",
  "vault": "ai-employee",
  "payload": {
    "task_file": "filename.md",
    "from_folder": "/Active",
    "to_folder": "/Done",
    "metadata": {}
  }
}
```

---

## Log Categories (file naming)

| Category | Filename Pattern | What Goes Here |
|----------|----------------|----------------|
| Task lifecycle | `YYYY-MM-DD_tasks.md` | Claims, completions, moves |
| External actions | `YYYY-MM-DD_external_actions.md` | Emails sent, posts published |
| Approvals | `YYYY-MM-DD_approvals.md` | All approval decisions |
| Errors | `YYYY-MM-DD_errors.md` | All failures and degradations |
| Odoo | `YYYY-MM-DD_odoo_actions.md` | All Odoo reads/writes |
| Social media | `YYYY-MM-DD_social_media_actions.md` | All social media operations |
| Personal | `personal/YYYY-MM-DD_personal.md` | Personal domain only (private) |
| Audit audit | `YYYY-MM-DD_meta.md` | Log of when audits were generated |

---

## Required Log Entries

The following events MUST be logged (no exceptions):

| Event | Level | Log Category |
|-------|-------|--------------|
| Task claimed | INFO | tasks |
| Task completed | INFO | tasks |
| Task moved to /Needs_Action | WARNING | tasks |
| Task escalated to /Review | WARNING | tasks |
| Any email sent | ACTION + SECURITY | external_actions |
| Any social post published | ACTION + SECURITY | social_media_actions |
| Any Odoo write operation | ACTION | odoo_actions |
| Approval granted | APPROVAL | approvals |
| Approval rejected | APPROVAL | approvals |
| Any API error | ERROR | errors |
| Service offline (graceful degradation) | DEGRADED | errors |
| Rollback executed | ACTION | tasks |
| CEO briefing generated | INFO | meta |

---

## Graceful Degradation Logging

When a service is unavailable, log a DEGRADED event and continue:

```markdown
## [DEGRADED] odoo_unavailable — YYYY-MM-DDTHH:MM:SSZ

**Task:** 2026-02-23_weekly-audit.md
**Action:** Attempted to pull accounting data from Odoo
**Result:** Degraded — Odoo connection refused (http://localhost:8069)
**Impact:** Financial section of weekly audit is incomplete
**Notes:** Audit generated with available data. Odoo section marked "unavailable".
  Retry: Check Odoo is running at the configured URL.
```

---

## Retention Policy

| Log Type | Keep For |
|----------|---------|
| Task lifecycle | 90 days |
| External action logs | 1 year |
| Approval logs | 1 year |
| Error logs | 30 days |
| JSON events | 30 days |
| CEO briefings | Indefinitely |
| Personal logs | 30 days |

---

## Log Query Patterns

To investigate an issue, scan these files:
- What happened today? → `/Logs/2026-02-23_tasks.md`
- Did the email send? → `/Logs/2026-02-23_external_actions.md`
- Was it approved? → `/Logs/2026-02-23_approvals.md`
- Why did it fail? → `/Logs/2026-02-23_errors.md`
- Full event stream? → `/Logs/events/*.json` (sorted by timestamp)
