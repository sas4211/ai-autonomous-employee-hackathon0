# Skill: task_decomposition

> Type: Core System
> Trigger: When a claimed task has multiple steps or acceptance criteria
> Output: Subtask files in `/Inbox`

---

## Purpose

Break complex tasks into ordered, atomic subtasks. Each subtask is a standalone markdown file that flows through the same Inbox -> Active -> Done pipeline.

## When to Decompose

Decompose when the task has:
- More than 2 acceptance criteria
- Steps that could independently fail
- Steps that require different capabilities (e.g., read + write + MCP call)
- Dependencies between steps (step 2 needs step 1's output)

Do NOT decompose when:
- Task is a single clear action
- All criteria are verified in one step

## How It Works

### 1. Analyze the Parent Task

Read the task file. Identify:
- Distinct actions required
- Dependencies between actions
- Which actions might need approval

### 2. Create Subtasks

For each action, create a file:

**Filename**: `YYYY-MM-DD_{{parent-slug}}_step-{{N}}.md`

**Content**:
```markdown
# Subtask: {{title}}

> Parent: [[{{parent_filename}}]]
> Step: {{N}} of {{total}}
> Status: **New**
> Created: {{date}}
> Owner: --
> Depends On: {{previous subtask filename or "none"}}

---

## Description

{{what this specific step accomplishes}}

## Acceptance Criteria

- [ ] {{single clear criterion}}
```

### 3. Update Parent File

Add a subtasks section to the parent:

```markdown
## Subtasks

| # | File | Status |
|---|------|--------|
| 1 | [[step-1 filename]] | New |
| 2 | [[step-2 filename]] | New |
| 3 | [[step-3 filename]] | New |
```

### 4. Process In Order

- Only claim a subtask if its `Depends On` task is in `/Done`
- Process one subtask at a time through the full pipeline
- After each subtask completes, update the parent's subtask table

### 5. Complete Parent

When all subtasks are in `/Done`:
1. Verify all parent acceptance criteria are met
2. Mark parent `Status: Complete`
3. Move parent to `/Done`
4. Log: parent task completed with N subtasks

## Example

Parent task: "Deploy new feature"

Decomposes into:
1. `2026-01-27_deploy-feature_step-1.md` — Write the code
2. `2026-01-27_deploy-feature_step-2.md` — Run tests (depends on step 1)
3. `2026-01-27_deploy-feature_step-3.md` — Request deploy approval (depends on step 2)
4. `2026-01-27_deploy-feature_step-4.md` — Execute deploy via MCP (depends on step 3)
