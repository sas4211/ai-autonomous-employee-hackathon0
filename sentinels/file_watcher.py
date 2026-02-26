"""
Sentinel: Vault Inbox Watcher
Monitors /Inbox for new .md files and logs arrival events.
When a new task arrives, it writes an event file to /Logs/events/
so Claude Code can pick it up on next autonomy loop cycle.

Usage:
    python sentinels/file_watcher.py

Install deps first:
    uv pip install watchdog
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:
    print("ERROR: watchdog not installed. Run: uv pip install watchdog")
    sys.exit(1)


VAULT_ROOT = Path(__file__).parent.parent
INBOX = VAULT_ROOT / "Inbox"
LOGS_EVENTS = VAULT_ROOT / "Logs" / "events"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _datestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class InboxHandler(FileSystemEventHandler):
    """Fires when a new .md file appears in /Inbox."""

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix != ".md":
            return

        LOGS_EVENTS.mkdir(parents=True, exist_ok=True)

        event_payload = {
            "event_id": f"{int(time.time())}",
            "event_type": "task.inbound",
            "timestamp": _now(),
            "source": "file_watcher",
            "vault": "ai-employee",
            "payload": {
                "task_file": path.name,
                "from_folder": "external",
                "to_folder": "/Inbox",
                "metadata": {},
            },
        }

        event_file = LOGS_EVENTS / f"{_datestamp()}_task_inbound_{path.stem}.json"
        event_file.write_text(json.dumps(event_payload, indent=2))

        print(f"[{_now()}] NEW TASK DETECTED: {path.name}")
        print(f"  Event logged: {event_file.name}")
        print("  Run `claude` in the vault directory to process it.")


def main():
    INBOX.mkdir(parents=True, exist_ok=True)
    print(f"[Sentinel] Watching {INBOX} for new tasks...")
    print("Press Ctrl+C to stop.\n")

    observer = Observer()
    observer.schedule(InboxHandler(), str(INBOX), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
    print("\n[Sentinel] Stopped.")


if __name__ == "__main__":
    main()
