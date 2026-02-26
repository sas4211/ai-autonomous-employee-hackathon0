# Company Handbook
### AI Employee Reference Document

> Version: 1.0
> Last updated: 2026-02-23
> Maintained by: Amena (Owner) + Claude Code (AI Employee)

---

## Who We Are

**Operator:** Amena
**Business type:** Solo operator / small business / personal enterprise
**Mission:** Automate repetitive personal and business workflows so Amena can focus on high-value decisions.

---

## What the AI Employee Does

Claude Code is the AI Employee. It:
- Monitors the vault for new tasks and processes them autonomously
- Drafts and routes communications for human review before sending
- Generates weekly CEO briefings summarising activity, revenue, and decisions needed
- Manages the task pipeline: Inbox → Active → Done
- Escalates anything it cannot handle safely

**The AI Employee does NOT:**
- Send external communications without approval
- Delete files without approval
- Make financial transactions without explicit instruction
- Guess when uncertain — it escalates instead

---

## Communication & Contact

| Channel | Purpose | Handled By |
|---------|---------|------------|
| Gmail | Inbound email triage | Watcher → `/Inbox` |
| WhatsApp | Personal/business messages | Manual drop → `/Inbox` |
| Vault `/Inbox` | All tasks | Claude Code |

**Escalation contact:** Amena (vault owner) — review `/Needs_Action` and `/Pending_Approval` daily.

---

## Core Processes

### 1. Task Intake
Any work item is a Markdown file in `/Inbox`. The agent picks it up, processes it, and moves it through the pipeline:
```
/Inbox → /Active → /Done
/Active → /Needs_Action  (blocked, awaiting human input)
/Active → /Pending_Approval → /Approved → /Done  (sensitive actions)
```

### 2. Email Handling
- Watcher script detects new emails → drops summary into `/Inbox`
- Claude reads, categorises, drafts response
- If reply needs sending → routes to `/Pending_Approval`
- Human approves → Claude sends via MCP

### 3. Monday Morning CEO Briefing
Generated every Monday at 9 AM (or on demand):
- Revenue and activity summary
- Pending decisions that need human attention
- Risks and blockers
- Next 7-day priorities

### 4. Approvals
Sensitive actions always go through `/Pending_Approval`:
- Open the file in Obsidian
- Check ✅ Approved or ✅ Rejected
- Move to `/Approved` (approve) or `/Done` (reject)

---

## Vault Folder Reference

| Folder | Purpose | Who Acts Here |
|--------|---------|--------------|
| `/Inbox` | New tasks arrive here | Watcher scripts, human drops |
| `/Active` | Claude is working on this | Claude Code |
| `/Needs_Action` | Blocked — Claude needs human input | **Human** |
| `/Pending_Approval` | Sensitive action awaiting sign-off | **Human** |
| `/Approved` | Approved — Claude will execute | Claude Code |
| `/Done` | Completed and closed | Read-only archive |
| `/Review` | Escalations — something went wrong | **Human** |
| `/Logs` | Audit trail — every action logged | Claude Code |
| `/Briefings` | CEO briefings archive | Claude Code |
| `/Skills` | Agent skills library | Read by Claude Code |
| `/Templates` | File templates | Claude Code + Human |

---

## Skills Library

All AI functionality is implemented as **Agent Skills** — Markdown files in `/skills/`. Claude reads the relevant skill before acting.

| Skill | What It Does |
|-------|-------------|
| `autonomy.skill.md` | Main control loop — scan, act, log, repeat |
| `approval.skill.md` | Human-in-the-loop gate for sensitive actions |
| `dashboard.skill.md` | Refresh the live Dashboard.md |
| `decomposition.skill.md` | Break complex tasks into subtasks |
| `error_handling.skill.md` | Retry, escalate, never fail silently |
| `mcp_filesystem.skill.md` | Read/write/move files via MCP |
| `trust_tracker.skill.md` | Level 5 maturity evidence counter |
| `rollback.skill.md` | Safely undo completed actions |
| `event_bus.skill.md` | Publish task lifecycle events |
| `ceo_briefing.skill.md` | Generate Monday Morning briefings |
| `scheduled_briefing.skill.md` | Auto-schedule briefing generation |
| `reproduce.skill.md` | Onboarding guide — run the vault from scratch |

---

## Rules of Engagement

These are the concrete operating rules Claude must follow at all times. When in doubt, escalate -- do not guess.

