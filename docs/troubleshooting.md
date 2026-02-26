# Troubleshooting FAQ

---

## Setup Issues

**Q: Claude Code says "command not found"**
A: Ensure Claude Code is installed globally and your PATH is configured:
```bash
npm install -g @anthropic/claude-code
```
Then restart your terminal.

---

**Q: Obsidian vault isn't being read by Claude**
A: Check that you're running Claude Code from the vault directory, or using the `--cwd` flag to point to it:
```bash
claude --cwd /path/to/ai-empolyee
```
Verify file permissions allow read access.

---

**Q: Gmail API returns 403 Forbidden**
A: Your OAuth consent screen may need verification, or the Gmail API is not enabled in Google Cloud Console. Check the project settings at [console.cloud.google.com](https://console.cloud.google.com).

---

**Q: MCP server won't connect**
A: Check that the server process is running:
```bash
ps aux | grep mcp
```
Verify the path in `.claude/mcp.json` is absolute. Check Claude Code logs for connection errors.

---

## Runtime Issues

**Q: Watcher scripts stop running overnight**
A: Use a process manager to keep them alive. Options:

*PM2 (recommended for quick setup):*
```bash
npm install -g pm2
pm2 start sentinels/gmail_watcher.py --interpreter python3
pm2 save
pm2 startup
```

*Custom watchdog (already in this vault):*
```bash
python sentinels/watchdog.py
```

See `docs/architecture.md` — Orchestration Layer for details.

---

**Q: Claude is making incorrect decisions**
A: Review your `Company_Handbook.md` rules. Add more specific examples. Consider lowering autonomy thresholds so more actions require approval — edit the Auto-Approve Thresholds table in `skills/approval.skill.md`.

---

**Q: Claude keeps restarting (infinite loop)**
A: The Ralph Wiggum iteration guard should stop this at 20 iterations. If it's still looping:
```bash
# Reset the state file
rm .claude/wiggum_state.json
```
Then investigate what task is being re-created on each iteration.

---

**Q: Stop hook not triggering**
A: Verify `.claude/settings.json` exists and contains the Stop hook config:
```json
{
  "hooks": {
    "Stop": [{ "matcher": "", "hooks": [{ "type": "command", "command": "python sentinels/check_work_remaining.py" }] }]
  }
}
```

---

## Security Concerns

**Q: How do I know my credentials are safe?**
A: Never commit `.env` files. Use environment variables. Regularly rotate credentials. All access is tracked via the audit logging in `/Logs/`. See `Company_Handbook.md` — Security & Privacy Architecture.

---

**Q: What if Claude tries to pay the wrong person?**
A: That's why HITL is critical for payments. Any payment action creates an approval file first. The auto-approve threshold is < $50 recurring to *known payees only*. New payees always require approval regardless of amount. See `skills/approval.skill.md`.

---

**Q: A watcher is creating duplicate task files**
A: Each sentinel should check for an existing file before creating one (idempotency rule). Check the sentinel's state file in `.claude/` — it tracks which events have already been processed. If the state file is missing or corrupted, delete it and restart the watcher.

---

## Log Locations

| What | Where |
|------|-------|
| Task logs (human-readable) | `/Logs/YYYY-MM-DD_action.md` |
| JSON event stream | `/Logs/events/*.json` |
| Trust ledger | `/Logs/trust_ledger.md` |
| Watcher state | `.claude/*.state.json` |
| Ralph Wiggum state | `.claude/wiggum_state.json` |
| Process PIDs | `.claude/pids/*.pid` |
