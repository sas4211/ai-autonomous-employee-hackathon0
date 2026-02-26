---
type: whatsapp
from: Client A
received: 2026-02-26T13:10:00Z
keywords: invoice
priority: high
status: pending
---

# WhatsApp: Message from Client A

**From:** Client A
**Keywords detected:** invoice
**Received:** 2026-02-26T13:10:00Z

---

## Message Content

Hey, can you send me the invoice for the latest milestone? We're ready to process payment.

---

## Rules of Engagement

- Always be polite on WhatsApp (see `Company_Handbook.md`)
- Do NOT send any reply without human approval
- If message contains a payment request > $500, flag immediately

## Suggested Actions

- [ ] Generate invoice
- [ ] Send via email
- [ ] Log transaction

## What Claude Should Do

1. Read and understand the message intent
2. Look up client in `/Accounting/Rates.md`
3. Calculate invoice amount
4. Create approval request in `/Pending_Approval/`
5. Move this task to `/Done` after approval decision
