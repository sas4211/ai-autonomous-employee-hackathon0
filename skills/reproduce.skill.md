# Skill: Reproduce (Judge & Onboarding Guide)

> Skill Name: `reproduce`
> Category: Documentation / Reproducibility
> Type: Reference
> Audience: Judges, new users, contributors
> Output: This file — a step-by-step guide to reproduce the full autonomy loop

---

## Purpose

Allow anyone (hackathon judges, teammates, future users) to clone this vault and run the full autonomous AI Employee loop from scratch in under 30 minutes.

---

## Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Claude Code | Latest | `claude --version` |
| Node.js | v24+ LTS | `node --version` |
| Python | 3.13+ | `python --version` |
| UV | Latest | `uv --version` |
| Obsidian | v1.10.6+ | Open app |
| Git | Any | `git --version` |

---

## Setup (One-Time)

### Step 1 — Clone or Copy the Vault

```bash
git clone <repo-url>
cd ai-empolyee
```

Or copy the vault folder to your machine.

### Step 2 — Install Python Dependencies

```bash
pip install -e .
```

This installs: watchdog, fastmcp, schedule, python-dotenv, requests, google-auth, google-auth-oauthlib, google-api-python-client, tweepy

Or install manually:

```bash
pip install watchdog fastmcp schedule python-dotenv requests tweepy
```

### Step 3 — Configure Credentials (Optional for Demo)

```bash
cp .env.example .env
# Edit .env with your API keys
```

All integrations degrade gracefully — you can skip this for a demo and all sentinels + MCP servers will report "not configured" instead of crashing.

### Step 4 — Verify MCP Servers

```bash
python mcp_servers/communications.py --test   # expect: 4 tools registered
python mcp_servers/odoo.py --test             # expect: 6 tools registered
python mcp_servers/social_media.py --test     # expect: 7 tools registered
```

The filesystem MCP server uses `npx @modelcontextprotocol/server-filesystem` — downloaded automatically on first use.

### Step 5 — Open in Obsidian (Optional)

1. Open Obsidian
2. Open vault → select this folder
3. You should see `Dashboard.md` as the home view

### Step 6 — Verify Claude Code Reads the Vault

```bash
claude
```

Claude Code will:
1. Read `CLAUDE.md` and load all 25 agent skills
2. Scan `/Approved`, `/Active`, `/Inbox`, `/Needs_Action` in priority order
3. Act on the highest-priority item found
4. Update `Dashboard.md`

---

## Running the Autonomy Loop

### Option A — Manual Trigger

1. Drop a task file into `/Inbox` (use the template below)
2. Run `claude` in the vault directory
3. Watch Claude pick it up, move it to `/Active`, execute it, move it to `/Done`
4. Open `Dashboard.md` to see the updated state

### Option B — Sentinel Watcher (Auto-Trigger)

Start the master scheduler (runs all sentinels):

```bash
python sentinels/scheduler.py
```

Or start all sentinels at once:

```powershell
.\scripts\start_sentinels.ps1
```

Or start individual sentinels:

```bash
python sentinels/file_watcher.py               # real-time /Inbox monitor
python sentinels/gmail_watcher.py --loop        # Gmail every 5 min
python sentinels/odoo_watcher.py --loop         # Odoo every 30 min
python sentinels/social_media_watcher.py --loop # FB + Twitter every 15 min
```

Now events from external systems (Gmail, Odoo, Facebook, Twitter) automatically become task files in `/Inbox`.

### Option C — Stop Hook (Ralph Wiggum)

With `.claude/settings.json` configured, Claude Code will automatically check for remaining work after each task. As long as files exist in `/Inbox`, `/Active`, or `/Approved`, it keeps iterating without manual re-runs.

The iteration guard prevents infinite loops — Claude stops automatically after 20 iterations per session.

---

## Task File Template

Create a file in `/Inbox` named `YYYY-MM-DD_your-task-name.md`:

```markdown
# Task: Your Task Name

> Status: **New**
> Created: YYYY-MM-DD
> Priority: High | Medium | Low
> Owner: --

---

## Description

What needs to be done and why.

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Notes

Any context Claude needs.
```

---

## Demo Scenario (5-Minute Walkthrough)

1. Drop `2026-02-23_demo-task.md` into `/Inbox`
2. Run `claude`
3. Show Claude claiming the task → moving to `/Active`
4. Show Claude executing → moving to `/Done`
5. Open `Dashboard.md` — point out audit log, trust progress
6. Show `/Logs` — show the claim + complete entries
7. Drop a "sensitive action" task → show it route to `/Pending_Approval`
8. Approve it (move to `/Approved`) → show Claude execute it

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Agent instructions — the "brain" |
| `Dashboard.md` | Live operational view — the "UI" |
| `Company_Handbook.md` | Business context + tone guidelines |
| `.claude/mcp.json` | MCP server config (4 servers) |
| `.claude/settings.json` | Stop hook (Ralph Wiggum) |
| `skills/autonomy.skill.md` | Control loop logic |
| `skills/approval.skill.md` | Human-in-the-loop gate |
| `skills/trust_tracker.skill.md` | Level 5 evidence tracker |
| `skills/ralph_wiggum.skill.md` | Stop hook / autonomous iteration pattern |
| `skills/sentinel.skill.md` | Watcher/sentinel design contract |
| `sentinels/scheduler.py` | Master scheduler (all watchers) |
| `sentinels/file_watcher.py` | Filesystem watcher (real-time /Inbox monitor) |
| `mcp_servers/communications.py` | Email, LinkedIn, WhatsApp MCP server |
| `mcp_servers/odoo.py` | Odoo accounting MCP server (6 tools) |
| `mcp_servers/social_media.py` | FB, IG, Twitter MCP server (7 tools) |
| `pyproject.toml` | Python project / dependencies |
| `docs/architecture.md` | Full system architecture deep-dive |
| `docs/lessons_learned.md` | Design insights and lessons |

---

## Demo Scenario (Gold Tier — 10 Minutes)

1. Run `python sentinels/scheduler.py --once` — shows all 7 sentinels running with graceful degradation
2. Drop `2026-02-23_demo-task.md` into `/Inbox` — shows task entry point
3. Run `claude` — shows Claude claiming the task, moving it through the pipeline
4. Open `Dashboard.md` — shows audit log, trust progress, vault state
5. Show `/Logs` — shows JSON events from sentinel + Markdown audit entries
6. Run `python mcp_servers/odoo.py --test` — shows 6 MCP tools registered
7. Run `python mcp_servers/social_media.py --test` — shows 7 MCP tools registered
8. Drop a "sensitive action" task → show it route to `/Pending_Approval`
9. Move it to `/Approved` → show Claude execute the approved action
10. Open `skills/` folder — show the 25 skill files as the "agent's procedure manual"

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| MCP server not connecting | Run `npx @modelcontextprotocol/server-filesystem` manually; check mcp.json path |
| Claude doesn't pick up tasks | Check that `/Inbox` has `.md` files (not just README.md); re-run `claude` |
| Stop hook not firing | Verify `.claude/settings.json` exists and Python is in PATH |
| watchdog not found | Run `pip install watchdog` |
| fastmcp not found | Run `pip install fastmcp` |
| Sentinel crashes on startup | Check `.env` — all credentials are optional; sentinel should degrade gracefully |
| Iteration limit hit immediately | Delete `.claude/wiggum_state.json` to reset iteration counter |
| Unicode error in Python scripts | Set `PYTHONIOENCODING=utf-8` before running any sentinel |
