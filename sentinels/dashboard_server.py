#!/usr/bin/env python3
"""
dashboard_server.py
~~~~~~~~~~~~~~~~~~~~
Serves dashboard.html at http://localhost:9191 with a full JSON API.
Tries port 9191 first, then 8765, then 8080 if the preferred port is taken.

All Quick-Action buttons in the dashboard call these endpoints.

GET   /                         → dashboard.html
GET   /api/state                → vault folders + trust metrics
GET   /api/feed                 → recent audit-log entries
GET   /api/files/<folder>       → list .md files in a vault folder
POST  /api/claim                → move oldest /Inbox file → /Active
POST  /api/task                 → create task file in /Inbox
POST  /api/briefing             → generate CEO briefing in /Briefings
POST  /api/social               → create social-post task → /Pending_Approval
POST  /api/invoice              → create invoice task → /Inbox
POST  /api/audit                → create weekly-audit task → /Inbox
GET   /api/gmail                → check gmail_watcher configuration status
POST  /api/approve/<filename>   → move /Pending_Approval → /Approved
POST  /api/reject/<filename>    → move /Pending_Approval → /Rejected
POST  /api/sync                 → re-run dashboard_sync.py

Usage
-----
    python sentinels/dashboard_server.py           # auto-picks port
    python sentinels/dashboard_server.py --open    # also opens browser
    python sentinels/dashboard_server.py --port 9191
"""

import importlib.util
import json
import re
import shutil
import socket
import subprocess
import sys
import webbrowser
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

VAULT           = Path(__file__).parent.parent
PREFERRED_PORTS = [9191, 8765, 8080, 7070]

WORKFLOW_FOLDERS = [
    "Inbox", "Active", "Needs_Action", "Pending_Approval",
    "Review", "Approved", "Done", "Logs", "Briefings",
]


# ── helpers ───────────────────────────────────────────────────────────────────

