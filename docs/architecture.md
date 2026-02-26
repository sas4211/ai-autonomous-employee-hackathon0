# AI Employee — Architecture Deep Dive

> System design, component relationships, data flows, and design decisions.

---

## System Overview

The AI Employee is a **five-layer autonomous agent**:

```
Layer 1: BRAIN      Claude Code + CLAUDE.md + Agent Skills
Layer 2: MEMORY     Obsidian vault (Markdown files + folder state machine)
Layer 3: SENSES     Sentinel/watcher scripts (Gmail, Odoo, FB, Twitter, FS)
Layer 4: HANDS      MCP servers (filesystem, communications, odoo, social_media)
Layer 5: CONTROL    Ralph Wiggum stop hook (autonomous iteration loop)
```

Each layer has a single responsibility. They are decoupled — Claude Code can run without any sentinels. Sentinels can run without Claude Code. MCP servers are invoked only when Claude executes approved actions.

---

## Layer 1: Brain (Claude Code + Skills)

### How CLAUDE.md Works

Claude Code reads `CLAUDE.md` at session start. This file defines:
- **Scan order** — which folders to check, in what priority
- **Lifecycle rules** — when to move files, when to log, when to escalate
- **Planning rule** — create a Plan.md for any 2+ step task
- **Skills Reference** — a table pointing to every skill file

The **25 Agent Skills** in `/skills/` are the procedures. Each skill is a Markdown file Claude reads before performing that category of work. Skills are:
- **Readable by humans** — auditable, reviewable, editable without code changes
- **Referenced by name** — task files include `> Type: email_response` which tells Claude to load `gmail_send.skill.md`
- **Composable** — the planning skill references the approval skill; the weekly audit skill references the CEO briefing skill

### Skill Discovery

```
Task file: > Type: odoo_followup
               ↓
Claude reads: skills/odoo_accounting.skill.md
               ↓
Skill says: use get_accounting_summary MCP tool
               ↓
Claude calls: mcp_servers/odoo.py → get_accounting_summary()
```

---

## Layer 2: Memory (Vault as State Machine)

### Folder = State

```
/Inbox            "new, unclaimed"
/Active           "in progress"
/Pending_Approval "waiting for human sign-off"
/Approved         "green-lit, execute immediately"
/Needs_Action     "blocked, waiting for human input"
/Review           "error escalated, human must resolve"
/Done             "complete, immutable"
```

### Transitions

```
New task arrives
      |
      v
   /Inbox  ──────────────────────────────────── (sentinel writes here)
      |
      | Claude claims it
      v
  /Active  ──── needs input? ──── /Needs_Action ── human answers ──> /Active
      |
      | sensitive action?
      v
/Pending_Approval ── rejected? ──────────────────────────────────> /Done
      |
      | approved
      v
  /Approved ── Claude executes ──────────────────────────────────> /Done
      |
      | no approval needed
      v
   /Done
```

Every transition is a **file move** — atomic, auditable, and visible in any file browser or Obsidian view.

### Log Anatomy

Every action produces two records:

1. **Markdown log** in `/Logs/YYYY-MM-DD_action.md` — human-readable, linked from Dashboard
2. **JSON event** in `/Logs/events/TIMESTAMP_event_type.json` — machine-readable, consumed by sentinels

```json
{
  "event_id": "1740312000",
  "event_type": "task.completed",
  "timestamp": "2026-02-23T10:00:00Z",
  "source": "autonomy_loop",
  "payload": {
    "task": "2026-02-23_ceo-briefing.md",
    "from": "/Active",
    "to": "/Done"
  }
}
```

---

## Layer 3: Senses (Sentinels)

### What Sentinels Do

Sentinels watch external systems and translate events into vault task files. They are the only way work enters the vault automatically (without a human typing a prompt).

```
External Event                Sentinel              Vault Effect
─────────────    ─────────────────────────────    ─────────────────────────
Unread email  →  gmail_watcher.py (IMAP)       →  /Inbox/YYYY-MM-DD_email.md
Overdue invoice  odoo_watcher.py (JSON-RPC)    →  /Inbox/YYYY-MM-DD_odoo.md
FB comment    →  social_media_watcher.py (API) →  /Inbox/YYYY-MM-DD_fb.md
Twitter mention  social_media_watcher.py       →  /Inbox/YYYY-MM-DD_twitter.md
New /Inbox file  file_watcher.py (watchdog)    →  /Logs/events/*.json
```

### Sentinel Design Contract

Every sentinel obeys five rules (documented in `skills/sentinel.skill.md`):

1. **Graceful degradation** — if credentials are missing, print a message and return; never crash the scheduler
2. **Idempotency** — check if a task file already exists before creating one (prevent duplicates)
3. **Structured event logging** — write a JSON event to `/Logs/events/` for every external event
4. **State persistence** — track "what have I seen" in `.claude/` state files (e.g., last Twitter mention ID)
5. **Task file format** — always include `> Type:` and `> Source:` so Claude knows which skill to use

