# Vault Maturity Checklist

> Track the AI Employee vault from scaffolding to production-ready.

---

## 🥉 Bronze Tier (Hackathon Minimum Viable Deliverable)

- [x] `Dashboard.md` at vault root
- [x] `Company_Handbook.md` at vault root
- [x] File system watcher (`sentinels/file_watcher.py`) — confirmed working
- [x] Claude Code reads from and writes to the vault (MCP filesystem)
- [x] `/Inbox` folder
- [x] `/Needs_Action` folder
- [x] `/Done` folder
- [x] All AI functionality implemented as Agent Skills (`/skills/`)

**Bronze status: ✅ COMPLETE**

---

## 🥈 Silver Tier (Hackathon Intermediate)

- [x] All Bronze requirements met
- [x] Gmail watcher (`sentinels/gmail_watcher.py`) — IMAP polling, drops email tasks to /Inbox
- [x] LinkedIn poster watcher (`sentinels/linkedin_poster.py`) — publishes approved posts, queues drafts
- [x] LinkedIn auto-post skill (`skills/linkedin_post.skill.md`) — generate, approve, publish
- [x] Plan.md reasoning loop (`skills/planning.skill.md`) — Claude creates plan before every multi-step task
- [x] `Templates/plan.md` — Plan.md template
- [x] Communications MCP server (`mcp_servers/communications.py`) — send_email, post_to_linkedin, send_whatsapp_message, log_to_vault (FastMCP, self-test passing)
- [x] Communications MCP registered in `.claude/mcp.json`
- [x] Human-in-the-loop approval workflow — `skills/approval.skill.md` + /Pending_Approval pipeline
- [x] Gmail send skill (`skills/gmail_send.skill.md`) — draft + approve + send
- [x] Master scheduler (`sentinels/scheduler.py`) — schedule library, all jobs wired
- [x] Windows Task Scheduler setup (`scripts/setup_scheduler.ps1`) — registers 5 tasks
- [x] Credentials template (`.env.example`) — Gmail, LinkedIn, WhatsApp
- [x] All AI functionality as Agent Skills (17 skills total)

**Silver status: ✅ COMPLETE** _(credentials needed in .env to activate Gmail + LinkedIn)_

---

## 🥇 Gold Tier (Hackathon Advanced)

- [x] All Silver requirements met
- [x] Cross-domain routing (`skills/cross_domain.skill.md`) — personal vs business domain tagging
- [x] Odoo MCP server (`mcp_servers/odoo.py`) — 6 tools: P&L, invoices, sales, cashflow, customers, create_invoice
- [x] Odoo watcher (`sentinels/odoo_watcher.py`) — overdue invoices + new orders drop to /Inbox
- [x] Odoo accounting skill (`skills/odoo_accounting.skill.md`) — full workflow + graceful degradation
- [x] Facebook MCP tools — post_to_facebook, get_facebook_insights
- [x] Instagram MCP tools — post_to_instagram, get_instagram_insights
- [x] Twitter/X MCP tools — post_to_twitter, get_twitter_mentions
- [x] Social media MCP server (`mcp_servers/social_media.py`) — 7 tools, self-test passing
- [x] Social media watcher (`sentinels/social_media_watcher.py`) — FB comments + Twitter mentions
- [x] Social media skill (`skills/social_media.skill.md`) — cross-platform content calendar
- [x] get_social_summary — aggregates FB + IG + Twitter in one call
- [x] 4 MCP servers registered in `.claude/mcp.json` (filesystem, communications, odoo, social_media)
- [x] Weekly business + accounting audit (`skills/weekly_audit.skill.md`) — all domains combined
- [x] Weekly audit queued every Monday by scheduler
- [x] Error recovery + graceful degradation — every MCP server handles missing credentials + offline services
- [x] Comprehensive audit logging (`skills/audit_log.skill.md`) — 7 levels, structured JSON + markdown
- [x] Enhanced Ralph Wiggum (`sentinels/check_work_remaining.py`) — iteration guard (max 20), priority-aware, rich instructions
- [x] Session state tracking (`.claude/wiggum_state.json`) — prevents infinite loops
- [x] Master scheduler upgraded — 9 jobs covering all 4 platforms + Odoo
- [x] `scripts/start_sentinels.ps1` — one-command sentinel startup

**Gold status: ✅ COMPLETE** _(credentials needed in .env to activate all integrations)_

---

## Level 0: Skeleton

- [x] Vault folder structure created
- [x] `Dashboard.md` generated
- [x] `/Logs` folder with audit entries
- [x] `/Templates` folder with at least one template

## Level 1: Workflow

- [x] `/Inbox` -> `/Active` -> `/Done` pipeline defined
- [x] `/Pending_Approval` folder and approval skill
- [x] Approval request template with decision checkboxes
- [x] File moves = state transitions documented
- [x] First task processed end-to-end (Inbox -> Done)

## Level 2: Awareness

- [x] CEO briefing skill (`/Briefings`)
- [x] Skills folder with documented skill files
- [x] Claude Code reads folder state before acting
- [x] Claude Code updates Dashboard after every action
- [x] Scheduled briefing generation (daily or on-change) — `scheduled_briefing.skill.md` + sentinel heartbeat

## Level 3: Execution

- [x] At least one MCP server connected
- [x] Claude Code executes an approved action via MCP — filesystem MCP runtime-tested
- [x] Result logged in `/Logs` with success/failure
- [x] Post-execution file moved to `/Done`

## Level 4: Autonomy

- [x] Claude Code picks up tasks from `/Inbox` without prompting
- [x] Escalation criteria applied automatically
- [x] Multi-step task decomposition (parent -> subtasks)
- [x] Error handling: failed actions logged, retried or escalated

## Level 5: Trust

- [ ] 10+ tasks completed end-to-end
- [ ] 5+ approvals processed (mix of approved/rejected)
- [ ] Briefings reference historical trends
- [ ] Human override log reviewed with no surprises
- [ ] Rollback executed successfully at least once

---

## Current Level: **4**

Level 4 skills are defined and wired into `CLAUDE.md`. Next milestone: Level 5 (Trust) — accumulate 10+ completed tasks, 5+ approvals, historical briefings, and a successful rollback.
