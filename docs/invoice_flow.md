# End-to-End Invoice Flow

> A complete walkthrough from trigger to action, showing how all components work together.

---

## Scenario

A client sends a WhatsApp message asking for an invoice. The AI Employee:
1. Detects the request
2. Generates the invoice
3. Sends it via email
4. Logs the transaction

---

## Step 1: Detection (WhatsApp Watcher)

The WhatsApp Watcher detects a message containing the keyword "invoice":

```
# Detected message:
# From: Client A
# Text: "Hey, can you send me the invoice for January?"

# Watcher creates:
# /Inbox/WHATSAPP_client_a_2026-01-07.md
```

---

## Step 2: Reasoning (Claude Code)

Claude reads the task file and creates a plan:

```
# /Active/PLAN_invoice_client_a.md
---
created: 2026-01-07T10:30:00Z
status: pending_approval
---

## Objective
Generate and send January invoice to Client A

## Steps
- [x] Identify client: Client A (client_a@email.com)
- [x] Calculate amount: $1,500 (from /Accounting/Rates.md)
- [ ] Generate invoice PDF
- [ ] Send via email (REQUIRES APPROVAL)
- [ ] Log transaction

## Approval Required
Email send requires human approval. See /Pending_Approval/
```

---

## Step 3: Approval (Human-in-the-Loop)

Claude creates an approval request and halts:

```markdown
# /Pending_Approval/EMAIL_invoice_client_a.md
---
action: send_email
to: client_a@email.com
subject: January 2026 Invoice - $1,500
attachment: /Invoices/2026-01_Client_A.pdf
risk_level: Low
status: pending
---

Ready to send. Move to /Approved to proceed.
```

Human reviews and moves the file to `/Approved`.

---

## Step 4: Action (Email MCP)

Claude detects the approved file and calls the Email MCP:

```javascript
// MCP call (simplified)
await email_mcp.send_email({
  to: 'client_a@email.com',
  subject: 'January 2026 Invoice - $1,500',
  body: 'Please find attached your invoice for January 2026.',
  attachment: '/Invoices/2026-01_Client_A.pdf'
});

// Result logged to /Logs/2026-01-07_invoice-sent.md
```

---

## Step 5: Completion

Claude updates the Dashboard and moves all task files to `/Done`:

```
Dashboard.md updated:
## Recent Activity
- [2026-01-07 10:45] Invoice sent to Client A ($1,500)

Files moved:
  /Inbox/WHATSAPP_client_a_...     → /Done/
  /Active/PLAN_invoice_client_a... → /Done/
  /Approved/EMAIL_invoice_...      → /Done/
```

---

## File Lifecycle Summary

```
WhatsApp message
      ↓
/Inbox/WHATSAPP_client_a.md          (sentinel creates)
      ↓ Claude claims
/Active/PLAN_invoice_client_a.md     (Claude creates plan)
      ↓ sensitive action detected
/Pending_Approval/EMAIL_invoice.md   (Claude halts)
      ↓ human approves
/Approved/EMAIL_invoice.md           (human moves)
      ↓ Claude executes
Email sent + logged
      ↓
All files → /Done/
```

---

## Related Skills

- `skills/gmail_send.skill.md` — email drafting and sending
- `skills/approval.skill.md` — approval request format
- `skills/planning.skill.md` — plan file creation
- `skills/odoo_accounting.skill.md` — invoice generation via Odoo