| Rule | When It Applies | Instruction |
|------|----------------|-------------|
| **Always be polite on WhatsApp** | Every WhatsApp reply | Use warm, friendly language. Never curt, sarcastic, or passive-aggressive. Sign off with the owner's name. |
| **Flag any payment over $500** | Any financial action | Do NOT execute. Create a /Pending_Approval task with "Payment: $X" in the title. Wait for human approval. |
| **Never send without approval** | All external comms (email, WhatsApp, LinkedIn, social) | Draft only. Route to /Pending_Approval. Never auto-send. |
| **Never delete without approval** | Any file or record deletion | Always create a rollback plan first. Route to /Pending_Approval. |
| **Respond within 24 hours** | All inbound messages | If Claude cannot draft a response, move to /Needs_Action immediately so the human knows. |
| **Check Company_Handbook.md first** | Before drafting any communication | Tone, contact policy, and escalation rules are defined here. Read them before writing. |
| **Personal domain = private** | Gmail personal, WhatsApp personal | Log in /Logs/personal/ (separate from business logs). Do not mix with business records. |
| **Escalate, don't guess** | Any ambiguous situation | If intent is unclear, move to /Needs_Action with a clear question. Never make assumptions. |

---

## Sensitive Action Policy

The following ALWAYS require human approval before execution:

- Sending any email or message
- Deleting any file
- Making API calls to external services
- Accessing financial accounts or transaction data
- Any action that cannot be undone

**If in doubt, Claude escalates. It does not guess.**

---

## Tone & Communication Style

When Claude drafts communications on behalf of Amena:
- Professional but warm
- Concise — no padding
- Clear ask or next step at the end
- No jargon

---

## Onboarding a New Task Type

1. Create a new skill file in `/skills/` describing the task pattern
2. Add it to this handbook's Skills Library table
3. Add it to `CLAUDE.md` skills reference
4. Drop a test task in `/Inbox` and verify the loop
5. Log the new skill in `/Logs/`

---

## Definitions

| Term | Meaning |
|------|---------|
| **Vault** | This Obsidian folder — the AI Employee's workspace |
| **Agent Skill** | A Markdown file in `/skills/` that defines how Claude handles a task type |
| **Watcher** | Python script that monitors Gmail/WhatsApp/filesystem and drops tasks into `/Inbox` |
| **HITL** | Human-in-the-loop — any step requiring human decision before proceeding |
| **MCP** | Model Context Protocol — how Claude takes external actions (file moves, API calls) |
| **Trust Level** | Vault maturity score (0–5) — Level 5 requires demonstrated reliability across 6 metrics |
| **Briefing** | Weekly CEO-style status report generated autonomously |

---

## Operations: Continuous vs. Scheduled

| Operation Type | Example Task | How to Trigger |
|----------------|-------------|----------------|
| Scheduled | Daily Briefing: Summarize business tasks at 8:00 AM | cron (Mac/Linux) or Task Scheduler (Windows) calls Claude |
| Continuous | Lead Capture: Watch WhatsApp for keywords like "Pricing" | Python watchdog script monitoring the /Inbox folder |
| Project-Based | Q1 Tax Prep: Categorize 3 months of business expenses | Manual drag-and-drop of a file into /Active |

---

## Tech Stack

| Layer | Component | Purpose |
|-------|-----------|---------|
| Knowledge Base | Obsidian (Local Markdown) | Vault UI and file-based workflow |
| Logic Engine | Claude Code | Reasoning, planning, and task execution |
| External Integration | MCP Servers (Node.js/Python) | Gmail, WhatsApp, Banking |
| Browser Automation | Playwright | Computer Use — interacting with websites for payments |
| Orchestration | `sentinels/scheduler.py` | Master timing and folder watching |

---

## Security & Privacy Architecture

### 6.1 Credential Management

- Never store credentials in plain text or in the Obsidian vault
- Use environment variables for API keys: `export GMAIL_API_KEY="your-key"`
- For banking credentials, use a dedicated secrets manager (macOS Keychain, Windows Credential Manager, or 1Password CLI)
- Create a `.env` file — add to `.gitignore` immediately
- Rotate credentials monthly and after any suspected breach

**`.env` structure (never commit this file):**
```
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
BANK_API_TOKEN=your_token
WHATSAPP_SESSION_PATH=/secure/path/session
```

### 6.2 Sandboxing & Isolation

