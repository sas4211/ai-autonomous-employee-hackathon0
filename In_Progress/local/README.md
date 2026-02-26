# /In_Progress/local/

Tasks currently being processed by the **Local agent** (Claude Code).

**Claim-by-move rule:** The Local agent moves a task here from `/Needs_Action/local/`
or `/Inbox/` atomically (move + git push) to claim ownership.

**Cloud agent rule:** Never touch files in this folder.
