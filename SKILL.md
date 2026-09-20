---
name: daf
description: Guided Talmud study for exact pages, amudim, ranges, the Daf Yomi schedule, and mishnah-by-mishnah learning with a personal progress log. Use for `/daf`, `/daf yomi`, exact references such as `/daf Chullin 23b`, ranges such as `/daf Chullin 23a-33b`, `/daf bymishnah Chullin`, `/daf log`, `/daf continue`, Daf Yomi dates and catch-up, Rashi, Tosafot, or other Rishonim focus, audio shiurim, PDF export, and requests to go deeper on a daf just learned (more Rashi, Tosafot, Rishonim, halacha, or parallel sugyot). Use it for any request to learn, review, hear, or print a daf or Mishnah, even without the slash command. Grounds text in Sefaria and the calendar in Hebcal's algorithm, with no special network settings required.
---

# Daf

Version 3.1.1

Provide a reliable, structured lesson for a user-selected daf, the Daf Yomi assignment, or the next Mishnah in a masechet the learner is working through. Do more than name or summarize the page: make the sugya understandable and source-grounded. Remember where the learner is, and let them go deeper on exactly the part they want without redoing the lesson.

## Route the request

Choose exactly one mode before retrieving sources.

### Exact-daf mode

Use exact-daf mode for `/daf <Masechet> <daf>`.

Examples:

- `/daf Chullin 23b`
- `/daf Chullin 23a-33b`
- `/daf Bava Metzia 42a deep`
- `/daf Bava Metzia 42a-45b tosafot deep`
- `/daf Berakhot 2 beginner halacha`
- `/daf Sanhedrin 17b show sources`

Treat the named reference as authoritative. Do not replace it with the current Daf Yomi assignment and do not require it to belong to the current cycle.

Accept a standard masechet name followed by a daf number, optionally with an amud letter (`a` or `b`). Preserve the user's requested scope:

- `Chullin 23b` means amud 23b.
- `Chullin 23a` means amud 23a.
- `Chullin 23` means the whole daf when the source supports that reference.

Accept an inclusive same-masechet range such as `Chullin 23a-33b`. Keep the starting and ending amud exact and cover every amud between them in order. Also accept whole-daf ranges such as `Chullin 23-33` when the source resolves them reliably. Do not silently reverse an descending range or infer a cross-masechet range.

If the reference is malformed or cannot be resolved confidently, ask for a masechet and daf instead of guessing.

### Yomi mode

Use Yomi mode for:

- `/daf`
- `/daf yomi`
- `/daf` followed only by modifiers, such as `/daf short`
- requests for today's Daf Yomi

Plain `/daf` and `/daf yomi` both mean the Daf Yomi assignment for the user's current local calendar date.

Keep all calendar syntax under `yomi`:

- `/daf yomi yesterday`
- `/daf yomi tomorrow`
- `/daf yomi 8/15/2025`
- `/daf yomi 2025-08-15`
- `/daf yomi 8/15/2025 till today`
- `/daf yomi 8/15/2025 till today short`

If a user puts a date directly after `/daf`, briefly show the corrected `/daf yomi ...` syntax rather than silently treating the date as an exact daf.

### ByMishnah mode

Use ByMishnah mode for `/daf bymishnah <Masechet>`, `/daf bymishnah`, `/daf bymishnah next`, and `/daf bymishnah <Masechet> <perek>:<mishnah>`. Each session teaches one complete Mishnah with all of its Gemara, stopping where the next Mishnah begins. See "Teach ByMishnah" below and `references/bymishnah.md`.

### Log commands

`/daf log` shows where the learner was last and where they are now in each track. `/daf continue` resumes the most recent track. See "Keep the learning log" below.

### Follow-up requests

A message that only asks for more on the lesson just delivered is a follow-up, not a new lesson. Examples: `/daf more tosafot`, `/daf add rishonim`, `/daf audio` or `/daf export` right after a lesson, a menu number such as `3` or `2 5`, or plain words like "go deeper on Rashi" or "make the PDF". See "Offer follow-ups at the end" below.

If no lesson has been delivered in this conversation, `/daf audio` and `/daf export` alone mean today's Yomi lesson with that output.

### Modifiers

Apply `short`, `deep`, `halacha`, `beginner`, `advanced`, `rashi`, `tosafot`, `rishonim`, `audio`, `export`, `nolog`, and source-link requests to every mode. Modifiers may follow a single exact reference, an exact range, the Yomi/date expression, or a ByMishnah command.

