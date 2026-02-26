"""
watchdog.py — Monitor and restart critical AI Employee processes.

Checks each registered process every 60 seconds. If a process is not running,
it restarts it and notifies the human via a /Needs_Action task file.

Usage:
    python sentinels/watchdog.py

Environment:
    DRY_RUN=true   Log intended restarts without actually restarting (default: true)
    VAULT_ROOT      Override vault path (default: parent of this file's directory)

---

ALTERNATIVE: PM2 (recommended for production / always-on deployments)
-----------------------------------------------------------------------
PM2 is a battle-tested Node.js process manager that handles Python scripts
equally well. It provides auto-restart, startup persistence, and log rotation
without requiring a custom watchdog script.

Install and start:
    npm install -g pm2
    pm2 start sentinels/file_watcher.py   --interpreter python3 --name file_watcher
    pm2 start sentinels/gmail_watcher.py  --interpreter python3 --name gmail_watcher
    pm2 start sentinels/scheduler.py      --interpreter python3 --name scheduler

Persist across reboots:
    pm2 save
    pm2 startup   # follow the printed instruction to register with the OS init system

Useful commands:
    pm2 list              # status of all processes
    pm2 logs gmail_watcher  # tail logs for a specific process
    pm2 restart scheduler   # manual restart
    pm2 stop all            # stop everything

Use this watchdog.py script instead of PM2 if:
  - You want vault-native alerting (writes to /Needs_Action on restart)
  - You prefer not to install Node.js on the server
  - You need to customise restart behaviour beyond PM2's config options
"""

import logging
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(os.getenv("VAULT_ROOT", Path(__file__).parent.parent))
PID_DIR = VAULT_ROOT / ".claude" / "pids"
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
CHECK_INTERVAL = 60  # seconds

# Registered processes: name → command (run from VAULT_ROOT)
PROCESSES: dict[str, str] = {
    "file_watcher": "python sentinels/file_watcher.py",
    "gmail_watcher": "python sentinels/gmail_watcher.py",
    "scheduler": "python sentinels/scheduler.py",
}


# ---------------------------------------------------------------------------
# Process management
# ---------------------------------------------------------------------------


def is_process_running(pid_file: Path) -> bool:
    """Return True if the PID in `pid_file` corresponds to a live process."""
    if not pid_file.exists():
        return False
    try:
        pid = int(pid_file.read_text().strip())
        # Signal 0 checks if process exists without killing it
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError, ValueError):
        return False


def start_process(name: str, cmd: str) -> int | None:
    """Start a process and record its PID. Returns PID or None on dry run."""
    if DRY_RUN:
        logger.info("[DRY RUN] Would start: %s → %s", name, cmd)
        return None

    proc = subprocess.Popen(
        cmd.split(),
        cwd=str(VAULT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    PID_DIR.mkdir(parents=True, exist_ok=True)
    (PID_DIR / f"{name}.pid").write_text(str(proc.pid))
    logger.info("[watchdog] Started %s (PID %d)", name, proc.pid)
    return proc.pid


def notify_human(name: str, pid: int | None) -> None:
    """Write a Needs_Action task so the human knows a process was restarted."""
    needs_action = VAULT_ROOT / "Needs_Action"
    needs_action.mkdir(exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"{date_str}_watchdog-restarted-{name}.md"
    content = (
        f"# Watchdog Alert: {name} restarted\n\n"
        f"> Generated: {ts}\n"
        f"> Process: `{name}`\n"
        f"> New PID: {pid}\n\n"
        "---\n\n"
        f"The `{name}` process was not running and has been restarted automatically.\n\n"
        "**Please verify**:\n"
        "- Check logs for the root cause of the crash\n"
        "- Confirm the process is functioning correctly\n\n"
        "Move to `/Approved` to acknowledge, or `/Rejected` to flag for investigation.\n"
    )

    if DRY_RUN:
        logger.info("[DRY RUN] Would write Needs_Action: %s\n%s", filename, content)
        return

    (needs_action / filename).write_text(content, encoding="utf-8")
    logger.info("[watchdog] Needs_Action task written: %s", filename)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def check_and_restart() -> None:
    for name, cmd in PROCESSES.items():
        pid_file = PID_DIR / f"{name}.pid"
        if not is_process_running(pid_file):
            logger.warning("[watchdog] %s not running — restarting", name)
            pid = start_process(name, cmd)
            notify_human(name, pid)
        else:
            logger.debug("[watchdog] %s OK", name)


if __name__ == "__main__":
    logger.info("[watchdog] Starting — DRY_RUN=%s, interval=%ds", DRY_RUN, CHECK_INTERVAL)
    PID_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        try:
            check_and_restart()
        except Exception as e:
            logger.error("[watchdog] Unexpected error in check loop: %s", e)
        time.sleep(CHECK_INTERVAL)
