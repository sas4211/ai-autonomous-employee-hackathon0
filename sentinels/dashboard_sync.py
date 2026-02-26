#!/usr/bin/env python3
"""
dashboard_sync.py — One-way sync: Dashboard.md → dashboard.html

Reads live metrics from Dashboard.md (the agent's source of truth) and
updates the hardcoded numbers in dashboard.html so both stay in sync.

Usage:
    python sentinels/dashboard_sync.py            # sync once
    python sentinels/dashboard_sync.py --watch    # re-sync whenever Dashboard.md changes
"""

import re
import sys
import time
from pathlib import Path

VAULT     = Path(__file__).parent.parent
MD_PATH   = VAULT / "Dashboard.md"
HTML_PATH = VAULT / "dashboard.html"


# ─── PARSE ───────────────────────────────────────────────────────────────────

def parse_md() -> dict:
    """Extract key metrics from Dashboard.md."""
    text = MD_PATH.read_text(encoding="utf-8")
    m = {}

    # Trust Progress table rows
    # | Tasks completed | **3** | 10 | -- |
    hit = re.search(r'\| Tasks completed\s*\|\s*\*\*(\d+)\*\*\s*\|\s*(\d+)', text)
    m["tasks_done"]     = int(hit.group(1)) if hit else 0
    m["tasks_target"]   = int(hit.group(2)) if hit else 10

    hit = re.search(r'\| Approvals processed\s*\|\s*\*?\*?(\d+)\*?\*?\s*\|\s*(\d+)', text)
    m["approvals_done"] = int(hit.group(1)) if hit else 0

    # Briefings: may or may not have **bold**
    hit = re.search(r'\| Briefing dates\s*\|\s*\*?\*?(\d+)\*?\*?\s*\|\s*(\d+)', text)
    m["briefings_done"]   = int(hit.group(1)) if hit else 0
    m["briefings_target"] = int(hit.group(2)) if hit else 3

    hit = re.search(r'\| Successful rollback\s*\|\s*\*?\*?(\d+)\*?\*?\s*\|\s*(\d+)', text)
    m["rollbacks_done"] = int(hit.group(1)) if hit else 0

    hit = re.search(r'\| Human audit review\s*\|\s*\*?\*?(\d+)\*?\*?\s*\|\s*(\d+)', text)
    m["audits_done"] = int(hit.group(1)) if hit else 0

    # Pending Approvals — count checkbox lines
    pending_block = re.search(r'## .*?Pending Approvals(.*?)---', text, re.DOTALL)
    if pending_block:
        m["pending_approvals"] = len(re.findall(r'- \[', pending_block.group(1)))
    else:
        m["pending_approvals"] = 0

    # Active folder count from Vault State table
    hit = re.search(r'\| Active\s+\|\s*(\d+)', text)
    m["active_tasks"] = int(hit.group(1)) if hit else 0

    # Trust / maturity level
    hit = re.search(r'Vault maturity.*?Level (\d+)', text)
    m["trust_level"] = int(hit.group(1)) if hit else 4

    # How many trust targets are met (non-zero progress bars)
    targets_met = sum([
        m["tasks_done"]     >= m["tasks_target"],
        m["approvals_done"] >= 5,
        m["briefings_done"] >= m["briefings_target"],
        m["rollbacks_done"] >= 1,
        m["audits_done"]    >= 1,
        True,                            # skills are always 25/25
    ])
    m["targets_met"] = targets_met

    # Last-sync date
    hit = re.search(r'Last sync:\s*(\d{4}-\d{2}-\d{2})', text)
    m["last_sync"] = hit.group(1) if hit else "—"

    # Activity feed from Audit Log section (up to 12 rows)
    # Use \n--- to avoid matching the | --- | table header separator
    audit_block = re.search(r'## .*?Audit Log.*?\n(.*?)\n---', text, re.DOTALL)
    feed = []
    if audit_block:
        rows = re.findall(
            r'\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|',
            audit_block.group(1)
        )
        badge_map = {
            "error": "ERROR", "fail": "ERROR",
            "warn":  "WARNING", "unanswer": "WARNING", "block": "WARNING",
            "approv": "APPROVAL", "reject": "APPROVAL",
            "complet": "ACTION", "creat": "ACTION", "generat": "ACTION",
            "fix": "ACTION", "install": "ACTION", "build": "ACTION",
        }
        for date, action, file_ in rows[:12]:
            action_l = action.lower()
            badge = "INFO"
            for kw, b in badge_map.items():
                if kw in action_l:
                    badge = b
                    break
            file_clean = file_.strip().replace("'", "\\'").replace("`", "")
            msg = f"{date} — {action.strip()} ({file_clean})"
            feed.append({"badge": badge, "msg": msg, "time": date})
    m["feed"] = feed
    return m


def pct(done, total):
    return min(100, round(done / total * 100)) if total else 0


# ─── PATCH HTML ──────────────────────────────────────────────────────────────