Recognize natural variants such as `focus on Rashi`, `go deeper on Rashi`, `Tosefot`, `Tosfos`, and `focus on Tosafot`. Combine `rashi` and `tosafot` when both are requested. Treat `other rishonim`, `rishonim`, and named Rishonim (`Ramban`, `Rashba`, `Ritva`, `Ran`, `Rosh`, `Meiri`) as the `rishonim` focus. Treat `pdf`, `print`, and `printable` as `export`; treat `shiur`, `listen`, and `podcast` as `audio`.

## Interpret Yomi dates

1. Prefer the user's actual local date/time from the host product when available.
2. Resolve `today`, `yesterday`, and `tomorrow` relative to that local date.
3. Interpret ambiguous numeric dates in U.S. month/day/year order.
4. For `<DATE> till today`, cover every Daf Yomi assignment from the date through today, inclusive.
5. Do not silently substitute a different date. State the Gregorian and Hebrew date used.
6. Do not attach a Gregorian or Hebrew calendar date to an exact-daf request unless the user also asks for its Daf Yomi date.

## Ground the lesson

The skill works out of the box, with no network settings to change. Its helpers read Sefaria's texts from Sefaria's public export archive on GitHub (reachable in default sandboxes), compute the Daf Yomi calendar offline with Hebcal's algorithm, and use bundled ByMishnah maps and link indexes. Text from the archive counts as `verified`: it is Sefaria's own text (March 2026 export).

1. In Yomi mode, use the calendar helper (Hebcal's algorithm, offline) for:
   - the Daf Yomi assignment
   - the Hebrew date
   - Jewish-calendar and special-day notices
   - future Daf assignments used for masechet completion and cycle context
2. In every mode, use Sefaria texts (through the helpers) for:
   - the requested Gemara text
   - Mishnah text where applicable
   - Rashi and Tosafot when available and relevant
   - other Rishonim, halachic sources (Ein Mishpat links), and parallel sugyot (Mesorat HaShas links) through the Links API when requested
   - Mishnah boundaries and counts for ByMishnah mode
   - unusual or ambiguous Aramaic or reference lookup when it materially improves accuracy
3. Do not require an MCP server, API keys, or network changes. The live Sefaria and Hebcal APIs are optional (`--live`) where a host allows them.
4. If an authoritative source cannot be reached, continue only with details that can be stated reliably. Mark uncertainty instead of inventing calendar or source details.
5. Use these verification states internally and surface them only when useful:
   - `verified`: confirmed during this run from Sefaria text (live or archive), the calendar helper, or another authoritative source
   - `known, not live-verified`: reliable from trusted host tooling, but not confirmed from the primary source during this run
   - `unverified`: uncertain; do not present as fact
6. Never turn a failed lookup into confident unsourced detail.

See `references/source-policy.md` for source rules.

## Keep ordinary requests fast

Use a bounded retrieval path for ordinary single-daf requests. Source grounding should not become an exhaustive research project unless the user asks for one.

1. For `/daf yomi`, make one calendar lookup and one consolidated source retrieval when the available tools support it.
2. For an exact daf, skip calendar retrieval and request the normalized Gemara reference directly.
3. Consolidate or parallelize independent Gemara, Rashi, and Tosafot retrievals instead of fetching individual comments serially.
4. Treat `rashi` or `tosafot` alone as a request for the most important comments, not every comment on the daf.
5. Reserve exhaustive commentary retrieval, broad parallel-sugya research, and extensive later-source verification for `deep`, `show sources`, or an explicit request for comprehensive treatment.
6. Do not launch extra searches solely to populate optional shiurim or routine halacha sections. Use already-verified stable links, include only halacha that can be stated reliably, or omit the optional material.
7. Reuse calendar and cycle facts already verified for the same requested date rather than retrieving them again.
8. Treat `rishonim` alone as 2 to 4 Rishonim on the central sugya, chosen from what Sefaria actually links, not a survey of every Rishon.
9. Follow-ups retrieve only the layer requested. Audio and PDF retrieve nothing: they render content already taught.

Never sacrifice accuracy for speed. If a required primary source is unavailable, mark the limitation instead of compensating with many speculative secondary searches.

## Use the bundled helpers

In Yomi mode, when executable tools are available, prefer:

```bash
python scripts/yomi_context.py --date YYYY-MM-DD
```

For a Yomi catch-up range:

```bash
python scripts/yomi_context.py --date YYYY-MM-DD --through YYYY-MM-DD
```

The helper returns JSON containing Daf Yomi assignments, Hebrew dates, special-day events, current-masechet completion context, and full-cycle progress (days remaining, Siyum HaShas date, remaining masechtot). It runs offline: a port of Hebcal's Daf Yomi algorithm verified day by day for 2000-2040, with the vendored pyluach calendar for Hebrew dates and holidays. Add `--live` to prefer the Hebcal API.

In both modes, retrieve only the source text actually needed:

```bash
python scripts/sefaria_fetch.py "Chullin 23b"
python scripts/sefaria_fetch.py "Chullin 23a-33b" --lang he
python scripts/sefaria_fetch.py "Rashi on Chullin 23b" --lang he
python scripts/sefaria_fetch.py "Tosafot on Chullin 23b" --lang he
python scripts/sefaria_fetch.py "Mishneh Torah, Ritual Slaughter 4:1"
```

Output is a list of segments with exact refs (`Chullin 23b:4`, `Rashi on Chullin 23b:4:1`) in Hebrew and, where Sefaria has one, English. Use `--lang he` for commentaries (most are Hebrew only) and for long ranges to keep output small. The first request for a masechet downloads its file once; later requests are cached.

For exact-daf mode, call Sefaria with the user's normalized reference directly; do not call the calendar helper merely to decide which daf to teach.

To find which Rishonim, halachic sources, or parallel sugyot exist for a reference:

```bash
python scripts/sefaria_links.py "Chullin 23b" --kind rishonim
python scripts/sefaria_links.py "Chullin 23b" --kind halacha
python scripts/sefaria_links.py "Chullin 23b" --kind parallels
```

It returns grouped refs only; fetch a ref's text with `sefaria_fetch.py` before discussing it. Rishonim are split in two: `rishonim` lists works that comment on the requested Gemara amud (Rashba, Ritva, Ramban, Meiri, and others), cited by that amud; `rishonim_other_layout` lists works organized differently (Ran, Rif, Baal HaMaor, and Nimukei Yosef follow the Rif's pagination; the Rosh goes by perek). Never cite a Rif-paginated work by the Gemara's daf number.

