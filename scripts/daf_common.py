#!/usr/bin/env python3
"""Shared zero-dependency helpers for the Daf skill scripts."""

# Created by Adam Blumenthal in honor of David and Barbara Blumenthal,
# who always pushed him to keep asking questions.

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "daf/3.0 (+Agent Skills)"
SEFARIA = "https://www.sefaria.org"

AMUD_RE = re.compile(r"^(?P<book>.+?)\s+(?P<daf>\d+)(?P<amud>[ab])?(?::(?P<seg>\d+))?$")


def utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


class NetworkBlocked(RuntimeError):
    """The sandbox's network allowlist refused the host."""


def get_json(url: str, timeout: int = 25):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        deny = exc.headers.get("x-deny-reason") if exc.headers else None
        if exc.code == 403 and deny:
            host = urllib.parse.urlparse(url).hostname
            raise NetworkBlocked(
                f"{host} is blocked by this environment's network allowlist ({deny}). "
                f"The user can add {host} to the allowed domains for code execution in their "
                f"settings; until then, use the host's web tool or continue without live data."
            ) from exc
        raise


# Bavli masechtot with Gemara (Vilna Shas; Shekalim there is Yerushalmi, so it is excluded).
BAVLI = [
    "Berakhot", "Shabbat", "Eruvin", "Pesachim", "Rosh Hashanah", "Yoma", "Sukkah", "Beitzah",
    "Taanit", "Megillah", "Moed Katan", "Chagigah", "Yevamot", "Ketubot", "Nedarim", "Nazir",
    "Sotah", "Gittin", "Kiddushin", "Bava Kamma", "Bava Metzia", "Bava Batra", "Sanhedrin",
    "Makkot", "Shevuot", "Avodah Zarah", "Horayot", "Zevachim", "Menachot", "Chullin",
    "Bekhorot", "Arakhin", "Temurah", "Keritot", "Meilah", "Tamid", "Niddah",
]
# Mishnah tractates with no Bavli Gemara.
MISHNAH_ONLY = [
    "Peah", "Demai", "Kilayim", "Sheviit", "Terumot", "Maasrot", "Maaser Sheni", "Challah",
    "Orlah", "Bikkurim", "Shekalim", "Eduyot", "Pirkei Avot", "Middot", "Kinnim", "Kelim",
    "Oholot", "Negaim", "Parah", "Tahorot", "Mikvaot", "Makhshirin", "Zavim", "Tevul Yom",
    "Yadayim", "Oktzim",
]
ALIASES = {
    "brachot": "Berakhot", "berachot": "Berakhot", "brachos": "Berakhot", "berachos": "Berakhot",
    "shabbos": "Shabbat", "eiruvin": "Eruvin", "pesachim": "Pesachim", "psachim": "Pesachim",
    "rosh hashana": "Rosh Hashanah", "succah": "Sukkah", "sukka": "Sukkah", "beitza": "Beitzah",
    "betzah": "Beitzah", "taanis": "Taanit", "megilla": "Megillah", "moed katan": "Moed Katan",
    "chagiga": "Chagigah", "yevamos": "Yevamot", "kesubos": "Ketubot", "ketubos": "Ketubot",
    "kesuvos": "Ketubot", "gitin": "Gittin", "kidushin": "Kiddushin", "bava basra": "Bava Batra",
    "bava kama": "Bava Kamma", "bava metziah": "Bava Metzia", "makkos": "Makkot", "makos": "Makkot",
    "shevuos": "Shevuot", "avoda zara": "Avodah Zarah", "avodah zara": "Avodah Zarah",
    "horayos": "Horayot", "zevachim": "Zevachim", "menachos": "Menachot", "chulin": "Chullin",
    "bechoros": "Bekhorot", "bechorot": "Bekhorot", "erchin": "Arakhin", "arachin": "Arakhin",
    "temura": "Temurah", "kerisus": "Keritot", "kerisos": "Keritot", "meila": "Meilah",
    "nida": "Niddah", "pea": "Peah", "kilaim": "Kilayim", "shviis": "Sheviit", "trumot": "Terumot",
    "maaseros": "Maasrot", "chala": "Challah", "orla": "Orlah", "bikurim": "Bikkurim",
    "shekolim": "Shekalim", "eduyos": "Eduyot", "avot": "Pirkei Avot", "avos": "Pirkei Avot",
    "midos": "Middot", "kinim": "Kinnim", "ohalot": "Oholot", "tohorot": "Tahorot",
    "mikvaos": "Mikvaot", "machshirin": "Makhshirin", "uktzin": "Oktzim", "yadaim": "Yadayim",
}


