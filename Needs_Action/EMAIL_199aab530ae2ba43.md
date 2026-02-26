---
type: email
from: Stripe <notifications@stripe.com>
subject: [Action required] Resolve a security issue to continue processing
received: 2026-02-24T18:17:21.757161+00:00
date_sent: Fri, 3 Oct 2025 15:33:44 +0000
gmail_id: 199aab530ae2ba43
priority: high
status: pending
---

# Email: [Action required] Resolve a security issue to continue processing

**From:** Stripe <notifications@stripe.com>
**Received:** Fri, 3 Oct 2025 15:33:44 +0000

---

## Email Content

Hi Designatrix!

We noticed that you passed a customer's full credit card number to Stripe's API. To keep your customer's information safe, we don't process charges that include full card numbers.

To continue processing payments with Stripe, use one of our official client integrations (https://stripe.com/docs/payments) to collect payment information securely. These integrations ensure that sensitive card data never needs to touch your server.

We strongly discourage passing full card numbers to our API because it:

- Can expose your customers' sensitive data to bad actors

- Requires you to meet complex PCI compliance requirements (https://stripe.com/docs/security#pci-dss-guidelines)

- Makes it harder for Radar (https://stripe.com/docs/radar), Stripe's fraud protection tool, to protect your business

In very rare cases, you might need to pass full card numbers. If this applies to you, you can allow it in your integration settings (https://dashboard.stripe.com/b/acct_1RwVt8AchYWcXnyn?destination=%2Faccount%2Fintegration%2Fsettings).

This is only a first-time notification; we won't email you about this again in the future. If you have questions, you can contact us via our support site (https://support.stripe.com/contact/).

Request Id: req_EXmFrsQuTDB0JI (https://dashboard.stripe.com/b/acct_1RwVt8AchYWcXnyn?destination=%2Flogs%2Freq_EXmFrsQuTDB0JI)

Thanks,  The Stripe team

===
This email relates to your Designatrix Stripe account.
Account ID: acct_1RwVt8AchYWcXnyn

Need to refer to this message? Use this ID: em_tgb4pdf6jzz8us3yd7k06zepbzyfr7

Stripe, 354 Oyster Point Blvd, South San Francisco, CA 94080

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
