#!/usr/bin/env python3
"""
List the Rishonim, halachic sources, or parallel sugyot that Sefaria links
to a Gemara reference. Uses Sefaria's public Links API; no key required.

Examples:
  python scripts/sefaria_links.py "Chullin 23b" --kind rishonim
  python scripts/sefaria_links.py "Chullin 23a-24b" --kind halacha
  python scripts/sefaria_links.py "Chullin 23b" --kind parallels
  python scripts/sefaria_links.py "Chullin 23b" --kind all
  python scripts/sefaria_links.py "Chullin 23b" --kind rishonim --links-json saved.json
  python scripts/sefaria_links.py "Chullin 23b" --live        # prefer the live Links API

By default this works offline: Rishonim come from the Sefaria export archive on
GitHub (checked for content on the requested amudim), and halacha and parallel
refs come from the bundled per-amud index in data/links/.

The output is a map of what exists, grouped by work, with refs to fetch next
with sefaria_fetch.py. It never returns commentary text itself.
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
    NetworkBlocked, expand_amudim, get_json, page_url, parse_amud_ref, ref_book, sefaria_url, utf8_stdio,
)

# Display name -> pattern matched against collectiveTitle / index_title.
RISHONIM = [
    ("Rif", r"\brif\b"),
    ("Rosh", r"(?<!tosafot ha)\brosh\b"),
    ("Tosafot HaRosh", r"tosafot harosh"),
    ("Ran", r"\bran\b"),
    ("Ramban", r"\bramban\b"),
    ("Milchamot HaShem", r"milch[ae]m[oe]t"),
    ("Baal HaMaor", r"maor hagadol|maor hakatan|ba'?al hamaor"),
    ("Rashba", r"\brashba\b"),
    ("Ritva", r"\britva\b"),
    ("Meiri", r"\bmeiri\b|beit habechirah"),
    ("Tosafot Rid", r"tosafot rid"),
    ("Tosafot Yeshanim", r"tosafot yeshanim"),
    ("Rabbeinu Chananel", r"rabbeinu chananel"),
    ("Rabbeinu Gershom", r"rabbeinu gershom"),
    ("Rashbam", r"\brashbam\b"),
    ("Rabbeinu Yonah", r"rabbeinu yonah"),
    ("Nimukei Yosef", r"nimukei yosef"),
    ("Mordechai", r"\bmordechai\b"),
    ("Yad Ramah", r"yad ramah"),
    ("Raavad", r"\bra'?avad\b"),
    ("Ri Migash", r"ri migash"),
    ("Shita Mekubetzet (compiles Rishonim)", r"shita mekubetzet"),
]
NOT_RISHONIM = re.compile(r"maharsha|maharam|rashash|akiva eiger|gilyon|pnei yehoshua|korban netanel|"
                          r"pilpula|maadanei|chokhmat manoach|hagahot|steinsaltz|mesorat|ein mishpat|"
                          r"anshei shem|shiltei|piskei tosafot", re.I)
HALACHA_WORKS = [
    ("Rambam, Mishneh Torah", r"^mishneh torah"),
    ("Shulchan Arukh", r"^shulchan arukh"),
    ("Tur", r"^tur\b|^arbaah turim"),
    ("Mishnah Berurah", r"^mishnah berurah"),
    ("Sefer HaChinukh", r"chinukh"),
]
TALMUD_BOOK = re.compile(r"^(jerusalem talmud\s+)?[A-Z][\w' ]+ \d+[ab]", re.I)


def _title(link: dict) -> str:
    ct = link.get("collectiveTitle")
    if isinstance(ct, dict) and ct.get("en"):
        return ct["en"]
    return link.get("index_title") or ref_book(link.get("ref", ""))


def _comp_year(link: dict):
    cd = link.get("compDate")
    if isinstance(cd, list) and cd:
        cd = cd[0]
    try:
        return int(cd)
    except (TypeError, ValueError):
        return None


def classify_rishon(link: dict):
    title = _title(link) + " | " + (link.get("index_title") or "")
    low = title.lower()
    if NOT_RISHONIM.search(low):
        return None
    if re.match(r"^(rashi|tosafot)( on|$| \|)", low):
        return None  # already covered by the core lesson
    year = _comp_year(link)
    if year and year > 1560:
        return None
    for name, pat in RISHONIM:
        if re.search(pat, low):
            return name
    return None


def classify_halacha(link: dict):
    if link.get("category") not in ("Halakhah", "Halacha"):
        return None
    ref = link.get("ref", "")
    for name, pat in HALACHA_WORKS:
        if re.search(pat, ref, re.I):
            return name
    if classify_rishon(link):
        return None
    return "Other halachic sources"


def classify_parallel(link: dict, source_book: str, source_amudim: set[str]):
    cat = link.get("category")
    ref = link.get("ref", "")
    if cat == "Tosefta":
        return "Tosefta"
    if cat != "Talmud" or not TALMUD_BOOK.match(ref):
        return None
    parsed = parse_amud_ref(ref.split("-")[0])
    if parsed:
        book, daf, amud, _ = parsed
        if book == source_book and f"{book} {daf}{amud or ''}" in source_amudim:
            return None
    if ref.lower().startswith("jerusalem talmud"):
        return "Yerushalmi"
    return "Bavli"


def group_links(links: list[dict], kind: str, source_ref: str, per_group: int = 12) -> dict:
    amudim = expand_amudim(source_ref)
    source_book = parse_amud_ref(amudim[0])[0] if parse_amud_ref(amudim[0]) else ""
    source_set = set(amudim)
    kinds = ["rishonim", "halacha", "parallels"] if kind == "all" else [kind]
    result = {}
    for k in kinds:
        groups: dict[str, dict] = {}
        for link in links:
            if k == "rishonim":
                name = classify_rishon(link)
            elif k == "halacha":
                name = classify_halacha(link)
            else:
                name = classify_parallel(link, source_book, source_set)
            if not name:
                continue
            g = groups.setdefault(name, {"work": name, "refs": [], "anchors": []})
            ref = link.get("ref")
            if ref and ref not in g["refs"] and len(g["refs"]) < per_group:
                g["refs"].append(ref)
                g["anchors"].append(link.get("anchorRef"))
        ordered = sorted(groups.values(), key=lambda g: (-len(g["refs"]), g["work"]))
        for g in ordered:
            g["links"] = [page_url(r) for r in g["refs"]]
        result[k] = ordered
    return result


DATA = Path(__file__).resolve().parents[1] / "data" / "links"


def offline_groups(ref: str, kind: str, per_group: int = 12) -> dict:
    """Same shape as group_links, built from the archive and bundled link index."""
    import archive_source
    amudim = expand_amudim(ref)
    parsed = parse_amud_ref(amudim[0])
    book = parsed[0] if parsed else ref
    kinds = ["rishonim", "halacha", "parallels"] if kind == "all" else [kind]
    result = {}
    if "rishonim" in kinds:
        groups, other_layout = [], []
        titles = archive_source.commentaries(book).get("Rishonim on Talmud", [])
        for title in titles:
            short = title.rsplit(" on ", 1)[0] if " on " in title else title.split(" ")[0]
            name = classify_rishon({"collectiveTitle": {"en": short}, "index_title": title})
            if not name:
                continue
            lay = archive_source.layout(title)
            if lay != "gemara":
                note = ("paginated by the Rif's pages, not the Gemara's; locate the sugya by content"
                        if lay == "rif" else "organized by perek and siman; fetch the perek")
                entry = {"work": name, "title": title, "layout": lay, "note": note}
                if lay == "perek":
                    perek = _perek_of(book, amudim[0])
                    if perek:
                        entry["refs"] = [f"{title} {perek}"]
                other_layout.append(entry)
                continue
            refs = []
            for a in amudim:
                try:
                    segs = archive_source.get(f"{title} {a[len(book) + 1:]}", ("he",))["segments"]
                except Exception:
                    segs = []
                if segs:
                    refs.append(f"{title} {a[len(book) + 1:]}")
            if refs:
                groups.append({"work": name, "title": title, "refs": refs[:per_group],
                               "links": [page_url(r) for r in refs[:per_group]]})
        result["rishonim"] = sorted(groups, key=lambda g: g["work"])
        result["rishonim_other_layout"] = sorted(other_layout, key=lambda g: g["work"])
    for k, key in (("halacha", "h"), ("parallels", "p")):
        if k not in kinds:
            continue
        f = DATA / f"{book.replace(' ', '_')}.json"
        per_amud = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        links = []
        for a in amudim:
            for other in per_amud.get(a[len(book) + 1:], {}).get(key, []):
                cat = "Halakhah" if key == "h" else (
                    "Tosefta" if other.startswith("Tosefta") else "Talmud")
                links.append({"ref": other, "category": cat, "anchorRef": a})
        result[k] = group_links(links, k, ref, per_group)[k]
    return result


def _perek_of(book: str, amud: str):
    """Perek number containing an amud, from the bundled ByMishnah map."""
    maps_file = Path(__file__).resolve().parents[1] / "data" / "mishnah_maps.json"
    try:
        from daf_common import amud_key
        units = json.loads(maps_file.read_text(encoding="utf-8"))["maps"][book]["units"]
        target = amud_key(amud)
        perek = None
        for u in units:
            if u.get("bavli_start") and amud_key(u["bavli_start"])[:2] <= target[:2]:
                perek = int(u["mishnayot"][0].split(":")[0])
        return perek
    except Exception:
        return None


def fetch_links(ref: str) -> tuple[list[dict], list[str]]:
    links, errors = [], []
    for amud in expand_amudim(ref):
        try:
            payload = get_json(sefaria_url("links", amud, with_text="0"))
        except NetworkBlocked as exc:
            errors.append(str(exc))
            break
        except Exception as exc:  # network or HTTP failure
            errors.append(f"{amud}: {exc}")
            continue
        if isinstance(payload, list):
            links.extend(payload)
        else:
            errors.append(f"{amud}: unexpected payload")
    return links, errors


def main() -> int:
    utf8_stdio()
    p = argparse.ArgumentParser()
    p.add_argument("ref", help='Gemara ref, e.g. "Chullin 23b" or "Chullin 23a-24b"')
    p.add_argument("--kind", choices=["rishonim", "halacha", "parallels", "all"], default="all")
    p.add_argument("--per-group", type=int, default=12)
    p.add_argument("--links-json", help="Use a saved Links API payload (list) instead of fetching")
    p.add_argument("--live", action="store_true", help="Try the live Sefaria Links API first")
    args = p.parse_args()

    errors: list[str] = []
    groups = None
    if args.links_json:
        links = json.loads(Path(args.links_json).read_text(encoding="utf-8"))
        groups = group_links(links, args.kind, args.ref, args.per_group)
    elif args.live:
        links, errors = fetch_links(args.ref)
        if links:
            groups = group_links(links, args.kind, args.ref, args.per_group)
    if groups is None:
        groups = offline_groups(args.ref, args.kind, args.per_group)

    out = {
        "requested_ref": args.ref,
        "amudim": expand_amudim(args.ref),
        "groups": groups,
        "errors": errors,
        "note": "Availability varies by masechet. Fetch a ref's text before discussing it.",
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
