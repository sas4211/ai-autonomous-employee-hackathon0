"""
Ralph Wiggum Stop Hook — Enhanced (Gold Tier + Promise Detection)
=================================================================
Claude Code Stop hook: checks if work remains and decides whether to
continue the autonomy loop or allow Claude to stop.

Two completion strategies (checked in order):

  1. PROMISE-BASED (simple):
     Claude outputs <promise>TASK_COMPLETE</promise> in its last message.
     The stop hook reads the transcript, finds the promise, exits 0.

  2. FILE MOVEMENT (advanced — Gold tier default):
     Stop hook checks /Approved, /Active, /Inbox, /Needs_Action.
     If any have work files → exit 1 (continue).
     If all empty → exit 0 (stop).

The ralph-loop command stores a state file (.claude/wiggum_state.json)
with the active completion promise and per-task tracking.

Exit codes:
  0 — vault idle OR promise detected → Claude may stop
  1 — work remains → Claude continues (output feeds back as prompt)

Triggered by: .claude/settings.json Stop hook
Claude Code passes hook context via stdin as JSON.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent
STATE_FILE = VAULT_ROOT / ".claude" / "wiggum_state.json"
MAX_ITERATIONS = 20

PROMISE_PATTERN = re.compile(r"<promise>(.*?)</promise>", re.DOTALL)

WORK_FOLDERS = {
    "Approved":     (VAULT_ROOT / "Approved",     1, "Execute the approved action immediately"),
    "Active":       (VAULT_ROOT / "Active",        2, "Resume work on the in-progress task"),
    "Inbox":        (VAULT_ROOT / "Inbox",         3, "Claim and begin the next queued task"),
    "Needs_Action": (VAULT_ROOT / "Needs_Action",  4, "Check if human has responded to your question"),
}


def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "iteration": 0,
        "session_start": _now_str(),
        "last_active": _now_str(),
        "completion_promise": None,   # e.g. "TASK_COMPLETE"
        "max_iterations": MAX_ITERATIONS,
    }


def _save_state(state: dict):
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _list_md_files(folder: Path) -> list:
    if not folder.exists():
        return []
    return sorted(
        f.name for f in folder.iterdir()
        if f.suffix == ".md"
        and not f.name.startswith(".")
        and f.name != "README.md"
    )


# ── Strategy 1: Promise-based detection ───────────────────────────────────────

def _read_hook_payload() -> dict:
    """
    Claude Code passes a JSON payload to the stop hook via stdin.
    Contains: stop_hook_active, transcript_path, session_id, etc.
    Returns {} if stdin has no data or is not valid JSON.
    """
    try:
        if not sys.stdin.isatty():
            raw = sys.stdin.read(64 * 1024)  # cap at 64KB
            if raw.strip():
                return json.loads(raw)
    except Exception:
        pass
    return {}


def _get_last_assistant_message(transcript_path: str) -> str:
    """
    Read the transcript JSONL and return the last assistant message content.
    Returns "" if transcript cannot be read or has no assistant messages.
    """
    try:
        path = Path(transcript_path)
        if not path.exists():
            return ""
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        # Walk from end to find last assistant message
        for line in reversed(lines):
            try:
                entry = json.loads(line)
                if entry.get("role") == "assistant":
                    content = entry.get("content", "")
                    if isinstance(content, list):
                        # Content blocks format
                        return " ".join(
                            block.get("text", "")
                            for block in content
                            if isinstance(block, dict) and block.get("type") == "text"
                        )
                    return str(content)
            except Exception:
                continue
    except Exception:
        pass
    return ""


def _check_promise(state: dict, payload: dict) -> bool:
    """
    Return True if Claude's last message contains the active completion promise.
    E.g. if state["completion_promise"] == "TASK_COMPLETE",
    look for <promise>TASK_COMPLETE</promise> in the transcript.
    """
    required_promise = state.get("completion_promise")
    if not required_promise:
        return False  # no promise configured — use file movement strategy

    transcript_path = payload.get("transcript_path", "")
    if not transcript_path:
        return False

    last_message = _get_last_assistant_message(transcript_path)
    if not last_message:
        return False

    matches = PROMISE_PATTERN.findall(last_message)
    for match in matches:
        if match.strip() == required_promise.strip():
            return True

    return False


# ── Strategy 2: File movement detection ───────────────────────────────────────

def _scan_work_folders() -> list:
    """Return list of (folder_name, files, instruction) for non-empty work folders."""
    found = []
    for folder_name, (folder_path, priority, instruction) in WORK_FOLDERS.items():
        files = _list_md_files(folder_path)
        if files:
            found.append((folder_name, files, instruction, priority))
    found.sort(key=lambda x: x[3])
    return found


# ── Rejected folder check ─────────────────────────────────────────────────────

def _check_rejected() -> list:
    """Return list of files in /Rejected that haven't been logged yet."""
    rejected = VAULT_ROOT / "Rejected"
    return _list_md_files(rejected)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    payload = _read_hook_payload()
    state = _load_state()
    max_iters = state.get("max_iterations", MAX_ITERATIONS)

    iteration = state.get("iteration", 0) + 1
    state["iteration"] = iteration
    state["last_active"] = _now_str()

    # ── Iteration guard ───────────────────────────────────────────────────────
    if iteration > max_iters:
        print(
            f"[Ralph Wiggum] Iteration limit reached ({max_iters}). Stopping.\n"
            f"  Review /Active and /Logs. Reset: delete .claude/wiggum_state.json"
        )
        state["iteration"] = 0
        state["completion_promise"] = None
        _save_state(state)
        sys.exit(0)

    # ── Strategy 1: Promise-based completion ──────────────────────────────────
    if _check_promise(state, payload):
        print(
            f"[Ralph Wiggum] Promise detected: '{state['completion_promise']}' "
            f"(iteration {iteration}). Task complete — stopping."
        )
        state["iteration"] = 0
        state["completion_promise"] = None
        _save_state(state)
        sys.exit(0)

    # ── Handle /Rejected files (log them before continuing) ───────────────────
    rejected_files = _check_rejected()
    if rejected_files:
        print(
            f"[Ralph Wiggum] /Rejected has {len(rejected_files)} file(s) to process:\n"
            + "\n".join(f"  - {f}" for f in rejected_files)
        )
        # These feed into the continuation message below

    # ── Strategy 2: File movement detection ───────────────────────────────────
    found = _scan_work_folders()

    # Also surface rejected files as work (Claude needs to log them)
    if rejected_files and not any(f[0] == "Rejected" for f in found):
        found.append(("Rejected", rejected_files, "Log the rejection and move file to /Done", 0))
        found.sort(key=lambda x: x[3])

    if not found:
        print(f"[Ralph Wiggum] Vault idle (iteration {iteration}). No work remains. Stopping.")
        state["iteration"] = 0
        state["completion_promise"] = None
        _save_state(state)
        sys.exit(0)

    # ── Work remains — build continuation message ─────────────────────────────
    _save_state(state)

    lines = [
        f"[Ralph Wiggum] Work remains (iteration {iteration}/{max_iters}). Continue the autonomy loop.\n"
    ]

    for folder_name, files, instruction, _ in found:
        count = len(files)
        label = f"/{folder_name} ({count} item{'s' if count != 1 else ''})"
        lines.append(f"{label}: {instruction}")
        for f in files[:3]:
            lines.append(f"  - {f}")
        if count > 3:
            lines.append(f"  ... and {count - 3} more")
        lines.append("")

    top_folder, top_files, top_instruction, _ = found[0]
    lines.append(f"NEXT ACTION: {top_instruction}")
    lines.append(f"  File: {top_files[0]}")
    lines.append(f"  Follow the autonomy loop in CLAUDE.md and skills/autonomy.skill.md")

    if state.get("completion_promise"):
        lines.append(
            f"\nCompletion promise active: output <promise>{state['completion_promise']}</promise> "
            f"when the task is fully complete."
        )

    if iteration >= max_iters - 3:
        lines.append(
            f"\nWARNING: Approaching iteration limit ({iteration}/{max_iters}). "
            f"Complete current task before limit is reached."
        )

    print("\n".join(lines))
    sys.exit(0)


if __name__ == "__main__":
    main()
