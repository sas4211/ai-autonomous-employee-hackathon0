"""
Sentinel: Drop Folder Watcher
==============================
Watches a configurable "drop folder" for any new file and:
  1. Copies it to /Needs_Action/
  2. Creates a /Needs_Action/FILE_<name>.md metadata task file
     so Claude knows a new file has arrived and can process it.

Use this as a local inbox: drag any file (PDF invoice, screenshot, CSV,
voice note) into the drop folder and Claude will pick it up automatically.

Unlike file_watcher.py (which monitors /Inbox for .md task files),
this watcher handles arbitrary file types from an external drop folder.

Uses watchdog (event-driven) -- does NOT extend BaseWatcher (which is
for polling sentinels). Event-driven watchers use FileSystemEventHandler.

Setup:
  Set DROP_FOLDER_PATH in .env to the folder you want to monitor.
  Default: ~/Desktop/ai_drop

Usage:
    python sentinels/drop_watcher.py           # watch forever
    python sentinels/drop_watcher.py --once    # scan existing files once and exit
"""

import os
import shutil
import sys
import time
import logging
from datetime import datetime, timezone
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("ERROR: Run: pip install watchdog")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("ERROR: Run: pip install python-dotenv")
    sys.exit(1)

load_dotenv(VAULT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [DropWatcher] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("DropWatcher")

# Files to ignore (system files, hidden files, temp files)
IGNORE_PATTERNS = {".DS_Store", "Thumbs.db", "desktop.ini"}
IGNORE_SUFFIXES = {".tmp", ".part", ".crdownload", ".download"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _datestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class DropFolderHandler(FileSystemEventHandler):
    """
    Fires when any new file appears in the drop folder.
    Copies the file to /Needs_Action and creates a metadata .md task file.
    """

    def __init__(self, vault_path: str):
        super().__init__()
        self.needs_action = Path(vault_path) / "Needs_Action"
        self.needs_action.mkdir(parents=True, exist_ok=True)

    def on_created(self, event):
        if event.is_directory:
            return

        source = Path(event.src_path)

        # Skip system/temp files
        if source.name in IGNORE_PATTERNS:
            return
        if source.suffix.lower() in IGNORE_SUFFIXES:
            return
        if source.name.startswith("."):
            return

        # Small delay to ensure file write is complete before copying
        time.sleep(0.5)

        try:
            dest = self.needs_action / f"FILE_{source.name}"

            # Avoid overwriting existing files
            if dest.exists():
                stem = source.stem
                suffix = source.suffix
                dest = self.needs_action / f"FILE_{stem}_{int(time.time())}{suffix}"

            shutil.copy2(source, dest)
            logger.info(f"FILE DROP: {source.name} >> {dest.name}")

            self.create_metadata(source, dest)

        except Exception as exc:
            logger.error(f"Failed to process dropped file {source.name}: {exc}")

    def create_metadata(self, source: Path, dest: Path):
        """
        Create a .md task file alongside the copied file so Claude
        knows what arrived, its size, and what to do with it.
        """
        meta_path = self.needs_action / f"FILE_{source.stem}.md"

        try:
            size_bytes = source.stat().st_size
            size_str = (
                f"{size_bytes / 1024:.1f} KB"
                if size_bytes >= 1024
                else f"{size_bytes} bytes"
            )
        except OSError:
            size_str = "unknown"

        content = (
            f"---\n"
            f"type: file_drop\n"
            f"original_name: {source.name}\n"
            f"copied_to: {dest.name}\n"
            f"file_type: {source.suffix.lstrip('.') or 'unknown'}\n"
            f"size: {size_str}\n"
            f"received: {_now()}\n"
            f"status: pending\n"
            f"---\n\n"
            f"# New File: {source.name}\n\n"
            f"A new file was dropped into the AI Employee inbox.\n\n"
            f"| Field | Value |\n"
            f"|-------|-------|\n"
            f"| File | `{source.name}` |\n"
            f"| Type | {source.suffix.lstrip('.').upper() or 'Unknown'} |\n"
            f"| Size | {size_str} |\n"
            f"| Received | {_now()} |\n"
            f"| Copied to | `/Needs_Action/{dest.name}` |\n\n"
            f"---\n\n"
            f"## What Claude Should Do\n\n"
            f"1. Identify the file type and its likely purpose\n"
            f"2. If it is an **invoice** (PDF/image) — cross-check against Odoo, create follow-up task\n"
            f"3. If it is a **CSV** — check if it is a bank statement; run `finance_watcher` logic\n"
            f"4. If it is a **document** — summarise and route to the relevant task\n"
            f"5. If purpose is unclear — move this task to `/Needs_Action` with a question\n\n"
            f"## Acceptance Criteria\n\n"
            f"- [ ] File type identified\n"
            f"- [ ] Correct skill or action triggered\n"
            f"- [ ] Task moved to `/Done` when processing complete\n"
        )

        meta_path.write_text(content, encoding="utf-8")
        logger.info(f"Metadata created: {meta_path.name}")


def scan_existing(drop_folder: Path, handler: DropFolderHandler):
    """Process any files already in the drop folder (for --once mode)."""
    files = [
        f for f in drop_folder.iterdir()
        if f.is_file()
        and f.name not in IGNORE_PATTERNS
        and f.suffix.lower() not in IGNORE_SUFFIXES
        and not f.name.startswith(".")
    ]
    if not files:
        logger.info("Drop folder is empty — nothing to process.")
        return
    logger.info(f"Processing {len(files)} existing file(s) in drop folder...")
    for f in files:
        import types
        fake_event = types.SimpleNamespace(is_directory=False, src_path=str(f))
        handler.on_created(fake_event)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Drop folder watcher")
    parser.add_argument("--once", action="store_true", help="Scan existing files once and exit")
    parser.add_argument(
        "--drop-folder",
        default=os.getenv("DROP_FOLDER_PATH", str(Path.home() / "Desktop" / "ai_drop")),
        help="Folder to watch for incoming files",
    )
    args = parser.parse_args()

    drop_folder = Path(args.drop_folder)
    drop_folder.mkdir(parents=True, exist_ok=True)

    handler = DropFolderHandler(str(VAULT_ROOT))

    if args.once:
        scan_existing(drop_folder, handler)
        return

    logger.info(f"Watching drop folder: {drop_folder}")
    logger.info(f"New files will be copied to: {VAULT_ROOT / 'Needs_Action'}")
    logger.info("Press Ctrl+C to stop.\n")

    observer = Observer()
    observer.schedule(handler, str(drop_folder), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
    logger.info("Drop folder watcher stopped.")


if __name__ == "__main__":
    main()
