# Daf — portable Agent Skill

**Version 3.1.1**

A source-grounded Talmud tutor with two simple entry points:

- `/daf Chullin 23b` teaches that exact daf or amud, independent of the Daf Yomi schedule.
- `/daf Chullin 23a-33b` creates a grouped catch-up lesson across that exact inclusive range.
- `/daf yomi` teaches today's Daf Yomi assignment.
- `/daf bymishnah Chullin` teaches the next complete Mishnah in a masechet, with all of its Gemara.
- `/daf log` shows where you were last and where you are now.

Plain `/daf` is a shortcut for `/daf yomi`. The skill explains the Mishnah and major sugyot, makes the Gemara's logic clear, highlights useful Rashi and Tosafot, connects relevant halacha, teaches Aramaic, gives three key takeaways and review questions, and previews the next material.

## Dedication

Created by **Adam Blumenthal** in honor of his mother and father, **David and Barbara Blumenthal**, who always pushed him to keep asking questions.

That spirit is part of the goal of this skill: learning a daf should not stop at *what* the Gemara says, but should keep asking *why*, *how*, and *what follows from it*.

## Command guide

### Study any daf

- `/daf Chullin 23b`
- `/daf Chullin 23a-33b`
- `/daf Bava Metzia 42a deep`
- `/daf Bava Metzia 42a-45b tosafot deep`
- `/daf Berakhot 2 beginner halacha`
- `/daf Sanhedrin 17b show sources`

The requested reference is taught directly, even when it is not part of the current Daf Yomi cycle. A reference ending in `a` or `b` limits the lesson to that amud; a reference without an amud letter requests the whole daf when supported by the source.

Exact ranges stay within one masechet and are inclusive. `/daf Chullin 23a-33b` covers every amud from 23a through 33b, groups the material by perek and major sugya, and includes a compact coverage checklist. It does not add unrelated Daf Yomi dates or cycle statistics.

### Follow Daf Yomi

- `/daf`
- `/daf yomi`
- `/daf yomi yesterday`
- `/daf yomi 8/15/2025`
- `/daf yomi 2025-08-15`
- `/daf yomi yesterday short`
- `/daf yomi 8/15/2025 till today short`

Date syntax belongs after `yomi`. Plain `/daf` and `/daf yomi` use the user's current local date.

Yomi mode preserves the original calendar and progress context: current-masechet days remaining, exact completion dates and siyum-planning reminders when close, final-daf notices, and full-cycle progress when reliably available. This material appears only in Yomi mode, not when studying a named page or exact range.

### Learn mishnah by mishnah

- `/daf bymishnah Chullin`
- `/daf bymishnah`
- `/daf bymishnah Chullin 3:2`
- `/daf bymishnah status`

Each session covers one complete Mishnah and all of its Gemara, so it may be more or less than a daf. The header shows the masechet's total mishnayot and your position, for example "Mishnah 13 of N · Perek 2, Mishnah 1," with the exact Gemara span. The order follows the Bavli. Mishnayot the Bavli prints together are learned together, and very long units can be split into parts.

### Track your progress

- `/daf log` shows your last session and your position in each track
- `/daf continue` resumes where you left off
- `/daf log reset` clears the log after confirming
- add `nolog` to any request to skip recording

The log is kept in a persistent file where the host allows (`~/.daf/learning-log.json`), otherwise in the host's memory store, otherwise as a file you re-attach.

### Study modes

Both exact-daf and Yomi requests support:

- `short` — compact lesson
- `deep` — expanded shakla v'tarya and commentaries
- `halacha` — emphasize the path to practical halacha
- `beginner` — explain terminology and logical steps
- `advanced` — emphasize Rishonim, conceptual distinctions, and exact references
- `rashi` — expand the most important Rashi comments and how they shape the peshat
- `tosafot` / `tosefot` / `tosfos` — expand major questions, answers, parallels, and consequences
- `rishonim` — add other Rishonim such as Ramban, Rashba, Ritva, Ran, Rosh, and Meiri
- `audio` — also deliver an MP3 audio shiur of the lesson
- `export` — also deliver a formatted PDF
- `show sources` — provide direct source links

### Go deeper after a lesson

