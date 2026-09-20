#!/usr/bin/env python3
"""
Build a ByMishnah learning map for a Bavli masechet: every Mishnah, in the
order it appears in the Bavli, with the Gemara span that belongs to it.

Examples:
  python scripts/mishnah_map.py Chullin
  python scripts/mishnah_map.py "Bava Metzia" --unit 13
  python scripts/mishnah_map.py Chullin --find 3:2
  python scripts/mishnah_map.py Chullin --cache ~/.daf/maps
  python scripts/mishnah_map.py Chullin --offline saved.json
  python scripts/mishnah_map.py Chullin --live              # rebuild from the live Sefaria API

By default the map comes from data/mishnah_maps.json, prebuilt for all 37 Bavli
masechtot from Sefaria's export archive (tools/build_data.py), so no network is needed.

Exit codes: 1 lookup failed, 2 unknown masechet or unit, 3 no Bavli Gemara,
5 network blocked by the sandbox allowlist.

Data: Sefaria Shape API (mishnayot per perek) and Links API
("mishnah in talmud" links from each Mishnah to the Bavli).

Offline JSON format:
  {"chapters": [7, 10, ...], "links": {"1:1": ["Chullin 2a:1"], ...},
   "bavli_last": "Chullin 142a"}
"""

# Created by Adam Blumenthal in honor of David and Barbara Blumenthal,
# who always pushed him to keep asking questions.

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from daf_common import (  # noqa: E402
    NetworkBlocked, amud_key, get_json, normalize_masechet, page_url, sefaria_url, utf8_stdio,
)


# ---------- pure logic (unit-tested) ----------

def ordinal_table(chapters: list[int]) -> dict[str, int]:
    table, n = {}, 0
    for c, count in enumerate(chapters, start=1):
        for m in range(1, count + 1):
            n += 1
            table[f"{c}:{m}"] = n
    return table


def _fmt_amud(key) -> str:
    daf, am, _ = key
    return f"{daf}{'ab'[am]}"


def _prev_amud(key):
    daf, am, _ = key
    return (daf, 0, 0) if am == 1 else (daf - 1, 1, 0)


def range_end_key(ref: str):
    """End position of a Bavli ref or range: 'X 2a:1-3' -> (2,0,3); 'X 2a:5-2b:2' -> (2,1,2)."""
    start = amud_key(ref)
    if not start or "-" not in ref:
        return start
    tail = ref.split("-", 1)[1].strip()
    m = re.match(r"^(?:.*\s)?(\d+)([ab]):(\d+)$", tail)
    if m:
        return (int(m.group(1)), 0 if m.group(2) == "a" else 1, int(m.group(3)))
    if tail.isdigit():
        return (start[0], start[1], int(tail))
    return start


