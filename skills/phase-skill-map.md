# Phase-to-Skill Mapping (II–V)

> Maps hackathon phases to vault skills, showing what to demonstrate at each stage.

---

## Phase II — Functional Agent (Bronze)

**Goal**: Agent works with supervision. Skills exist, dashboard runs, approval gates defined.

| Requirement | Skill / Asset | Status |
|-------------|--------------|--------|
| Skills are Markdown-based | All `/skills/*.skill.md` | Done |
| Agents operate via filesystem (not UI) | `autonomy.skill.md`, folder pipeline | Done |
| `dashboard.generate` skill exists | `dashboard.skill.md` | Done |
| `approval.request` skill exists | `approval.skill.md` | Done |
| Manual execution possible | CLAUDE.md autonomy loop | Done |
| Clear phase separation (I–V) | `maturity-checklist.md` | Done |

**Vault maturity equivalent**: Levels 0–2 (Skeleton + Workflow + Awareness)

**Actions to demonstrate**:
1. Show the folder structure and explain the state machine
2. Walk through a task moving Inbox -> Active -> Done
3. Show Dashboard.md updating after each action
4. Show an approval request in `/Pending_Approval`

---

## Phase III — Autonomous System (Silver)

**Goal**: Agent operates independently with oversight. Recovery, event-driven flow, reusable skills.

| Requirement | Skill / Asset | Status |
|-------------|--------------|--------|
| Skills reusable across projects | All skill files are project-agnostic | Done |
| MCP Code Execution (not agent glue) | `mcp_filesystem.skill.md` + `.claude/mcp.json` | Done (path + package fixed) |
| Clear HITL boundaries | `approval.skill.md` trigger list | Done |
| Agents recover from failure | `error_handling.skill.md` (retry 2x, escalate to `/Review`) | Done |
| Event-driven workflows (Kafka/Dapr) | `event_bus.skill.md` (file-based fallback active) | Done (file fallback; Kafka/Dapr optional) |
| Dashboard auto-updates on state change | `dashboard.skill.md` refresh rule | Done |

**Vault maturity equivalent**: Levels 3–4 (Execution + Autonomy)

**Actions to demonstrate**:
1. Execute an approved MCP action end-to-end (close Level 3 gap)
2. Trigger error handling: show retry + escalation to `/Review`
3. Process 5+ approvals (mix of approved and rejected)
4. Show Dashboard refreshing automatically after each file move
5. *Stretch*: Add a Kafka/Dapr event skill (see Phase V extras)

**New skills needed**:

| Skill | File | Purpose |
|-------|------|---------|
| Event Bus | `event_bus.skill.md` | Publish/subscribe to task events via Kafka or Dapr |

---

## Phase IV — Digital FTE (Gold)

**Goal**: Agent behaves like a reliable employee. Reproducible, portable, production-safe.

| Requirement | Skill / Asset | Status |
|-------------|--------------|--------|
| Skills tested with BOTH Claude Code and Goose | Need Goose validation pass | TODO |
| Zero manual application code | All logic in skill files + CLAUDE.md | Done |
| Agents deploy infrastructure autonomously | Need infra deployment skill | TODO |
| Production-safe K8s + Helm skills | **Not yet built** | TODO |
| Clear rollback + safety skills | `rollback.skill.md` + approval gate | Done |
| Skills documented as reusable products | Skill files have inputs/outputs/templates | Done |
| Obsidian vault as primary UI | Dashboard.md + folder state machine | Done |
| Judges can reproduce results | `reproduce.skill.md` | Done |

**Vault maturity equivalent**: Level 5 (Trust) — all evidence targets met

**Actions to demonstrate**:
1. Complete 10+ tasks end-to-end (trust ledger target)
2. Execute a successful rollback and log it
3. Have a human audit the override log with no surprises
4. Generate briefings across 3+ dates showing historical trends
5. Provide a judge-facing README that reproduces the full loop

**New skills needed**:

| Skill | File | Purpose | Status |
|-------|------|---------|--------|
| Rollback | `rollback.skill.md` | Undo a completed action safely, log evidence | Done |
| Infra Deploy | `infra_deploy.skill.md` | Deploy K8s/Helm resources via MCP or CLI | TODO |
| Reproducibility | `reproduce.skill.md` | Step-by-step guide for judges to run the vault | Done |

---

## Phase V — Extras and Differentiators

**Goal**: Stand out. Show event-driven architecture, cross-agent portability, historical intelligence.

| Differentiator | Skill / Asset | Priority |
|----------------|--------------|----------|
| Kafka/Dapr event-driven workflows | `event_bus.skill.md` | High |
| Cross-agent testing (Goose) | `goose_compat.skill.md` | High |
| Historical trend briefings | Extend `dashboard.skill.md` with time-series | Medium |
| Scheduled briefing cron | `scheduled_briefing.skill.md` | Medium |
| Multi-vault orchestration | `vault_sync.skill.md` | Low |

---

## Progress Summary

| Phase | Completion | Blockers |
|-------|-----------|----------|
| II (Bronze) | **100%** | None |
| III (Silver) | **~90%** | Kafka/Dapr runtime (file fallback active); 5 approval cycle needed |
| IV (Gold) | **~65%** | Infra deploy skill, Goose compat, 10 task completions needed |
| V (Extras) | **~30%** | Kafka/Dapr live broker, cross-agent tests, multi-vault sync |

---

## Recommended Next Steps (Priority Order)

1. **Run an MCP action through an approved task** — closes the Level 3 gap and proves Silver execution
2. **Build `rollback.skill.md`** — required for Gold, also earns trust ledger evidence
3. **Build `event_bus.skill.md`** — Kafka or Dapr event publishing for Silver event-driven requirement
4. **Create `reproduce.skill.md`** — judge-facing guide to reproduce the full autonomy loop
5. **Test with Goose** — validate skills are agent-agnostic (Gold requirement)
6. **Queue 10+ tasks through the pipeline** — accumulate trust ledger evidence for Level 5
