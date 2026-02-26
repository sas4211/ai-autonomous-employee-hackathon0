---
type: email
from: "service@intl.paypal.com" <service@intl.paypal.com>
subject: You changed your password
received: 2026-02-24T18:17:24.584705+00:00
date_sent: Fri, 15 Aug 2025 14:03:00 -0700
gmail_id: 198af8b047ed90d5
priority: high
status: pending
---

# Email: You changed your password

**From:** "service@intl.paypal.com" <service@intl.paypal.com>
**Received:** Fri, 15 Aug 2025 14:03:00 -0700

---

## Email Content

Samina safdari, You just made changes to your account. Hello, Samina safdari Your password changed If you didn&#39;t change your password, please contact us right away. Just a reminder: Never share

---

## Rules of Engagement

- Always reply politely and professionally (see `Company_Handbook.md`)
- Do NOT send any reply without human approval
- If the email contains a payment request > $500, flag to /Needs_Action

## Suggested Actions

- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing

## What Claude Should Do

1. Read and understand the email
2. Load skill: `skills/gmail_send.skill.md`
3. Draft a reply using tone from `Company_Handbook.md`
4. Save draft to `/Pending_Approval/` — do NOT send directly
5. Move this task to `/Done` after approval decision