def build_units(masechet: str, chapters: list[int], starts: dict[str, str],
                bavli_last: str | None = None) -> dict:
    """
    chapters: mishnayot per perek (Mishnah numbering).
    starts:   "perek:mishnah" -> Bavli start ref, e.g. "Chullin 2a:1".
    Returns units in Bavli order, merging mishnayot that share a Gemara section.
    """
    order = ordinal_table(chapters)
    total = len(order)
    mapped = []
    for label, ref in starts.items():
        key = amud_key(ref)
        if key and label in order:
            mapped.append((key, order[label], label, ref.split("-")[0].strip(), range_end_key(ref)))
    mapped.sort()

    # Merge mishnayot whose Gemara section is empty (same or adjacent segment start).
    units: list[dict] = []
    for key, ordn, label, ref, end in mapped:
        if units:
            last = units[-1]
            le = last["_end"]
            adjacent = (le[:2] == key[:2] and le[2] > 0 and key[2] > 0 and key[2] - le[2] <= 1)
            if key <= le or adjacent:
                last["mishnayot"].append(label)
                last["_end"] = max(le, end)
                continue
        units.append({"mishnayot": [label], "bavli_start": ref, "_key": key, "_end": end})

    # Gemara spans: each unit runs until the next unit begins.
    last_key = None
    if bavli_last:
        lk = amud_key(bavli_last)
        last_key = (lk[0], lk[1], 0) if lk else None
    for i, u in enumerate(units):
        k = u["_key"]
        nxt = units[i + 1]["_key"] if i + 1 < len(units) else None
        if nxt:
            if nxt[2] > 1:
                end_amud, stop = nxt, f"{masechet} {_fmt_amud(nxt)}:{nxt[2] - 1}"
            else:
                end_amud = _prev_amud(nxt) if nxt[:2] != k[:2] else nxt
                stop = f"end of {masechet} {_fmt_amud(end_amud)}"
            u["next_mishnah_starts"] = units[i + 1]["bavli_start"]
        else:
            end_amud = last_key or k
            stop = f"end of {masechet}"
            u["next_mishnah_starts"] = None
        s, e = _fmt_amud(k), _fmt_amud(end_amud)
        u["fetch_ref"] = f"{masechet} {s}" if s == e else f"{masechet} {s}-{e}"
        u["gemara_span"] = f"{u['bavli_start']} through {stop}"
        u["amudim"] = (end_amud[0] * 2 + end_amud[1]) - (k[0] * 2 + k[1]) + 1
        u["sefaria_link"] = page_url(u["fetch_ref"])

    # Mishnayot with no Bavli link (no Gemara on that perek, or missing data):
    # place each right after the unit holding its predecessor in Mishnah order.
    placed = {lbl for u in units for lbl in u["mishnayot"]}
    unmapped = [lbl for lbl in order if lbl not in placed]
    for lbl in unmapped:
        prev_ord = order[lbl] - 1
        idx = 0
        for j, u in enumerate(units):
            if any(order[m] == prev_ord for m in u["mishnayot"]):
                idx = j + 1
                break
        else:
            idx = next((j for j, u in enumerate(units)
                        if min(order[m] for m in u["mishnayot"]) > order[lbl]), len(units))
        units.insert(idx, {"mishnayot": [lbl], "bavli_start": None, "fetch_ref": None,
                           "gemara_span": None, "amudim": 0, "mishnah_only": True,
                           "_key": None, "_end": None})

    seq = 0
    for n, u in enumerate(units, start=1):
        u.pop("_key", None)
        u.pop("_end", None)
        u["unit"] = n
        u["seq_start"] = seq + 1
        seq += len(u["mishnayot"])
        u["seq_end"] = seq
        first, last = u["mishnayot"][0], u["mishnayot"][-1]
        p1, m1 = first.split(":")
        u["label"] = (f"Perek {p1}, Mishnah {m1}" if first == last
                      else f"Perek {p1}, Mishnayot {m1}-{last.split(':')[1]}"
                      if last.split(":")[0] == p1 else f"Mishnayot {first}-{last}")
        u["mishnah_ref"] = f"Mishnah {masechet} {first}" + ("" if first == last else f"-{last}")
        u["position"] = (f"Mishnah {u['seq_start']} of {total}" if u["seq_start"] == u["seq_end"]
                         else f"Mishnayot {u['seq_start']}-{u['seq_end']} of {total}")
        u.setdefault("mishnah_only", False)

    annotate_perakim(masechet, units)
    bavli_order_differs = [u["mishnayot"][0] for u in units if not u["mishnah_only"]] != \
        sorted([u["mishnayot"][0] for u in units if not u["mishnah_only"]], key=lambda x: order[x])
    return {
        "masechet": masechet,
        "total_mishnayot": total,
        "perakim": len(chapters),
        "mishnayot_per_perek": chapters,
        "total_units": len(units),
        "bavli_order_differs_from_mishnah_order": bavli_order_differs,
        "mishnah_only_units": [u["mishnayot"][0] for u in units if u["mishnah_only"]],
        "units": units,
    }


def annotate_perakim(masechet: str, units: list[dict]) -> None:
    """Give each unit its perek's position in the Bavli and a note when that differs."""
    order: dict[int, int] = {}
    for u in units:
        perek = int(u["mishnayot"][0].split(":")[0])
        if perek not in order:
            order[perek] = len(order) + 1
    for u in units:
        perek = int(u["mishnayot"][0].split(":")[0])
        u["bavli_perek"] = order[perek]
        u["perek_note"] = (f"The Bavli prints this as Perek {order[perek]} of {masechet}; standard "
                           f"Mishnah numbering calls it Perek {perek}." if order[perek] != perek else None)


def find_unit(result: dict, label: str | None = None, unit: int | None = None):
    for u in result["units"]:
        if unit is not None and u["unit"] == unit:
            return u
        if label and label in u["mishnayot"]:
            return u
    return None


# ---------- Sefaria retrieval ----------

def _chapters_from_shape(payload) -> list[int] | None:
    items = payload if isinstance(payload, list) else [payload]
    for item in items:
        if isinstance(item, dict) and isinstance(item.get("chapters"), list):
            return [c if isinstance(c, int) else len(c) for c in item["chapters"]]
    return None


def fetch_chapters(masechet: str) -> list[int]:
    shape = get_json(sefaria_url("shape", f"Mishnah {masechet}"))
    chapters = _chapters_from_shape(shape)
    if chapters:
        return chapters
    raise RuntimeError("Could not read mishnah counts from Sefaria shape API")


def fetch_bavli_last(masechet: str) -> str | None:
    try:
        shape = get_json(sefaria_url("shape", masechet))
        amudim = _chapters_from_shape(shape)
        if amudim:
            i = len(amudim) - 1  # index 0 is 1a
            return f"{masechet} {i // 2 + 1}{'ab'[i % 2]}"
    except Exception:
        pass
    return None


