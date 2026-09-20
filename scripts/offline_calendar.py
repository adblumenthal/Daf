#!/usr/bin/env python3
"""
Offline Daf Yomi and Jewish-calendar context. No network required.

Daf Yomi: a Python port of Hebcal's public-domain algorithm (@hebcal/learning
dafYomiBase, itself a port of Bob Newell's daf.el), verified day by day against
@hebcal/learning. Hebrew dates and holidays: the vendored pyluach library (MIT).

Examples:
  python scripts/offline_calendar.py --date 2026-09-20
  python scripts/offline_calendar.py --date 2026-08-15 --through 2026-08-30
"""

# Created by Adam Blumenthal in honor of David and Barbara Blumenthal,
# who always pushed him to keep asking questions.

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))
from pyluach import dates as hdates, parshios  # noqa: E402

# (Hebcal name, last daf) in Daf Yomi order.
SHAS = [
    ("Berachot", 64), ("Shabbat", 157), ("Eruvin", 105), ("Pesachim", 121), ("Shekalim", 22),
    ("Yoma", 88), ("Sukkah", 56), ("Beitzah", 40), ("Rosh Hashana", 35), ("Taanit", 31),
    ("Megillah", 32), ("Moed Katan", 29), ("Chagigah", 27), ("Yevamot", 122), ("Ketubot", 112),
    ("Nedarim", 91), ("Nazir", 66), ("Sotah", 49), ("Gitin", 90), ("Kiddushin", 82),
    ("Baba Kamma", 119), ("Baba Metzia", 119), ("Baba Batra", 176), ("Sanhedrin", 113),
    ("Makkot", 24), ("Shevuot", 49), ("Avodah Zarah", 76), ("Horayot", 14), ("Zevachim", 120),
    ("Menachot", 110), ("Chullin", 142), ("Bechorot", 61), ("Arachin", 34), ("Temurah", 34),
    ("Keritot", 28), ("Meilah", 22), ("Kinnim", 4), ("Tamid", 9), ("Midot", 5), ("Niddah", 73),
]
DAF_OFFSETS = {36: 21, 37: 24, 38: 32}  # Kinnim starts at 23, Tamid at 26, Midot at 34
SHEKALIM_INDEX, SHEKALIM_OLD = 4, 13
OLD_START, NEW_START = dt.date(1923, 9, 11), dt.date(1975, 6, 24)
OLD_LEN, NEW_LEN, FIRST_NEW = 2702, 2711, 8

# Hebcal spelling -> the Sefaria spelling used elsewhere in this skill.
CANONICAL = {
    "Berachot": "Berakhot", "Rosh Hashana": "Rosh Hashanah", "Gitin": "Gittin",
    "Baba Kamma": "Bava Kamma", "Baba Metzia": "Bava Metzia", "Baba Batra": "Bava Batra",
    "Bechorot": "Bekhorot", "Arachin": "Arakhin", "Midot": "Middot",
}


def daf_yomi(day: dt.date) -> dict:
    if day < OLD_START:
        raise ValueError("Daf Yomi began on 1923-09-11")
    if day >= NEW_START:
        elapsed = (day - NEW_START).days
        cycle, in_cycle, length = FIRST_NEW + elapsed // NEW_LEN, elapsed % NEW_LEN, NEW_LEN
    else:
        elapsed = (day - OLD_START).days
        cycle, in_cycle, length = 1 + elapsed // OLD_LEN, elapsed % OLD_LEN, OLD_LEN
    last = [n for _, n in SHAS]
    if cycle < FIRST_NEW:
        last[SHEKALIM_INDEX] = SHEKALIM_OLD
    so_far = 0
    for i, (name, _) in enumerate(SHAS):
        so_far += last[i] - 1
        if in_cycle < so_far:
            daf = last[i] + 1 - (so_far - in_cycle) + DAF_OFFSETS.get(i, 0)
            canon = CANONICAL.get(name, name)
            return {"tractate": canon, "hebcal_name": name, "page": daf, "daf": f"{canon} {daf}",
                    "cycle": cycle, "day_in_cycle": in_cycle + 1, "cycle_length": length,
                    "index": i}
    raise RuntimeError("masechet table inconsistent")