### Scheduler Architecture

```
scheduler.py (master process)
  |
  |── every  1 min  → heartbeat (vault state log)
  |── every  5 min  → gmail_watcher.py (subprocess)
  |── every 10 min  → linkedin_poster.py (subprocess)
  |── every 15 min  → social_media_watcher.py (subprocess)
  |── every 30 min  → odoo_watcher.py (subprocess)
  |── every  1 hr   → check_work_remaining.py (subprocess)
  |── Monday 09:00  → CEO briefing task → /Inbox
  |── Monday 09:00  → weekly_audit task → /Inbox
  └── Monday 09:05  → linkedin_post_draft task → /Inbox
```

Each sentinel runs as an **isolated subprocess** — one crash cannot affect others. The `schedule` library provides the timing; subprocess isolation provides the fault boundary.

---

## Layer 4: Hands (MCP Servers)

### What MCP Servers Do

MCP servers give Claude Code the ability to take **external actions** — not just read files, but send emails, post to social media, create Odoo invoices. Without MCP, Claude can only read/write local files.

Claude Code connects to MCP servers at startup via `.claude/mcp.json`. Each server exposes tools that Claude can invoke.

### Server Inventory

| Server | Transport | Tools |
|--------|-----------|-------|
| filesystem | `npx @modelcontextprotocol/server-filesystem` | read_file, write_file, move_file, list_directory, delete_file |
| communications | `python mcp_servers/communications.py` (FastMCP) | send_email, post_to_linkedin, send_whatsapp_message, log_to_vault |
| odoo | `python mcp_servers/odoo.py` (FastMCP) | get_accounting_summary, list_unpaid_invoices, get_sales_summary, get_cashflow_position, list_customers, create_invoice |
| social_media | `python mcp_servers/social_media.py` (FastMCP) | post_to_facebook, post_to_instagram, post_to_twitter, get_facebook_insights, get_instagram_insights, get_twitter_mentions, get_social_summary |

### Why FastMCP?

FastMCP is a Python library that wraps the MCP protocol. Instead of implementing the JSON-RPC wire protocol manually, we decorate functions with `@mcp.tool()` and FastMCP handles the rest. This reduced each MCP server from ~300 lines of boilerplate to ~80 lines of actual logic.

### Action Safety Model

```
Claude wants to send an email
          |
          v
    Is this action in /Approved?
          |
       Yes |  No
          |   |
          |   v
          |  Create /Pending_Approval task
          |  Wait for human to move to /Approved
          |
          v
    Call MCP tool: send_email(...)
          |
          v
    Log result in /Logs
          |
          v
    Move task to /Done
```

External actions NEVER happen without a prior `/Approved` file (unless the task was already low-risk per the approval skill rules).

---

## Layer 5: Control (Ralph Wiggum Stop Hook)

### The Problem

Claude Code stops after each response. Without intervention, a human must type `claude` again for each task. This breaks autonomy.

### The Solution

The Stop hook in `.claude/settings.json` runs `check_work_remaining.py` every time Claude is about to stop. The script:

1. Checks `/Approved`, `/Active`, `/Inbox`, `/Needs_Action` in priority order
2. If any folder has work → exits with code `1` and prints a continuation message
3. Claude Code treats exit code 1 as "user said continue" → resumes
4. If all folders are empty → exits with code `0` → Claude stops normally

### Iteration Guard

To prevent infinite loops (e.g., a bug that keeps creating tasks):

```python
MAX_ITERATIONS = 20

state = load_state()           # from .claude/wiggum_state.json
if state["iteration"] >= MAX_ITERATIONS:
    reset_state()
    exit(0)                    # stop even if work remains

state["iteration"] += 1
save_state()
exit(1)                        # continue
```

At iteration 17-19, warnings are printed. At 20, the loop stops and the state file resets for the next session.

---

## Data Flow: End-to-End Example

Here is a complete trace of an email arriving and Claude responding:

```
1. Gmail receives email from client
         |
2. gmail_watcher.py (polling every 5 min)
   - connects to Gmail IMAP
   - finds unread email
   - creates: /Inbox/2026-02-23_email-from-client.md
   - writes:  /Logs/events/1740312000_email.inbound.json
   - marks email as read
         |
3. Stop hook fires (Claude finishes previous task or is idle)
   - finds /Inbox has 1 file
   - exits 1 → Claude resumes
         |
4. Claude reads the task file
   - sees > Type: email_response
   - loads skills/gmail_send.skill.md
   - reads Company_Handbook.md for tone guidelines
         |
5. Claude creates a plan
   - writes /Active/2026-02-23_email-from-client_plan.md
   - plan contains: draft reply → request approval → send
         |
6. Claude drafts the reply
   - assesses: sending email = sensitive action
   - creates /Pending_Approval/2026-02-23_email-reply.md
   - moves task to /Active (stalled, waiting for approval)
   - updates Dashboard.md
         |
7. Human reviews /Pending_Approval/2026-02-23_email-reply.md
   - moves file to /Approved
         |
8. Stop hook fires again
   - finds /Approved has 1 file
   - exits 1 → Claude resumes
         |
9. Claude executes
   - calls MCP tool: send_email(to=..., body=...)
   - communications.py sends via SMTP
   - result: {"status": "sent"}
         |
10. Claude logs and closes
    - writes /Logs/2026-02-23_email-sent.md
    - moves task from /Active to /Done
    - updates Dashboard.md (tasks completed: +1)
    - updates /Logs/trust_ledger.md
         |
11. Stop hook fires
    - /Inbox empty, /Active empty, /Approved empty
    - exits 0 → Claude stops
```

