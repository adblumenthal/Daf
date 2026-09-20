#!/usr/bin/env python3
"""
Maintainer tool: rebuild the Daf skill's bundled data from Sefaria's public
export archive on GitHub (Sefaria/Sefaria-Export-Archive, pinned commit).

Not needed at runtime. Run from a machine with git and network access:

  python tools/build_data.py --workdir /tmp/daf-build

Outputs (under data/):
  archive_index.json   title -> {language: path} for Bavli, Mishnah, and their commentaries
  mishnah_maps.json    ByMishnah units for every Bavli masechet
  links/<Masechet>.json  per-amud halacha (Ein Mishpat) and parallel (Mesorat HaShas) refs

Sefaria texts are available under their respective licenses (mostly CC-BY / CC-BY-SA /
public domain); see https://www.sefaria.org/terms and each version's license.
"""

# Created by Adam Blumenthal in honor of David and Barbara Blumenthal,
# who always pushed him to keep asking questions.

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from daf_common import BAVLI  # noqa: E402
from mishnah_map import build_units  # noqa: E402

REPO = "https://github.com/Sefaria/Sefaria-Export-Archive.git"
SHA = "3f1013631fdfe452e953a93a2c5f921319e394ed"  # last commit with texts in git (2026-03-23 export)
RAW = f"https://raw.githubusercontent.com/Sefaria/Sefaria-Export-Archive/{SHA}/"
KEEP = re.compile(r"^json/(Talmud/Bavli|Talmud/Yerushalmi|Mishnah|Tosefta|Halakhah)/")
# Under Halakhah, keep primary works and these classic commentaries only.
HALAKHAH_COMMENTARY = re.compile(
    r"/(Hasagot HaRa'avad|Kesef Mishneh|Maggid Mishneh|Lechem Mishneh|Beit Yosef|Darkhei Moshe|"
    r"Mishnah Berurah|Magen Avraham|Taz|Turei Zahav|Siftei Kohen|Shakh|Be'er Hetev|Ba'er Hetev|"
    r"Beur HaGra|Bi'ur Halakhah)/")


def sh(*args, cwd=None, out=None):
    return subprocess.run(args, cwd=cwd, check=True, stdout=out or subprocess.PIPE, text=out is None)


def raw_json(path: str):
    url = RAW + urllib.parse.quote(path)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "daf-build"}), timeout=60) as r:
        return json.load(r)


def build_index(repo: Path) -> dict:
    listing = sh("git", "ls-tree", "-r", "--name-only", SHA, "--", "json/Talmud/Bavli",
                 "json/Talmud/Yerushalmi", "json/Mishnah", "json/Tosefta", "json/Halakhah",
                 cwd=repo).stdout.splitlines()
    index: dict[str, dict] = {}
    for p in listing:
        if not p.endswith("/merged.json") or not KEEP.match(p):
            continue
        if p.startswith("json/Halakhah/") and "/Commentary/" in p and not HALAKHAH_COMMENTARY.search(p):
            continue
        parts = p.split("/")
        title, lang = parts[-3], parts[-2]
        group = parts[3] if parts[1] == "Talmud" else parts[2]
        if parts[1] == "Halakhah":
            group = "Halakhah"
        entry = index.setdefault(title, {"group": group})
        entry[{"Hebrew": "he", "English": "en"}.get(lang, lang)] = p
    return index


def extract_links(repo: Path, workdir: Path) -> dict:
    bav = set(BAVLI)
    out = {"mishnah": [], "halacha": [], "parallel": []}
    names = [n for n in sh("git", "ls-tree", "--name-only", f"{SHA}:links", cwd=repo).stdout.split()
             if re.fullmatch(r"links\d+\.csv", n)]
    for name in names:
        tmp = workdir / name
        with open(tmp, "wb") as fh:
            subprocess.run(["git", "cat-file", "-p", f"{SHA}:links/{name}"], cwd=repo, check=True, stdout=fh)
        with open(tmp, encoding="utf-8", newline="") as fh:
            rows = csv.reader(fh)
            next(rows)
            for row in rows:
                if len(row) < 7:
                    continue
                c1, c2, kind, x1, x2, k1, k2 = row[:7]
                for a, b, xa, xb, kb in ((c1, c2, x1, x2, k2), (c2, c1, x2, x1, k1)):
                    if xa not in bav:
                        continue
                    if kind == "mishnah in talmud" and xb.startswith("Mishnah "):
                        out["mishnah"].append([a, b])
                    elif kind.startswith("ein mishpat") and kb == "Halakhah":
                        out["halacha"].append([a, b])
                    elif kind == "mesorat hashas" and (xb in bav or xb.startswith("Jerusalem Talmud")
                                                       or kb == "Tosefta"):
                        out["parallel"].append([a, b])
        tmp.unlink()
        print("  processed", name, file=sys.stderr)
    return out


