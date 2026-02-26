# Lessons Learned — Building a Personal AI Employee

> Post-mortem and design insights from building an autonomous AI employee
> on top of Claude Code + an Obsidian vault for Hackathon 0.

---

## The Core Insight: Folders as State Machines

The biggest architectural decision — and the one that made everything else simpler — was **using the filesystem as the state machine**.

Instead of a database, a message queue, or a custom API:
- A file in `/Inbox` means "not started"
- Moving it to `/Active` means "claimed"
- Moving it to `/Done` means "complete"

This had unexpected benefits:
1. **No serialization** — Claude reads Markdown natively; no parsing
2. **Human transparency** — any non-technical person can open the vault in Obsidian and see exactly what's happening
3. **Crash safety** — if Claude crashes mid-task, the file stays in `/Active` and is resumed on next start
4. **No hidden state** — the folder IS the state; there's no secondary database to get out of sync

The lesson: **match your state storage to your agent's native data format**. Claude thinks in Markdown, so Markdown is the right state medium.

---

## What Worked Exceptionally Well

### 1. Agent Skills as Markdown Files

Defining all AI behavior as skill files (`/skills/*.skill.md`) was the right call. Benefits:
- Skills are **auditable** — a human can read them and understand what Claude will do
- Skills are **editable without code changes** — change a prompt by editing a Markdown file
- Skills are **portable** — copy the skills folder to a new project and Claude inherits all procedures
- Skills enable **task routing** — the `> Type: email_response` field in a task file tells Claude exactly which skill to load

The pattern: **every capability should have a documented procedure**.

### 2. Graceful Degradation Everywhere

Every sentinel and MCP server checks for credentials before doing anything:

```python
if not os.getenv("GMAIL_ADDRESS"):
    print("Gmail not configured — skipping.")
    return
```

This meant:
- The system could be demoed without any credentials
- Adding credentials activates capabilities without code changes
- Missing credentials never crash the scheduler or break other watchers

The lesson: **design for the unconfigured state first**. It makes the system more robust and easier to onboard.

### 3. Ralph Wiggum (Stop Hook Pattern)

The Stop hook that keeps Claude working autonomously was the most impactful single component after the folder state machine. Without it, a human had to type `claude` after every task. With it, Claude processes an entire inbox autonomously.

The iteration guard (max 20 iterations) was essential — without it, a bug that keeps creating tasks could run Claude indefinitely and rack up API costs. **Any autonomous loop needs a hard stop condition.**

### 4. FastMCP for External Actions

FastMCP reduced each MCP server from ~300 lines of wire protocol boilerplate to ~80 lines of actual business logic. The `@mcp.tool()` decorator pattern is clean and the self-test flag (`--test`) made verification easy.

---

## What Was Harder Than Expected

### 1. Windows Encoding (cp1252)

The first production bug was a character encoding error. Python scripts using Unicode characters like `✓`, `→`, and `✗` in print statements failed on Windows with:

```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2713'
```

Windows terminal defaults to cp1252 encoding, which doesn't support these characters. The fix was replacing emoji/symbols with ASCII equivalents (`[OK]`, `>>`, `[NOT SET]`).

**Lesson**: On Windows, never use non-ASCII characters in Python stdout unless you explicitly set `sys.stdout.reconfigure(encoding='utf-8')` or `PYTHONIOENCODING=utf-8`.

### 2. MCP Configuration Path Sensitivity

The initial MCP config (`mcp.json`) had two bugs:
1. Wrong package name (`@anthropic/mcp-filesystem` instead of `@modelcontextprotocol/server-filesystem`)
2. Wrong path with a space in the directory name

Both caused silent failures — the MCP server didn't connect but Claude Code didn't clearly surface the error. The fix required carefully re-reading the Claude Code documentation on MCP configuration.

**Lesson**: MCP configuration errors are often silent. Always test with a `--test` flag or by calling a known-good tool immediately after setup.

### 3. Subprocess Output Capture

When running Python scripts as background processes in bash, piping stdout and capturing PIDs simultaneously is tricky on Windows. The command `python script.py & echo "PID: $!"` only captures the echo output, not the script's PID.

We worked around this by using indirect verification: checking that the sentinel's expected output artifacts (event JSON files) were created, rather than capturing the PID directly.

**Lesson**: For background process management on Windows, use Windows-native tools (Task Scheduler, `start /B`) rather than bash process management.

### 4. Sentinel Idempotency

The first version of `gmail_watcher.py` would create duplicate task files on every poll cycle because it didn't track which emails had already been processed. Adding IMAP `SEEN` flag marking (and checking) solved this, but required understanding IMAP state management.

