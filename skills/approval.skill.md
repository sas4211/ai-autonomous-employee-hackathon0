# Skill: Approval Workflow (Human-in-the-Loop Gate)

> Skill Name: `approval.request`
> Category: Safety / Governance / HITL
> Type: Workflow
> Trigger: Sensitive or irreversible action detected
> Output: `/Pending_Approval/<action-name>.md`

---

## Purpose

Enforce explicit human approval for sensitive or irreversible actions using
file-based workflows instead of UI buttons.

The agent MUST NOT execute a gated action until the approval file has been
moved to `/Approved` by a human.

---

## Auto-Approve Thresholds

Some low-risk actions may be executed without an approval file. Check this table first:

| Action Category | Auto-Approve (no file needed) | Always Require Approval |
|----------------|------------------------------|------------------------|
| Email replies | To known contacts | New contacts, bulk sends |
| Payments | < $50 recurring (known payee) | All new payees, > $100 |
| Social media | Scheduled posts | Replies, DMs |
| File operations | Create, read | Delete, move outside vault |

If the action is not listed above, or if there is any doubt → require approval.

---

## When This Skill Is Triggered

- Any external communication that exceeds auto-approve threshold (email to new contact, bulk send)
- Any financial action above threshold (new payee, > $100, all transfers)
- Social media replies or DMs
- Data deletion or migration
- External API write operations (via MCP)
- Any action with no rollback path
- Any action whose cost or risk exceeds threshold (default: $500)
- Infrastructure changes or deployments

---

## Approval File Format (YAML Frontmatter)

Every approval request MUST use this format:

```markdown
---
type: approval_request
action: <one-line summary>
amount: <dollar amount if financial, else omit>
recipient: <who receives the action, if applicable>
reason: <why this is needed>
created: <ISO8601 timestamp>
expires: <ISO8601 timestamp — 24 hours after created>
risk_level: <Low | Medium | High>
status: pending
---

# Approval Request: <action summary>

## Action Details
<clear description of exactly what will happen>

## Why This Is Needed
<business justification>

## Risk Level
<Low | Medium | High> — <reasoning>

## Impacted Components
- <system or person affected>

## Rollback Plan
<how to undo if something goes wrong after approval>

## Requested By
Claude Code (AI Employee)

## Expires
<ISO8601 expiry>

---

## To Approve
Move this file to `/Approved` folder.

## To Reject
Add a note in Human Notes below, then move to `/Rejected` folder.

---

## Human Notes
> _Write decision notes here before moving the file._
```

---

## Steps

1. Detect that an action requires approval (see trigger list above)
2. Generate the approval file using the template above
3. Fill in all YAML frontmatter fields — `expires` = created + 24 hours
4. Name the file: `YYYY-MM-DD_<action-slug>.md`
5. Save to `/Pending_Approval/`
6. Log the creation in `/Logs/`
7. Update `Dashboard.md` (Pending Approvals section)
8. **HALT** — do not proceed until file moves

---

## Human Decision Paths

| Decision | How | What Claude Does |
|----------|-----|-----------------|
| **Approve** | Move file to `/Approved` | Executes the action via MCP, logs result, moves to `/Done` |
| **Reject** | Move file to `/Rejected` | Logs rejection + Human Notes reason, does NOT execute, moves to `/Done` after logging |
| **No response** | File stays in `/Pending_Approval` | After expiry time, flags as stale risk on Dashboard |

---

## Post-Decision Logic

### If moved to `/Approved`

```
1. Read the approval file
2. Execute the action via the appropriate MCP tool
3. Log the result in /Logs/ (success or failure)
4. Move the approval file to /Done/
5. Update trust ledger (+1 approval processed)
6. Update Dashboard.md
```

### If moved to `/Rejected`

```
1. Read the file — capture Human Notes (rejection reason)
2. Log the rejection in /Logs/:
     "REJECTED: <action> — Reason: <human notes>"
3. Do NOT execute the action under any circumstances
4. Move the rejection file to /Done/ (keep as audit record)
5. Update trust ledger (+1 rejection processed)
6. Update Dashboard.md
7. Resume autonomy loop
```

### If expired (still in `/Pending_Approval` after 24h)

```
1. Flag on Dashboard.md as stale
2. Do NOT auto-approve or auto-reject
3. Escalate to /Needs_Action with a note asking the human to decide
```

---

## Rules

- Never execute a gated action without the file in `/Approved`
- Never auto-approve — only humans move files
- Always log every decision (approved, rejected, expired) in `/Logs/`
- Always update the trust ledger after each approval decision
- `/Rejected` is for explicit rejections — `/Done` is for completions
- Stale approvals (>24h unanswered) are a risk — surface them on Dashboard