MONTHS = {1: "Nisan", 2: "Iyyar", 3: "Sivan", 4: "Tamuz", 5: "Av", 6: "Elul", 7: "Tishrei",
          8: "Cheshvan", 9: "Kislev", 10: "Tevet", 11: "Sh'vat", 12: "Adar", 13: "Adar II"}


def hebrew_date(day: dt.date) -> str:
    h = hdates.HebrewDate.from_pydate(day)
    name = MONTHS[h.month]
    if h.month == 12 and _is_leap(h.year):
        name = "Adar I"
    return f"{h.day} {name} {h.year}"


def _is_leap(year: int) -> bool:
    return ((7 * year) + 1) % 19 < 7


def special_shabbatot(year: int) -> dict:
    """Special Shabbatot for a Hebrew year (diaspora), keyed by Gregorian ISO date."""
    adar = 13 if _is_leap(year) else 12
    out = {}

    def shabbat_on_or_before(hd):
        while hd.weekday() != 7:
            hd = hd - 1
        return hd

    rc_adar = hdates.HebrewDate(year, adar, 1)
    out[shabbat_on_or_before(rc_adar).to_pydate().isoformat()] = "Shabbat Shekalim"
    purim = hdates.HebrewDate(year, adar, 14)
    out[shabbat_on_or_before(purim - 1).to_pydate().isoformat()] = "Shabbat Zachor"
    rc_nisan = hdates.HebrewDate(year, 1, 1)
    hachodesh = shabbat_on_or_before(rc_nisan)
    out[hachodesh.to_pydate().isoformat()] = "Shabbat HaChodesh"
    out[(hachodesh - 7).to_pydate().isoformat()] = "Shabbat Parah"
    out[shabbat_on_or_before(hdates.HebrewDate(year, 1, 14)).to_pydate().isoformat()] = "Shabbat HaGadol"
    tisha = hdates.HebrewDate(year, 5, 9)
    chazon = shabbat_on_or_before(tisha)
    out[chazon.to_pydate().isoformat()] = "Shabbat Chazon"
    out[(chazon + 7).to_pydate().isoformat()] = "Shabbat Nachamu"
    rh_next = hdates.HebrewDate(year + 1, 7, 1)
    shuva = rh_next + 1
    while shuva.weekday() != 7:
        shuva = shuva + 1
    out[shuva.to_pydate().isoformat()] = "Shabbat Shuva"
    return out


EREV = {  # (month, day) of the holiday -> title of its eve
    (7, 1): "Erev Rosh Hashana", (7, 10): "Erev Yom Kippur", (7, 15): "Erev Sukkot",
    (1, 15): "Erev Pesach", (3, 6): "Erev Shavuot",
}


def _erev_and_minor(h: hdates.HebrewDate) -> list[dict]:
    items = []
    tomorrow = h + 1
    title = EREV.get((tomorrow.month, tomorrow.day))
    if title:
        items.append({"title": title, "category": "holiday"})
    adar = 13 if _is_leap(h.year) else 12
    if (tomorrow.month, tomorrow.day) == (adar, 14):
        items.append({"title": "Erev Purim", "category": "holiday"})
    # Erev Tisha B'Av: the day before the (possibly deferred) fast.
    if tomorrow.fast_day() == "9 of Av":
        items.append({"title": "Erev Tish'a B'Av", "category": "fast"})
    # Ta'anit Bechorot: 14 Nisan, or Thursday 12 Nisan when 14 Nisan is Shabbat.
    if h.month == 1 and ((h.day == 14 and h.weekday() != 7) or
                         (h.day == 12 and hdates.HebrewDate(h.year, 1, 14).weekday() == 7)):
        items.append({"title": "Ta'anit Bechorot", "category": "fast"})
    return items