For the Odoo and social media watchers, state tracking required a dedicated state file (`.claude/social_watcher_state.json`) to track last-seen IDs.

**Lesson**: Every watcher that polls an external API needs **explicit state tracking** to avoid duplicate processing. Design idempotency in from the start.

---

## Design Patterns Discovered

### Pattern 1: The Approval Gate

```
Claude wants to take an external action
  → Create /Pending_Approval file
  → Wait for human to move to /Approved
  → Execute only after file is in /Approved
  → Log result, move to /Done
```

This pattern is simple but powerful. The human's file move is the authorization. No passwords, no confirmation prompts, no API tokens for approval — just a file move that any human can do in a file browser.

### Pattern 2: Type-Based Skill Routing

Task files include a `> Type:` field that acts as a routing key:

```markdown
> Type: email_response
> Source: gmail_watcher
```

Claude reads this and loads the corresponding skill. This decouples task creation (sentinels) from task execution (skills) — a new sentinel can create tasks that an existing skill handles.

### Pattern 3: Priority-Ordered Scanning

The autonomy loop checks folders in strict priority order: Approved → Active → Inbox → Needs_Action. This means:
- Approved items (time-sensitive, already reviewed) always execute first
- Partially-complete Active tasks are always resumed before new Inbox items
- Blocked items (Needs_Action) are checked last to see if a human responded

This priority ordering prevents starvation of high-priority work by low-priority inbox items.

### Pattern 4: The Trust Ledger

Trust is not self-declared — it's accumulated evidence. The trust ledger (`/Logs/trust_ledger.md`) tracks six concrete metrics:
- Tasks completed (target: 10)
- Approvals processed with mix of approved/rejected (target: 5)
- Briefing dates (target: 3)
- Successful rollback (target: 1)
- Human audit review (target: 1)

This prevents the agent from claiming to be trustworthy without evidence. It also gives the human a clear, auditable path to granting higher autonomy.

---

## What We Would Do Differently

### 1. Start with Encoding Configuration

Add to the top of every Python script:

```python
import sys
sys.stdout.reconfigure(encoding='utf-8')
```

Or set `PYTHONIOENCODING=utf-8` as an environment variable for all processes.

### 2. Add MCP Health Checks to Startup

Add a startup check in `CLAUDE.md` or as a skill that tests each MCP server:

```bash
python mcp_servers/communications.py --test
python mcp_servers/odoo.py --test
python mcp_servers/social_media.py --test
```

Surface failures to the Dashboard before any task processing begins.

### 3. Use Structured Task IDs

Task files currently use `YYYY-MM-DD_slug.md` naming. A UUID prefix would prevent slug collisions when multiple tasks arrive on the same day with similar names:

```
2026-02-23_a3f2_email-from-client.md
```

### 4. Separate the Plan from the Task

Currently, plans are written to `/Active/` alongside the task file. A dedicated `/Plans/` folder would make plans easier to audit and reference after tasks are moved to `/Done/`.

### 5. Add a `/Failed/` Folder

Currently, failed tasks that cannot be retried go to `/Review`. A separate `/Failed/` folder (distinct from `/Review/`) would make it easier to distinguish "needs human review" from "definitively failed after all retries".

---

## Metrics from This Build

| Metric | Value |
|--------|-------|
| Skill files created | 25 |
| MCP servers built | 3 custom + 1 pre-built |
| MCP tools registered | 18 (4 + 4 + 6 + 7, minus overlap) |
| Sentinel scripts | 7 |
| External platforms integrated | 6 (Gmail, LinkedIn, Facebook, Instagram, Twitter/X, Odoo) |
| Bugs fixed during build | 7 (encoding, MCP config, path, watchdog, Unicode ×2, sentinel output) |
| Autonomy loop iterations (demo) | 3 tasks end-to-end |
| Lines of Python written | ~1,200 |
| Lines of Markdown written | ~3,500 |

---

## Key Takeaways

1. **Markdown is a better database than a database** for AI agents that reason in natural language
2. **File moves are the right abstraction for workflow state** — atomic, visible, auditable
3. **Every capability should be a documented procedure** (skill file) not just code
4. **Graceful degradation is not optional** — design the unconfigured state first
5. **Autonomous loops need hard stop conditions** — the iteration guard is not optional
6. **Trust must be earned, not declared** — the maturity model forces evidence accumulation
7. **Windows encoding will bite you** — solve it on day one, not when demoing
8. **Idempotency in watchers prevents duplicate work** — state tracking from the start
9. **Human approval via file move is simpler than any approval API** — match the operator's mental model
10. **The Stop hook is the most powerful single component** — without it, autonomy requires a human to keep re-running `claude`
