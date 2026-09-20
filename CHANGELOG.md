# Changelog

All notable changes to Daf are documented here.

## 3.1.1 — 2026-09-20

### Fixed

- ByMishnah lessons for a perek the Bavli numbers differently (Sanhedrin's Perek Chelek, Megillah perakim 3-4, Menachot's Perek Rabbi Yishmael) now carry the note. The masechet-wide flag was in the data but missing from single-unit lookups; each unit now has `bavli_perek` and a ready-made `perek_note`, and single-unit output includes the masechet flag.

## 3.1.0 — 2026-09-20

Works out of the box: no settings for anyone who installs it.

### Added

- `archive_source.py`: reads Sefaria texts from Sefaria's public export archive on GitHub (pinned commit), which default sandboxes can reach even when sefaria.org is blocked. Covers Bavli, Mishnah, Rashi, Tosafot, Rishonim, Steinsaltz, Bartenura, Rambam, Shulchan Arukh, Tur, Yerushalmi, and Tosefta, with per-file caching.
- `offline_calendar.py`: Daf Yomi, Hebrew dates, holidays, fasts, Rosh Chodesh, special Shabbatot, masechet completion, and full-cycle progress, computed offline. The Daf Yomi port matches `@hebcal/learning` for all 14,976 days from 2000 to 2040; holidays match Hebcal on 588 of 589 significant dates for 2024-2032 (the exception is the Jerusalem-only Purim Meshulash).
- Bundled data (`data/`): ByMishnah maps for all 37 Bavli masechtot, an archive path index, and per-amud halacha (Ein Mishpat) and parallel (Mesorat HaShas) links.
- `tools/build_data.py` to rebuild the bundled data.
- Vendored pyluach 2.3.0 (MIT) for the Hebrew calendar.
- Rishonim output separates works cited by Gemara amud from those on the Rif's pagination or by perek, so a Rif-page number is never presented as a Gemara daf.

### Changed

- `sefaria_fetch.py`, `sefaria_links.py`, `mishnah_map.py`, and `yomi_context.py` are offline-first; `--live` prefers the live APIs where allowed and falls back automatically.
- `sefaria_fetch.py` gains `--lang he|en|both`.

## 3.0.1 — 2026-09-20

Fixes from the first live checklist run.

### Fixed

- `self_check.py` no longer fails in an installed package because repo-only files (`evals/`, `docs/`, CI workflow) are absent; it notes them instead.
- `learning_log.py reset` now refuses to clear anything without `--yes`, so the confirmation step is enforced in code as well as in the instructions.
- ByMishnah now distinguishes an unknown masechet (exit 2), a tractate with no Bavli Gemara such as Peah (exit 3), and a blocked network (exit 5) before and during lookup, so "no Gemara" can no longer be confused with a network failure.

### Added

- Masechet registry with common Ashkenazi and alternate spellings.
- Clear, actionable errors in every helper when the sandbox's network allowlist blocks Sefaria or Hebcal, and instructions for telling the learner how to allow those domains.

## 3.0.0 — 2026-09-19

Feature release. All 2.0 commands behave as before.

### Added

- `/daf bymishnah <Masechet>`: learn a Bavli masechet one complete Mishnah per session, with all of its Gemara, stopping where the next Mishnah begins. Shows the masechet's total mishnayot and the learner's position ("Mishnah 13 of N · Perek 2, Mishnah 1"), follows Bavli order where it differs from the Mishnah, merges Mishnayot that share a Gemara section, handles Mishnayot without Gemara, and splits very long units into parts without advancing early.
- Personal learning log: `/daf log`, `/daf continue`, `/daf log reset`, and the `nolog` modifier. Tracks ByMishnah position per masechet, the exact-daf track, and Daf Yomi.
- `rishonim` focus modifier for other Rishonim (Ramban, Rashba, Ritva, Ran, Rosh, Rif, Meiri, and others linked on Sefaria).
- `audio` modifier: a spoken shiur script rendered to MP3 with a neural voice, with espeak-ng and macOS fallbacks and a pronunciation lexicon.
- `export` modifier: a formatted PDF with right-to-left Hebrew, callouts, tables, addenda, and page numbers.
- End-of-lesson follow-up menu (audio, PDF, deeper Rashi, deeper Tosafot, other Rishonim, more halacha, parallel sugyot) that shows only unused options and adds a focused addendum without regenerating the lesson.
- Helpers: `sefaria_links.py`, `mishnah_map.py`, `learning_log.py`, `make_audio.py`, `make_pdf.py`, and shared `daf_common.py`.
- References: `bymishnah.md`, `learning-log.md`, `audio-and-export.md`.
- `evals/evals.json` (19 evals, including multi-turn follow-ups), `docs/testing-checklist` (one-page live checklist), and a GitHub Actions workflow for release checks.
- `--compact` option for `make_pdf.py` handouts.

### Changed

- Trigger description, routing, modifiers, fast-path rules, source policy, README, acceptance cases, and release tests updated for the new modes.

## 2.0.0 — 2026-08-31

Breaking command update.

### Added

- `/daf <Masechet> <daf>` for a full lesson on any exact daf or amud, independent of the Daf Yomi schedule.
- Inclusive same-masechet ranges such as `/daf Chullin 23a-33b`, grouped by perek and major sugya with a coverage checklist.
- `/daf yomi` for the current daily assignment, preserving the original guided Daf Yomi study experience.
- Plain `/daf` as a shortcut for `/daf yomi`.
- Exact-daf continuity rules that locate a request within its perek and preview the next amud or daf.
- `rashi` and `tosafot` focus modes for single dafim, exact ranges, and Yomi requests, including common Tosafot spelling variants.
- Automated release checks for command routing, exact ranges, commentary focus, documentation, and mode-specific progress behavior.

### Changed

- Renamed the skill and primary command from `/dafyomi` to `/daf`.
- Moved relative dates, explicit dates, and date-based catch-up ranges under `/daf yomi`.
- Kept masechet countdowns, siyum planning, and cycle progress in Yomi mode while excluding them from named-daf and exact-range requests.
- Updated help, examples, source guidance, UI metadata, helper behavior, and acceptance cases for the expanded command model.
- Added a bounded fast path for ordinary single-daf requests: consolidated source retrieval, selected commentary by default, and comprehensive research reserved for `deep`, `show sources`, or explicit requests.

### Removed

- Calendar and cycle-progress material from exact-daf and exact-range output.

## 1.0.0 — 2026-08-30

First public-ready release as Daf Yomi Tutor.

### Added

- Guided lesson structure with Mishnah, sugyot, Rashi/Tosafot, halacha, Aramaic, key takeaways, and review.
- `short`, `deep`, `halacha`, `beginner`, and `advanced` modes.
- Relative dates, explicit dates, and inclusive catch-up ranges.
- "Where are we?" perek/continuity context and next-page preview.
- Special-day notices.
- Masechet completion countdowns, siyum planning, and Daf Yomi cycle context.
- Hebcal and Sefaria grounding without API keys or an MCP requirement.
- Optional outside shiur links.
- Source links on demand.
- Verification and failure-state rules.
- Acceptance-test checklist.
- MIT License.
- Dedication to David and Barbara Blumenthal.
