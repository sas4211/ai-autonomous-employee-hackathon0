---
type: approval_request
action: {{action_summary}}
amount: {{amount_if_financial}}
recipient: {{recipient_if_applicable}}
reason: {{reason}}
created: {{ISO8601_timestamp}}
expires: {{ISO8601_expiry_24h}}
risk_level: {{Low|Medium|High}}
status: pending
---

# Approval Request: {{action_summary}}

## Action Details

{{clear_description_of_what_will_happen}}

## Why This Is Needed

{{business_or_technical_justification}}

## Risk Level

{{Low | Medium | High}}

**Reasoning:** {{why_this_risk_level}}

## Impacted Components

- {{component_1}}
- {{component_2}}

## Rollback Plan

{{how_to_undo_safely_if_approved_and_then_something_goes_wrong}}

## Requested By

Claude Code (AI Employee) on behalf of the autonomy loop.

## Expires

This request expires at `{{ISO8601_expiry_24h}}`. If not actioned by then, Claude will log it as expired and move on.

---

## To Approve

Move this file to `/Approved` folder.

Claude will execute the action on the next loop cycle.

## To Reject

Add a note below, then move this file to `/Rejected` folder.

Claude will log the rejection without executing the action.

---

## Human Notes

> _Write your decision notes here before moving the file._
>
> Example: "Rejected — amount is wrong, should be $250."
> Example: "Approved — confirmed with client directly."
