# Skill: Gmail Send (Email Response)

> Skill Name: `gmail_send.draft_and_send`
> Category: Communications / External Action
> Type: External Action (requires approval)
> Trigger: Email task in /Inbox (from gmail_watcher sentinel)
> Output: Draft in `/Pending_Approval/` → sent via MCP

---

## Purpose

Draft and send email responses on behalf of the operator. All outbound emails go through the human-in-the-loop approval gate. Claude reads, understands, and drafts — the human reviews before anything is sent.

---

## Workflow

### Step 1 — Read the Inbound Email

Read the task file created by `gmail_watcher.py` in `/Inbox/`. Extract:
- Sender name and email
- Subject and message content
- What the sender wants or needs
- Urgency indicators

### Step 2 — Categorise

| Category | Action |
|----------|--------|
| Requires a reply | Draft response → `/Pending_Approval/` |
| For information only | Log and move to `/Done/` |
| Requires escalation | Move to `/Review/` with notes |
| Spam / irrelevant | Move to `/Done/` with note "no action needed" |

### Step 3 — Draft the Response

Follow tone guidelines in `Company_Handbook.md`:
- Professional but warm
- Concise — no padding
- Clear ask or next step at the end
- Sign off as the operator

### Step 4 — Create Approval Request

Save to `/Pending_Approval/YYYY-MM-DD_email-reply-<slug>.md`:

```markdown
# Approval Request — Email Reply

> Status: Pending
> Created: YYYY-MM-DD
> Requested by: Claude Code
> Type: email_response
> Risk Level: Medium

---

## Action

Send the email reply below via Gmail.

## Original Email

**From:** {{sender}}
**Subject:** {{subject}}

{{original message summary}}

## Drafted Reply

**To:** {{sender email}}
**Subject:** Re: {{subject}}

{{drafted reply body}}

## Rollback Plan

Email cannot be unsent. If sent in error, follow up immediately with a correction email.

## Status

- [ ] Approved — move this file to /Approved
- [ ] Rejected — move this file to /Done with notes

## Human Notes

> _Edit the reply above if needed. Then move file._
```

### Step 5 — Wait for Approval

Do not send. Log the pending action in `/Logs/`.

### Step 6 — Send (after approval)

When file is moved to `/Approved/`:

Use the `communications` MCP tool:
```
send_email(
  to="<recipient>",
  subject="Re: <subject>",
  body="<drafted reply>"
)
```

### Step 7 — Log and Complete

- Log send result (success/failure) in `/Logs/`
- Move task and approval file to `/Done/`
- Update Dashboard

---

## MCP Tool

```
Server: communications
Tool: send_email(to, subject, body, cc="")
```

Requires `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` in `.env`.

---

## Rules

- Never send without an approval file in `/Approved/`
- Never modify the approved reply content after approval
- Always log the sent email (to, subject, timestamp) in `/Logs/`
- If send fails, log the error and move to `/Review/`
- Spam / phishing emails must be moved to `/Done/` without a reply