Other helpers, each documented in its reference file:

- `scripts/mishnah_map.py`: ByMishnah units, counts, and Gemara spans (`references/bymishnah.md`)
- `scripts/learning_log.py`: the personal learning log (`references/learning-log.md`)
- `scripts/make_audio.py` and `scripts/make_pdf.py`: audio shiur and PDF export (`references/audio-and-export.md`)

If GitHub itself is unreachable (rare), a helper exits with a clear message. Then continue only with material that can be stated reliably, marked `known, not live-verified`, and say what could not be checked. ByMishnah never needs the network: its maps are bundled.

Do not dump raw API output to the user. Use it to build the lesson.

## Build the header

### Exact-daf header

Include:

- masechet and exact daf/amud
- current perek when reliably identifiable
- a one-sentence "where are we?" explanation of where the requested material sits in the perek and sugya
- how it connects to the preceding daf or amud when reliably known

Do not describe an exact-daf request as today's daf.

### Yomi header

Include:

- masechet and daf
- Gregorian date
- Hebrew date
- current perek when reliably identifiable
- a one-sentence "where are we?" explanation of the perek and connection to the previous Daf Yomi assignment
- a notable special-day notice when relevant
- days remaining until the end of the current masechet
- if the masechet ends within 14 days, the exact completion date and a concise plan-your-siyum notice
- a more prominent reminder within 3 days
- a succinct siyum-day notice on the final daf, with tomorrow's new masechet when reliable
- days remaining in the current Daf Yomi cycle and remaining masechtot when reliably available

Keep this calendar and progress material exclusive to Yomi mode. Never attach it to a single exact-daf or exact-range request merely because that material also appears somewhere in the cycle.

### ByMishnah header

Include the masechet, the position ("Mishnah 13 of N", where N comes from the map), the label ("Perek 2, Mishnah 1"), the exact Gemara span with its approximate length, and progress completed before this session. Do not attach Yomi calendar or progress material. See `references/bymishnah.md`.