def _load_parse_md():
    spec = importlib.util.spec_from_file_location(
        "dashboard_sync", VAULT / "sentinels" / "dashboard_sync.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.parse_md


parse_md = _load_parse_md()


def _free_port():
    for p in PREFERRED_PORTS:
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", p))
            s.close()
            return p
        except OSError:
            pass
    raise RuntimeError(f"None of {PREFERRED_PORTS} are available")


# ── request handler ───────────────────────────────────────────────────────────

class DashboardHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  [{ts}] {fmt % args}")

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, path: Path):
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self) -> dict:
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n) if n else b"{}"
        try:
            return json.loads(raw)
        except Exception:
            return {}

    # ── routing ───────────────────────────────────────────────────────────────

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        p = urlparse(self.path).path
        if p in ("/", "/dashboard.html"):
            self.send_html(VAULT / "dashboard.html")
        elif p == "/api/state":
            self.api_state()
        elif p == "/api/feed":
            self.api_feed()
        elif p.startswith("/api/files/"):
            self.api_files(p.removeprefix("/api/files/"))
        elif p == "/api/gmail":
            self.api_gmail()
        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        p = urlparse(self.path).path
        b = self.read_body()
        if p == "/api/claim":
            self.api_claim()
        elif p == "/api/task":
            self.api_create_task(b)
        elif p == "/api/briefing":
            self.api_briefing()
        elif p == "/api/social":
            self.api_social(b)
        elif p == "/api/invoice":
            self.api_invoice(b)
        elif p == "/api/audit":
            self.api_audit()
        elif p.startswith("/api/approve/"):
            self.api_move(p.removeprefix("/api/approve/"), "Pending_Approval", "Approved")
        elif p.startswith("/api/reject/"):
            self.api_move(p.removeprefix("/api/reject/"), "Pending_Approval", "Rejected")
        elif p == "/api/sync":
            self.api_sync()
        else:
            self.send_json({"error": "not found"}, 404)

    # ── API: state ─────────────────────────────────────────────────────────────

    def api_state(self):
        state = {
            "folders": {},
            "metrics": {},
            "pending_files": [],
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        for folder in WORKFLOW_FOLDERS:
            d = VAULT / folder
            files = sorted(d.glob("*.md")) if d.exists() else []
            state["folders"][folder] = {"count": len(files), "files": [f.name for f in files]}

        try:
            m = parse_md()
            m.pop("feed", None)
            state["metrics"] = m
        except Exception as exc:
            state["metrics_error"] = str(exc)

        pa = VAULT / "Pending_Approval"
        if pa.exists():
            for f in sorted(pa.glob("*.md")):
                text = f.read_text(encoding="utf-8", errors="replace")
                lines = [l.strip() for l in text.splitlines()
                         if l.strip() and not l.startswith(("#", "|", "---", ">"))]
                desc = lines[0][:140] if lines else ""
                try:
                    ds = re.search(r"(\d{4}-\d{2}-\d{2})", f.name)
                    age = f"{(datetime.now() - datetime.strptime(ds.group(1), '%Y-%m-%d')).days}d ago" if ds else ""
                except Exception:
                    age = ""
                state["pending_files"].append({"name": f.name, "desc": desc, "age": age})

        self.send_json(state)

    # ── API: feed ─────────────────────────────────────────────────────────────

    def api_feed(self):
        try:
            m = parse_md()
            entries = m.get("feed", [])
            self.send_json({"ok": True, "entries": entries, "count": len(entries)})
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc), "entries": []})

    # ── API: files ────────────────────────────────────────────────────────────

    def api_files(self, folder):
        d = VAULT / folder
        if not d.exists():
            self.send_json({"error": f"{folder} not found"}, 404)
            return
        files = []
        for f in sorted(d.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
            s = f.stat()
            files.append({
                "name": f.name,
                "size": s.st_size,
                "modified": datetime.fromtimestamp(s.st_mtime).strftime("%Y-%m-%d %H:%M"),
            })
        self.send_json({"folder": folder, "files": files, "count": len(files)})

    # ── API: claim task ───────────────────────────────────────────────────────

    def api_claim(self):
        inbox = VAULT / "Inbox"
        if not inbox.exists():
            self.send_json({"empty": True, "msg": "/Inbox does not exist"})
            return
        candidates = sorted(inbox.glob("*.md"), key=lambda f: f.stat().st_mtime)
        if not candidates:
            self.send_json({"empty": True, "msg": "Inbox is empty — no tasks to claim"})
            return
        f = candidates[0]
        active = VAULT / "Active"
        active.mkdir(exist_ok=True)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        text = f.read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"Status:\s*\*\*New\*\*", "Status: **In Progress**", text)
        text = text.replace("> Owner: --", f"> Owner: Claude Code\n> Claimed: {now_str}")
        f.write_text(text, encoding="utf-8")
        shutil.move(str(f), str(active / f.name))
        print(f"  [CLAIM] {f.name}: /Inbox -> /Active")
        self.send_json({"ok": True, "file": f.name, "msg": f"Claimed {f.name}"})

    # ── API: create task ──────────────────────────────────────────────────────

    def api_create_task(self, data):
        title = (data.get("title") or "").strip()
        if not title:
            self.send_json({"error": "title is required"}, 400)
            return
        description = (data.get("description") or "").strip()
        priority    = data.get("priority", "Medium")
        today       = datetime.now().strftime("%Y-%m-%d")
        slug        = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40]
        fname       = f"{today}_{slug}.md"
        fpath       = VAULT / "Inbox" / fname
        (VAULT / "Inbox").mkdir(exist_ok=True)
        fpath.write_text(
            f"# Task: {title}\n\n"
            f"> Status: **New**\n> Created: {today}\n"
            f"> Priority: {priority}\n> Owner: --\n\n---\n\n"
            f"## Description\n\n{description or '_No description provided._'}\n\n"
            f"## Acceptance Criteria\n\n- [ ] Task completed\n",
            encoding="utf-8",
        )
        print(f"  [TASK] /Inbox/{fname}")
        self.send_json({"ok": True, "file": fname})

    # ── API: generate briefing ────────────────────────────────────────────────

    def api_briefing(self):
        today    = datetime.now().strftime("%Y-%m-%d")
        now_str  = datetime.now().strftime("%Y-%m-%d %H:%M")
        fname    = f"{today}_ceo_briefing.md"
        fpath    = VAULT / "Briefings" / fname
        (VAULT / "Briefings").mkdir(exist_ok=True)

        try:
            metrics = parse_md()
        except Exception:
            metrics = {}

        counts = {}
        for folder in WORKFLOW_FOLDERS:
            d = VAULT / folder
            counts[folder] = len(list(d.glob("*.md"))) if d.exists() else 0

        done_files = sorted((VAULT / "Done").glob("*.md"),
                            key=lambda f: f.stat().st_mtime, reverse=True) \
                     if (VAULT / "Done").exists() else []
        recent = "\n".join(f"- {f.stem}" for f in done_files[:5]) or "- None yet"

        action_items = []
        if counts.get("Pending_Approval", 0):
            action_items.append(f"- [ ] Resolve {counts['Pending_Approval']} pending approval(s)")
        if counts.get("Inbox", 0):
            action_items.append(f"- [ ] Process {counts['Inbox']} task(s) in /Inbox")
        if counts.get("Active", 0):
            action_items.append(f"- [ ] Check {counts['Active']} in-progress task(s)")
        if not action_items:
            action_items = ["- [x] No immediate action required — system idle"]

        content = (
            f"# CEO Briefing — {today}\n\n"
            f"> Generated: {now_str}\n"
            f"> Maturity: Level {metrics.get('trust_level', 4)} — Autonomy\n"
            f"> Source: AI Employee Command Center (auto)\n\n---\n\n"
            f"## Executive Summary\n\n"
            f"The AI Employee is operational at Trust Level {metrics.get('trust_level', 4)}. "
            f"Pipeline status: {'active' if counts.get('Active',0) else 'idle'}. "
            f"{counts.get('Inbox', 0)} task(s) queued.\n\n---\n\n"
            f"## Trust Level 5 Progress\n\n"
            f"| Metric | Current | Target |\n|--------|---------|--------|\n"
            f"| Tasks completed | {metrics.get('tasks_done', 0)} | {metrics.get('tasks_target', 10)} |\n"
            f"| Approvals processed | {metrics.get('approvals_done', 0)} | 5 |\n"
            f"| Briefings generated | {metrics.get('briefings_done', 0)} | 3 |\n"
            f"| Rollbacks executed | {metrics.get('rollbacks_done', 0)} | 1 |\n\n---\n\n"
            f"## Vault State\n\n"
            f"| Folder | Files |\n|--------|-------|\n"
            + "\n".join(f"| {k} | {v} |" for k, v in counts.items())
            + f"\n\n---\n\n"
            f"## Recently Completed\n\n{recent}\n\n---\n\n"
            f"## Action Required\n\n" + "\n".join(action_items) + "\n\n---\n\n"
            f"*Auto-generated by `dashboard_server.py` · {now_str}*\n"
        )
        fpath.write_text(content, encoding="utf-8")
        print(f"  [BRIEFING] /Briefings/{fname}")
        self.send_json({"ok": True, "file": fname, "msg": f"Briefing written: /Briefings/{fname}"})

    # ── API: social post ──────────────────────────────────────────────────────

    def api_social(self, data):
        content   = (data.get("content") or "").strip()
        platforms = data.get("platforms") or ["Twitter"]
        if not content:
            self.send_json({"error": "content required"}, 400)
            return
        today    = datetime.now().strftime("%Y-%m-%d")
        slug     = re.sub(r"[^a-z0-9]+", "-", content[:30].lower()).strip("-")
        fname    = f"{today}_social-post_{slug}.md"
        fpath    = VAULT / "Pending_Approval" / fname
        (VAULT / "Pending_Approval").mkdir(exist_ok=True)
        platform_list = "\n".join(f"- [ ] {p}" for p in platforms)
        fpath.write_text(
            f"# Social Post: {content[:60]}\n\n"
            f"> Status: **Pending Approval**\n> Created: {today}\n"
            f"> Platforms: {', '.join(platforms)}\n> Risk: Medium\n\n---\n\n"
            f"## Post Content\n\n{content}\n\n"
            f"## Platforms\n\n{platform_list}\n\n"
            f"## Approval Required\n\n"
            f"Review content above. Move to /Approved to publish.\n",
            encoding="utf-8",
        )
        print(f"  [SOCIAL] /Pending_Approval/{fname}")
        self.send_json({"ok": True, "file": fname, "msg": f"Queued for approval: {fname}"})

    # ── API: invoice ──────────────────────────────────────────────────────────

    def api_invoice(self, data):
        customer = (data.get("customer") or "").strip()
        amount   = (data.get("amount")   or "").strip()
        due_date = (data.get("due_date") or "").strip()
        desc     = (data.get("description") or "Services rendered").strip()
        if not customer or not amount:
            self.send_json({"error": "customer and amount required"}, 400)
            return
        today = datetime.now().strftime("%Y-%m-%d")
        if not due_date:
            due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        slug  = re.sub(r"[^a-z0-9]+", "-", customer.lower()).strip("-")[:30]
        fname = f"{today}_invoice-{slug}.md"
        fpath = VAULT / "Inbox" / fname
        (VAULT / "Inbox").mkdir(exist_ok=True)
        fpath.write_text(
            f"# Task: Invoice — {customer}\n\n"
            f"> Status: **New**\n> Created: {today}\n"
            f"> Priority: High\n> Owner: --\n> Type: invoice\n\n---\n\n"
            f"## Invoice Details\n\n"
            f"| Field | Value |\n|-------|-------|\n"
            f"| Customer | {customer} |\n"
            f"| Amount | {amount} |\n"
            f"| Due Date | {due_date} |\n"
            f"| Description | {desc} |\n\n"
            f"## Acceptance Criteria\n\n"
            f"- [ ] Invoice created in Odoo\n"
            f"- [ ] Sent to {customer}\n"
            f"- [ ] Payment tracked\n",
            encoding="utf-8",
        )
        print(f"  [INVOICE] /Inbox/{fname}")
        self.send_json({"ok": True, "file": fname})

    # ── API: weekly audit ─────────────────────────────────────────────────────

    def api_audit(self):
        today = datetime.now().strftime("%Y-%m-%d")
        fname = f"{today}_weekly-audit.md"
        fpath = VAULT / "Inbox" / fname
        (VAULT / "Inbox").mkdir(exist_ok=True)
        if fpath.exists():
            self.send_json({"ok": True, "file": fname, "msg": "Audit task already queued for today"})
            return
        fpath.write_text(
            f"# Task: Weekly Business & Accounting Audit\n\n"
            f"> Status: **New**\n> Created: {today}\n"
            f"> Priority: High\n> Owner: --\n> Type: weekly_audit\n\n---\n\n"
            f"## Description\n\n"
            f"Generate the weekly business + accounting audit using `weekly_audit.generate` skill.\n\n"
            f"## Acceptance Criteria\n\n"
            f"- [ ] Audit file created in /Briefings/\n"
            f"- [ ] Odoo accounting data included\n"
            f"- [ ] Social media summary included\n"
            f"- [ ] Dashboard refreshed\n",
            encoding="utf-8",
        )
        print(f"  [AUDIT] /Inbox/{fname}")
        self.send_json({"ok": True, "file": fname, "msg": f"Audit queued: {fname}"})

    # ── API: gmail status ─────────────────────────────────────────────────────

    def api_gmail(self):
        watcher = VAULT / "sentinels" / "gmail_watcher.py"
        if not watcher.exists():
            self.send_json({"status": "missing", "msg": "gmail_watcher.py not found in /sentinels"})
            return
        creds = VAULT / "credentials.json"
        token = VAULT / "token.json"
        if not creds.exists() and not token.exists():
            self.send_json({
                "status": "unconfigured",
                "msg": "Gmail not configured — add credentials.json to vault root to enable"
            })
            return
        try:
            r = subprocess.run(
                [sys.executable, str(watcher), "--check"],
                capture_output=True, text=True, cwd=str(VAULT), timeout=6,
            )
            self.send_json({"status": "ok", "msg": r.stdout.strip() or "Watcher available"})
        except subprocess.TimeoutExpired:
            self.send_json({"status": "timeout", "msg": "Gmail watcher timed out"})
        except Exception as exc:
            self.send_json({"status": "error", "msg": str(exc)})

    # ── API: move file ────────────────────────────────────────────────────────

    def api_move(self, fname, src: str, dst: str):
        src_path = VAULT / src / fname
        if not src_path.exists():
            self.send_json({"error": f"{fname} not in /{src}"}, 404)
            return
        dst_dir = VAULT / dst
        dst_dir.mkdir(exist_ok=True)
        shutil.move(str(src_path), str(dst_dir / fname))
        print(f"  [MOVE] {fname}: /{src} -> /{dst}")
        self.send_json({"ok": True, "file": fname, "to": dst})

    # ── API: sync ─────────────────────────────────────────────────────────────

    def api_sync(self):
        try:
            r = subprocess.run(
                [sys.executable, str(VAULT / "sentinels" / "dashboard_sync.py")],
                capture_output=True, text=True, cwd=str(VAULT), timeout=15,
            )
            self.send_json({"ok": r.returncode == 0, "output": r.stdout.strip()})
        except Exception as exc:
            self.send_json({"error": str(exc)}, 500)


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    auto_open = "--open" in sys.argv
    port = None

    for arg in sys.argv[1:]:
        if arg.startswith("--port="):
            port = int(arg.split("=")[1])
        elif arg == "--port":
            idx = sys.argv.index(arg)
            if idx + 1 < len(sys.argv):
                port = int(sys.argv[idx + 1])

    if port is None:
        port = _free_port()

    url = f"http://localhost:{port}"
    server = HTTPServer(("127.0.0.1", port), DashboardHandler)
    print(f"[AI Employee Dashboard] {url}")
    print(f"  Vault : {VAULT}")
    print(f"  Ctrl+C to stop\n")

    if auto_open:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[stopped]")
        server.server_close()


if __name__ == "__main__":
    main()
