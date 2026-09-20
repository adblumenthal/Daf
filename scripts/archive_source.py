#!/usr/bin/env python3
"""
Read Sefaria texts from Sefaria's public export archive on GitHub, pinned to one
commit. Works in sandboxes that block sefaria.org but allow GitHub (the default
in Claude and most agent hosts).

Examples:
  python scripts/archive_source.py "Chullin 23b"
  python scripts/archive_source.py "Rashi on Chullin 23b" --lang he
  python scripts/archive_source.py "Chullin 23a-24b" --lang en
  python scripts/archive_source.py "Mishnah Chullin 1:1-2"
  python scripts/archive_source.py "Mishneh Torah, Ritual Slaughter 4:1"
  python scripts/archive_source.py --commentaries Chullin     # what exists for a masechet

Texts are Sefaria's (see each version's license at sefaria.org); the export is
from March 2026.
"""

# Created by Adam Blumenthal in honor of David and Barbara Blumenthal,
# who always pushed him to keep asking questions.

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEX_FILE = HERE.parent / "data" / "archive_index.json"
CACHE = Path(os.environ.get("DAF_CACHE", "~/.cache/daf/archive")).expanduser()
TAG = re.compile(r"<[^>]+>")
_index = None


def index() -> dict:
    global _index
    if _index is None:
        _index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    return _index


def split_ref(ref: str) -> tuple[str, str]:
    """Split 'Rashi on Chullin 23b:4' into ('Rashi on Chullin', '23b:4') using the index."""
    ref = " ".join(ref.strip().replace("_", " ").split())
    titles = index()["titles"]
    best = None
    for t in titles:
        if (ref == t or ref.startswith(t + " ")) and (best is None or len(t) > len(best)):
            best = t
    if not best:
        low = ref.lower()
        for t in titles:
            if (low == t.lower() or low.startswith(t.lower() + " ")) and (best is None or len(t) > len(best)):
                best = t
    if not best:
        raise KeyError(f"'{ref}' is not in the archive index")
    return best, ref[len(best):].strip()