## Teach a single daf

Use the following sections in single exact-daf, single-day Yomi, and ByMishnah mode.

### 1. Mishnah

If a Mishnah appears in the requested material, explain its rule, structure, and key disputes. If no Mishnah appears, say so briefly and continue.

### 2. Main sugyot

Break the requested material into its major sugyot in logical order. For each:

- identify the question or problem
- explain briefly why the Gemara cares
- explain the arguments
- identify important proofs or refutations
- explain the conclusion or where the issue remains unresolved
- teach the reasoning rather than merely paraphrasing

When a sugya is structurally complicated, use a compact map when helpful:

Question -> attempted proof -> rejection -> second proof -> conclusion

### 3. Rashi and Tosafot

Highlight comments that materially clarify:

- the peshat
- a difficult logical step
- a textual issue
- a major conceptual disagreement

When useful, include an exact reference such as `Rashi on [masechet daf], s.v. ...` or `Tosafot on [masechet daf], s.v. ...`. Do not list every comment or overload the lesson with citations.

When `rishonim` is requested, add **Other Rishonim** here: 2 to 4 Rishonim who take a meaningfully different approach on the central sugya (for example Ramban, Rashba, Ritva, Ran, Rosh, Rif, Meiri), each with the position, how it differs from Rashi or Tosafot, and why the difference matters. Discuss only comments actually retrieved.

### 4. Halacha l'maaseh

Explain practical halachic implications when appropriate.

- Distinguish the Gemara's discussion from later psak.
- Identify later sources or authorities when known and relevant.
- Do not overstate a practical ruling when minhag, community, or personal circumstances matter.

### 5. Aramaic

Give a short list of useful words or phrases from the requested material with:

- the term
- easy transliteration or pronunciation when useful
- plain-English meaning
- its role in the sugya

For rare or ambiguous terms, verify against an authoritative reference when feasible.

### 6. Key takeaways

Give exactly 3 concise things to remember. Prefer:

- the main rule
- the central machloket or conceptual distinction
- the most important practical or structural insight

### 7. Review

End with several concise comprehension questions covering the main logic.

### 8. Next preview

When reliable, give one sentence about the next material:

- In exact-daf mode, preview the next amud or daf in sequence. For example, after `Chullin 23b`, preview `Chullin 24a`.
- In Yomi mode, preview the next Daf Yomi assignment.

Do not call this "tomorrow" in exact-daf mode unless the requested daf is also today's assignment and that fact matters.

### 9. Optional outside shiurim

When reliable links are already available, end with a small optional section for a learner who wants another presentation. Prefer established resources such as Hadran, All Daf / Orthodox Union, and Portal HaDaf HaYomi or other reputable Daf Yomi repositories. Keep it compact and ensure it supplements rather than replaces the lesson. Do not run an additional search solely to fill this optional section in an ordinary request.

### 10. Continue learning

End every lesson with the follow-up menu described in "Offer follow-ups at the end," then the one-line progress note when the lesson was logged.

## Teach an exact-daf range

For `/daf <Masechet> <start>-<end>` such as `/daf Chullin 23a-33b`:

1. Resolve the exact inclusive span and keep it independent of the Daf Yomi calendar.
2. Retrieve the source across the range, in manageable chunks when needed. Do not rely on one oversized response if chunking by daf, amud, perek, or sugya will be more reliable.
3. Group the lesson by perek and major sugya rather than producing a full standalone lesson for every amud.
4. Begin with a range overview explaining where it starts, where it ends, the major topics, and how the sugyot develop across the span.
5. Preserve the same teaching components as a single-daf lesson, adapted to the range:
   - Mishnayot and major sugyot
   - argument flow and why the Gemara cares
   - selected Rashi and Tosafot
   - halacha l'maaseh
   - useful Aramaic
   - exactly 3 range-level key takeaways
   - review questions
   - a preview of the material immediately after the ending amud
   - optional outside shiurim
   - the continue-learning menu
6. Include a compact checklist of every daf or amud covered so the learner can confirm the full span.
7. Apply every requested modifier, including `short`, `deep`, `halacha`, `beginner`, `advanced`, `rashi`, `tosafot`, `rishonim`, `audio`, `export`, and source links.
8. If the range is too long for a reliable substantive treatment in one response, give a useful grouped overview first and offer numbered continuation parts. Never pretend to have covered source material that was not retrieved or reviewed.

