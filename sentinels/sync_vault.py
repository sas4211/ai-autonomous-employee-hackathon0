"""
sync_vault.py — Git-based vault sync between Local and Cloud agents.
====================================================================

Provides three primitives:
  git_pull()        — pull latest from remote (called every 30s by scheduler)
  git_push(msg)     — stage all .md changes + commit + push (called after any file move)
  claim_task(path)  — atomic move + immediate push (prevents double-processing)

Usage:
    from sentinels.sync_vault import git_pull, git_push, claim_task

    git_pull()
    new_path = claim_task("/Needs_Action/cloud/2026-02-26_email.md")
    # ... process task ...
    git_push("agent/cloud: complete 2026-02-26_email")
"""

import logging
import os
import shutil
import subprocess
import time
from pathlib import Path

logger = logging.getLogger(__name__)

VAULT_ROOT = Path(os.getenv("VAULT_ROOT", str(Path(__file__).parent.parent)))
AGENT_ID = os.getenv("AGENT_ID", "local")
GIT_REMOTE = "origin"
GIT_BRANCH = "main"
MAX_PUSH_RETRIES = 2
PUSH_RETRY_DELAY = 5  # seconds


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _run_git(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    """Run a git command in the vault root."""
    cmd = ["git"] + list(args)
    result = subprocess.run(
        cmd,
        cwd=str(VAULT_ROOT),
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def git_pull() -> bool:
    """
    Pull latest changes from remote using rebase.

    Returns True on success, False on conflict/error (logs warning).
    Conflicts are never auto-resolved — logged to /Review for human.
    """
    result = _run_git("pull", "--rebase", GIT_REMOTE, GIT_BRANCH)

    if result.returncode == 0:
        if "Already up to date" not in result.stdout:
            logger.info("[sync] git pull: %s", result.stdout.strip().splitlines()[0] if result.stdout.strip() else "up to date")
        return True

    # Rebase conflict
    logger.warning("[sync] git pull conflict detected — aborting rebase, keeping local")
    _run_git("rebase", "--abort")

    # Write conflict notice to /Review
    review_dir = VAULT_ROOT / "Review"
    review_dir.mkdir(exist_ok=True)
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
    (review_dir / f"{ts}_git-conflict.md").write_text(
        f"# Git Conflict — {ts}\n\n"
        f"> Agent: {AGENT_ID}\n"
        f"> Action required: Resolve git conflict manually\n\n"
        f"```\n{result.stderr.strip()}\n```\n",
        encoding="utf-8",
    )
    return False


def git_push(message: str) -> bool:
    """
    Stage all changes, commit with message, and push to remote.

    Retries up to MAX_PUSH_RETRIES times on failure.
    Returns True on success, False if all retries exhausted.
    """
    # Stage all .md changes (never stage .env or secrets — covered by .gitignore)
    _run_git("add", "-A")

    # Check if there's anything to commit
    status = _run_git("status", "--porcelain")
    if not status.stdout.strip():
        logger.debug("[sync] Nothing to commit — skipping push")
        return True

    commit_result = _run_git("commit", "-m", f"agent/{AGENT_ID}: {message}")
    if commit_result.returncode != 0:
        logger.warning("[sync] git commit failed: %s", commit_result.stderr.strip())
        return False

    for attempt in range(1, MAX_PUSH_RETRIES + 1):
        push_result = _run_git("push", GIT_REMOTE, GIT_BRANCH)
        if push_result.returncode == 0:
            logger.info("[sync] git push OK: %s", message)
            return True

        logger.warning("[sync] git push attempt %d/%d failed — %s", attempt, MAX_PUSH_RETRIES, push_result.stderr.strip()[:80])
        if attempt < MAX_PUSH_RETRIES:
            # Pull + rebase before retry (remote may have new commits)
            git_pull()
            time.sleep(PUSH_RETRY_DELAY)

    logger.error("[sync] git push failed after %d retries: %s", MAX_PUSH_RETRIES, message)
    return False


def claim_task(task_path: str | Path, destination_folder: str | Path) -> Path | None:
    """
    Claim a task by atomically moving it to destination_folder + immediately pushing.

    This is the core of the claim-by-move protocol:
      - First agent to successfully push wins
      - If push fails (another agent pushed first), returns None

    Args:
        task_path: current path of the task file (e.g. /Needs_Action/cloud/task.md)
        destination_folder: folder to move it to (e.g. /In_Progress/cloud/)

    Returns:
        New path of the task file if claim succeeded, None if another agent won.
    """
    src = Path(task_path)
    dst_dir = Path(destination_folder)
    dst = dst_dir / src.name

    if not src.exists():
        logger.info("[sync] Task already gone (claimed by other agent): %s", src.name)
        return None

    # Sync latest state before claiming
    git_pull()

    # Re-check after pull (another agent may have claimed during pull)
    if not src.exists():
        logger.info("[sync] Task claimed by other agent during git pull: %s", src.name)
        return None

    # Move the file (atomic on same filesystem)
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    logger.info("[sync] Claimed: %s → %s", src.name, dst_dir.name)

    # Push immediately — first push wins
    success = git_push(f"claim {src.name}")
    if success:
        return dst

    # Push failed — another agent may have won; undo our move
    logger.warning("[sync] Claim push failed for %s — undoing move", src.name)
    if dst.exists():
        shutil.move(str(dst), str(src))
    return None


# ---------------------------------------------------------------------------
# CLI entry point (for manual testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "pull"
    if cmd == "pull":
        ok = git_pull()
        print("Pull OK" if ok else "Pull had conflicts — check /Review")
    elif cmd == "push":
        msg = sys.argv[2] if len(sys.argv) > 2 else "manual push"
        ok = git_push(msg)
        print("Push OK" if ok else "Push failed")
    else:
        print(f"Usage: python sync_vault.py [pull|push <message>]")
