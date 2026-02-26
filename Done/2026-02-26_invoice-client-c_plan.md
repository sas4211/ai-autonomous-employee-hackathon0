# Plan: Generate & Send Invoice — Client C

---
created: 2026-02-26T13:20:00Z
status: in_progress
task_source: /Needs_Action/2026-02-26_whatsapp_client-c.md
domain: business
risk: medium
---

## Objective

Generate invoice INV-2026-02-007 for Client C (monthly retainer) and send via email after approval.

## Client Lookup (from /Accounting/Rates.md)

| Field | Value |
|-------|-------|
| Client ID | CLIENT_C |
| Name | Client C |
| Email | client_c@email.com |
| Rate Type | retainer |
| Rate | $3,200.00/month flat |
| Payment Terms | Net 30 |

## Invoice Calculation

| Line | Value |
|------|------:|
| Monthly retainer (February 2026) | $3,200.00 |
| Hours included | 20 (unused hours expire end of month) |
| Overage hours | 0 |
| Rush surcharge | $0.00 |
| Late fee | $0.00 |
| Tax (0%) | $0.00 |
| **Total** | **$3,200.00** |

Invoice number: **INV-2026-02-007**
Due date: **2026-03-28** (Net 30 from today)

## Execution Checklist

- [x] Read /Needs_Action trigger file
- [x] Looked up Client C in /Accounting/Rates.md
- [x] Calculated invoice amount: retainer flat fee = $3,200.00
- [x] Assigned invoice number: INV-2026-02-007
- [ ] Create approval request in /Pending_Approval/
- [ ] Human approves → send email via Gmail MCP
- [ ] Log transaction to /Accounting/Current_Month.md
- [ ] Update invoice counter in /Accounting/Rates.md
- [ ] Move task files to /Done

## Risk Assessment

- Email send to external party → requires human approval
- Amount $3,200 > $500 → covered by approval gate
- Retainer: invoice on 1st of month; sending end-of-Feb is acceptable for February
