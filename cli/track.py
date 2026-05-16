"""Watchlist & snapshot tracking for senior_analyst.

Stores company snapshots and computes deltas between them.
Data lives in ~/.config/senior_analyst/ by default.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".config" / "senior_analyst"
WATCHLIST_PATH = CONFIG_DIR / "watchlist.json"
SNAPSHOTS_DIR = CONFIG_DIR / "snapshots"


def _ensure_dirs():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def load_watchlist() -> list[dict]:
    """Load the watchlist from disk."""
    _ensure_dirs()
    if not WATCHLIST_PATH.exists():
        return []
    try:
        return json.loads(WATCHLIST_PATH.read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_watchlist(entries: list[dict]):
    """Save the watchlist to disk."""
    _ensure_dirs()
    WATCHLIST_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=2), "utf-8")


def add_to_watchlist(name: str, ticker: str) -> dict:
    """Add a company to the watchlist. Returns the entry."""
    entries = load_watchlist()
    # Check for duplicates
    for e in entries:
        if e.get("ticker") == ticker or e.get("name") == name:
            return e  # Already exists
    entry = {"name": name, "ticker": ticker, "added_at": datetime.now().isoformat()}
    entries.append(entry)
    save_watchlist(entries)
    return entry


def remove_from_watchlist(ticker: str) -> bool:
    """Remove a company from the watchlist by ticker."""
    entries = load_watchlist()
    before = len(entries)
    entries = [e for e in entries if e.get("ticker") != ticker]
    if len(entries) < before:
        save_watchlist(entries)
        return True
    return False


def save_snapshot(company: str, ticker: str, metrics: dict,
                  key_judgments: list[str] | None = None,
                  confidence: float | None = None) -> str:
    """Save a snapshot of a company's analysis. Returns the filename."""
    _ensure_dirs()
    date_str = datetime.now().strftime("%Y%m%d")
    safe_name = company.replace("/", "_").replace(" ", "_")
    filename = f"{safe_name}_{date_str}.json"
    filepath = SNAPSHOTS_DIR / filename

    snapshot = {
        "company": company,
        "ticker": ticker,
        "date": datetime.now().isoformat(),
        "metrics": metrics,
        "key_judgments": key_judgments or [],
        "confidence": confidence,
    }
    filepath.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), "utf-8")
    return filename


def load_latest_snapshot(company: str) -> dict | None:
    """Load the most recent snapshot for a company."""
    _ensure_dirs()
    safe_name = company.replace("/", "_").replace(" ", "_")
    matches = sorted(SNAPSHOTS_DIR.glob(f"{safe_name}_*.json"), reverse=True)
    if not matches:
        return None
    try:
        return json.loads(matches[0].read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def compute_delta(current: dict, previous: dict) -> dict:
    """Compute the delta between two snapshots' metrics.

    Returns a dict of {metric: {"current": x, "previous": y, "change": z, "change_pct": p}}
    """
    delta = {}
    cur_m = current.get("metrics", {})
    prev_m = previous.get("metrics", {})

    all_keys = set(cur_m.keys()) | set(prev_m.keys())
    for key in sorted(all_keys):
        cur_val = cur_m.get(key)
        prev_val = prev_m.get(key)
        entry = {"current": cur_val, "previous": prev_val}

        if isinstance(cur_val, (int, float)) and isinstance(prev_val, (int, float)):
            change = cur_val - prev_val
            entry["change"] = change
            if prev_val != 0:
                entry["change_pct"] = round(change / abs(prev_val) * 100, 2)

        delta[key] = entry

    return delta


def list_snapshots(company: str | None = None) -> list[dict]:
    """List all snapshots, optionally filtered by company name."""
    _ensure_dirs()
    results = []
    for fp in sorted(SNAPSHOTS_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(fp.read_text("utf-8"))
            if company and data.get("company") != company:
                continue
            data["_filename"] = fp.name
            results.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: track.py [--list | --add NAME TICKER | --remove TICKER | --delta COMPANY | --snapshots [COMPANY]]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "--list":
        for e in load_watchlist():
            snap = load_latest_snapshot(e["name"])
            latest = snap["date"][:10] if snap else "no snapshot"
            print(f"  {e['name']} ({e['ticker']}) — added {e['added_at'][:10]}, latest: {latest}")
    elif cmd == "--add" and len(sys.argv) >= 4:
        entry = add_to_watchlist(sys.argv[2], sys.argv[3])
        print(f"Added: {entry}")
    elif cmd == "--remove" and len(sys.argv) >= 3:
        if remove_from_watchlist(sys.argv[2]):
            print(f"Removed: {sys.argv[2]}")
        else:
            print(f"Not found: {sys.argv[2]}")
    elif cmd == "--delta" and len(sys.argv) >= 3:
        company = sys.argv[2]
        snaps = list_snapshots(company)
        if len(snaps) < 2:
            print(f"Need ≥2 snapshots for {company}, found {len(snaps)}")
        else:
            delta = compute_delta(snaps[0], snaps[1])
            for k, v in delta.items():
                pct = v.get("change_pct", "")
                pct_str = f" ({pct:+.1f}%)" if isinstance(pct, (int, float)) else ""
                print(f"  {k}: {v['current']} ← {v['previous']}{pct_str}")
    elif cmd == "--snapshots":
        company = sys.argv[2] if len(sys.argv) >= 3 else None
        for s in list_snapshots(company)[:10]:
            print(f"  {s.get('company', '?')} | {s.get('date', '?')[:10]} | conf={s.get('confidence', '?')}")
    else:
        print(f"Unknown command: {cmd}")
