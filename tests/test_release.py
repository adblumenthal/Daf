"""Zero-dependency release tests for the Daf skill."""

from __future__ import annotations

import datetime as dt
import importlib.util
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def load_module(name: str, path: str):
    target = ROOT / path
    spec = importlib.util.spec_from_file_location(name, target)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = read("SKILL.md")
        cls.readme = read("README.md")
        cls.acceptance = read("tests/acceptance-cases.md")

    def test_minimal_frontmatter_and_name(self):
        match = re.match(r"^---\n(.*?)\n---\n", self.skill, re.DOTALL)
        self.assertIsNotNone(match)
        keys = [
            line.split(":", 1)[0]
            for line in match.group(1).splitlines()
            if line and not line.startswith(" ") and ":" in line
        ]
        self.assertEqual(keys, ["name", "description"])
        self.assertIn("name: daf\n", self.skill)

    def test_exact_daf_contract(self):
        for example in (
            "/daf Chullin 23b",
            "/daf Bava Metzia 42a deep",
            "/daf Berakhot 2 beginner halacha",
        ):
            self.assertIn(example, self.skill)
        self.assertIn("Treat the named reference as authoritative", self.skill)
        self.assertIn("preview `Chullin 24a`", self.skill)

    def test_exact_range_contract(self):
        self.assertIn("/daf Chullin 23a-33b", self.skill)
        self.assertIn("inclusive same-masechet range", self.skill)
        self.assertIn("## Teach an exact-daf range", self.skill)
        self.assertIn("compact checklist of every daf or amud covered", self.skill)
        self.assertIn("Do not include Yomi dates", self.skill)

    def test_yomi_contract_and_progress(self):
        for example in (
            "/daf yomi",
            "/daf yomi yesterday",
            "/daf yomi 8/15/2025",
            "/daf yomi 8/15/2025 till today",
        ):
            self.assertIn(example, self.skill)
        self.assertIn("Plain `/daf` and `/daf yomi`", self.skill)
        self.assertIn("## Provide Yomi completion and cycle context", self.skill)
        self.assertIn("within 14 days", self.skill)
        self.assertIn("Siyum HaShas", self.skill)

    def test_progress_is_yomi_only(self):
        self.assertIn("Only in Yomi mode", self.skill)
        self.assertIn("Never add this section to exact-daf mode", self.skill)
        self.assertIn("Yomi mode preserves the original calendar and progress context", self.readme)
        self.assertIn("It does not add unrelated Daf Yomi dates or cycle statistics", self.readme)

    def test_commentary_focus_contract(self):
        for heading in ("### `rashi`", "### `tosafot`"):
            self.assertIn(heading, self.skill)
        for example in (
            "/daf Chullin 23a-33b rashi deep",
            "/daf Chullin 23a-33b tosafot halacha",
            "/daf Chullin 23a-33b rashi tosafot advanced",
            "/daf yomi tosafot deep",
        ):
            self.assertIn(example, self.skill)
        self.assertIn("`tosafot`, `tosefot`, and `tosfos`", self.skill)

    def test_bounded_fast_path_contract(self):
        self.assertIn("## Keep ordinary requests fast", self.skill)
        self.assertIn("one calendar lookup and one consolidated source retrieval", self.skill)
        self.assertIn("not every comment on the daf", self.skill)
        self.assertIn("Reserve exhaustive commentary retrieval", self.skill)
        self.assertIn("## Performance boundaries", self.acceptance)
        self.assertIn("/daf yomi tosafot", self.acceptance)

    def test_legacy_command_removed_from_current_docs(self):
        current_docs = "\n".join((self.skill, self.readme, self.acceptance))
        self.assertNotIn("/dafyomi", current_docs)

    def test_acceptance_covers_expanded_modes(self):
        for heading in (
            "## Exact-daf mode",
            "## Exact-daf ranges",
            "## Yomi mode",
            "## Yomi completion and cycle context",
            "## Commentary and study modes",
        ):
            self.assertIn(heading, self.acceptance)
        self.assertIn("Mode isolation", self.acceptance)


class CalendarHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = load_module("yomi_context", "scripts/yomi_context.py")

    def test_record_keeps_yomi_assignment_and_special_day(self):
        record = self.context._record(
            dt.date(2026, 8, 30),
            [
                {
                    "category": "dafyomi",
                    "title": "Chullin 122",
                    "hdate": "17 Elul 5786",
                    "hebrew": "Chullin 122 Hebrew",
                    "link": "https://www.sefaria.org/Chullin.122",
                },
                {"category": "roshchodesh", "title": "Rosh Chodesh"},
            ],
        )
        self.assertEqual(record["daf"], "Chullin 122")
        self.assertEqual(record["tractate"], "Chullin")
        self.assertEqual(record["page"], 122)
        self.assertEqual(record["special_days"][0]["title"], "Rosh Chodesh")

    def test_split_daf_title_handles_spaced_masechet(self):
        self.assertEqual(
            self.context._split_daf_title("Bava Batra 42"),
            ("Bava Batra", 42),
        )

    def test_find_masechet_finish_returns_yomi_countdown(self):
        start = dt.date(2026, 8, 30)
        payload = {
            "items": [
                {"date": "2026-08-30", "category": "dafyomi", "title": "Chullin 122"},
                {"date": "2026-08-31", "category": "dafyomi", "title": "Chullin 123"},
                {"date": "2026-09-01", "category": "dafyomi", "title": "Bekhorot 2"},
            ]
        }
        original = self.context._hebcal
        self.context._hebcal = lambda *_args, **_kwargs: payload
        try:
            finish, remaining = self.context._find_masechet_finish(start, "Chullin")
        finally:
            self.context._hebcal = original
        self.assertEqual(finish, dt.date(2026, 8, 31))
        self.assertEqual(remaining, 1)


class SefariaHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sefaria = load_module("sefaria_fetch", "scripts/sefaria_fetch.py")

    def test_range_urls_preserve_exact_boundaries(self):
        api_url, source_url = self.sefaria.build_urls("Chullin 23a-33b")
        self.assertIn("Chullin%2023a-33b", api_url)
        self.assertEqual(source_url, "https://www.sefaria.org/Chullin_23a-33b")

    def test_commentary_range_urls_preserve_scope(self):
        api_url, source_url = self.sefaria.build_urls("Tosafot on Chullin 23a-33b")
        self.assertIn("Tosafot%20on%20Chullin%2023a-33b", api_url)
        self.assertEqual(source_url, "https://www.sefaria.org/Tosafot_on_Chullin_23a-33b")


class V3ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = read("SKILL.md")
        cls.readme = read("README.md")

    def test_version_and_new_sections(self):
        self.assertRegex(self.skill, r"Version 3\.\d+\.\d+")
        for heading in ("## Teach ByMishnah", "## Offer follow-ups at the end",
                        "## Keep the learning log", "## Produce audio and PDF on request",
                        "### `rishonim`"):
            self.assertIn(heading, self.skill)

    def test_follow_ups_do_not_regenerate(self):
        self.assertIn("It never regenerates it", self.skill)
        self.assertIn("options below that were **not** already part of this lesson", self.skill)
        for option in ("Audio shiur", "Formatted PDF", "Go deeper on Rashi", "Go deeper on Tosafot",
                       "Other Rishonim", "More halacha context", "Parallel sugyot"):
            self.assertIn(option, self.skill)

    def test_bymishnah_contract(self):
        self.assertIn("how many mishnayot the masechet has", self.skill)
        self.assertIn("Never cut a unit at a daf boundary", self.skill)
        self.assertIn("ByMishnah mode has its own progress line", self.skill)


class MishnahMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load_module("mishnah_map", "scripts/mishnah_map.py")
        cls.result = cls.m.build_units(
            "Test", [3, 2, 2],
            {"1:1": "Test 2a:1", "1:2": "Test 5b:4-6", "1:3": "Test 5b:7",
             "2:1": "Test 20a:1", "2:2": "Test 22b:3", "3:1": "Test 10a:2"},
            "Test 25b",
        )

    def test_counts_and_positions(self):
        r = self.result
        self.assertEqual(r["total_mishnayot"], 7)
        self.assertEqual(r["units"][0]["position"], "Mishnah 1 of 7")
        self.assertEqual(r["units"][-1]["seq_end"], 7)

    def test_shared_gemara_merges(self):
        u = self.result["units"][1]
        self.assertEqual(u["mishnayot"], ["1:2", "1:3"])
        self.assertEqual(u["position"], "Mishnayot 2-3 of 7")

    def test_span_stops_at_next_mishnah(self):
        u = self.result["units"][0]
        self.assertEqual(u["fetch_ref"], "Test 2a-5b")
        self.assertEqual(u["gemara_span"], "Test 2a:1 through Test 5b:3")
        self.assertEqual(u["amudim"], 8)

    def test_bavli_order_and_mishnah_only(self):
        labels = [u["mishnayot"][0] for u in self.result["units"]]
        self.assertEqual(labels, ["1:1", "1:2", "3:1", "3:2", "2:1", "2:2"])
        self.assertTrue(self.result["bavli_order_differs_from_mishnah_order"])
        self.assertEqual(self.result["mishnah_only_units"], ["3:2"])

    def test_find_unit(self):
        u = self.m.find_unit(self.result, label="1:3")
        self.assertEqual(u["unit"], 2)


class LearningLogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = load_module("learning_log", "scripts/learning_log.py")

    def test_bymishnah_progress_and_partial(self):
        L = self.log.empty_log()
        self.log.record(L, mode="bymishnah", ref="Chullin 2a-12a", date="2026-09-18",
                        masechet="Chullin", unit=1, seq_end=1, total=74, label="Perek 1, Mishnah 1")
        self.log.record(L, mode="bymishnah", ref="Chullin 12a-20a", date="2026-09-19",
                        masechet="Chullin", unit=2, seq_end=2, total=74, label="Perek 1, Mishnah 2",
                        partial="1/2")
        t = L["tracks"]["bymishnah"]["Chullin"]
        self.assertEqual(t["completed_through"], 1)
        self.assertEqual(t["next_unit"], 2)
        self.log.record(L, mode="bymishnah", ref="Chullin 12a-20a", date="2026-09-20",
                        masechet="Chullin", unit=2, seq_end=2, total=74, label="Perek 1, Mishnah 2",
                        partial="2/2")
        t = L["tracks"]["bymishnah"]["Chullin"]
        self.assertEqual((t["completed_through"], t["next_unit"], t["in_progress"]), (2, 3, None))
        self.assertIn("2 of 74 mishnayot complete", self.log.summary(L))

    def test_exact_and_yomi_tracks(self):
        L = self.log.empty_log()
        self.log.record(L, mode="exact", ref="Chullin 23b", nxt="Chullin 24a", date="2026-09-19")
        self.log.record(L, mode="yomi", ref="Chullin 122", date="2026-09-20")
        self.assertEqual(L["tracks"]["exact"]["next_ref"], "Chullin 24a")
        self.assertEqual(L["active_track"], "yomi")
        self.assertEqual(len(L["history"]), 2)


class SefariaLinksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.l = load_module("sefaria_links", "scripts/sefaria_links.py")
        cls.links = [
            {"ref": "Rashba on Chullin 23b:1", "collectiveTitle": {"en": "Rashba"}, "category": "Commentary"},
            {"ref": "Rashi on Chullin 23b:1", "collectiveTitle": {"en": "Rashi"}, "category": "Commentary"},
            {"ref": "Maharsha on Chullin 23b", "collectiveTitle": {"en": "Maharsha"}, "category": "Commentary"},
            {"ref": "Mishneh Torah, Ritual Slaughter 1:1", "category": "Halakhah"},
            {"ref": "Shulchan Arukh, Yoreh De'ah 1:1", "category": "Halakhah"},
            {"ref": "Zevachim 30a:2", "category": "Talmud"},
            {"ref": "Chullin 23b:5", "category": "Talmud"},
        ]

    def test_rishonim_filter(self):
        works = [g["work"] for g in self.l.group_links(self.links, "rishonim", "Chullin 23b")["rishonim"]]
        self.assertEqual(works, ["Rashba"])

    def test_halacha_and_parallels(self):
        g = self.l.group_links(self.links, "all", "Chullin 23b")
        self.assertEqual(sorted(x["work"] for x in g["halacha"]), ["Rambam, Mishneh Torah", "Shulchan Arukh"])
        self.assertEqual([x["refs"] for x in g["parallels"]], [["Zevachim 30a:2"]])

    def test_expand_amudim(self):
        common = load_module("daf_common", "scripts/daf_common.py")
        self.assertEqual(common.expand_amudim("Chullin 23b-24b"), ["Chullin 23b", "Chullin 24a", "Chullin 24b"])
        self.assertEqual(common.expand_amudim("Chullin 23"), ["Chullin 23a", "Chullin 23b"])


