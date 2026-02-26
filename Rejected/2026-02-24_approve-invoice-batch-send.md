# Approval Request — Invoice Batch Send

**Date:** 2026-02-24  
**Risk Level:** High  
**Action:** Send 3 overdue invoices (Feb) to clients via Odoo email  
**Requested by:** Claude Code (autonomous)  
**Timeout:** 24 hours — auto-reject if no response

## Invoices to send
| Client | Amount | Overdue by |
|--------|--------|------------|
| Acme Ltd | £1,250.00 | 12 days |
| Bright Futures | £890.00 | 7 days |
| NovaTech | £3,100.00 | 21 days |

## What will happen if approved
- 3 invoice reminder emails sent via Odoo
- Payment tracking enabled

## What will happen if rejected
- No emails sent — invoices remain as drafts
