# ByMishnah mode

> Every count, perek label, and Gemara span in this file is a placeholder that shows format only. Always take real values from `mishnah_map.py` (Sefaria data); never repeat an example number as fact.

Learn a Bavli masechet one complete Mishnah per session, with all of the Gemara that belongs to it. A session ends where the next Mishnah begins, never at an arbitrary daf boundary, so it can be shorter or longer than a daf.

## Commands

| Command | Meaning |
|---|---|
| `/daf bymishnah Chullin` | Start Chullin, or resume it at the next unlearned Mishnah if the log has progress |
| `/daf bymishnah` or `/daf bymishnah next` | Continue the active ByMishnah masechet |
| `/daf bymishnah Chullin 3:2` | Jump to Perek 3, Mishnah 2; later sessions continue from there |
| `/daf bymishnah status` | Show position only, no lesson |
| `/daf bymishnah Chullin restart` | Reset that masechet's progress after the learner confirms (`reset ... --yes`) |

Treat `by mishnah`, `mishnah by mishnah`, `bymishna`, and `ByMishnah` as the same command. All study and output modifiers apply (`short`, `deep`, `beginner`, `advanced`, `halacha`, `rashi`, `tosafot`, `rishonim`, `audio`, `export`, `show sources`).

If no masechet is given and the log has no active ByMishnah masechet, ask which masechet to start.

## Build the map

```bash
python scripts/mishnah_map.py Chullin --find 3:2          # unit containing a Mishnah
python scripts/mishnah_map.py Chullin --unit 13           # a unit by learning order
python scripts/mishnah_map.py Chullin --cache ~/.daf/maps # whole map, cached
```

The map lists every Mishnah in the order it appears in the Bavli, with:

- `position`: "Mishnah 13 of N" (learning order) and `total_mishnayot`
- `label`: "Perek 2, Mishnah 1" (standard Mishnah numbering)
- `gemara_span`: exact start and stop, e.g. "Chullin 27b:3 through Chullin 32a:2"
- `fetch_ref`: the amud range to retrieve, e.g. "Chullin 27b-32a"
- `amudim`: approximate length
- `next_unit`: tomorrow's Mishnah and span

Retrieve `fetch_ref` with `sefaria_fetch.py`, then teach only from `bavli_start` up to the stop point. Material before the start or after the stop belongs to neighboring Mishnayot.

The script recognizes masechet names and common spellings (`Brachos`, `Kesubos`, `Chulin`). It exits 2 for an unrecognized name (ask; never guess) and 3 for a tractate with no Bavli Gemara.

Maps for all 37 Bavli masechtot are bundled in `data/mishnah_maps.json` (built from Sefaria's data by `tools/build_data.py`), so this works offline. `--live` rebuilds a map from the Sefaria API where a host allows it.

## Edge cases the map already handles

- **Shared Gemara.** When the Bavli prints two Mishnayot together with no Gemara between them, they form one unit ("Mishnayot 13-14 of N"). Say so in the header.
- **Bavli order differs.** Some masechtot arrange perakim differently in the Bavli (in the bundled data: Megillah, Sanhedrin, and Menachot). The learning order follows the Bavli; the label keeps standard Mishnah numbering. Each unit carries `bavli_perek` and, when the two numberings differ, a ready-made `perek_note` ("The Bavli prints this as Perek 11 of Sanhedrin..."). Whenever `perek_note` is present, put it in the header.
- **Mishnah with no Bavli Gemara.** Units with `mishnah_only: true` are taught as a Mishnah lesson (text, structure, classic explanation such as Bartenura when retrieved) and labeled "No Bavli Gemara on this Mishnah."
- **Masechet with no Bavli.** If the script exits 3 (for example Peah, Shekalim, Middot), explain that ByMishnah needs a Bavli masechet and offer an exact-daf or Mishnah-only alternative.

## Header

```
Chullin · Mishnah by Mishnah
Mishnah 13 of N · Perek 2, Mishnah 1
Gemara: Chullin 27b:3 through 32a:2 (about 5 amudim)
Progress: 12 of N complete before today
```

Add one line when relevant: shared-Gemara unit, Bavli order note, a mid-perek start, or the first Mishnah of a new perek (name the perek). Do not add Daf Yomi dates, countdowns, or cycle progress.

## Teach the unit

1. **The Mishnah in full.** It is the spine of the session: translate or paraphrase closely, show its structure, and name the disputes.
2. **The Gemara on it, in order.** Group by sugya. Show how each sugya grows out of a word or problem in the Mishnah. Use the range-teaching rules when the span exceeds about 4 amudim.
3. The standard components: Rashi and Tosafot, halacha l'maaseh, Aramaic, exactly 3 key takeaways, review questions.
4. **Next session preview.** One sentence: "Next: Mishnah 14 of N (Perek 2, Mishnah 2), Gemara about 32a to 33b."

### Very long units

Some Mishnayot carry many dafim of Gemara. Teach the whole unit. If it cannot be covered reliably in one response, split it into numbered parts ("Part 1 of 3") at sugya boundaries, deliver Part 1 now, and log the unit with `--partial 1/3`. The unit counts as complete, and the position advances, only when the final part is delivered. `/daf bymishnah` resumes the next part.

### Finishing the masechet

On the final unit, celebrate the siyum succinctly, report the total mishnayot and sessions from the log, suggest the traditional Hadran, and offer to start another masechet.

## Logging

After the lesson, record it (see `references/learning-log.md`):

```bash
python scripts/learning_log.py record --mode bymishnah --masechet Chullin \
  --unit 13 --seq-end 13 --total <N> --label "Perek 2, Mishnah 1" \
  --ref "Chullin 27b-32a" --date <user's local date>
```

If the learner runs ByMishnah twice in one day, teach the next unit and note it is an extra Mishnah today.
