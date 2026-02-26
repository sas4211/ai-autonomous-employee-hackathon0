# /Needs_Action

Tasks land here when Claude is **blocked and cannot proceed without human input**.

This is different from `/Pending_Approval` (which is a formal approval gate for sensitive actions). `/Needs_Action` is a general "waiting for human" state — Claude needs a clarification, a missing piece of information, or a decision that isn't a full approval gate.

---

## How It Works

1. Claude hits a blocker on a task in `/Active`
2. It moves the task file here and adds a `## Blocked: What I Need` section
3. Human opens the file in Obsidian, reads the question, adds their answer under `## Human Response`
4. Human moves the file back to `/Inbox` or `/Active`
5. Claude resumes

---

## File Convention

When moving a task here, Claude adds:

```markdown
## Blocked: What I Need

> Moved to /Needs_Action on: YYYY-MM-DD
> Reason: [clear description of what's missing]

- Question 1
- Question 2

## Human Response

> _Write your answer here, then move file back to /Inbox_
```

---

## For Humans

Check this folder daily. Items here are blocking Claude from making progress.
