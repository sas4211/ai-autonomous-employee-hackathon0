# Skill: Cloud Agent Behavior

> Skill Name: `cloud_agent.autonomy`
> Category: Architecture / Cloud Operations
> Type: Operational — defines cloud agent's autonomy loop

---

## Purpose

The Cloud agent runs 24/7 on Oracle Cloud Free Tier VM.
It handles email triage, reply drafting, and social post drafts autonomously.
It NEVER executes sends, payments, or approvals — all final actions belong to Local + human.

---

## Autonomy Loop

```
Every 5 minutes (PM2 managed, systemd auto-boot):

1. git pull --rebase origin main           ← sync vault
2. Scan /Needs_Action/cloud/ + /Inbox/     ← find work
3. If task found:
   a. Claim: move to /In_Progress/cloud/ + git push
   b. Read task content + relevant skills
   c. Build prompt → call Anthropic API (claude-sonnet-4-6)
   d. Parse response → write draft to /Pending_Approval/cloud/
   e. git push
   f. Log to /Logs/cloud/YYYY-MM-DD_<task>.md
   g. Write signal to /Updates/YYYY-MM-DD_<task>-complete.md
   h. git push
4. If nothing to do: write heartbeat to /Updates/health_<datetime>.md + git push
5. Sleep 5 minutes
```

---

## Permitted Actions (Cloud)

| Action | Allowed | Notes |
|--------|---------|-------|
| git pull / git push | ✅ | Core of all coordination |
| Read any vault file | ✅ | Full read access |
| Write to /Needs_Action/cloud/ | ✅ | Self-routing |
| Write to /In_Progress/cloud/ | ✅ | Claim-by-move |
| Write to /Plans/cloud/ | ✅ | Multi-step planning |
| Write to /Pending_Approval/cloud/ | ✅ | Drafts only |
| Write to /Logs/ | ✅ | Audit trail |
| Write to /Updates/ | ✅ | Signals to Local |
| Call Anthropic API | ✅ | Core reasoning |
| Call Odoo read tools | ✅ | Reports, invoice lists |
| Write to /Done/ | ✅ | Close completed drafts |

---

## Forbidden Actions (Cloud)

| Action | Reason |
|--------|--------|
| `communications.send_email()` | External action — Local only after approval |
| `communications.post_to_linkedin()` | External action — Local only after approval |
| `social_media.post_to_*()` | External action — Local only after approval |
| Any payment / banking action | Local + human approval required |
| Write to `Dashboard.md` | Single-writer rule — Local only |
| Access WhatsApp session | No Playwright session on Cloud VM |
| Move files to /Approved/ | Human action only |
| `odoo.create_invoice()` | Draft in /Pending_Approval/cloud/ — Local posts |

---

## Draft Format

When the Cloud agent completes a draft, it writes to `/Pending_Approval/cloud/`:

```markdown
# Cloud Draft — Email Reply: <subject>

> Status: Pending Human Review
> Created: YYYY-MM-DDT HH:MM:SSZ
> Agent: cloud
> Source: /In_Progress/cloud/<task>.md
> Risk Level: Medium
> Action Required: Review draft below, move file to /Approved/ or /Rejected/

---

## Original Message

**From:** sender@example.com
**Subject:** Original subject

[summary of original message]

---

## Drafted Reply

**To:** sender@example.com
**Subject:** Re: Original subject

[full draft email body]

---

## Human Notes

> Edit the draft above if needed, then move this file.
```

---

## Anthropic API Integration

```python
import anthropic
import os

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def draft_reply(task_content: str, skill_content: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=(
            "You are the Cloud AI Employee. Your job is to draft replies and content "
            "for human review. You NEVER send, post, or execute actions directly. "
            "Always write drafts in the approval file format from cloud_agent.skill.md."
        ),
        messages=[{"role": "user", "content": f"{skill_content}\n\n---\n\n{task_content}"}],
    )
    return response.content[0].text
```

---

## Health Signals

Every loop iteration (whether work was done or idle), write to `/Updates/`:

```markdown
# Cloud Health — YYYY-MM-DD HH:MM

> Agent: cloud
> Status: [active | idle]
> Tasks processed: N
> Last git sync: YYYY-MM-DDT HH:MM:SSZ
> Uptime: Xh Ym
```

Local agent reads this every 5 minutes and merges into Dashboard.md.

---

## Error Handling

Follow `error_handling.skill.md`. Additionally:
- Anthropic API rate limit → exponential backoff (retry_handler.py)
- Anthropic API down → log DEGRADED to /Updates/, sleep 10 min, retry
- git push conflict → retry after pull; if 3 failures → log to /Updates/ as WARNING
- Task content unreadable → move to /Review/ + log ERROR
