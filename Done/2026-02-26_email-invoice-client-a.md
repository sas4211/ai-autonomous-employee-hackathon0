# Approval Request — Invoice Email to Client A

> Status: **Pending**
> Created: 2026-02-26T13:10:00Z
> Requested by: Claude Code
> Type: email_send + invoice
> Risk Level: Medium
> Amount: $2,450.00

---

## Action

Send invoice INV-2026-02-005 to Client A via Gmail.

---

## Invoice Details

| Field | Value |
|-------|-------|
| Invoice # | INV-2026-02-005 |
| Client | Client A |
| To | client_a@email.com |
| Amount | $2,450.00 |
| Due Date | 2026-03-28 (Net 30) |
| Description | Project milestone payment |

---

## Email to be Sent

**To:** client_a@email.com
**Subject:** Invoice INV-2026-02-005 — $2,450.00

---

Hi,

Please find below your invoice for the latest project milestone.

**Invoice Number:** INV-2026-02-005
**Description:** Project milestone payment
**Amount Due:** $2,450.00
**Due Date:** 28 March 2026 (Net 30)

**Payment Details:**
- Bank: [Your Bank]
- Account: [XXXX]
- Reference: INV-2026-02-005

Please don't hesitate to reach out if you have any questions.

Best regards,
[Your Name]

---

## Source

- WhatsApp message: `/Needs_Action/2026-02-26_whatsapp_client-a.md`
- Plan: `/Active/2026-02-26_invoice-client-a_plan.md`
- Rates source: `/Accounting/Rates.md`

---

## Rollback Plan

Email cannot be unsent. If sent in error, send a correction email immediately referencing
the same invoice number and explaining the mistake.

---

## Decision

**To approve:** Move this file to `/Approved/`
**To reject:** Move this file to `/Rejected/` (add notes below if needed)

## Human Notes

> _Edit the email above if needed before approving._
