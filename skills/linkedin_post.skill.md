# Skill: LinkedIn Post Generator

> Skill Name: `linkedin_post.generate`
> Category: Business Development / Content
> Type: External Action (requires approval)
> Trigger: Weekly schedule (Monday) OR manual task in /Inbox
> Output: Approval request in `/Pending_Approval/` → published via MCP

---

## Purpose

Automatically generate LinkedIn posts that promote the business, demonstrate expertise, and generate inbound sales interest. Posts go through the approval gate before publishing — the human reviews tone, accuracy, and messaging before anything goes live.

---

## Content Strategy

When generating posts, follow these principles (also see `Company_Handbook.md`):

| Principle | Guidance |
|-----------|----------|
| Hook first | First line must stop the scroll. No "I am excited to announce." |
| Lead with value | Give the reader something useful in the first 3 lines |
| Specific > generic | Use real numbers, real situations, concrete outcomes |
| Soft CTA | One ask at the end: comment, DM, or visit link |
| Length | 150–300 words. Short paragraphs. White space. |
| Hashtags | 3–5 relevant tags at the very end |
| Frequency | Maximum 1 post per business day |

---

## Post Types to Rotate

| Type | When | Example Hook |
|------|------|-------------|
| **Insight** | Weekly | "Most businesses waste 3 hours a day on X. Here's the fix:" |
| **Behind the scenes** | Monthly | "This is how our AI Employee handles Monday mornings:" |
| **Result/Case study** | When available | "We automated X and saved Y hours. Here's exactly how:" |
| **Question/Poll** | Bi-weekly | "What's the biggest bottleneck in your business right now?" |
| **Tool/Resource** | As relevant | "5 tools we use every day that most people don't know about:" |

---

## Workflow

### Step 1 — Generate Draft

Read the task file for any topic hint. If none provided, choose a post type from the rotation schedule (check recent `/Briefings/` to see what was last posted).

Write the post following the content strategy above.

### Step 2 — Create Approval Request

Save to `/Pending_Approval/YYYY-MM-DD_linkedin-post.md`:

```markdown
# Approval Request — LinkedIn Post

> Status: Pending
> Created: YYYY-MM-DD
> Requested by: Claude Code
> Type: linkedin_post
> Risk Level: Medium

---

## Action

Publish the following post to LinkedIn.

## Why This Is Needed

Weekly LinkedIn posting to maintain visibility and generate inbound interest.

## Risk Level

Medium — public-facing content representing the business.

## Rollback Plan

LinkedIn posts can be deleted via the LinkedIn app within minutes of publishing.

## Status

- [ ] Approved — move this file to /Approved
- [ ] Rejected — move this file to /Done with notes

## Human Notes

> _Review the post below. Edit directly if needed. Then move file._

---

## LinkedIn Post Content

{{the full post text here}}
```

### Step 3 — Wait for Approval

Do not publish. Set agent status to "Awaiting approval."

### Step 4 — Publish (after approval)

When file is moved to `/Approved/`:

Use the `communications` MCP tool:
```
post_to_linkedin(content="<post text>")
```

### Step 5 — Log and Complete

- Log result in `/Logs/`
- Update trust ledger
- Move task and approval file to `/Done/`
- Update Dashboard

---

## MCP Tool

```
Server: communications
Tool: post_to_linkedin(content, visibility="PUBLIC")
```

Requires `LINKEDIN_ACCESS_TOKEN` and `LINKEDIN_AUTHOR_URN` in `.env`.

---

## Rules

- Never post without an approval file in `/Approved/`
- Never post more than once per day
- Always log the published post ID in `/Logs/`
- If the LinkedIn API returns an error, log it and move to `/Review/`
- Always update the trust ledger after an approval decision