def patch_html(m: dict):
    html = HTML_PATH.read_text(encoding="utf-8")

    # ── KPI counters (boot-sequence countUp calls) ──────────────────────────
    html = re.sub(
        r"countUp\(document\.getElementById\('kpi0'\),\s*\d+\)",
        f"countUp(document.getElementById('kpi0'), {m['tasks_done']})",
        html,
    )
    html = re.sub(
        r"countUp\(document\.getElementById\('kpi1'\),\s*\d+\)",
        f"countUp(document.getElementById('kpi1'), {m['pending_approvals']})",
        html,
    )
    html = re.sub(
        r"countUp\(document\.getElementById\('kpi2'\),\s*\d+\)",
        f"countUp(document.getElementById('kpi2'), {m['active_tasks']})",
        html,
    )
    html = re.sub(
        r"countUp\(document\.getElementById\('kpi3'\),\s*\d+\)",
        f"countUp(document.getElementById('kpi3'), {m['trust_level']})",
        html,
    )

    # ── KPI sub-labels ──────────────────────────────────────────────────────
    html = re.sub(
        r'(<div class="kpi-sub">)\d+ of \d+ for Level 5(</div>)',
        f'\\g<1>{m["tasks_done"]} of {m["tasks_target"]} for Level 5\\g<2>',
        html,
    )
    pending_label = (
        f'{m["pending_approvals"]} file — action required'
        if m["pending_approvals"] else "0 files — all clear"
    )
    html = re.sub(
        r'(<div class="kpi-sub">)\d+ file[^<]*(</div>)',
        f'\\g<1>{pending_label}\\g<2>',
        html,
    )
    active_label = "Idle — queue empty" if m["active_tasks"] == 0 else f"{m['active_tasks']} task(s) running"
    html = re.sub(
        r'(<div class="kpi-sub">)Idle[^<]*(</div>)',
        f'\\g<1>{active_label}\\g<2>',
        html,
    )
    html = re.sub(
        r'(<div class="kpi-sub">)Autonomy Phase[^<]*(</div>)',
        f'\\g<1>Autonomy Phase — {m["targets_met"]} of 6 targets met\\g<2>',
        html,
    )

    # ── Trust bar values and percentages ────────────────────────────────────
    trust_rows = [
        ("Tasks",        m["tasks_done"],     m["tasks_target"]),
        ("Approvals",    m["approvals_done"],  5),
        ("Briefings",    m["briefings_done"],  m["briefings_target"]),
        ("Rollbacks",    m["rollbacks_done"],  1),
        ("Human Audits", m["audits_done"],     3),
        ("Skills Active", 25,                  25),
    ]

    for label, done, target in trust_rows:
        p = pct(done, target)

        # Update trust-val text: "3 / 10"
        html = re.sub(
            rf'(<span class="trust-label">{re.escape(label)}</span>\s*'
            rf'<span class="trust-val">)[^<]+(</span>)',
            rf'\g<1>{done} / {target}\g<2>',
            html,
        )

        # Update data-w and data-target on the bar inside the same trust-item
        # Use a non-greedy match anchored to the label within the trust-item block
        html = re.sub(
            rf'(<span class="trust-label">{re.escape(label)}</span>.*?'
            rf'<div class="t-fill" )data-w="\d+" data-target="[^"]*"',
            rf'\g<1>data-w="{p}" data-target="{p}%"',
            html,
            flags=re.DOTALL,
        )

    # ── Trust progress tracker sub-label ────────────────────────────────────
    html = re.sub(
        r'(Trust Level 5 — Progress Tracker.*?current: )\d+ / \d+',
        rf'\g<1>{m["targets_met"]} / 6',
        html,
        flags=re.DOTALL,
    )

    # ── Last-sync date ───────────────────────────────────────────────────────
    html = re.sub(
        r'(<span class="sec-sub">as of )\d{4}-\d{2}-\d{2}(</span>)',
        rf'\g<1>{m["last_sync"]}\g<2>',
        html,
    )

    # ── Activity feed (FEED_DATA array) ─────────────────────────────────────
    if m["feed"]:
        lines = ["const FEED_DATA = ["]
        badge_pad = max(len(e["badge"]) for e in m["feed"])
        for e in m["feed"]:
            msg_esc = e["msg"].replace("\\", "\\\\").replace("'", "\\'")
            lines.append(
                f"  {{ badge:'{e['badge']:<{badge_pad}}', "
                f"msg:'{msg_esc}', "
                f"time:'{e['time']}' }},"
            )
        lines.append("];")
        new_feed = "\n".join(lines)
        html = re.sub(
            r'const FEED_DATA = \[.*?\];',
            new_feed,
            html,
            flags=re.DOTALL,
        )

    HTML_PATH.write_text(html, encoding="utf-8")


# ─── MAIN ────────────────────────────────────────────────────────────────────

def sync_once():
    metrics = parse_md()
    patch_html(metrics)
    print("[OK] dashboard_sync -- synced successfully")
    print(f"   Tasks       : {metrics['tasks_done']}/{metrics['tasks_target']}")
    print(f"   Approvals   : {metrics['approvals_done']}/5  (pending: {metrics['pending_approvals']})")
    print(f"   Briefings   : {metrics['briefings_done']}/{metrics['briefings_target']}")
    print(f"   Rollbacks   : {metrics['rollbacks_done']}/1")
    print(f"   Trust Level : {metrics['trust_level']}  ({metrics['targets_met']}/6 targets met)")
    print(f"   Feed entries: {len(metrics['feed'])}")


def watch():
    print(f"[WATCH] Watching {MD_PATH} -- will sync on every save. Ctrl+C to stop.\n")
    last_mtime = None
    try:
        while True:
            mtime = MD_PATH.stat().st_mtime
            if mtime != last_mtime:
                last_mtime = mtime
                if last_mtime is not None:   # skip the first boot read
                    print(f"\n[{time.strftime('%H:%M:%S')}] Change detected -- syncing...")
                    sync_once()
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nWatcher stopped.")


if __name__ == "__main__":
    if not MD_PATH.exists():
        print(f"ERROR: {MD_PATH} not found", file=sys.stderr)
        sys.exit(1)
    if not HTML_PATH.exists():
        print(f"ERROR: {HTML_PATH} not found", file=sys.stderr)
        sys.exit(1)

    if "--watch" in sys.argv:
        watch()
    else:
        sync_once()
