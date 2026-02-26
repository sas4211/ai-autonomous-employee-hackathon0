# Approval Request

> Status: **Pending**
> Created: 2026-01-27
> Requested by: Claude Code

---

## Action

- **Type**: Sensitive Action
- **Target**: Vault System
- **Risk Level**: High

## Description

A sensitive action has been flagged for human review before execution. This request was generated automatically because the action meets one or more escalation criteria.

## Why This Needs Approval

- Action is classified as **sensitive**
- No prior approval exists for this action type
- Vault policy requires explicit human sign-off

## What Will Happen

1. Human reviews this file in Obsidian
2. Human checks **Approved** or **Rejected** and adds notes
3. File is moved to `/Approved` or `/Done` accordingly
4. Claude Code reads the decision and proceeds or halts

## Rollback Plan

No changes are made until approval is granted. If approved and later reverted, the action log in `/Logs` will contain the full execution record for undo.

---

## Decision

- [ ] **Approved** -- move this file to `/Approved`
- [ ] **Rejected** -- move this file to `/Done` with note below

### Notes

> _Human writes here before moving the file._