Every lesson ends with a short menu of options you did not already use: audio shiur, PDF, deeper Rashi, deeper Tosafot, other Rishonim, more halacha context, and parallel sugyot elsewhere in Shas. Reply with a number, several numbers, or a phrase such as `more tosafot`. Each choice adds a focused addendum to the lesson you just learned; it does not redo the daf.

Modifiers can be combined for a page, range, or Yomi request, such as `/daf Chullin 23a-33b rashi tosafot advanced`, `/daf Chullin 23b advanced deep`, or `/daf yomi halacha beginner`.

Ordinary requests use a streamlined source path. A `rashi` or `tosafot` modifier selects the most important comments without exhaustively retrieving every commentary passage. Add `deep` or `show sources` when you want broader research and more extensive source verification.

## Designed for easy installation

- No Sefaria account
- No API key
- No MCP server
- No network allowlist changes
- No pip/npm dependencies for the core lesson (audio uses the optional `piper-tts` voice, installed on demand, or espeak-ng; PDF uses wkhtmltopdf, Chrome, or WeasyPrint when present)
- One skill folder
- Open Agent Skills `SKILL.md` format

The source, calendar, map, and log helpers use Python 3's standard library and public Hebcal/Sefaria HTTP APIs.

## Install in ChatGPT Skills

Where Skills are available:

1. Open **Plugins → Skills**.
2. Choose **Create → Upload from your computer**.
3. Upload the complete `Daf` repository folder or release package.
4. Install or enable the skill.

Availability depends on plan, workspace settings, surface, and rollout.

## Install in another Agent-Skills-compatible client

Install or copy the complete repository folder into the location your client uses for Agent Skills. Keep `SKILL.md`, `scripts/`, `references/`, and `agents/` together.

The package follows the open Agent Skills directory format:

- `SKILL.md` — required instructions and trigger metadata
- `agents/openai.yaml` — optional UI metadata
- `scripts/` — zero-dependency source and calendar helpers
- `references/` — supporting source and installation guidance
- `tests/` — release acceptance coverage

## Data sources

- **Sefaria**: Gemara, Mishnah, Rashi, Tosafot, Rishonim, Rambam, Shulchan Arukh, Tur, Yerushalmi, and Tosefta, from Sefaria's export archive on GitHub (or the live API with `--live`). Sefaria's texts carry their own licenses; see sefaria.org.
- **Hebcal**: the Daf Yomi algorithm (public domain), ported to Python.
- **pyluach** (MIT, vendored in `scripts/vendor/`): Hebrew dates and holidays.

Texts are downloaded at runtime (one file per masechet, cached). Only compact derived data is bundled in `data/`: ByMishnah maps, a path index, and per-amud halacha and parallel links. Maintainers can rebuild it with `python tools/build_data.py`.

**Works out of the box.** Many AI sandboxes, including Claude's, block sefaria.org and hebcal.com by default. This skill does not need them: it reads Sefaria's texts from Sefaria's public export archive on GitHub, computes the Daf Yomi calendar offline with Hebcal's algorithm (verified day by day for 2000-2040), and ships prebuilt ByMishnah maps and link indexes. Nobody installing it has to change any settings. Where a host does allow the live APIs, `--live` uses them.

## Quality checks

Run:

```bash
python scripts/self_check.py
```

and

```bash
python -m unittest tests/test_release.py
```

Then review `tests/acceptance-cases.md`.

For a live run with the skill installed:

- `docs/testing-checklist.pdf` is a one-page printable checklist (about 45 minutes).
- `evals/evals.json` holds 19 formal evals with 62 checkable expectations, including multi-turn follow-up tests. They work with Anthropic's skill-creator eval workflow or by hand.

GitHub Actions runs the self-check and unit tests on every push (`.github/workflows/tests.yml`). The `evals/` folder is kept out of the installable `.skill` package automatically. It covers exact-daf routing, exact ranges, Daf Yomi dates and ranges, Rashi/Tosafot focus, study modes, Yomi-only completion context, source behavior, and special days.

## Publishing

This project is released under the **MIT License**. See `LICENSE`.

See `CHANGELOG.md` for release history, including the 3.0 additions and the 2.0 command migration notes.