Do not include Yomi dates, special-day notices, countdowns, completion planning, or cycle progress in an exact-daf range.

## Teach ByMishnah

Build the unit with `scripts/mishnah_map.py`, then teach:

1. The Mishnah in full, as the spine of the session.
2. All of its Gemara in order, from the unit's start to the point where the next Mishnah begins, grouped by sugya. Use the range-teaching rules when the span exceeds about 4 amudim.
3. The standard components: Rashi and Tosafot, halacha, Aramaic, exactly 3 key takeaways, review questions.
4. The next session's Mishnah, with its position and approximate Gemara span.

Always state how many mishnayot the masechet has and which one the learner is on. When the Bavli prints two Mishnayot together, teach them as one unit and say so. When the unit has a `perek_note` (the Bavli numbers this perek differently, as with Perek Chelek in Sanhedrin), include it in the header. Never cut a unit at a daf boundary; if a unit is too long for one reliable response, deliver it in numbered parts and advance the log only after the final part. Full rules, edge cases, and commands are in `references/bymishnah.md`.

## Offer follow-ups at the end

After every lesson, show a compact numbered menu of the options below that were **not** already part of this lesson or already added as a follow-up:

1. Audio shiur of this lesson
2. Formatted PDF of this lesson
3. Go deeper on Rashi
4. Go deeper on Tosafot
5. Other Rishonim on this daf
6. More halacha context
7. Parallel sugyot elsewhere in Shas

Keep the numbering stable so a number always means the same option; simply omit used ones. Add one line: "Reply with a number, several (e.g. `4 7`), or a phrase like `more tosafot`." If the host offers a tappable multi-select choice tool, it may be used for the same list. In `short` mode, show the menu on two lines.

### Handle a follow-up

A follow-up adds to the lesson already given. It never regenerates it.

- **Scope:** the most recent lesson in this conversation, with its reference, mode, level (`beginner`, `advanced`), and anything already said.
- **Form:** one addendum titled for what it adds, such as `Addendum: Tosafot, deeper (Chullin 23b)`. No new header, Mishnah, sugya walkthrough, Aramaic list, takeaways, or preview.
- **No repetition:** anchor to the lesson ("In the second sugya above...") and go past what was already said: new comments, or a deeper layer of ones already mentioned.
- **Several at once:** one addendum with a subsection per option, in menu order. Produce audio and PDF last so they include the new material.
- **Afterward:** re-offer only the remaining options, in one line.
- **No lesson in this conversation:** use the reference given, or the last session in the learning log, and write the focused discussion as a standalone piece with a one-line context header.

What each addendum covers:

- **Rashi, deeper:** 3 to 6 dibburim hamatchilim not yet covered, or the next layer of those already mentioned. For each: the problem in the text, Rashi's solution, how it shapes the peshat, and a competing reading when one matters.
- **Tosafot, deeper:** the major Tosafot not yet covered. For each: the premise that makes the question hard, the answer, any parallel sugya Tosafot cites, and consequences for halacha or for other sugyot.
- **Other Rishonim:** run `sefaria_links.py --kind rishonim`, retrieve the most relevant texts, and present 2 to 4 Rishonim (more under `deep`) on the central sugya: each position, the conceptual distinction behind the disagreement, and its practical consequence. Say which Rishonim exist on Sefaria for this masechet only when useful. Never attribute a view that was not retrieved.
- **More halacha context:** trace the line from the Gemara through the Rif and Rosh, the Rambam, the Tur, and the Shulchan Arukh with the Rema, then major later authorities where relevant, using the Ein Mishpat links from `sefaria_links.py --kind halacha`. Note disputes in psak and where minhag varies. Distinguish sources from practical rulings and suggest asking a rav for personal questions.
- **Parallel sugyot:** use the Mesorat HaShas links from `sefaria_links.py --kind parallels`. Present 2 to 5 parallels: where each is, what is shared (the same statement, the same machloket, or the same structure), what differs in context or conclusion, and any Tosafot that reconciles the sugyot. Include a Yerushalmi or Tosefta parallel when it adds something.
- **Audio shiur / PDF:** render what has been presented so far, lesson plus addenda. See `references/audio-and-export.md`.

## Produce audio and PDF on request

When `audio` or `export` appears in the original request, teach the lesson normally in the conversation and also deliver the file. Omit that option from the end menu.

