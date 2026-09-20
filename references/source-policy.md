# Source policy

## Hebcal

Use Hebcal's calendar (computed offline by default) only for calendar-aware Yomi mode:

- Daf Yomi date assignment
- Hebrew date
- Jewish holiday, fast, Rosh Chodesh, and special-Shabbat context
- forward assignments used to determine masechet completion, the next masechet, and cycle progress

Do not use the current Daf Yomi assignment to replace or reinterpret an exact-daf request. Hebcal's public web APIs require no registration or API key. Attribute Hebcal when presenting data substantially derived from its API.

## Sefaria

Use Sefaria texts for source grounding in every mode, through `sefaria_fetch.py` (archive by default, live v3 Texts API with `--live`).

Use source retrieval selectively:

- Gemara: verify the exact daf or amud before summarizing it.
- Mishnah: retrieve the requested portion when it appears on the page.
- Rashi/Tosafot: retrieve the relevant commentary before discussing a specific comment.
- Aramaic: use reference or dictionary resources for unusual or ambiguous terms when feasible.

For exact-daf mode, preserve the user's requested scope. Do not silently expand `23b` to the entire daf or substitute today's assignment.

For an exact range such as `Chullin 23a-33b`, retrieve the inclusive range in reliable chunks when necessary. Verify every summarized sugya against material inside the requested boundaries. Do not attach Daf Yomi calendar or progress data to the range.

When `rashi` or `tosafot` focus is requested, retrieve the selected comments before explaining them. On a long range, prioritize comments that clarify a major textual, logical, conceptual, or halachic issue rather than claiming to exhaust every comment.

For `rishonim`, halacha context, and parallel sugyot, use Sefaria's Links API (`scripts/sefaria_links.py`) to learn which sources exist, then retrieve each text before discussing it. A link proves a source is connected to the daf, not what it says.

For ByMishnah, use Sefaria's Shape API for mishnayot per perek and its Links API (`mishnah in talmud` links) for where each Mishnah sits in the Bavli. Never estimate Mishnah boundaries from memory.

Audio and PDF exports render content already taught and do not add new source claims.

Do not reproduce long copyrighted translations. Summarize and quote only brief phrases when needed.

## Where the data comes from

The skill runs with no network configuration:

- **Texts**: Sefaria's public export archive on GitHub (`Sefaria/Sefaria-Export-Archive`, pinned to one commit, March 2026 export), read by `scripts/archive_source.py`. GitHub is reachable in default sandboxes where sefaria.org is not.
- **Daf Yomi calendar**: `scripts/offline_calendar.py`, a port of Hebcal's public-domain algorithm, verified against `@hebcal/learning` for every day from 2000 to 2040, plus the vendored pyluach library (MIT) for Hebrew dates and holidays.
- **ByMishnah maps and halacha/parallel link indexes**: prebuilt from Sefaria's data and bundled in `data/`.
- **Live APIs (optional)**: `--live` prefers the Sefaria or Hebcal API where a host allows it, falling back automatically.

To refresh the bundled data, a maintainer runs `tools/build_data.py`.

## Failure behavior

If network access fails:

1. Do not make up an API result.
2. If the requested reference or Yomi assignment can still be determined reliably from trusted host tools, continue.
3. Otherwise state which part could not be verified.
4. A failed Sefaria lookup does not automatically prevent a lesson if the underlying text is reliably available another way.
5. A failed Hebcal lookup affects Yomi calendar resolution, not a valid exact-daf request.
