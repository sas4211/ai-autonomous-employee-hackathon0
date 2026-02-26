# Skill: Ralph Wiggum (Autonomous Iteration Loop)

> Skill Name: `ralph_wiggum.loop`
> Category: Autonomy / Control
> Type: Core System
> Trigger: Claude Code Stop hook (`.claude/settings.json`)
> Output: Either "continue working" (exit 1) or "stop cleanly" (exit 0)
> Implementation: `sentinels/check_work_remaining.py`

---

## Purpose

The "Ralph Wiggum" pattern keeps Claude Code working autonomously until the vault is truly idle — without requiring a human to re-run `claude` after each task.

Named after the Simpsons character who keeps trying even when odds are against him, this hook prevents the agent from stopping prematurely while work remains.

---

## Completion Strategies

The stop hook supports two strategies, checked in order:

### Strategy 1 — Promise-Based (Simple)

Claude outputs a structured promise tag in its last message:

```
<promise>TASK_COMPLETE</promise>
```

The hook reads the transcript, finds the tag, and exits 0 immediately.
Use this for short tasks where you want explicit signal from Claude.

**To activate:** set `completion_promise` in `.claude/wiggum_state.json`:
```json
{ "completion_promise": "TASK_COMPLETE", "max_iterations": 10 }
```

**Claude's obligation:** output `<promise>TASK_COMPLETE</promise>` as the
last thing in its response when done.

### Strategy 2 — File Movement (Gold Tier Default)

The hook scans work folders in priority order. If any have task files
→ continue. If all empty → stop. No explicit promise needed.

This is the default. Claude completes tasks naturally by moving files
to `/Done` — the emptied inbox IS the completion signal.

---

## How It Works

Claude Code fires the Stop hook **every time it is about to exit**. The hook:

1. Reads the Claude transcript via stdin hook payload
2. Checks for `<promise>TASK_COMPLETE</promise>` in the last message (Strategy 1)
3. Scans `/Approved`, `/Rejected`, `/Active`, `/Inbox`, `/Needs_Action` (Strategy 2)
4. If work is found → exits with code `1` and prints a continuation message
5. Claude Code receives that message as if a user typed it → resumes working
6. If vault is idle OR promise found → exits with code `0` → Claude stops

```
Claude finishes a task
        |
        v
Stop hook fires (check_work_remaining.py)
        |
   ┌────┴────┐
   |         |
Work?      Idle?
   |         |
   v         v
exit(1)    exit(0)
   |         |
   v         v
Claude    Claude
continues  stops
```

---

## Priority Order

The hook checks folders in this order — the first non-empty folder drives the continuation message:

| Priority | Folder | Continuation Instruction |
|----------|--------|--------------------------|
| 0 | `/Rejected` | Log the rejection, skip action, move to `/Done` |
| 1 | `/Approved` | Execute the approved action immediately |
| 2 | `/Active` | Resume work on the in-progress task |
| 3 | `/Inbox` | Claim and begin the next queued task |
| 4 | `/Needs_Action` | Check if human has responded to your question |

---

## Iteration Guard

To prevent infinite loops, the hook tracks a session iteration counter in `.claude/wiggum_state.json`.

| State | Behaviour |
|-------|-----------|
| Iteration < 20 | Continue normally |
| Iteration = 17–19 | Continue + print warning "approaching limit" |
| Iteration >= 20 | Exit 0 (stop) + reset counter + print message |

Reset the counter manually by deleting `.claude/wiggum_state.json`.

---

## Session State File

`.claude/wiggum_state.json`:
```json
{
  "iteration": 4,
  "session_start": "2026-02-23T08:00:00Z",
  "last_active": "2026-02-23T08:14:33Z"
}
```

---

## Configuration

In `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python sentinels/check_work_remaining.py"
          }
        ]
      }
    ]
  }
}
```

---

## Continuation Message Format

When work is found, the hook outputs a structured message:

```
[Ralph Wiggum] Work remains (iteration 3/20). Continue the autonomy loop.

/Approved (1 item): Execute the approved action immediately
  - 2026-02-23_send-linkedin-post.md

NEXT ACTION: Execute the approved action immediately
  File: 2026-02-23_send-linkedin-post.md
  Follow the autonomy loop in CLAUDE.md and skills/autonomy.skill.md
```

---

## Interaction with Other Skills

| Skill | Relationship |
|-------|-------------|
| `autonomy.skill.md` | The loop Ralph Wiggum continues |
| `planning.skill.md` | Plans are created during the loop iterations |
| `error_handling.skill.md` | Errors encountered during iterations are logged |
| `trust_tracker.skill.md` | Each completed iteration contributes to trust metrics |

---

## Rules

- Never set `MAX_ITERATIONS` below 10 (tasks need multiple steps)
- Never skip the iteration guard — it prevents runaway loops
- The hook must be fast — it runs after every Claude response
- Do not add external API calls to the hook — filesystem reads only
- If the hook itself errors, it must exit 0 (fail safe = stop, not infinite loop)

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Claude keeps restarting forever | Iteration guard not firing | Check wiggum_state.json exists and is writable |
| Claude stops even with work in /Inbox | README.md in folder counts | README.md is excluded from the file count |
| Claude stops after 1 task | Hook not registered | Verify `.claude/settings.json` exists |
| "Iteration limit reached" immediately | Stale state file | Delete `.claude/wiggum_state.json` |
