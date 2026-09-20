#!/usr/bin/env python3
"""
Personal learning log for the Daf skill: where you were last, and where you
are now, in each track (Yomi, exact daf/range, ByMishnah).

Storage: --log PATH, else $DAF_LOG, else ~/.daf/learning-log.json.

Examples:
  python scripts/learning_log.py show
  python scripts/learning_log.py record --mode exact --ref "Chullin 23b" --next "Chullin 24a"
  python scripts/learning_log.py record --mode yomi --ref "Chullin 122" --date 2026-08-30
  python scripts/learning_log.py record --mode bymishnah --masechet Chullin \\
      --unit 13 --seq-end 14 --total 74 --label "Perek 2, Mishnah 1" --ref "Chullin 27b-32a"
  python scripts/learning_log.py summary          # compact text for a memory store
  python scripts/learning_log.py reset --track bymishnah --masechet Chullin --yes  # after confirming
"""

# Created by Adam Blumenthal in honor of David and Barbara Blumenthal,
# who always pushed him to keep asking questions.

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

HISTORY_CAP = 400
SCHEMA = 1


def log_path(explicit: str | None = None) -> Path:
    raw = explicit or os.environ.get("DAF_LOG") or "~/.daf/learning-log.json"
    return Path(raw).expanduser()


def empty_log() -> dict:
    return {"schema": SCHEMA, "last_session": None, "active_track": None,
            "tracks": {"yomi": None, "exact": None, "bymishnah": {}},
            "active_bymishnah": None, "history": []}


def load(path: Path) -> dict:
    if not path.exists():
        return empty_log()
    data = json.loads(path.read_text(encoding="utf-8"))
    base = empty_log()
    base.update(data)
    base["tracks"] = {**empty_log()["tracks"], **data.get("tracks", {})}
    return base


