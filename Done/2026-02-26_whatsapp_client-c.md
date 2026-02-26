---
type: whatsapp
from: Client C
received: 2026-02-26T13:20:00Z
keywords: invoice
priority: high
status: pending
---

# WhatsApp: Message from Client C

**From:** Client C
**Keywords detected:** invoice
**Received:** 2026-02-26T13:20:00Z

---

## Message Content

Hey, it's the end of the month — please send over our monthly retainer invoice. Thanks!

---

## Rules of Engagement

- Always be polite on WhatsApp (see `Company_Handbook.md`)
- Do NOT send any reply without human approval
- If message contains a payment request > $500, flag immediately

## What Claude Should Do

1. Look up Client C in `/Accounting/Rates.md` — retainer rate
2. Calculate: monthly flat fee = $3,200.00
3. Create approval request in `/Pending_Approval/`
4. Move this task to `/Done` after approval decision
