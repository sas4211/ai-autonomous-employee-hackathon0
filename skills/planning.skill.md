# Skill: Planning (Plan.md Reasoning Loop)

> Skill Name: `planning.create`
> Category: Reasoning / Execution
> Type: Core System
> Trigger: Before executing any task with 2+ steps or any uncertainty about approach
> Output: `/Active/YYYY-MM-DD_<task-slug>_plan.md`

---

## Purpose

Before acting on a non-trivial task, Claude externalises its reasoning into a `Plan.md` file. This makes reasoning visible, reviewable, and recoverable. It prevents the agent from starting down the wrong path before understanding the full scope.

**Why this matters:**
- Visible reasoning builds trust (the human can see the plan before execution)
- Plans can be reviewed and corrected without undoing work
- Plans serve as execution checklists — each step gets checked off
- Failed steps are obvious — the plan shows exactly where things went wrong

---

## When to Create a Plan

**Always create a Plan.md when the task:**
- Has 2 or more distinct steps
- Involves any external action (email, API, file delete)
- Has uncertain requirements or multiple valid approaches
- Could have irreversible consequences
- Is flagged as `Type: linkedin_post`, `Type: email_response`, `Type: sensitive`

**Skip the plan (act directly) when:**
- Task is a single clear action (e.g., "move file X to /Done")
- Task is a status check or read-only query

---

## Plan File Location

Save as: `/Active/YYYY-MM-DD_<task-slug>_plan.md`

The plan lives alongside the task file in `/Active/`.

---

## Plan.md Template

```markdown
# Plan: {{task title}}

> Task file: [[{{task_filename}}]]
> Created: YYYY-MM-DD
> Status: **Drafting** → In Progress → Complete
> Author: Claude Code

---

## Goal

{{one sentence: what does success look like?}}

---

## Context Analysis

{{2–4 sentences: what Claude understood from reading the task, any ambiguity, assumptions made}}

---

## Approach

{{chosen approach and why — mention alternatives considered if relevant}}

---

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| {{risk 1}} | Low/Med/High | {{mitigation}} |

---

## Steps

- [ ] **Step 1** — {{description}} *(sensitive? approval needed?)*
- [ ] **Step 2** — {{description}}
- [ ] **Step 3** — {{description}}
- [ ] **Verify** — confirm all acceptance criteria are met
- [ ] **Log** — write completion log to /Logs/
- [ ] **Move task to /Done**

---

## Acceptance Criteria (from task)

{{copy from task file}}

---

## Execution Notes

*(Claude fills this in as it works through the steps)*
```

---

## Workflow

### 1. Read the Task

Read the task file fully. Extract:
- Goal and acceptance criteria
- Any constraints or dependencies
- Risk signals (external calls, deletes, sends)

### 2. Analyse

Answer these questions internally before writing the plan:
- What is the simplest path to completion?
- What could go wrong?
- Which steps need approval?
- Are there missing inputs?

### 3. Write the Plan

Create the plan file at `/Active/YYYY-MM-DD_<slug>_plan.md`.
Fill in all sections. Mark risky steps clearly.

### 4. Pause if High Risk

If the plan contains any steps classified as **High** risk, route the plan itself to `/Pending_Approval` before executing. The human reviews the plan, not just the action.

### 5. Execute Step by Step

Work through the plan's checkbox list:
- Check off each step as it completes
- Add execution notes under each step
- If a step fails, stop — log the failure, do not continue

### 6. Complete

When all steps are checked:
1. Verify acceptance criteria
2. Mark plan `Status: Complete`
3. Move task file to `/Done`
4. Plan file stays in `/Active/` until task is in `/Done`, then archive to `/Done/` as well

---

## Rules

- Never skip the plan for multi-step tasks
- Plans for sensitive actions require human review before execution
- If a step fails, annotate the plan with the failure — do not delete
- Plans are evidence — they contribute to the trust ledger
- A plan is not a formality. If the plan is wrong, fix it before acting