def fetch_book(title: str, lang: str):
    entry = index()["titles"][title]
    path = entry.get(lang)
    if not path:
        return None
    sha = index()["sha"]
    cache_file = CACHE / sha[:12] / (hashlib.sha1(path.encode()).hexdigest() + ".json")
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))
    url = index()["raw_base"] + urllib.parse.quote(path)
    req = urllib.request.Request(url, headers={"User-Agent": "daf/3.1 (+Agent Skills)"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


# Commentaries paginated by the Rif's pages (not the Gemara's) or by perek.
RIF_PAGED = re.compile(r"^(Ran|HaMaor|Milchemet|Milchamot|Nimukei Yosef|Shiltei|Chiddushei Anshei Shem|Rif)\b")
BY_PEREK = re.compile(r"^(Rosh|Tosafot HaRosh on Nedarim)\b")


def layout(title: str) -> str:
    """'gemara' (cite by Gemara amud), 'rif' (Rif pages), 'perek', or 'other'."""
    if RIF_PAGED.match(title):
        return "rif"
    if BY_PEREK.match(title):
        return "perek"
    return "gemara"


def _is_talmud_like(book: dict) -> bool:
    names = book.get("sectionNames") or []
    return bool(names) and names[0] == "Daf"


def _body(book: dict):
    """Unwrap complex texts (e.g. Meiri: {'Introduction': [...], '': [...]}) to the main node."""
    text = book["text"]
    if isinstance(text, dict):
        return text.get("", next(iter(text.values())))
    return text


def _amud_index(tok: str) -> int:
    m = re.fullmatch(r"(\d+)([ab])", tok)
    if not m:
        raise ValueError(f"bad daf '{tok}'")
    return (int(m.group(1)) - 1) * 2 + (0 if m.group(2) == "a" else 1)


def _amud_label(i: int) -> str:
    return f"{i // 2 + 1}{'ab'[i % 2]}"


def _parse_addr(tok: str, talmud: bool) -> list[int]:
    parts = tok.split(":")
    out = []
    for n, p in enumerate(parts):
        out.append(_amud_index(p) if (talmud and n == 0) else int(p) - 1)
    return out


def _flatten(node, prefix: list[str], out: list):
    if isinstance(node, list):
        for i, child in enumerate(node):
            _flatten(child, prefix + [str(i + 1)], out)
    elif isinstance(node, str) and node.strip():
        out.append((":".join(prefix), TAG.sub("", node).strip()))


def select(book: dict, section: str) -> list[tuple[str, str]]:
    """Return [(address, text)] for a section like '23b', '23a-24b', '23b:4', '1:1-3', '4'."""
    text = _body(book)
    talmud = _is_talmud_like(book) or book.get("_daf_layout", False)
    if not section:
        out: list = []
        for i, node in enumerate(text):
            _flatten(node, [_amud_label(i) if talmud else str(i + 1)], out)
        return out
    if talmud and re.fullmatch(r"\d+", section):
        section = f"{section}a-{section}b"
    elif talmud and re.fullmatch(r"\d+-\d+", section):
        a, b = section.split("-")
        section = f"{a}a-{b}b"
    start_tok, _, end_tok = section.partition("-")
    start = _parse_addr(start_tok, talmud)
    if end_tok:
        end_parts = end_tok.split(":")
        # A short end ('1:1-3', '23b:4-8') replaces only the trailing levels of the start.
        if talmud and not re.match(r"\d+[ab]", end_parts[0]):
            end = start[: len(start) - len(end_parts)] + [int(p) - 1 for p in end_parts]
        else:
            parsed = _parse_addr(end_tok, talmud)
            end = start[: len(start) - len(parsed)] + parsed
    else:
        end = list(start)
    out: list = []

    def walk(node, path):
        if isinstance(node, list):
            for i, child in enumerate(node):
                p = path + [i]
                k1, k2 = min(len(p), len(start)), min(len(p), len(end))
                if p[:k1] < start[:k1] or p[:k2] > end[:k2]:
                    continue
                walk(child, p)
        elif isinstance(node, str) and node.strip():
            label = [(_amud_label(x) if (talmud and n == 0) else str(x + 1)) for n, x in enumerate(path)]
            out.append((":".join(label), TAG.sub("", node).strip()))

    walk(text, [])
    return out


def get(ref: str, langs=("he", "en")) -> dict:
    title, section = split_ref(ref)
    result = {"requested_ref": ref, "title": title, "section": section,
              "source": "Sefaria export archive (GitHub, pinned commit)",
              "source_url": "https://www.sefaria.org/" + urllib.parse.quote(ref.replace(" ", "_"), safe="_:.,-'"),
              "segments": []}
    merged: dict[str, dict] = {}
    order: list[str] = []
    entry = index()["titles"][title]
    daf_layout = entry.get("group") in ("Rishonim on Talmud", "Acharonim on Talmud") and \
        layout(title) == "gemara"
    result["layout"] = layout(title) if " on " in title or title.startswith("Rif ") else "text"
    for lang in langs:
        book = fetch_book(title, lang)
        if not book:
            continue
        book["_daf_layout"] = daf_layout
        for addr, txt in select(book, section):
            if addr not in merged:
                merged[addr] = {"ref": f"{title} {addr}"}
                order.append(addr)
            merged[addr][lang] = txt
    result["segments"] = [merged[a] for a in order]
    if not result["segments"]:
        result["note"] = "No text found for this reference in the archive."
    return result


def commentaries(masechet: str) -> dict:
    """Commentaries on a Bavli masechet in the archive, grouped (Rishonim, Acharonim, ...)."""
    groups: dict[str, list] = {}
    suffix = f" on {masechet}"
    for title, entry in index()["titles"].items():
        if title.endswith(suffix) or title == f"Rif {masechet}":
            group = entry.get("group", "Other")
            if title.startswith("Rif "):
                group = "Rishonim on Talmud"
            groups.setdefault(group, []).append(title)
    return {k: sorted(v) for k, v in sorted(groups.items())}


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("ref", nargs="?")
    p.add_argument("--lang", choices=["he", "en", "both"], default="both")
    p.add_argument("--commentaries", metavar="MASECHET")
    args = p.parse_args()
    if args.commentaries:
        json.dump(commentaries(args.commentaries), sys.stdout, ensure_ascii=False, indent=2)
        print()
        return 0
    if not args.ref:
        p.error("ref required")
    langs = ("he", "en") if args.lang == "both" else (args.lang,)
    try:
        out = get(args.ref, langs)
    except KeyError as exc:
        print(str(exc).strip("'\""), file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Archive fetch failed: {exc}", file=sys.stderr)
        return 1
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