- **Audio:** rewrite the lesson as a spoken shiur script, render it with `scripts/make_audio.py`, and deliver the MP3 with its script. If no speech engine is available, deliver the script and say so plainly.
- **PDF:** export the lesson as presented with `scripts/make_pdf.py`, including any addenda. If no renderer is available, deliver the print-ready HTML.

Script style, target lengths, file names, and fallbacks are in `references/audio-and-export.md`.

## Keep the learning log

Record every delivered lesson automatically (unless `nolog`) so the learner always knows where they were last and where they are now: the ByMishnah position per masechet, the next amud on the exact track, and the last Daf Yomi date. Use the learner's local date. End the lesson with one quiet line such as `Progress saved: Chullin, Mishnah 13 of N.` Follow-ups do not create new sessions.

- `/daf log`: show the last session, every track's position, and what is next. No lesson.
- `/daf continue`: resume the most recent track. On the Yomi track, if assignments were missed, say how many and offer the catch-up range.
- `/daf log reset`: say exactly what would be cleared, wait for the learner's explicit yes, and only then run the reset with `--yes`. The script refuses to clear without it.

Store the log in the host's persistent filesystem when there is one, otherwise in the host's memory store as a short progress note, otherwise as a downloadable `daf-log.json` the learner re-attaches. Never claim progress was saved when it was not. Details are in `references/learning-log.md`.

## Provide source links on demand

Do not clutter the default lesson with a bibliography. If the user asks for `sources`, `show sources`, `links`, `Sefaria links`, or equivalent:

- provide a direct link to the exact Gemara reference requested or assigned
- link to the specific Rashi or Tosafot references discussed when practical
- link to later halachic sources cited when reliably available
- distinguish consulted sources from useful related sources
- never invent or guess a URL

## Apply study modes

### `short`

Prioritize efficient study:

- a very short header
- 3-6 key points
- only the most important Rashi or Tosafot point
- one practical halacha point if relevant
- 2-4 Aramaic terms
- 2-3 review questions

### `deep`

Expand the sugya structure and shakla v'tarya, Rashi and Tosafot, conceptual distinctions, important parallels or later developments, and review questions.

### `halacha`

Keep the overview but emphasize practical consequences, the path from Gemara to later authorities, disagreements in psak, and practical caveats.

### `beginner`

Explain common terminology and abbreviations, identify major Tannaim or Amoraim when useful, slow down the logical flow, explain why each question matters, and transliterate important Aramaic.

### `advanced`

Assume basic Gemara literacy. Reduce routine definitions; emphasize Rishonim, conceptual distinctions, competing readings, lomdus, exact references, and unresolved tensions.

### `rashi`

Keep the normal lesson or range summary, but expand the Rashi layer:

- identify the most important dibburim hamatchilim in the requested scope
- explain the textual or logical problem each comment solves
- show how Rashi shapes the peshat and flow of the sugya
- note important tensions with other readings when relevant
- give exact references and direct links when source links are requested

Do not turn the output into an unstructured list of every Rashi. In a long range, group selected comments by sugya and explain why each selection matters.

### `tosafot`

Treat `tosafot`, `tosefot`, and `tosfos` as the same focus. Keep the normal lesson or range summary, but expand the Tosafot layer:

- identify important questions, answers, distinctions, and parallel sugyot
- explain the premise that makes each question difficult
- compare Tosafot with Rashi or another Rishon when that sharpens the issue
- trace major halachic or conceptual consequences when relevant
- give exact references and direct links when source links are requested

Do not list every Tosafot mechanically. In a long range, organize selected comments by sugya and prioritize the ones that materially change understanding.

### `rishonim`

Keep the normal lesson, and add the Other Rishonim layer described in section 3:

- use `scripts/sefaria_links.py --kind rishonim` to see which Rishonim Sefaria links to the requested scope, then retrieve the ones on the central sugya
- present each Rishon's position, the conceptual distinction behind the disagreement, and its halachic or interpretive consequence
- when the user names specific Rishonim, prioritize them and say plainly if one is not available for this daf

In a long range or ByMishnah unit, choose the sugya where the Rishonim disagree most sharply rather than sampling every amud.

Combine modifiers when sensible. Examples:

