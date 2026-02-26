# Accounting — Client Rates & Pricing

---
last_updated: 2026-02-26
currency: USD
default_payment_terms: Net 30
late_fee_pct: 1.5
tax_rate_pct: 0
---

## How Claude Uses This File

When a client requests an invoice (via WhatsApp, Gmail, or /Inbox task), Claude reads this
file to look up the correct rate, calculate the amount, and populate the invoice draft.

Lookup order:
1. Match client name in **Client Register** → use their specific rate/package
2. Fall back to **Service Rates** for the service type requested
3. If still ambiguous → move task to /Needs_Action for human clarification

---

## Client Register

| Client ID | Client Name | Email | Rate Type | Rate | Notes |
|-----------|-------------|-------|-----------|-----:|-------|
| CLIENT_A | Client A | client_a@email.com | project | 2450.00 | Fixed per milestone |
| CLIENT_B | Client B | client_b@email.com | hourly | 95.00 | Per hour, max 40h/mo |
| CLIENT_C | Client C | client_c@email.com | retainer | 3200.00 | Monthly flat fee |
| CLIENT_D | Client D | client_d@email.com | project | 5000.00 | Fixed per project |

> Add new clients here. Claude will not invoice unknown clients without human approval.

---

## Service Rates (defaults when no client-specific rate applies)

| Service | Unit | Rate | Notes |
|---------|------|-----:|-------|
| Consulting | per hour | 100.00 | Standard hourly rate |
| Strategy Session | per session | 350.00 | 3-hour block |
| Monthly Retainer | per month | 2500.00 | Includes up to 20h |
| Project: Small | fixed | 1500.00 | < 10 deliverables |
| Project: Medium | fixed | 3500.00 | 10–30 deliverables |
| Project: Large | fixed | 7500.00 | 30+ deliverables |
| Rush Surcharge | % of base | 25% | Turnaround < 48h |
| Revision (extra) | per round | 150.00 | After 2 free rounds |

---

## Package Definitions

### Retainer Package (Monthly)
- Hours included: 20
- Overage rate: $110/hr
- Rollover: unused hours expire end of month
- Invoice date: 1st of each month

### Project Package
- Payment schedule: 50% upfront, 50% on delivery
- Revision rounds included: 2
- Change request rate: $150/round after included rounds

---

## Invoice Calculation Rules

Claude follows these rules when generating an invoice:

```
1. Look up client in Client Register by name or email
2. Determine rate type:
   - hourly  → amount = hours_worked × rate
   - project → amount = fixed rate for the milestone
   - retainer → amount = monthly flat fee
3. Apply rush surcharge if turnaround < 48h (+25%)
4. Apply late fee if prior invoice is overdue (+1.5% per month)
5. Apply tax only if tax_rate_pct > 0
6. Round final amount to 2 decimal places
7. Assign invoice number: INV-YYYY-MM-<sequence>
```

---

## Payment Terms

| Term | Definition |
|------|-----------|
| Net 30 | Payment due 30 days from invoice date (default) |
| Net 15 | Payment due 15 days — use for new/unknown clients |
| Due on Receipt | Immediate — use for rush or first-time clients |
| 50/50 | 50% upfront before work begins, 50% on delivery |

---

## Invoice Numbering

Format: `INV-YYYY-MM-NNN`

| Last Invoice | Next |
|-------------|------|
| INV-2026-02-007 | INV-2026-02-008 |

> Update "Next" after each invoice is sent. Claude reads this to assign the correct number.

---

## Bank & Payment Details

> Populate before sending real invoices.

```
Account Name   : [Your Name / Business Name]
Bank           : [Your Bank]
Account Number : [XXXX]
Sort Code      : [XX-XX-XX]
IBAN           : [XXXX]
PayPal / Wise  : [your@email.com]
Reference      : Always quote invoice number
```

---

## Escalation Rules

Claude moves to /Needs_Action (does NOT invoice automatically) if:

- Client not found in Client Register
- Rate type is ambiguous (e.g., no hours logged for hourly client)
- Invoice amount would exceed $10,000
- Client has 2+ outstanding unpaid invoices
- Rush surcharge applies and total > $5,000
