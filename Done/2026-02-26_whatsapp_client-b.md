---
type: whatsapp
from: Client B
received: 2026-02-26T13:20:00Z
keywords: invoice
priority: high
status: pending
---

# WhatsApp: Message from Client B

**From:** Client B
**Keywords detected:** invoice
**Received:** 2026-02-26T13:20:00Z

---

## Message Content

Hi, could you send me the invoice for this month? I logged 20 hours of consulting work in February.

---

## Rules of Engagement

- Always be polite on WhatsApp (see `Company_Handbook.md`)
- Do NOT send any reply without human approval
- If message contains a payment request > $500, flag immediately

## What Claude Should Do

1. Look up Client B in `/Accounting/Rates.md` — hourly rate
2. Calculate: 20 hours × $95.00 = $1,900.00
3. Create approval request in `/Pending_Approval/`
4. Move this task to `/Done` after approval decision
