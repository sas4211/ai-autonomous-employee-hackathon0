# Skill: trust_tracker

> Type: Measurement
> Trigger: On every task completion, approval decision, or briefing generation
> Output: `/Logs/trust_ledger.md` (append-only)

---

## Purpose

Track runtime evidence toward Level 5 maturity. This is not self-declared — it's counted from real vault activity.

## What Counts

| Metric | How It's Measured | Target |
|--------|-------------------|--------|
| Tasks completed | Files in `/Done` that are tasks (not subtasks) | 10 |
| Approvals processed | Files that passed through `/Pending_Approval` → `/Approved` or `/Done` (rejected) | 5 |
| Approval mix | At least 1 rejection exists alongside approvals | Yes |
| Historical briefings | Files in `/Briefings` spanning multiple dates | 3+ dates |
| Rollback executed | A `/Logs` entry with event type "rollback" and outcome "success" | 1 |
| No surprises | Human has reviewed override log with no flags | 1 review |

## Trust Ledger Format

The ledger is a running scorecard. Updated after every qualifying event.

```markdown
# Trust Ledger

> Last updated: YYYY-MM-DD

| Metric | Current | Target | Met |
|--------|---------|--------|-----|
| Tasks completed end-to-end | N | 10 | [ ] |
| Approvals processed | N | 5 | [ ] |
| Rejections in mix | N | 1+ | [ ] |
| Briefing dates covered | N | 3+ | [ ] |
| Successful rollback | N | 1 | [ ] |
| Human audit review | N | 1 | [ ] |

## Event Log

| # | Date | Event | Metric Affected |
|---|------|-------|-----------------|
```

## Update Rules

- Read `/Done`, count task files (exclude subtasks)
- Read `/Logs`, count approval events and check for rollback entries
- Read `/Briefings`, count distinct dates
- Append new events to the Event Log section
- Recalculate all metrics
- When all targets are met, update `maturity-checklist.md` to Level 5

## Level 5 Gate

All six metrics must be met. No self-promotion. The checklist only updates when the ledger confirms every target is hit.