def fetch_starts(masechet: str, chapters: list[int]) -> tuple[dict[str, str], list[str]]:
    starts: dict[str, str] = {}
    errors: list[str] = []
    bavli = re.compile(rf"^{re.escape(masechet)} \d+[ab]", re.I)
    for c in range(1, len(chapters) + 1):
        try:
            links = get_json(sefaria_url("links", f"Mishnah {masechet} {c}", with_text="0"))
        except Exception as exc:
            errors.append(f"perek {c}: {exc}")
            continue
        best: dict[str, tuple] = {}
        for link in links if isinstance(links, list) else []:
            ref = link.get("ref", "")
            if link.get("category") != "Talmud" or not bavli.match(ref):
                continue
            anchor = (link.get("anchorRef") or "").replace(f"Mishnah {masechet} ", "")
            m = re.match(r"^(\d+):(\d+)(?:-(?:(\d+):)?(\d+))?$", anchor)
            if not m:
                continue
            p, a = int(m.group(1)), int(m.group(2))
            b = int(m.group(4)) if m.group(4) else a
            primary = "mishnah in talmud" in (link.get("type") or "").lower()
            for mi in range(a, b + 1):
                label = f"{p}:{mi}"
                cand = (0 if primary else 1, amud_key(ref) or (9999, 0, 0), ref)
                if label not in best or cand < best[label]:
                    best[label] = cand
        for label, (_, _, ref) in best.items():
            starts[label] = ref
    return starts, errors


def main() -> int:
    utf8_stdio()
    p = argparse.ArgumentParser()
    p.add_argument("masechet")
    p.add_argument("--unit", type=int, help="Return only this learning unit (1-based)")
    p.add_argument("--find", help='Return the unit containing a Mishnah, e.g. "3:2"')
    p.add_argument("--cache", help="Directory to cache the finished map")
    p.add_argument("--offline", help="Build from a saved JSON file instead of fetching")
    p.add_argument("--live", action="store_true", help="Rebuild from the live Sefaria API")
    args = p.parse_args()
    canon, kind = normalize_masechet(args.masechet)
    if kind == "unknown" and not args.offline:
        print(f"'{args.masechet}' is not a recognized masechet. Ask the learner which masechet "
              f"they mean; do not guess.", file=sys.stderr)
        return 2
    if kind == "mishnah_only":
        print(f"{canon} has no Bavli Gemara, so ByMishnah (Mishnah plus Gemara) does not apply. "
              f"Offer Mishnah-only study of {canon} or another masechet.", file=sys.stderr)
        return 3
    masechet = canon or args.masechet.strip()

    cache_file = None
    if args.cache:
        cache_dir = Path(args.cache).expanduser()
        cache_file = cache_dir / f"{masechet.replace(' ', '_')}.json"

    bundled = Path(__file__).resolve().parents[1] / "data" / "mishnah_maps.json"
    if not args.live and not args.offline and bundled.exists() and \
            masechet in json.loads(bundled.read_text(encoding="utf-8"))["maps"]:
        result = json.loads(bundled.read_text(encoding="utf-8"))["maps"][masechet]
        result.setdefault("lookup_errors", [])
        if result["units"] and "bavli_perek" not in result["units"][0]:
            annotate_perakim(masechet, result["units"])
    elif cache_file and cache_file.exists() and not args.offline:
        result = json.loads(cache_file.read_text(encoding="utf-8"))
    else:
        errors: list[str] = []
        if args.offline:
            data = json.loads(Path(args.offline).read_text(encoding="utf-8"))
            chapters, starts, bavli_last = data["chapters"], data["links"], data.get("bavli_last")
        else:
            try:
                chapters = fetch_chapters(masechet)
            except NetworkBlocked as exc:
                print(str(exc), file=sys.stderr)
                return 5
            except Exception as exc:
                print(f"Sefaria lookup failed for Mishnah {masechet}: {exc}", file=sys.stderr)
                return 1
            starts, errors = fetch_starts(masechet, chapters)
            bavli_last = fetch_bavli_last(masechet)
        if not starts:
            print(f"No Bavli Gemara found for {masechet}. ByMishnah needs a Bavli masechet "
                  f"(or the lookup failed: {errors})", file=sys.stderr)
            return 3
        result = build_units(masechet, chapters, starts, bavli_last)
        result["lookup_errors"] = errors
        result["attribution"] = "Mishnah counts and Bavli links: Sefaria.org"
        if cache_file and not errors:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")

    if args.unit or args.find:
        unit = find_unit(result, label=args.find, unit=args.unit)
        if not unit:
            print("No such unit or mishnah in this masechet", file=sys.stderr)
            return 2
        nxt = find_unit(result, unit=unit["unit"] + 1)
        out = {k: result.get(k) for k in ("masechet", "total_mishnayot", "total_units", "perakim",
                                            "bavli_order_differs_from_mishnah_order")}
        out.update({"unit": unit, "next_unit": nxt})
        json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    else:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
