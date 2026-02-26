# Skill: Rollback

## Skill Name
rollback.execute

## Category
Safety / Recovery

## Purpose
Undo a completed action safely when it produced unintended results or was later rejected. Provides an auditable reversal path and earns trust ledger evidence.

## When This Skill Is Triggered
- A completed task is flagged for reversal (file placed in `/Review` with tag `rollback-needed`)
- A human moves an approval to `/Done` marked as **Rejected** after execution already occurred
- An error is detected post-completion that requires state restoration

## Inputs
- **Target task file**: The `/Done` task file to roll back
- **Reason**: Why the rollback is needed
- **Scope**: Full rollback or partial (which steps to undo)

## Outputs
- Rollback log entry in `/Logs`
- Updated trust ledger in `/Logs/trust_ledger.md`
- Original task file annotated with rollback status
- Dashboard updated

## Workflow

### Step 1 — Identify Rollback Target
1. Read the task file from `/Done` (or `/Review` if escalated)
2. Extract the list of actions that were performed
3. Determine which actions are reversible

### Step 2 — Create Rollback Plan
Create `/Active/YYYY-MM-DD_rollback_<original-slug>.md`:

```md
# Rollback Plan

## Original Task
<link to original task file>

## Reason for Rollback
<why this is being reversed>

## Actions to Reverse
| # | Original Action | Reversal Action | Reversible |
|---|----------------|-----------------|------------|
| 1 | Created file X | Delete file X | Yes |
| 2 | Moved file Y to /Done | Move file Y back to /Active | Yes |
| 3 | Called external API | Cannot undo | No |

## Non-Reversible Items
<list any actions that cannot be undone, with mitigation>

## Status
- [ ] Plan reviewed
- [ ] Rollback executed
- [ ] Verified
```

### Step 3 — Request Approval (if sensitive)
If the rollback involves:
- Deleting files
- External system changes
- Infrastructure modifications

Then route through `approval.request` before executing. Place rollback plan in `/Pending_Approval`.

### Step 4 — Execute Rollback
1. Perform each reversal action in order (reverse of original execution order)
2. Log each step to `/Logs/YYYY-MM-DD_rollback_<slug>.md`
3. If any step fails: stop, log the failure, escalate to `/Review`

### Step 5 — Verify and Close
1. Confirm the system state matches pre-task state
2. Annotate original task file with rollback note:
   ```
   ## Rollback
   - **Date**: YYYY-MM-DD
   - **Reason**: <reason>
   - **Result**: Success / Partial
   ```
3. Move rollback plan to `/Done`
4. Update trust ledger: `rollback_executed: +1`
5. Refresh Dashboard

## Rollback Log Template

```md
# Rollback Log

- **Date**: {{date}}
- **Original Task**: {{task_file}}
- **Reason**: {{reason}}
- **Actions Reversed**: {{count}}
- **Non-Reversible**: {{count}}
- **Result**: Success | Partial | Failed
- **Performed By**: {{agent}}

## Steps Executed
1. {{step description}} — {{success/failed}}

## Post-Rollback State
{{description of system state after rollback}}
```

## Rules
- Never execute a rollback without a written plan
- Non-reversible actions must be documented, not skipped silently
- If rollback fails midway, escalate — do not retry automatically
- Always update the trust ledger after a rollback (success or failure)
- A partial rollback is still logged as a rollback attempt
