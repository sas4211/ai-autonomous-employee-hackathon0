# Personal AI Employee

> An autonomous AI employee built on Claude Code + an Obsidian vault.
> Hackathon 0: Building Autonomous FTEs — Gold Tier implementation.

---

## What This Is

The AI Employee uses **Claude Code as its brain** and **an Obsidian vault as its UI**. There is no web app, no database, no custom framework. Markdown files are the interface. Folder moves are the workflow transitions. File watchers are the senses.

The result is a fully autonomous agent that:
- Monitors Gmail, Odoo, Facebook, Instagram, and Twitter for work
- Processes that work through a human-gated approval pipeline
- Executes approved actions via MCP servers (email, LinkedIn, social posts, Odoo operations)
- Keeps the CEO informed with structured briefings
- Logs everything, never silently fails, and escalates when blocked

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                     BRAIN (Claude Code)                      │
│  CLAUDE.md + skills/*.skill.md = instructions + procedures  │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │                         │
┌─────────▼─────────┐   ┌──────────▼──────────┐
│   MEMORY (Vault)  │   │   CONTROL (Hooks)    │
│  /Inbox /Active   │   │  Stop hook → Ralph   │
│  /Done /Approved  │   │  Wiggum loop         │
│  /Pending_Approval│   │  Max 20 iterations   │
│  /Logs /Briefings │   └─────────────────────┘
└─────────┬─────────┘
          │
    ┌─────┴──────┐
    │            │
┌───▼───┐   ┌────▼────────────────────────────────┐
│SENSES │   │            HANDS (MCP Servers)       │
│       │   │  filesystem  communications          │
│Gmail  │   │  odoo        social_media            │
│Odoo   │   │                                      │
│FB/IG  │   │  send_email   post_to_linkedin       │
│Twitter│   │  post_to_facebook  post_to_instagram │
│Files  │   │  post_to_twitter   create_invoice    │
└───────┘   └─────────────────────────────────────┘
```

---

## Folder Structure

```
ai-empolyee/
├── CLAUDE.md                    # Agent instructions (the brain)
├── Dashboard.md                 # Live operational state (the UI)
├── Company_Handbook.md          # Business context + policies
├── README.md                    # This file
│
├── Inbox/                       # New tasks (sentinels drop here)
├── Active/                      # In-progress tasks + Plan.md files
├── Done/                        # Completed tasks (immutable audit trail)
├── Pending_Approval/            # Awaiting human sign-off
├── Approved/                    # Approved — Claude executes immediately
├── Needs_Action/                # Claude is blocked, needs human input
├── Review/                      # Escalated errors for human review
├── Briefings/                   # CEO briefings (dated)
├── Logs/                        # All audit logs + event JSON
│   ├── events/                  # Structured JSON event logs
│   ├── trust_ledger.md          # Level 5 maturity evidence
│   └── *.md                     # Action logs, approval logs
├── Templates/                   # Approval request template, plan template
│
├── skills/                      # All AI functionality as Agent Skills (25 files)
├── sentinels/                   # Watcher scripts (7 scripts)
│   ├── scheduler.py             # Master scheduler
│   ├── file_watcher.py          # Filesystem monitor (watchdog)
│   ├── gmail_watcher.py         # Gmail IMAP poller
│   ├── linkedin_poster.py       # LinkedIn publisher
│   ├── odoo_watcher.py          # Odoo invoice + order monitor
│   ├── social_media_watcher.py  # Facebook + Twitter monitor
│   └── check_work_remaining.py  # Ralph Wiggum stop hook
├── mcp_servers/                 # FastMCP external action servers (4 servers)
│   ├── communications.py        # Email, LinkedIn, WhatsApp
│   ├── odoo.py                  # Odoo JSON-RPC (6 tools)
│   └── social_media.py          # FB, IG, Twitter (7 tools)
├── scripts/                     # Setup scripts
│   ├── setup_scheduler.ps1      # Windows Task Scheduler registration
│   └── start_sentinels.ps1      # One-command sentinel startup
├── docs/                        # Technical documentation
│   ├── architecture.md          # Deep-dive architecture
│   └── lessons_learned.md       # What we learned building this
│
├── .claude/
│   ├── mcp.json                 # MCP server config (4 servers)
│   ├── settings.json            # Stop hook (Ralph Wiggum)
│   └── wiggum_state.json        # Iteration counter (auto-generated)
├── .env                         # Credentials (not in git)
├── .env.example                 # Credentials template
└── pyproject.toml               # Python project + dependencies
```

---

## Quick Start (5 Minutes)

### Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Claude Code | Latest | `claude --version` |
| Node.js | v18+ | `node --version` |
| Python | 3.11+ | `python --version` |

### Step 1 — Clone and Install

```bash
git clone <repo-url>
cd ai-empolyee
pip install -e .
```

### Step 2 — Configure Credentials

```bash
cp .env.example .env
# Edit .env and add your credentials
```

Minimum for basic demo (no external integrations):
- Leave `.env` empty — all sentinels degrade gracefully without credentials

### Step 3 — Verify MCP Servers

```bash
python mcp_servers/communications.py --test
python mcp_servers/odoo.py --test
python mcp_servers/social_media.py --test
```

### Step 4 — Start Claude Code

```bash
claude
```

Claude will:
1. Load `CLAUDE.md` and all skill files
2. Scan `/Approved`, `/Active`, `/Inbox`, `/Needs_Action`
3. Act on the highest-priority item
4. Update `Dashboard.md`

### Step 5 — Drop a Task

Create a file in `/Inbox`:

```bash
# Windows
type > "Inbox\2026-02-23_test-task.md"
```

Content:
```markdown
# Task: Test the autonomy loop

> Status: New
> Created: 2026-02-23
> Priority: Low

## Description
Verify that Claude picks up this task, moves it through the pipeline, and updates Dashboard.md.

## Acceptance Criteria
- [ ] Task moved from /Inbox to /Active
- [ ] Task moved from /Active to /Done
- [ ] Dashboard.md updated
```

---

## Hackathon Tier Status

| Tier | Status | Key Deliverables |
|------|--------|-----------------|
| Bronze | ✅ Complete | Dashboard, Company_Handbook, file watcher, MCP filesystem, 7 folders, skills |
| Silver | ✅ Complete | Gmail watcher, LinkedIn poster, Plan.md loop, Communications MCP, approval workflow, scheduler |
| Gold | ✅ Complete | Odoo MCP (6 tools), Social Media MCP (7 tools, FB+IG+Twitter), 4 MCP servers, 7 sentinels, 25 skills, enhanced Ralph Wiggum |

---

## Agent Skills (25 Files)

All AI functionality is defined as documented Markdown skill files in `/skills/`. Claude reads these before acting.

| Skill | Purpose |
|-------|---------|
| `autonomy.skill.md` | Main control loop |
| `approval.skill.md` | Human-in-the-loop gate |
| `planning.skill.md` | Plan.md reasoning before multi-step tasks |
| `dashboard.skill.md` | Refresh vault state display |
| `decomposition.skill.md` | Break complex tasks into subtasks |
| `error_handling.skill.md` | Fail safely, escalate clearly |
| `mcp_filesystem.skill.md` | File operations via MCP |
| `trust_tracker.skill.md` | Level 5 maturity evidence |
| `rollback.skill.md` | Undo completed actions safely |
| `event_bus.skill.md` | Publish/subscribe to task lifecycle events |
| `ceo_briefing.skill.md` | Executive briefing generation |
| `scheduled_briefing.skill.md` | Auto-trigger briefings on schedule |
| `reproduce.skill.md` | Judge-facing guide to run the full loop |
| `linkedin_post.skill.md` | Generate + publish LinkedIn posts via approval |
| `gmail_send.skill.md` | Draft + send email via approval |
| `odoo_accounting.skill.md` | Odoo P&L, invoices, sales, cashflow |
| `social_media.skill.md` | Cross-platform content + reporting |
| `weekly_audit.skill.md` | Weekly business + accounting CEO briefing |
| `cross_domain.skill.md` | Route personal vs business tasks |
| `audit_log.skill.md` | Comprehensive 7-level logging standard |
| `ralph_wiggum.skill.md` | Autonomous stop hook / iteration loop |
| `sentinel.skill.md` | Watcher pattern design contract |
| `maturity-checklist.md` | Bronze / Silver / Gold tier checklist |

---

## Running Sentinels

### One Command (All Sentinels)

```powershell
.\scripts\start_sentinels.ps1
```

### Master Scheduler (Recommended)

```bash
python sentinels/scheduler.py          # runs forever
python sentinels/scheduler.py --once   # run all once and exit
```

### Individual Sentinels

```bash
python sentinels/file_watcher.py               # real-time /Inbox monitor
python sentinels/gmail_watcher.py --loop        # Gmail every 5 min
python sentinels/linkedin_poster.py --watch     # LinkedIn publisher
python sentinels/odoo_watcher.py --loop         # Odoo every 30 min
python sentinels/social_media_watcher.py --loop # FB + Twitter every 15 min
```

---

## Credentials Required

| Platform | Environment Variables | Where to Get |
|----------|----------------------|--------------|
| Gmail | `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD` | Google Account > App Passwords |
| LinkedIn | `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN` | LinkedIn Developer Portal |
| Facebook | `FACEBOOK_ACCESS_TOKEN`, `FACEBOOK_PAGE_ID` | developers.facebook.com |
| Instagram | `INSTAGRAM_ACCOUNT_ID` | Meta Business Suite |
| Twitter/X | `TWITTER_BEARER_TOKEN`, `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_TOKEN_SECRET` | developer.twitter.com |
| Odoo | `ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD` | Self-hosted Odoo 19 |
| WhatsApp | `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` | Meta Business API |

All credentials are optional — every sentinel and MCP server degrades gracefully when credentials are missing.

---

## Technical Documentation

- [Architecture Deep Dive](docs/architecture.md)
- [Lessons Learned](docs/lessons_learned.md)
- [Reproduce / Judge Guide](skills/reproduce.skill.md)