def amud_of(ref: str):
    m = re.match(r"^(.+?) (\d+[ab])", ref)
    return (m.group(1), m.group(2)) if m else (None, None)


def build_maps(index: dict, links: dict) -> dict:
    starts: dict[str, dict] = defaultdict(dict)
    for bavli_ref, mishnah_ref in links["mishnah"]:
        book, _ = amud_of(bavli_ref)
        m = re.match(r"^Mishnah (.+?) (\d+):(\d+)(?:-(?:(\d+):)?(\d+))?$", mishnah_ref)
        if not book or not m or _norm(m.group(1)) != _norm(book):
            continue
        p, a = int(m.group(2)), int(m.group(3))
        b = int(m.group(5)) if m.group(5) and not m.group(4) else a
        for mi in range(a, b + 1):
            label = f"{p}:{mi}"
            prev = starts[book].get(label)
            if prev is None or _key(bavli_ref) < _key(prev):
                starts[book][label] = bavli_ref
    maps = {}
    for book in BAVLI:
        mtitle = next((t for t in index if _norm(t) == _norm(f"Mishnah {book}")), None)
        mishnah = index.get(mtitle, {}).get("he") if mtitle else None
        bavli = index.get(book, {}).get("he")
        if not mishnah or not bavli:
            print("  skip (missing text)", book, file=sys.stderr)
            continue
        chapters = [len(c) for c in raw_json(mishnah)["text"]]
        text = raw_json(bavli)["text"]
        last = max(i for i, amud in enumerate(text) if amud)
        bavli_last = f"{book} {last // 2 + 1}{'ab'[last % 2]}"
        result = build_units(book, chapters, starts.get(book, {}), bavli_last)
        result["attribution"] = "Mishnah counts and Bavli links: Sefaria.org (export archive)"
        maps[book] = result
        print(f"  {book}: {result['total_mishnayot']} mishnayot, {result['total_units']} units, "
              f"{len(result['mishnah_only_units'])} mishnah-only", file=sys.stderr)
    return maps


def _norm(name: str) -> str:
    return name.replace("'", "").lower()


def _key(ref: str):
    from daf_common import amud_key
    return amud_key(ref) or (9999, 0, 0)


def build_link_files(links: dict, dest: Path) -> None:
    per: dict[str, dict] = defaultdict(lambda: defaultdict(lambda: {"h": [], "p": []}))
    for kind, key in (("halacha", "h"), ("parallel", "p")):
        for bavli_ref, other in links[kind]:
            book, amud = amud_of(bavli_ref)
            if not book:
                continue
            bucket = per[book][amud][key]
            if other not in bucket:
                bucket.append(other)
    dest.mkdir(parents=True, exist_ok=True)
    for book, amudim in per.items():
        (dest / f"{book.replace(' ', '_')}.json").write_text(
            json.dumps(amudim, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--workdir", default="/tmp/daf-build")
    args = p.parse_args()
    work = Path(args.workdir)
    work.mkdir(parents=True, exist_ok=True)
    repo = work / "archive"
    if not repo.exists():
        sh("git", "clone", "-q", "--filter=tree:0", "--no-checkout", REPO, str(repo))
    data = ROOT / "data"
    data.mkdir(exist_ok=True)
    print("index...", file=sys.stderr)
    index = build_index(repo)
    (data / "archive_index.json").write_text(json.dumps(
        {"sha": SHA, "raw_base": RAW, "titles": index}, ensure_ascii=False, indent=0), encoding="utf-8")
    print("links...", file=sys.stderr)
    links = extract_links(repo, work)
    print("maps...", file=sys.stderr)
    maps = build_maps(index, links)
    (data / "mishnah_maps.json").write_text(json.dumps(
        {"sha": SHA, "maps": maps}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    build_link_files(links, data / "links")
    print("done", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