class OutputHelperTests(unittest.TestCase):
    def test_audio_text_is_speakable(self):
        audio = load_module("make_audio", "scripts/make_audio.py")
        out = audio.speakable("## Chullin 23b\nRashi s.v. hakol -> see \u05d4\u05db\u05dc. Rav ran home.")
        self.assertIn("twenty-three, ah-mood bet", out)
        self.assertIn("at the words", out)
        self.assertNotIn("\u05d4", out)
        self.assertIn("Rahv ran home", out)  # English "ran" untouched

    def test_pdf_markdown(self):
        pdf = load_module("make_pdf", "scripts/make_pdf.py")
        html = pdf.markdown_to_html("## Mishnah\n> **\u05d4\u05db\u05dc** all\n\n- [x] Chullin 2a\n\n| a | b |\n|---|---|\n| 1 | 2 |")
        self.assertIn("<h2>Mishnah</h2>", html)
        self.assertIn('dir="rtl"', html)
        self.assertIn("&#9745;", html)
        self.assertIn("<table>", html)



class V301FixTests(unittest.TestCase):
    def test_masechet_registry(self):
        common = load_module("daf_common", "scripts/daf_common.py")
        self.assertEqual(common.normalize_masechet("Brachos"), ("Berakhot", "bavli"))
        self.assertEqual(common.normalize_masechet("bava  basra"), ("Bava Batra", "bavli"))
        self.assertEqual(common.normalize_masechet("Peah"), ("Peah", "mishnah_only"))
        self.assertEqual(common.normalize_masechet("NotAMasechet"), (None, "unknown"))
        self.assertEqual(len(common.BAVLI), 37)

    def test_reset_requires_yes(self):
        import subprocess, sys, tempfile
        log = Path(tempfile.mkdtemp()) / "log.json"
        script = str(ROOT / "scripts" / "learning_log.py")
        subprocess.run([sys.executable, script, "--log", str(log), "record", "--mode", "exact",
                        "--ref", "Chullin 23b", "--date", "2026-09-20"], capture_output=True)
        dry = subprocess.run([sys.executable, script, "--log", str(log), "reset"], capture_output=True)
        self.assertEqual(dry.returncode, 6)
        self.assertIn("Chullin 23b", log.read_text(encoding="utf-8"))
        subprocess.run([sys.executable, script, "--log", str(log), "reset", "--yes"], capture_output=True)
        self.assertNotIn("Chullin 23b", log.read_text(encoding="utf-8"))

    def test_mishnah_map_rejects_before_network(self):
        import subprocess, sys
        script = str(ROOT / "scripts" / "mishnah_map.py")
        self.assertEqual(subprocess.run([sys.executable, script, "Peah"], capture_output=True).returncode, 3)
        self.assertEqual(subprocess.run([sys.executable, script, "NotAMasechet"],
                                        capture_output=True).returncode, 2)

    def test_offline_first_documented(self):
        skill = read("SKILL.md")
        self.assertIn("no network settings to change", skill)
        self.assertIn("Never cite a Rif-paginated work by the Gemara's daf number", skill)



class OfflineCalendarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        cls.cal = load_module("offline_calendar", "scripts/offline_calendar.py")

    def test_known_daf_yomi_dates(self):
        c = self.cal
        self.assertEqual(c.daf_yomi(dt.date(2020, 1, 5))["daf"], "Berakhot 2")   # 14th cycle begins
        self.assertEqual(c.daf_yomi(dt.date(2024, 4, 8))["daf"], "Bava Metzia 40")  # Hebcal doc example
        self.assertEqual(c.daf_yomi(dt.date(2026, 9, 19))["daf"], "Chullin 142")
        self.assertEqual(c.daf_yomi(dt.date(2027, 6, 7))["daf"], "Niddah 73")     # Siyum HaShas

    def test_masechet_and_cycle_context(self):
        ctx = self.cal.masechet_context(dt.date(2026, 9, 19))
        self.assertTrue(ctx["current_masechet"]["siyum_day"])
        self.assertEqual(ctx["current_masechet"]["next_masechet"], "Bekhorot")
        self.assertEqual(ctx["cycle"]["siyum_hashas_date"], "2027-06-07")

    def test_hebrew_date_and_special_days(self):
        c = self.cal
        self.assertEqual(c.hebrew_date(dt.date(2026, 9, 19)), "8 Tishrei 5787")
        titles = lambda d: [x["title"] for x in c.special_days(d)]
        self.assertIn("Shabbat Shuva", titles(dt.date(2026, 9, 19)))
        self.assertIn("Yom Kippur", titles(dt.date(2026, 9, 21)))
        self.assertIn("Shabbat Shirah", titles(dt.date(2026, 1, 31)))
        self.assertIn("Tish'a B'Av", titles(dt.date(2026, 7, 23)))


class BundledDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import json
        cls.maps = json.loads(read("data/mishnah_maps.json"))["maps"]
        cls.common = load_module("daf_common", "scripts/daf_common.py")

    def test_every_bavli_masechet_mapped(self):
        self.assertEqual(sorted(self.maps), sorted(self.common.BAVLI))

    def test_known_boundaries(self):
        b = self.maps["Berakhot"]
        self.assertEqual(b["total_mishnayot"], 57)
        self.assertEqual(b["units"][0]["gemara_span"], "Berakhot 2a:1 through Berakhot 9b:8")
        self.assertEqual(self.maps["Chullin"]["total_mishnayot"], 74)
        self.assertTrue(self.maps["Sanhedrin"]["bavli_order_differs_from_mishnah_order"])
        chelek = [u for u in self.maps["Sanhedrin"]["units"] if "10:1" in u["mishnayot"]][0]
        self.assertTrue(chelek["bavli_start"].startswith("Sanhedrin 90a"))

    def test_perek_notes(self):
        units = self.maps["Sanhedrin"]["units"]
        chelek = [u for u in units if "10:1" in u["mishnayot"]][0]
        self.assertEqual(chelek["bavli_perek"], 11)
        self.assertIn("Perek 11", chelek["perek_note"])
        self.assertIsNone(self.maps["Chullin"]["units"][0]["perek_note"])
        moved = sorted(m for m, d in self.maps.items() if any(u["perek_note"] for u in d["units"]))
        self.assertEqual(moved, ["Megillah", "Menachot", "Sanhedrin"])

    def test_find_output_carries_flag(self):
        import subprocess, sys, json
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "mishnah_map.py"), "Sanhedrin",
                              "--find", "10:1"], capture_output=True, text=True)
        d = json.loads(out.stdout)
        self.assertTrue(d["bavli_order_differs_from_mishnah_order"])
        self.assertIn("Perek 11", d["unit"]["perek_note"])

    def test_link_index(self):
        import json
        chullin = json.loads(read("data/links/Chullin.json"))
        self.assertTrue(any(r.startswith("Mishneh Torah, Ritual Slaughter") for r in chullin["2a"]["h"]))


class ArchiveSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        cls.a = load_module("archive_source", "scripts/archive_source.py")

    def test_split_ref_longest_title(self):
        self.assertEqual(self.a.split_ref("Rashi on Chullin 23b:4"), ("Rashi on Chullin", "23b:4"))
        self.assertEqual(self.a.split_ref("Bava Metzia 2a"), ("Bava Metzia", "2a"))
        self.assertEqual(self.a.split_ref("Mishneh Torah, Ritual Slaughter 4:1")[1], "4:1")

    def test_layouts(self):
        self.assertEqual(self.a.layout("Ran on Chullin"), "rif")
        self.assertEqual(self.a.layout("Rosh on Chullin"), "perek")
        self.assertEqual(self.a.layout("Rashba on Chullin"), "gemara")

    def test_select_talmud_and_ranges(self):
        book = {"sectionNames": ["Daf", "Line"],
                "text": [[], [], ["2a one", "2a two"], ["2b one"], ["3a one", "3a <b>two</b>"]]}
        sel = self.a.select
        self.assertEqual([x[0] for x in sel(book, "2a")], ["2a:1", "2a:2"])
        self.assertEqual([x[0] for x in sel(book, "2b-3a")], ["2b:1", "3a:1", "3a:2"])
        self.assertEqual(sel(book, "3a:2"), [("3a:2", "3a two")])
        self.assertEqual(len(sel(book, "2")), 3)

    def test_select_nested_commentary_and_mishnah(self):
        comm = {"sectionNames": ["Daf", "Line", "Comment"], "text": [[], [], [["c1", "c2"], [], ["c3"]]]}
        self.assertEqual([x[0] for x in self.a.select(comm, "2a:3")], ["2a:3:1"])
        mishnah = {"sectionNames": ["Chapter", "Mishnah"], "text": [["m1", "m2", "m3"], ["m4"]]}
        self.assertEqual([x[0] for x in self.a.select(mishnah, "1:2-3")], ["1:2", "1:3"])


if __name__ == "__main__":
    unittest.main()
