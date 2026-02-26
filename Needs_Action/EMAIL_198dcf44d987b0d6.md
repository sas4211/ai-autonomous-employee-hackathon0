---
type: email
from: Stripe <notifications@stripe.com>
subject: Suspected fraudulent payment on your Stripe account
received: 2026-02-24T18:17:23.747127+00:00
date_sent: Sun, 24 Aug 2025 16:40:54 +0000
gmail_id: 198dcf44d987b0d6
priority: high
status: pending
---

# Email: Suspected fraudulent payment on your Stripe account

**From:** Stripe <notifications@stripe.com>
**Received:** Sun, 24 Aug 2025 16:40:54 +0000

---

## Email Content

We recently noticed a suspicious payment on your Stripe account for Designatrix. For the majority of your payments, our machine learning system provides real-time transaction scoring at the time of a payment, but in some instances, as is the case here, we learn more about a payment’s risk level after it’s been processed. If you believe this payment was made with a stolen credit card, you should issue a refund to avoid a dispute and the dispute fee.

- ch_3RwX4RAchYWcXnyn0RozUddB (https://dashboard.stripe.com/b/acct_1RwVt8AchYWcXnyn?destination=%2Fpayments%2Fch_3RwX4RAchYWcXnyn0RozUddB)

Our fraud prevention system, Radar, is built directly into the payment flow and combines a customizable rules engine with powerful machine learning algorithms. You can use Radar to create a highly effective fraud prevention strategy, or upgrade to Radar for Fraud Teams (https://stripe.com/radar/fraud-teams) to customize your fraud prevention with rules and manual reviews.

We’ve created a few guides to fraud prevention to help you make sure you’re getting the most out of Radar:

1. Tips for preventing fraud and disputes (https://stripe.com/docs/disputes/prevention/best-practices).

2. Best practices for preventing card testing (https://stripe.com/docs/card-testing#mitigations).

As always, please don't hesitate to reach out with any questions.

Best,
The Stripe team

===
This email relates to your Designatrix Stripe account.
Account ID: acct_1RwVt8AchYWcXnyn

Need to refer to this message? Use this ID: em_no62b7rsbgtdlzdjv2k6p3u2ikesoq

Stripe, 354 Oyster Point Blvd, South San Francisco, CA 94080

You are subscribed to Fraudulent payments emails. Manage your communication preferences here: https://dashboard.stripe.com/b/acct_1RwVt8AchYWcXnyn?destination=%2Fsettings%2Fcommunication-preferences%23fraud_emails

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
