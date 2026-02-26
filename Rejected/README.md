# /Rejected — Rejected Approval Requests

This folder holds approval requests that were **explicitly rejected** by the human operator.

## How Files Arrive Here

1. Claude creates an approval request in `/Pending_Approval/`
2. Human reviews it and decides: **No**
3. Human moves the file to **this folder** (`/Rejected/`)
4. Claude detects it on the next loop and logs the rejection without executing the action

## What Claude Does When a File Appears Here

1. Reads the file to understand what was rejected and why (check Human Notes)
2. Logs the rejection in `/Logs/` with the reason
3. Updates the trust ledger (rejections are evidence of proper oversight)
4. Does **NOT** execute the rejected action under any circumstances
5. Moves the file to `/Done/` after logging
6. Resumes normal autonomy loop

## Difference from /Done

| Folder | Meaning |
|--------|---------|
| `/Done` | Task completed successfully |
| `/Rejected` | Approval explicitly denied — action was NOT taken |

## File Format

When you reject an approval, add a note before moving:

```markdown
## Human Notes
Rejected: payment amount incorrect — should be $250 not $500.
Please re-check the invoice number and resubmit.
```
