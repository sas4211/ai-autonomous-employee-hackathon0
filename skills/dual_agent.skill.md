# Skill: Dual-Agent Domain Ownership

> Skill Name: `dual_agent.protocol`
> Category: Architecture / Coordination
> Type: Reference — read before every autonomy loop

---

## Domain Ownership

| Action | Cloud Agent | Local Agent |
|--------|-------------|-------------|
| Email triage + draft reply | ✅ owns | ❌ skip |
| Social post draft | ✅ owns | ❌ skip |
| Odoo read (reports, invoices) | ✅ allowed | ✅ allowed |
| Odoo write (create invoice) | ✅ draft only → /Pending_Approval/cloud/ | ✅ after approval |
| Send email (execute) | ❌ never | ✅ only after approval |
| Send WhatsApp (execute) | ❌ never | ✅ only after approval |
| Post to social media (execute) | ❌ never | ✅ only after approval |
| Payments / banking | ❌ never | ✅ only after approval |
| Approve / Reject tasks | ❌ never | ✅ human via file move |
| Write Dashboard.md | ❌ never | ✅ single writer |
| Write /Updates/ | ✅ only | ❌ read only |
| WhatsApp session / browser | ❌ no session | ✅ owns |

---

## Claim-by-Move Protocol

Before processing any task, an agent MUST claim it atomically:

```
1. git pull --rebase origin main          ← sync latest state
2. Check if task is still in /Needs_Action/<domain>/
   - If gone → another agent claimed it → SKIP
3. Move task file:
   /Needs_Action/<domain>/<task>.md  →  /In_Progress/<agent>/<task>.md
4. git add + git commit + git push        ← publish claim immediately
5. If push succeeds → task is yours
6. If push fails (conflict) → another agent won → discard move → SKIP
```

**Rule:** Never process a task without completing the full claim-by-move + push cycle.

---

## Single-Writer Rules

| File / Folder | Writer | Reader |
|---------------|--------|--------|
| `Dashboard.md` | Local only | Both |
| `/Updates/*.md` | Cloud only | Local (merges into Dashboard) |
| `/Logs/` | Both (different filenames) | Both |
| `/Done/` | Both (different filenames) | Both |
| `/In_Progress/cloud/` | Cloud only | Local (read-only) |
| `/In_Progress/local/` | Local only | Cloud (read-only) |

---

## Inbox Routing

When a task arrives in `/Inbox/` (flat, unrouted):

1. **Both agents** see it on next git pull
2. **First to claim** (move + push) owns it
3. Routing heuristic (Cloud agent uses this to decide whether to claim):
   - Subject contains: invoice, email, reply, draft, social, post → Cloud claims
   - Subject contains: payment, whatsapp, approve, banking, delete → skip (Local owns)
   - Uncertain → Cloud skips, writes `/Updates/YYYY-MM-DD_routing-question.md` for Local

---

## Conflict Resolution

If `git push` fails after a claim-by-move:

```
1. git pull --rebase (get latest state)
2. Check if /In_Progress/<agent>/<task>.md exists from OTHER agent
3. If yes → other agent won → undo local move → restore to /Needs_Action/<domain>/
4. Log: "Race condition resolved — task claimed by other agent"
5. Continue to next task
```

Never force-push. Always let the first push win.

---

## Updates Merge (Local Scheduler — every 5 min)

```python
for update_file in glob("/Updates/*.md"):
    content = read(update_file)
    append_to_dashboard(content)          # merge signal into Dashboard.md
    move(update_file, "/Done/")           # archive
    git_push("local: merge cloud update")
```
