# Personal learning log

The log answers two questions for the learner: where was I last, and where am I now. It tracks three independent positions:

- **ByMishnah**: per masechet, mishnayot completed out of the total, last unit, next unit, any unit in progress
- **Exact track**: last daf or range studied and the next amud in sequence
- **Daf Yomi**: last assignment studied and its date

It also keeps a capped history of sessions.

## Commands

| Command | Behavior |
|---|---|
| `/daf log` (also `/daf progress`, `/daf where am i`) | Show last session, every track's position, and what is next. No lesson. |
| `/daf continue` | Resume the most recently used track: next ByMishnah unit, next exact amud, or today's Yomi daf |
| `/daf log reset` | Say what would be cleared, wait for an explicit yes, then run with `--yes`. `/daf log reset Chullin` clears one ByMishnah masechet |
| `nolog` modifier | Teach without recording, e.g. `/daf Chullin 23b nolog` |

For `/daf continue` on the Yomi track, if the last Yomi session was more than one day ago, say how many assignments were missed and offer `/daf yomi <date> till today`.

## When to record

Record every delivered lesson automatically unless `nolog` is present. Using this skill is the learner's standing request for tracking. End the lesson with one quiet line, such as `Progress saved: Chullin, Mishnah 13 of N.` Follow-up deepening, audio, and PDF do not create new sessions.

Always pass the learner's **local** date (`--date YYYY-MM-DD`); the container clock may be in another timezone.

## Where the log lives

Use the first option the host supports:

1. **Persistent filesystem** (Claude Code, Cowork, a local agent): `scripts/learning_log.py`, stored at `$DAF_LOG` or `~/.daf/learning-log.json`. Cache ByMishnah maps in `~/.daf/maps`.
2. **Host memory store** (for example Claude's memory in claude.ai, where the container resets): keep one short Daf progress note in the memory store and update it after each lesson. Follow that store's own formatting rules. Put in it only the summary lines that `learning_log.py summary` would print: last session, each ByMishnah masechet's position and next unit, exact-track next amud, last Yomi date. Read it at the start of any log-aware command (`/daf log`, `/daf continue`, `/daf bymishnah`). When scripts need the JSON log in that session, rebuild it from the note first.
3. **Neither**: at the end of the lesson, offer the updated `daf-log.json` as a downloadable file and ask the learner to attach it next time. Also accept a plain statement ("I'm up to Chullin 2:3") as the current position.

Never claim progress was saved when it was not.

## Script reference

```bash
python scripts/learning_log.py summary
python scripts/learning_log.py show                       # full JSON
python scripts/learning_log.py record --mode exact --ref "Chullin 23b" --next "Chullin 24a" --date 2026-09-19
python scripts/learning_log.py record --mode range --ref "Chullin 23a-33b" --next "Chullin 34a" --date 2026-09-19
python scripts/learning_log.py record --mode yomi --ref "Chullin 122" --date 2026-08-30
python scripts/learning_log.py record --mode bymishnah --masechet Chullin --unit 13 --seq-end 13 \
    --total <N> --label "Perek 2, Mishnah 1" --ref "Chullin 27b-32a" --date 2026-09-19 [--partial 1/3]
python scripts/learning_log.py activate --masechet Chullin
python scripts/learning_log.py reset --track bymishnah --masechet Chullin        # dry run, exits 6
python scripts/learning_log.py reset --track bymishnah --masechet Chullin --yes  # after the learner confirms
```

## `/daf log` output

```
Where you were last: Sep 18, ByMishnah Chullin, Perek 2, Mishnah 1 (Chullin 27b-32a)

Where you are now
- ByMishnah Chullin: 13 of N mishnayot. Next: Perek 2, Mishnah 2
- Exact track: last Berakhot 2a. Next: Berakhot 2b
- Daf Yomi: last Chullin 122 on Aug 30

Continue with /daf continue, or /daf bymishnah
```

Keep it this compact.
