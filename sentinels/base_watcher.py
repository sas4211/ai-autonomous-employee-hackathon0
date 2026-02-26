"""
Base Watcher (Abstract Base Class)
===================================
All AI Employee sentinel/watcher scripts extend this class.

Core contract:
  - check_for_updates() -> list   : poll the external service; return new items
  - create_action_file(item) -> Path : write a .md task file for Claude to process

The run() method handles the polling loop with per-item error isolation.
Graceful degradation: check_for_updates() must return [] (not raise) when the
service is unconfigured or unreachable.

Usage (for all subclasses):
    watcher = MyWatcher()
    watcher.run()          # blocking loop
    watcher.run_once()     # single check cycle (used by scheduler)

Note: file_watcher.py uses watchdog (event-driven) and does not extend BaseWatcher.
      All polling sentinels must extend BaseWatcher.
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    print("ERROR: python-dotenv not installed. Run: pip install python-dotenv")
    raise

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class BaseWatcher(ABC):
    """
    Abstract base class for all AI Employee polling sentinels.

    Each subclass monitors one external data source (Gmail, Odoo, WhatsApp,
    banking CSVs, etc.) and translates new events into vault task files that
    Claude Code can claim and process.

    Subclass must implement:
        check_for_updates(self) -> list
        create_action_file(self, item) -> Path
    """

    def __init__(self, vault_path: "str | Path", check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.inbox = self.vault_path / "Inbox"
        self.needs_action = self.vault_path / "Needs_Action"
        self.logs_events = self.vault_path / "Logs" / "events"
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)
        load_dotenv(self.vault_path / ".env")

    # ── Required overrides ────────────────────────────────────────────────────

    @abstractmethod
    def check_for_updates(self) -> list:
        """
        Poll the external service and return a list of new items to process.

        Contract:
        - MUST return [] (not raise) when the service is unconfigured or unreachable
        - Each item can be any dict — it is passed as-is to create_action_file()
        - Implement idempotency: track what you've already seen
        """
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        """
        Write a vault .md task file for a single item from check_for_updates().

        Contract:
        - File MUST be written to self.inbox or self.needs_action
        - File MUST include > Type: and > Source: frontmatter fields
        - Returns the Path of the created file (or None if skipped)
        """
        pass

    # ── Polling loop ──────────────────────────────────────────────────────────

    def run(self):
        """Blocking polling loop: check -> act -> sleep. Errors are isolated."""
        self.logger.info(
            f"Starting {self.__class__.__name__} (interval: {self.check_interval}s)"
        )
        while True:
            self._run_cycle()
            time.sleep(self.check_interval)

    def run_once(self) -> list:
        """Single check cycle — no loop. Used by scheduler and --once flag."""
        return self._run_cycle()

    def _run_cycle(self) -> list:
        """Internal: run one check-and-act cycle. Returns list of items processed."""
        try:
            items = self.check_for_updates()
            for item in items:
                try:
                    path = self.create_action_file(item)
                    if path:
                        self.logger.info(f"Created action file: {path.name}")
                except Exception as exc:
                    self.logger.error(f"Failed to create action file for item: {exc}")
            return items
        except Exception as exc:
            self.logger.error(f"Error in {self.__class__.__name__}: {exc}")
            return []

    # ── Shared utilities ──────────────────────────────────────────────────────

    @staticmethod
    def now() -> str:
        """UTC timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def datestamp() -> str:
        """UTC date in YYYY-MM-DD format."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def log_event(self, event_type: str, payload: dict):
        """Write a structured JSON event to /Logs/events/."""
        self.logs_events.mkdir(parents=True, exist_ok=True)
        ts = str(int(time.time()))
        slug = event_type.replace(".", "_")
        out = self.logs_events / f"{self.datestamp()}_{slug}_{ts}.json"
        out.write_text(
            json.dumps(
                {
                    "event_type": event_type,
                    "timestamp": self.now(),
                    "source": self.__class__.__name__,
                    "payload": payload,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def task_exists(self, slug: str) -> bool:
        """
        Return True if a task file containing 'slug' already exists in
        Inbox, Active, or Done — prevents duplicate task creation.
        """
        for folder in ["Inbox", "Active", "Done"]:
            if list((self.vault_path / folder).glob(f"*{slug}*")):
                return True
        return False

    def write_task(self, folder: Path, filename: str, content: str) -> Path:
        """Write content to folder/filename and return the Path."""
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / filename
        path.write_text(content, encoding="utf-8")
        return path