---

## Maturity Model

```
Level 0: Skeleton    — folder structure + Dashboard
Level 1: Workflow    — Inbox→Active→Done pipeline + approval
Level 2: Awareness   — CEO briefing, skills folder, Dashboard updates
Level 3: Execution   — MCP server connected, approved actions executed
Level 4: Autonomy    — Stop hook, inbox processing, escalation, decomposition
Level 5: Trust       — 10+ tasks, 5+ approvals, historical briefings, rollback
```

Current level: **4 (Autonomy)** — infrastructure complete, accumulating runtime evidence for Level 5.

---

## Technology Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| AI reasoning | Claude Code (claude-sonnet-4-6) | Best-in-class code + reasoning; native MCP support |
| UI / state | Obsidian Markdown vault | No-code UI; human-readable; survives Claude crashes |
| MCP protocol | @modelcontextprotocol/server-filesystem + FastMCP | Official protocol; FastMCP eliminates boilerplate |
| Scheduling | Python `schedule` library | Simple, no infrastructure dependency |
| Filesystem watching | Python `watchdog` | Cross-platform real-time file events |
| Gmail | Python `imaplib` (stdlib) | No OAuth dance needed with App Passwords |
| LinkedIn | LinkedIn UGC Posts API (REST) | Most stable LinkedIn posting API |
| Facebook/Instagram | Meta Graph API v19.0 | Official programmatic posting |
| Twitter/X | `tweepy` + Twitter API v2 | Best Python client for Twitter |
| Odoo | JSON-RPC via `requests` | Odoo's native API; no third-party library needed |
| WhatsApp | Meta Business API | Official API for WhatsApp Business |
| Python project | UV + pyproject.toml + hatchling | Modern Python packaging |

---

## Complete System Architecture (Visual)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERSONAL AI EMPLOYEE                         │
│                      SYSTEM ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SOURCES                           │
├─────────────────┬─────────────────┬──────────────┬─────────────┤
│     Gmail       │    WhatsApp     │   Bank APIs  │    Files    │
└────────┬────────┴────────┬────────┴──────┬───────┴──────┬──────┘
         │                 │               │              │
         ▼                 ▼               ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PERCEPTION LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐         │
│  │ Gmail Watcher│  │WhatsApp Watch│  │Finance Watcher│         │
│  │  (Python)    │  │ (Playwright) │  │   (Python)    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬────────┘         │
└─────────┼─────────────────┼─────────────────┼──────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OBSIDIAN VAULT (Local)                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ /Inbox  │ /Active  │ /Done  │ /Logs                      │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ Dashboard.md  │  Company_Handbook.md  │  Business_Goals  │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ /Pending_Approval  │  /Approved  │  /Rejected            │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    REASONING LAYER                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      CLAUDE CODE                          │  │
│  │   Read → Think → Plan → Write → Request Approval          │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────┘
                                 │
              ┌──────────────────┴──────────────────┐
              ▼                                     ▼
┌─────────────────────────┐       ┌─────────────────────────────┐
│    HUMAN-IN-THE-LOOP    │       │         ACTION LAYER        │
│  ┌─────────────────────┐│       │  ┌──────────────────────┐   │
│  │Review Approval Files││──────▶│  │      MCP SERVERS     │   │
│  │Move to /Approved    ││       │  │  ┌───────┐ ┌───────┐ │   │
│  └─────────────────────┘│       │  │  │ Email │ │Browser│ │   │
└─────────────────────────┘       │  │  │  MCP  │ │  MCP  │ │   │
                                  │  │  └───┬───┘ └───┬───┘ │   │
                                  │  └──────┼─────────┼─────┘   │
                                  └─────────┼─────────┼─────────┘
                                            │         │
                                            ▼         ▼
                                  ┌───────────────────────────────┐
                                  │       EXTERNAL ACTIONS        │
                                  │ Send Email  │  Make Payment   │
                                  │ Post Social │  Update Calendar│
                                  └───────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           sentinels/scheduler.py (Master Process)         │  │
│  │   Scheduling │ Folder Watching │ Process Management       │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           sentinels/watchdog.py (Health Monitor)          │  │
│  │   Restart Failed Processes │ Alert on Errors              │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```