def save(path: Path, log: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def record(log: dict, *, mode: str, ref: str | None, date: str, nxt: str | None = None,
           masechet: str | None = None, unit: int | None = None, seq_end: int | None = None,
           total: int | None = None, label: str | None = None, extras: list[str] | None = None,
           partial: str | None = None) -> dict:
    entry = {"date": date, "mode": mode, "ref": ref}
    if extras:
        entry["extras"] = extras
    if mode == "yomi":
        log["tracks"]["yomi"] = {"last_date": date, "last_daf": ref}
    elif mode in ("exact", "range"):
        log["tracks"]["exact"] = {"last_ref": ref, "next_ref": nxt, "date": date}
    elif mode == "bymishnah":
        if not masechet:
            raise ValueError("bymishnah records need --masechet")
        prev = log["tracks"]["bymishnah"].get(masechet, {})
        done_today = prev.get("last_date") == date
        finished = partial is None or _is_last_part(partial)
        track = {
            "total_mishnayot": total or prev.get("total_mishnayot"),
            "completed_through": (seq_end if (seq_end is not None and finished)
                                  else prev.get("completed_through", 0)),
            "last_unit": unit,
            "next_unit": ((unit + 1) if finished else unit) if unit else None,
            "in_progress": None if finished else {"unit": unit, "part_done": partial},
            "last_label": label,
            "last_gemara": ref,
            "last_date": date,
            "started": prev.get("started", date),
            "sessions": prev.get("sessions", 0) + 1,
            "sessions_today": (prev.get("sessions_today", 0) + 1) if done_today else 1,
        }
        t = track["total_mishnayot"]
        c = track["completed_through"]
        track["complete"] = bool(t and c and c >= t)
        log["tracks"]["bymishnah"][masechet] = track
        log["active_bymishnah"] = masechet
        entry.update({"masechet": masechet, "unit": unit, "label": label, "part": partial,
                      "position": f"{c} of {t}" if t and c else None})
    else:
        raise ValueError(f"unknown mode {mode}")
    log["active_track"] = mode if mode != "range" else "exact"
    log["last_session"] = entry
    log["history"] = (log["history"] + [entry])[-HISTORY_CAP:]
    return log


def _is_last_part(partial: str) -> bool:
    try:
        done, of = (int(x) for x in partial.split("/"))
        return done >= of
    except ValueError:
        return True


def summary(log: dict) -> str:
    lines = []
    ls = log.get("last_session")
    if ls:
        where = ls.get("label") or ls.get("ref")
        extra = f" ({ls['masechet']})" if ls.get("masechet") else ""
        lines.append(f"Last session: {ls['date']}, {ls['mode']}{extra}: {where}")
    for name, t in sorted(log["tracks"].get("bymishnah", {}).items()):
        pos = f"{t.get('completed_through')} of {t.get('total_mishnayot')} mishnayot complete"
        ip = t.get("in_progress")
        state = ("COMPLETE" if t.get("complete")
                 else f"unit {ip['unit']} in progress (parts done {ip['part_done']})" if ip
                 else f"next unit {t.get('next_unit')}")
        active = " [active]" if log.get("active_bymishnah") == name else ""
        lines.append(f"ByMishnah {name}{active}: {pos}; last {t.get('last_label')} "
                     f"({t.get('last_gemara')}) on {t.get('last_date')}; {state}")
    ex = log["tracks"].get("exact")
    if ex:
        lines.append(f"Exact track: last {ex.get('last_ref')} on {ex.get('date')}; next {ex.get('next_ref')}")
    yo = log["tracks"].get("yomi")
    if yo:
        lines.append(f"Daf Yomi: last {yo.get('last_daf')} on {yo.get('last_date')}")
    lines.append(f"Sessions logged: {len(log.get('history', []))}")
    return "\n".join(lines) if ls else "No sessions logged yet."


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--log", help="Path to the log file")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show")
    sub.add_parser("summary")
    sub.add_parser("path")
    r = sub.add_parser("record")
    r.add_argument("--mode", required=True, choices=["yomi", "exact", "range", "bymishnah"])
    r.add_argument("--ref")
    r.add_argument("--next", dest="nxt")
    r.add_argument("--date", default=dt.date.today().isoformat())
    r.add_argument("--masechet")
    r.add_argument("--unit", type=int)
    r.add_argument("--seq-end", type=int)
    r.add_argument("--total", type=int)
    r.add_argument("--label")
    r.add_argument("--extras", nargs="*", help="Output or depth options used, e.g. audio pdf rishonim")
    r.add_argument("--partial", help='For a unit taught in parts: parts done, e.g. "1/3"')
    rs = sub.add_parser("reset")
    rs.add_argument("--track", choices=["all", "yomi", "exact", "bymishnah"], default="all")
    rs.add_argument("--masechet")
    rs.add_argument("--yes", action="store_true",
                    help="Required to actually clear. Pass only after the learner confirms.")
    a = sub.add_parser("activate")
    a.add_argument("--masechet", required=True)
    args = p.parse_args()

    path = log_path(args.log)
    if args.cmd == "path":
        print(path)
        return 0
    log = load(path)
    if args.cmd == "show":
        json.dump(log, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return 0
    if args.cmd == "summary":
        print(summary(log))
        return 0
    if args.cmd == "record":
        try:
            record(log, mode=args.mode, ref=args.ref, date=args.date, nxt=args.nxt,
                   masechet=args.masechet, unit=args.unit, seq_end=args.seq_end,
                   total=args.total, label=args.label, extras=args.extras, partial=args.partial)
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 2
    elif args.cmd == "reset":
        if not args.yes:
            scope = (f"ByMishnah progress for {args.masechet}" if args.masechet
                     else "the entire log" if args.track == "all" else f"the {args.track} track")
            print(f"Not reset. This would clear {scope}. Ask the learner to confirm, "
                  f"then rerun with --yes.\n\nCurrent state:\n{summary(log)}")
            return 6
        if args.track == "all":
            log = empty_log()
        elif args.track == "bymishnah" and args.masechet:
            log["tracks"]["bymishnah"].pop(args.masechet, None)
        elif args.track == "bymishnah":
            log["tracks"]["bymishnah"] = {}
        else:
            log["tracks"][args.track] = None
    elif args.cmd == "activate":
        log["active_bymishnah"] = args.masechet
        log["active_track"] = "bymishnah"
    save(path, log)
    print(summary(log))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