def normalize_masechet(name: str) -> tuple[str | None, str]:
    """Return (canonical name, kind) where kind is 'bavli', 'mishnah_only', or 'unknown'."""
    key = " ".join(name.strip().replace("_", " ").split()).lower()
    for canon in BAVLI:
        if canon.lower() == key:
            return canon, "bavli"
    for canon in MISHNAH_ONLY:
        if canon.lower() == key:
            return canon, "mishnah_only"
    canon = ALIASES.get(key)
    if canon:
        return canon, ("bavli" if canon in BAVLI else "mishnah_only")
    return None, "unknown"


def sefaria_url(path: str, ref: str, **params) -> str:
    quoted = urllib.parse.quote(ref.replace(" ", "_"), safe="_:.,-")
    query = ("?" + urllib.parse.urlencode(params)) if params else ""
    return f"{SEFARIA}/api/{path}/{quoted}{query}"


def page_url(ref: str) -> str:
    return SEFARIA + "/" + urllib.parse.quote(ref.replace(" ", "_"), safe="_:.,-")


def parse_amud_ref(ref: str):
    """Parse 'Chullin 23b' or 'Chullin 23b:4' into (book, daf, amud|None, seg|None)."""
    m = AMUD_RE.match(ref.strip())
    if not m:
        return None
    return (
        m.group("book"),
        int(m.group("daf")),
        m.group("amud"),
        int(m.group("seg")) if m.group("seg") else None,
    )


def amud_key(ref: str):
    """Sortable position of a Bavli ref start: (daf, amud 0/1, segment)."""
    start = ref.split("-")[0].strip()
    parsed = parse_amud_ref(start)
    if not parsed:
        return None
    _, daf, amud, seg = parsed
    return (daf, 0 if amud in (None, "a") else 1, seg or 0)


def expand_amudim(ref: str, cap: int = 40) -> list[str]:
    """Expand 'Chullin 23a-24b', 'Chullin 23-24', or 'Chullin 23' into amud refs."""
    ref = ref.strip()
    m = re.match(r"^(?P<book>.+?)\s+(?P<s>\d+)(?P<sa>[ab])?(?:-(?P<e>\d+)(?P<ea>[ab])?)?$", ref)
    if not m:
        return [ref]
    book = m.group("book")
    s, sa = int(m.group("s")), m.group("sa")
    e = int(m.group("e")) if m.group("e") else s
    ea = m.group("ea")
    if m.group("e") is None:
        ea = sa
    start = (s, 0 if sa in (None, "a") else 1)
    end = (e, 1 if ea in (None, "b") else 0)
    out = []
    daf, am = start
    while (daf, am) <= end and len(out) < cap:
        out.append(f"{book} {daf}{'ab'[am]}")
        daf, am = (daf, 1) if am == 0 else (daf + 1, 0)
    return out


def ref_book(ref: str) -> str:
    """Book portion of a ref: 'Mishneh Torah, Forbidden Foods 4:1' -> 'Mishneh Torah, Forbidden Foods'."""
    m = re.match(r"^(.*?)(?:\s+\d+[ab]?(?::\d+)*(?:-.*)?)?$", ref.strip())
    return (m.group(1) if m else ref).strip()