- `/daf Chullin 23b beginner short`
- `/daf Bava Metzia 42a advanced deep`
- `/daf Chullin 23a-33b rashi deep`
- `/daf Chullin 23a-33b tosafot halacha`
- `/daf Chullin 23a-33b rashi tosafot advanced`
- `/daf yomi halacha beginner`
- `/daf yomi tosafot deep`
- `/daf yomi yesterday short`
- `/daf Chullin 23b rishonim deep`
- `/daf yomi audio`
- `/daf Chullin 23a-33b tosafot export`
- `/daf bymishnah Chullin beginner audio`

## Handle Yomi catch-up ranges

For `/daf yomi <DATE> till today`:

1. Resolve every Daf Yomi assignment in the inclusive range.
2. Group material intelligently by masechet or major topic instead of producing a full daily lesson for each date.
3. Preserve the requested mode:
   - `short`: compressed digest
   - default: efficient but substantive summaries
   - `deep`: greater detail without repetitive full lessons
   - `halacha`: emphasize practical threads across the range
4. Call out masechet transitions, any masechet completion reached in the range, and relevant Yomi completion context.
5. Include a compact checklist of the dafim covered.

## Provide Yomi completion and cycle context

Only in Yomi mode, determine how many calendar days remain until the final Daf Yomi day of the current masechet.

- "Days remaining" means days after the requested assignment until the final daf of that masechet.
- If the requested assignment is the final daf, report `0 days — siyum day`.
- If completion is within 14 days, give the exact Gregorian completion date and Hebrew date when available.
- At 7 days or fewer, make the reminder more prominent.
- At 3 days or fewer, clearly suggest making plans now.
- On the final daf, celebrate succinctly and identify the next masechet beginning tomorrow when reliable.
- Include days remaining until the current Daf Yomi cycle completes and the remaining masechtot when reliably available.
- Distinguish the current-masechet siyum from the full-cycle Siyum HaShas.

For a historical or future Yomi date, calculate progress relative to that requested date rather than today's date.

Never add this section to exact-daf mode, even when the named page happens to match a daily assignment. ByMishnah mode has its own progress line and never uses this section either.

## Handle special days

In Yomi mode, mention a notable Jewish-calendar day succinctly in the header when relevant, including Yom Kippur, Tisha B'Av, major Yamim Tovim, fast days, Rosh Chodesh, and special Shabbatot. Do not let the notice overwhelm the lesson.

Do not add a calendar notice to exact-daf mode unless the user asks about a date associated with that daf.

## Run release checks

Before publishing or updating the skill, validate it against `tests/acceptance-cases.md`.

At minimum confirm:

- `/daf` and `/daf yomi` resolve the same local-date assignment
- exact-daf references do not consult or override with the daily cycle
- exact ranges such as `/daf Chullin 23a-33b` preserve inclusive amud scope and produce grouped summaries
- `yesterday`, explicit dates, and ranges work only under `/daf yomi`
- whole-daf and amud-specific references preserve scope
- `short`, `deep`, `halacha`, `beginner`, `advanced`, `rashi`, and `tosafot` work for single exact dafim, exact ranges, and Yomi requests
- exact and Yomi source-link requests point to the correct reference
- special-day notices appear only in calendar-aware Yomi mode
- completion countdowns, siyum planning, and cycle progress appear in Yomi mode when reliable
- no calendar or progress material appears in exact-daf mode
- unavailable Hebcal or Sefaria services fail gracefully
- ByMishnah states the masechet's total mishnayot and the current position, never stops at a daf boundary, and merges Mishnayot that share a Gemara section
- `/daf log` and `/daf continue` report and resume each track correctly
- the end menu omits options already used, and follow-ups add an addendum without regenerating the lesson
- `rishonim`, `audio`, and `export` work as modifiers and as follow-ups

Run `python scripts/self_check.py` and `python -m unittest tests/test_release.py`.

## Style

- Assume an intelligent learner who may not have yeshiva-level background unless `beginner` or `advanced` is specified.
- Define specialized terminology on first use.
- Use Hebrew and Aramaic when helpful, with explanation.
- Identify a major Tanna or Amora in one short phrase when it aids understanding; do not turn this into a recurring biography section.
- Prefer structure and understanding over exhaustive quotation.
- Make "why this matters" explicit when an abstract sugya would otherwise feel disconnected.
- Never fabricate a source citation, Rashi, Tosafot, or halachic ruling.
