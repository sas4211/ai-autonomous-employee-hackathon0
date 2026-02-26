# Skill: Cross-Domain Routing (Personal + Business)

> Skill Name: `cross_domain.route`
> Category: Triage / Routing
> Type: Core System
> Trigger: On every task claimed from /Inbox
> Output: Domain-tagged task, routed to the correct workflow

---

## Purpose

The AI Employee handles two domains simultaneously:
- **Personal** — Gmail (personal), WhatsApp messages, personal appointments, private matters
- **Business** — Odoo, LinkedIn, Facebook, Instagram, Twitter, business email, sales, invoicing

This skill defines how Claude distinguishes between them and applies the right tools, tone, and privacy boundaries.

---

## Domain Definitions

### Personal Domain
Tasks that relate to Amena's private life, personal relationships, and individual affairs.

**Signals:**
- From personal Gmail (non-business email address)
- WhatsApp messages from known personal contacts
- Subject contains: appointment, doctor, family, personal, home, holiday
- Sender not in Odoo customer list
- No monetary/sales component

**Tools available:**
- `communications.send_email` (personal tone)
- `communications.send_whatsapp_message`
- Filesystem (vault)

**Privacy rule:** Personal domain content is NEVER posted to social media or shared with business contacts. Personal task logs are stored in `/Logs/personal/` (separate from business logs).

---

### Business Domain
Tasks that relate to the operation, growth, or administration of the business.

**Signals:**
- Business email address in To/From
- Contains: invoice, client, customer, order, proposal, contract, meeting, LinkedIn, social
- Sender exists in Odoo as a customer or vendor
- Social media mentions or DMs
- Odoo event (overdue invoice, new order)

**Tools available:**
- `odoo.*` — all accounting/sales tools
- `social_media.*` — all social posting/reading tools
- `communications.send_email` (business tone)
- `communications.post_to_linkedin`
- Filesystem (vault)

---

## Routing Decision Tree

```
Task arrives in /Inbox
         |
         v
  Read task content
         |
    ┌────┴────┐
    |         |
Business?  Personal?
    |         |
    v         v
Tag:        Tag:
Type: business  Type: personal
    |         |
    v         v
Use business  Use personal
tools + tone  tools + tone
    |         |
    v         v
Log in       Log in
/Logs/       /Logs/personal/
```

---

## Tagging Convention

Add a `Domain:` field to task files when claiming:

```markdown
> Domain: business    # or: personal, mixed
> Domain_confidence: high  # or: medium, low
```

If confidence is `low`, add a note: `# Domain unclear — defaulting to business / Ask human`

---

## Mixed-Domain Tasks

Some tasks span both domains (e.g., a personal email from a business contact). When mixed:
1. Identify the primary domain (which capability is most needed?)
2. Tag as `Domain: mixed`
3. Apply business privacy rules (more conservative)
4. Note the mix in the task description

---

## Privacy Boundaries

| Rule | Personal Domain | Business Domain |
|------|----------------|-----------------|
| Log in business audit | Never | Yes |
| Post to social media | Never | Requires approval |
| Share with clients/customers | Never | With approval |
| Include in CEO briefing | Never | Yes |
| Store in /Logs/personal/ | Yes | No |

---

## Tone Guide by Domain

| Domain | Tone | Signature | Sign-off |
|--------|------|-----------|----------|
| Personal | Warm, casual, first-person | Amena | (informal) |
| Business | Professional, clear, confident | Amena / Team name | Best regards / Kind regards |
| Social media | Engaging, value-first, no jargon | — | Soft CTA |

---

## Rules

- When in doubt, route as **business** (more conservative privacy rules)
- Never mix personal content into business reports or social posts
- Always tag domain before executing any external action
- If domain is ambiguous and action is sensitive, route to /Needs_Action with the question: "Is this personal or business?"
