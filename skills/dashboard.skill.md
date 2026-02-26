# Skill: Dashboard Generation (Agentic Frontend)

> Skill Name: `dashboard.generate`
> Category: Frontend-Equivalent / Observability / Human-in-the-Loop
> Type: System
> Trigger: On demand or after any vault state change
> Output: `/Dashboard.md`

---

## Purpose

Generate and continuously update a human-readable operational dashboard using Markdown files as the primary user interface.

This skill replaces a traditional web frontend by rendering system state, agent progress, risks, and next actions inside an Obsidian-compatible `Dashboard.md`.

## Inputs

- Vault directory structure
- Task states (`/Inbox`, `/Active`, `/Done`, `/Review`, `/Pending_Approval`, `/Approved`)
- Agent logs and summaries (`/Logs`)
- Approval queues (`/Pending_Approval`)
- Trust ledger (`/Logs/trust_ledger.md`)
- System health signals (MCP server status, skill count, error rate)

## Outputs

- `/Dashboard.md` (root)

## Behavior

The agent SHALL:
1. Scan the project vault and identify:
   - Active plans and in-progress tasks
   - Blocked or failed items
   - Pending approvals
   - Recently completed work
2. Summarize system status in concise, executive-readable language.
3. Highlight:
   - Risks and blockers
   - Bottlenecks (stalled tasks, unanswered approvals)
   - Recent completions
4. Update the dashboard incrementally without deleting historical context.

## Dashboard Structure (Required)

```
# Project Dashboard

## Current Phase
## Active Objectives
## Agent Activity
## Pending Approvals
## Risks & Blockers
## Recently Completed
## Next Recommended Actions
## Vault State (folder counts)
## Trust Progress (Level 5 metrics)
## Audit Log (recent)
## MCP Servers
```

## Steps

1. List every workflow folder and count files
2. Identify oldest item per folder and any stalled items
3. Read recent entries from `/Logs`
4. Check `/Pending_Approval` for open items
5. Read `/Logs/trust_ledger.md` for Level 5 progress
6. Assess risks: stalled tasks, empty inbox, missing MCP, unanswered approvals
7. Determine current phase from vault maturity level
8. Write `Dashboard.md` with all required sections

## Output Format

Markdown tables and bullet lists. Obsidian-compatible `[[wiki-links]]` and `[markdown links](path)`. Emoji headers for scannability.

## Update Rules

- Overwrite `Dashboard.md` on every run
- Preserve audit log entries (append, never truncate)
- Log the refresh in `/Logs`
