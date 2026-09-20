#!/usr/bin/env python3
"""
Zero-dependency Daf Yomi calendar helper.

Uses Hebcal's public API. No API key is required.

Examples:
  python scripts/yomi_context.py --date 2026-08-30
  python scripts/yomi_context.py --date 2026-08-15 --through 2026-08-30

This helper is for /daf yomi calendar resolution. Exact-daf requests go
directly to Sefaria and do not depend on the daily cycle.

By default it works fully offline (offline_calendar.py: Hebcal's Daf Yomi
algorithm plus the vendored pyluach calendar, verified against Hebcal).
Pass --live to prefer the Hebcal API; if Hebcal is unreachable it falls back
to the offline calculation automatically.
"""

# Created by Adam Blumenthal in honor of David and Barbara Blumenthal,
# who always pushed him to keep asking questions.

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HEBCAL = "https://www.hebcal.com/hebcal"

def _get_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "daf/3.0 (+Agent Skills)"}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)

def _hebcal(start: dt.date, end: dt.date, *, daf=True, calendar=True) -> dict:
    params = {
        "v": "1",
        "cfg": "json",
        "start": start.isoformat(),
        "end": end.isoformat(),
        "i": "off",
    }
    if daf:
        params["F"] = "on"
    if calendar:
        params.update({
            "maj": "on",
            "min": "on",
            "mf": "on",
            "nx": "on",
            "ss": "on",
            "mod": "on",
            "d": "on",
        })
    return _get_json(HEBCAL + "?" + urllib.parse.urlencode(params))

def _split_daf_title(title: str) -> tuple[str, int | None]:
    # Handles tractates with spaces, e.g. "Bava Batra 42".
    m = re.match(r"^(.*)\s+(\d+)$", title.strip())
    if not m:
        return title.strip(), None
    return m.group(1), int(m.group(2))

def _items_by_date(payload: dict) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for item in payload.get("items", []):
        out.setdefault(item.get("date", ""), []).append(item)
    return out

def _daf_item(items: list[dict]) -> dict | None:
    for item in items:
        if item.get("category") == "dafyomi":
            return item
    return None

def _calendar_items(items: list[dict]) -> list[dict]:
    # Exclude the Daf itself and bare Hebrew-date events.
    return [
        i for i in items
        if i.get("category") not in {"dafyomi", "hebdate"}
    ]


def _find_masechet_finish(
    start: dt.date,
    current_tractate: str,
) -> tuple[dt.date | None, int | None]:
    """Find the final daily assignment in the current masechet."""
    horizon = start + dt.timedelta(days=220)
    payload = _hebcal(start, horizon, daf=True, calendar=False)
    by_date = _items_by_date(payload)

    last_same = None
    for offset in range((horizon - start).days + 1):
        day = start + dt.timedelta(days=offset)
        item = _daf_item(by_date.get(day.isoformat(), []))
        if not item:
            continue
        tractate, _ = _split_daf_title(item.get("title", ""))
        if tractate == current_tractate:
            last_same = day
        elif last_same is not None:
            return last_same, (last_same - start).days
    return last_same, ((last_same - start).days if last_same else None)

def _record(day: dt.date, items: list[dict]) -> dict:
    daf = _daf_item(items)
    if not daf:
        return {
            "date": day.isoformat(),
            "daf": None,
            "special_days": _calendar_items(items),
        }
    tractate, page = _split_daf_title(daf.get("title", ""))
    return {
        "date": day.isoformat(),
        "hebrew_date": daf.get("hdate"),
        "daf": daf.get("title"),
        "daf_hebrew": daf.get("hebrew"),
        "tractate": tractate,
        "page": page,
        "sefaria_link": daf.get("link"),
        "special_days": [
            {
                "title": i.get("title"),
                "hebrew": i.get("hebrew"),
                "category": i.get("category"),
                "subcat": i.get("subcat"),
            }
            for i in _calendar_items(items)
        ],
    }

def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True, help="Start date YYYY-MM-DD")
    p.add_argument("--through", help="Inclusive end date YYYY-MM-DD")
    p.add_argument("--live", action="store_true", help="Prefer the Hebcal API over the offline calculation")
    args = p.parse_args()

    try:
        start = dt.date.fromisoformat(args.date)
        end = dt.date.fromisoformat(args.through) if args.through else start
    except ValueError:
        print("Dates must be YYYY-MM-DD", file=sys.stderr)
        return 2

    if end < start:
        print("--through may not be earlier than --date", file=sys.stderr)
        return 2

    def offline(note: str | None = None) -> int:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import offline_calendar
        result = offline_calendar.context(start, end)
        if note:
            result["note"] = note
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return 0

    if not args.live:
        return offline()
    try:
        payload = _hebcal(start, end, daf=True, calendar=True)
    except Exception as exc:
        return offline(f"Hebcal unreachable ({exc.__class__.__name__}); used the offline calculation.")
    by_date = _items_by_date(payload)
    records = []
    for offset in range((end - start).days + 1):
        day = start + dt.timedelta(days=offset)
        records.append(_record(day, by_date.get(day.isoformat(), [])))

    result = {
        "range": {"start": start.isoformat(), "end": end.isoformat()},
        "days": records,
        "attribution": "Calendar and Daf Yomi assignment data: Hebcal.com",
    }

    first = records[0] if records else None
    if first and first.get("tractate"):
        finish, remaining = _find_masechet_finish(start, first["tractate"])
        result["current_masechet"] = {
            "name": first["tractate"],
            "days_remaining_after_requested_daf": remaining,
            "finish_date": finish.isoformat() if finish else None,
            "within_14_days": bool(remaining is not None and remaining <= 14),
            "within_7_days": bool(remaining is not None and remaining <= 7),
            "within_3_days": bool(remaining is not None and remaining <= 3),
            "siyum_day": remaining == 0,
        }

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