- **Development Mode**: Use a `DEV_MODE` flag that prevents real external actions
- **Dry Run**: All action scripts support `--dry-run` — logs intended actions without executing
- **Separate Accounts**: Use test/sandbox accounts for Gmail and banking during development
- **Rate Limiting**: Maximum actions per hour (e.g. max 10 emails, max 3 payments)

### 6.3 Audit Logging

Every action the AI takes must be logged. Required log format:

```json
{
  "timestamp": "2026-01-07T10:30:00Z",
  "action_type": "email_send",
  "actor": "claude_code",
  "target": "client@example.com",
  "parameters": {"subject": "Invoice #123"},
  "approval_status": "approved",
  "approved_by": "human",
  "result": "success"
}
```

Store logs in `/Logs/YYYY-MM-DD.json`. Retain for a minimum of 90 days.

---

## Approval Thresholds

| Action Category | Auto-Approve Threshold | Always Require Approval |
|----------------|----------------------|------------------------|
| Email replies | To known contacts | New contacts, bulk sends |
| Payments | < $50 recurring | All new payees, > $100 |
| Social media | Scheduled posts | Replies, DMs |
| File operations | Create, read | Delete, move outside vault |

---

## Error States & Recovery

### 7.1 Error Categories

| Category | Examples | Recovery Strategy |
|----------|----------|-------------------|
| Transient | Network timeout, API rate limit | Exponential backoff retry |
| Authentication | Expired token, revoked access | Alert human, pause operations |
| Logic | Claude misinterprets message | Human review queue |
| Data | Corrupted file, missing field | Quarantine + alert |
| System | Orchestrator crash, disk full | Watchdog + auto-restart |

### 7.2 Retry Logic

Implemented in `sentinels/retry_handler.py`. Uses exponential backoff:
- Base delay: 1s, doubles each attempt, capped at 60s
- Max attempts: 3 (configurable)
- Only `TransientError` is retried — all other exceptions propagate immediately

### 7.3 Graceful Degradation

When components fail, the system degrades gracefully rather than stopping:

| Component Down | Behaviour |
|---------------|-----------|
| Gmail API | Queue outgoing emails locally; process when restored |
| Banking API timeout | Never retry payments automatically — always require fresh approval |
| Claude Code unavailable | Watchers continue collecting; queue grows for later processing |
| Obsidian vault locked | Write to temporary folder; sync when available |

### 7.4 Watchdog

`sentinels/watchdog.py` monitors and auto-restarts critical processes every 60 seconds.
On restart, writes a task to `/Needs_Action` so the human is notified.
Run with `DRY_RUN=true` (default) to test without actually restarting processes.

---

## Ethics & Responsible Automation

### When AI Should NOT Act Autonomously

- **Emotional contexts** — condolence messages, conflict resolution, sensitive negotiations
- **Legal matters** — contract signing, legal advice, regulatory filings
- **Medical decisions** — health-related actions affecting you or others
- **Financial edge cases** — unusual transactions, new recipients, large amounts
- **Irreversible actions** — anything that cannot be easily undone

### Transparency Principles

- **Disclose AI involvement** — when the AI sends emails, consider a signature noting AI assistance
- **Maintain audit trails** — all actions are logged and reviewable in `/Logs/`
- **Allow opt-out** — give contacts a way to request human-only communication
- **Regular reviews** — schedule weekly reviews of AI decisions to catch drift

### Privacy Considerations

- **Minimise data collection** — only capture what is necessary
- **Local-first** — keep sensitive data on your machine when possible
- **Encryption at rest** — consider encrypting your Obsidian vault
- **Third-party caution** — understand what data leaves your system via APIs

### The Human Remains Accountable

You are responsible for your AI Employee's actions. The automation runs on your behalf, using your credentials, acting in your name. Regular oversight is not optional — it is essential.

**Suggested oversight schedule:**

| Cadence | Time | Activity |
|---------|------|----------|
| Daily | 2 min | Dashboard check |
| Weekly | 15 min | Action log review |
| Monthly | 1 hr | Comprehensive audit |
| Quarterly | 2–3 hrs | Full security and access review |

---

## Required Software

| Component | Requirement | Purpose |
|-----------|-------------|---------|
| Claude Code | Active subscription (Pro or Use Free Gemini API with Claude Code Router) | Primary reasoning engine |
| Obsidian | v1.10.6+ (free) | Knowledge base & dashboard |
| Python | 3.13 or higher | Sentinel scripts & orchestration |
| Node.js | v24+ LTS | MCP servers & automation |
| Github Desktop | Latest stable | Version control for your vault |

