# Skill: autonomy_loop

> Type: Core System
> Trigger: On every Claude Code session start
> Output: Task execution, file moves, logs

---

## Purpose

Claude Code reads the vault state and acts without being told what to do. This is the main control loop.

## Control Loop

```
1. READ    /Inbox          — anything new?
2. READ    /Pending_Approval — anything decided?
3. READ    /Approved       — anything ready to execute?
4. READ    /Active         — anything stalled?
5. ACT     on the highest-priority item found
6. LOG     every action taken
7. UPDATE  Dashboard.md
8. REPEAT
```

## Priority Order

| Priority | Source Folder      | Action                                         |
|----------|--------------------|------------------------------------------------|
| 1        | `/Approved`        | Execute immediately                            |
| 2        | `/Active`          | Resume work                                    |
| 3        | `/Inbox`           | Claim and begin                                |
| 4        | `/Needs_Action`    | Check if human responded (file moved = yes)    |
| 5        | `/Pending_Approval`| Check if human has moved file                  |

## Claiming a Task

1. Read the file in `/Inbox`
2. Set `Owner: Claude Code` and `Status: Active`
3. Move file to `/Active`
4. Log: task claimed
5. If task is multi-step, decompose (see below)

## Decomposition Rules

When a task has more than one acceptance criterion or describes multiple actions:

1. Create subtask files in `/Inbox` named: `YYYY-MM-DD_parent-slug_step-N.md`
2. Each subtask references the parent file
3. Parent file lists subtask files and stays in `/Active` until all subtasks are in `/Done`
4. Process subtasks in order (respect dependencies)

### Subtask Template

```markdown
# Subtask: {{title}}

> Parent: {{parent_file}}
> Step: {{N}} of {{total}}
> Status: **New**
> Created: {{date}}
> Owner: --

---

## Description

{{what this step does}}

## Depends On

{{previous subtask or "none"}}

## Acceptance Criteria

- [ ] {{criteria}}
```

## Completion

1. Verify all acceptance criteria are checked
2. Set `Status: Complete` and `Completed: YYYY-MM-DD`
3. Move file to `/Done`
4. Log: task completed
5. If parent task exists, check if all subtasks are done
6. If all subtasks done, complete the parent too

## Blocked Task (Needs_Action)

When Claude cannot proceed without human input:

1. Add a `## Blocked: What I Need` section to the task file
2. Clearly state exactly what question or information is needed
3. Add a `## Human Response` section with a prompt line
4. Move task from `/Active` to `/Needs_Action`
5. Log: task blocked, reason
6. Continue to next priority item

When a task is moved back to `/Inbox` from `/Needs_Action`:
1. Read the `## Human Response` section
2. Resume the task with the provided information
3. If information is still insufficient, re-block with a more specific question

## Stall Detection

A task is stalled if:
- It has been in `/Active` for more than one session with no log entries
- A subtask is blocked with no clear next step

When stalled:
1. Log: task stalled, reason
2. Move to `/Review` with a note requesting human guidance
3. Continue to next priority item