DISPLAY = {
    "Rosh Hashana": "Rosh Hashana", "Succos": "Sukkot", "Shmini Atzeres": "Shmini Atzeret",
    "Simchas Torah": "Simchat Torah", "Chanuka": "Chanukah", "Tu B'shvat": "Tu BiShvat",
    "Shavuos": "Shavuot", "Tu B'av": "Tu B'Av", "Lag Baomer": "Lag BaOmer",
    "Tzom Gedalia": "Tzom Gedaliah", "10 of Teves": "Asara B'Tevet", "Taanis Esther": "Ta'anit Esther",
    "17 of Tammuz": "Tzom Tammuz", "9 of Av": "Tish'a B'Av",
}


def special_days(day: dt.date) -> list[dict]:
    h = hdates.HebrewDate.from_pydate(day)
    items = _erev_and_minor(h)
    fest = h.festival(israel=False, include_working_days=True)
    if fest:
        items.append({"title": DISPLAY.get(fest, fest), "category": "holiday"})
    fast = h.fast_day()
    if fast:
        items.append({"title": DISPLAY.get(fast, fast), "category": "fast"})
    if h.day == 30 or (h.day == 1 and h.month != 7):
        items.append({"title": "Rosh Chodesh", "category": "roshchodesh"})
    for y in (h.year - 1, h.year):
        name = special_shabbatot(y).get(day.isoformat())
        if name:
            items.append({"title": name, "category": "shabbat"})
    if h.weekday() == 7 and "Beshalach" in (parshios.getparsha_string(h, israel=False) or ""):
        items.append({"title": "Shabbat Shirah", "category": "shabbat"})
    return items


def day_record(day: dt.date) -> dict:
    d = daf_yomi(day)
    return {
        "date": day.isoformat(),
        "hebrew_date": hebrew_date(day),
        "daf": d["daf"],
        "tractate": d["tractate"],
        "page": d["page"],
        "sefaria_link": f"https://www.sefaria.org/{d['tractate'].replace(' ', '_')}.{d['page']}a",
        "special_days": special_days(day),
    }


def masechet_context(day: dt.date) -> dict:
    cur = daf_yomi(day)
    finish = day
    while daf_yomi(finish + dt.timedelta(days=1))["tractate"] == cur["tractate"]:
        finish += dt.timedelta(days=1)
    remaining = (finish - day).days
    nxt = daf_yomi(finish + dt.timedelta(days=1))
    cycle_days_left = cur["cycle_length"] - cur["day_in_cycle"]
    remaining_masechtot = [CANONICAL.get(n, n) for n, _ in SHAS[cur["index"] + 1:]]
    return {
        "current_masechet": {
            "name": cur["tractate"],
            "days_remaining_after_requested_daf": remaining,
            "finish_date": finish.isoformat(),
            "finish_hebrew_date": hebrew_date(finish),
            "within_14_days": remaining <= 14,
            "within_7_days": remaining <= 7,
            "within_3_days": remaining <= 3,
            "siyum_day": remaining == 0,
            "next_masechet": nxt["tractate"],
        },
        "cycle": {
            "number": cur["cycle"],
            "day": cur["day_in_cycle"],
            "days_remaining": cycle_days_left,
            "siyum_hashas_date": (day + dt.timedelta(days=cycle_days_left)).isoformat(),
            "remaining_masechtot": remaining_masechtot,
        },
    }


def context(start: dt.date, end: dt.date) -> dict:
    days = [day_record(start + dt.timedelta(days=i)) for i in range((end - start).days + 1)]
    out = {"range": {"start": start.isoformat(), "end": end.isoformat()}, "days": days,
           "source": "offline: Hebcal Daf Yomi algorithm + pyluach calendar",
           "attribution": "Daf Yomi algorithm: Hebcal (public domain); calendar: pyluach (MIT)"}
    out.update(masechet_context(start))
    return out


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True)
    p.add_argument("--through")
    a = p.parse_args()
    start = dt.date.fromisoformat(a.date)
    end = dt.date.fromisoformat(a.through) if a.through else start
    if end < start:
        print("--through may not be earlier than --date", file=sys.stderr)
        return 2
    json.dump(context(start, end), sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
