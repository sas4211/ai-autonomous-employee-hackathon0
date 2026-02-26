# Skill: Social Media (Cross-Platform)

> Skill Name: `social_media.post` / `social_media.report`
> Category: Business Development / Marketing
> Type: External Action (posts require approval) / Read (reports always safe)
> Trigger: Weekly schedule OR manual task
> MCP Server: `social_media`

---

## Purpose

Manage the business's social media presence across Facebook, Instagram, and Twitter/X.
Generate content, route through approval, publish, and report on performance.

---

## Platform Capabilities

| Platform | Post Type | Read | Approval Required |
|----------|-----------|------|------------------|
| Facebook | Text + optional link | Page insights, comments | Yes |
| Instagram | Image + caption | Post insights, follower count | Yes |
| Twitter/X | Text (280 chars) | Mentions, timeline | Yes |

---

## Content Calendar (Default)

| Day | Platform | Content Type |
|-----|----------|-------------|
| Monday | LinkedIn | Weekly insight or behind-the-scenes |
| Tuesday | Twitter/X | Tip or industry observation |
| Wednesday | Facebook | Blog post share or client win |
| Thursday | Instagram | Visual content (product/workspace) |
| Friday | All 3 | Weekly wrap-up / engagement post |

---

## Post Generation Workflow

### Step 1 — Read the Brief

Read the task file for:
- Platform target(s)
- Topic or content angle
- Any specific message or promotion
- Image URL (required for Instagram)

### Step 2 — Create Plan.md

Use `planning.skill.md` — plan the post for each platform:
- Facebook: longer text, professional, link optional
- Instagram: shorter caption, heavy hashtags, image required
- Twitter/X: punchy, under 280 chars, 1–2 hashtags max

### Step 3 — Draft Content

Follow content strategy from `Company_Handbook.md`. For each platform:

**Facebook:**
- 2–4 paragraphs
- Value-first structure
- Soft CTA at the end

**Instagram:**
- Hook line (first 125 chars visible before "more")
- Content body
- Hashtag block at end (10–15 tags)
- Requires `image_url` for the MCP call

**Twitter/X:**
- Under 280 characters
- No more than 2 hashtags
- Strong standalone statement

### Step 4 — Route to Approval

For EACH platform, create a separate approval request in `/Pending_Approval/`:

```markdown
# Approval Request — [Platform] Post

> Type: social_post
> Platform: Facebook | Instagram | Twitter
> Risk Level: Medium

## Post Content

[the full post]

## Status
- [ ] Approved — move to /Approved
- [ ] Rejected — move to /Done with notes
```

### Step 5 — Publish (after approval)

Use the `social_media` MCP server:
- Facebook: `post_to_facebook(content, link="")`
- Instagram: `post_to_instagram(caption, image_url)`
- Twitter/X: `post_to_twitter(content)`

### Step 6 — Log and Complete

Log each post (platform, post ID, timestamp) using `audit_log.write` (level: ACTION + SECURITY).

---

## Social Summary Report

When asked for a social summary:
1. Call `get_social_summary(days=7)` from `social_media` MCP
2. Summarise by platform: reach, engagement, top content
3. Include in CEO briefing under Social Media Performance
4. Flag any anomalies (sudden drop in reach, spike in negative mentions)

---

## Error Handling

| Scenario | Response |
|----------|---------|
| API returns 401 | Token expired — log WARNING, move task to /Review with note "Refresh access token" |
| Rate limit (429) | Log WARNING, reschedule for 1 hour later |
| Image URL invalid (Instagram) | Request new image from human — move to /Needs_Action |
| Post text too long | Trim to platform limit, re-draft |
| Platform temporarily down | Log DEGRADED, retry once in 30 minutes |

---

## Rules

- Never post without an approval file in /Approved/
- Instagram requires a valid public image URL — do not attempt text-only posts
- Log every post with level ACTION + SECURITY
- Never post personal domain content to any platform
- Max 1 promotional post per day per platform
