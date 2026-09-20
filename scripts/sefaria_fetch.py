#!/usr/bin/env python3
"""
Fetch a Sefaria textual reference using the public v3 Texts API.

Examples:
  python sefaria_fetch.py "Chullin 118a"
  python sefaria_fetch.py "Rashi on Chullin 118a" --lang he
  python sefaria_fetch.py "Chullin 23a-24b" --lang en
  python sefaria_fetch.py "Chullin 118a" --live      # prefer the live Sefaria API

By default this reads Sefaria's public export archive on GitHub
(archive_source.py), which works where sefaria.org itself is blocked. With
--live it tries the Sefaria API first and falls back to the archive.
"""

# Created by Adam Blumenthal in honor of David and Barbara Blumenthal,
# who always pushed him to keep asking questions.

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request

BASE = "https://www.sefaria.org/api/v3/texts/"
PAGE_BASE = "https://www.sefaria.org/"


def build_urls(ref: str, version: str = "primary") -> tuple[str, str]:
    """Build API and human-readable URLs without changing the requested scope."""
    tref_api = urllib.parse.quote(ref, safe="")
    tref_page = urllib.parse.quote(ref.replace(" ", "_"), safe="_:.:-")
    query = urllib.parse.urlencode({
        "version": version,
        "fill_in_missing_segments": "1",
        "return_format": "text_only",
    })
    return BASE + tref_api + "?" + query, PAGE_BASE + tref_page

def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    p = argparse.ArgumentParser()
    p.add_argument("ref", help='Sefaria ref, e.g. "Chullin 118a"')
    p.add_argument("--version", default="primary", help='Sefaria version selector; default "primary"')
    p.add_argument("--lang", choices=["he", "en", "both"], default="both")
    p.add_argument("--live", action="store_true", help="Try the live Sefaria API first")
    args = p.parse_args()

    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent))
    import archive_source

    def from_archive() -> int:
        langs = ("he", "en") if args.lang == "both" else (args.lang,)
        try:
            out = archive_source.get(args.ref, langs)
        except KeyError:
            print(f"'{args.ref}' is not in the archive index. Check the spelling "
                  "(for example 'Rashi on Chullin 23b'), or try --live.", file=sys.stderr)
            return 2
        except Exception as exc:
            print(f"Archive fetch failed: {exc}", file=sys.stderr)
            return 1
        json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return 0

    if not args.live:
        return from_archive()

    url, source_url = build_urls(args.ref, args.version)

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "daf/3.1 (+Agent Skills)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.load(resp)
    except Exception as exc:
        deny = getattr(getattr(exc, "headers", None), "get", lambda _k: None)("x-deny-reason")
        print(f"Sefaria API unavailable ({deny or exc}); using the archive.", file=sys.stderr)
        return from_archive()

    out = {
        "requested_ref": args.ref,
        "source_url": source_url,
        "data": payload,
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
