# Audio shiur and PDF export

Both outputs are renderings of content that has already been taught. Neither one re-retrieves sources or changes the substance of the lesson.

## Audio shiur (`audio`)

Triggers: the `audio` modifier (`/daf Chullin 23b audio`, `/daf yomi audio`, `/daf bymishnah audio`), or the audio option from the end-of-lesson menu. Treat `shiur`, `audio shiur`, `listen`, and `podcast` as the same request.

### Write the spoken script

Rewrite the lesson for the ear, as a maggid shiur would deliver it. Save it as `<Ref>_shiur.txt` and deliver it with the audio.

- Open warmly and orient: "Welcome to the shiur on Chullin, daf twenty-three, amud bet. We're in the second perek, and today's question is..."
- Walk the Mishnah, then each sugya with spoken signposts: "The Gemara's first question is...", "Now Rashi steps in here, because...", "Here's the twist."
- Turn visual structures into speech. A map like Question -> proof -> rejection becomes "The Gemara asks, tries a proof, rejects it, and lands on..."
- Include the halacha, the three takeaways, and the review questions. After each question write `[pause]` on its own line so the listener can think.
- Close with the preview of the next material and a short sign-off.
- Keep sentences short. No tables, bullet lists, checklists, URLs, or citations by line number.
- Write no Hebrew script. English voices cannot read it; use transliteration ("hakol shochatin"), then say what it means.
- Include any addenda the learner has already added, in the order they were added.

Target length: default about 12 to 20 minutes (roughly 1,800 to 3,000 words); `short` about 5 to 8 minutes; `deep` up to about 30 minutes; a follow-up addendum on its own, 3 to 8 minutes.

### Render it

```bash
python scripts/make_audio.py <Ref>_shiur.txt --out <Ref>_shiur.mp3 --title "<Ref> shiur" --install
```

- `--install` lets the script install the free neural voice (pip `piper-tts` plus a voice model from the Piper project's GitHub releases) when the environment allows. Omit it where installs are not appropriate.
- `--voice ryan` gives a different voice; `--rate 0.9` slows delivery.
- The script falls back to `espeak-ng`, then macOS `say`. It applies a pronunciation lexicon for common learning terms and masechet names; add more with `--lexicon extra.json`.
- Exit code 4 means no speech engine is available: deliver the written script, say plainly that audio could not be generated here, and name what is missing.

Deliver the MP3 and the script file through the host's file-delivery mechanism. Report the length in minutes and the voice used in one line. Mention once, briefly, that pronunciation of Hebrew and Aramaic terms is approximate with a synthetic voice.

## PDF export (`export`)

Triggers: the `export` modifier or the PDF option in the menu. Treat `pdf`, `export pdf`, `print`, and `printable` as the same request.

### Assemble the Markdown

Use the lesson exactly as presented in the conversation, plus any addenda, each preceded by a line `<!-- addendum -->`. Omit the end-of-lesson menu and the progress-saved line. Keep Hebrew as Hebrew; the renderer sets it right-to-left.

### Render it

```bash
python scripts/make_pdf.py lesson.md --out <Ref>_daf.pdf \
  --title "Chullin 23b" --subtitle "Perek 2 · <perek name or theme>" \
  --meta "Exact daf" --meta "Rashi · Tosafot · Rishonim"
```

Meta chips by mode:

- Exact daf or range: `Exact daf` or `Range: 23a-33b (22 amudim)`
- Yomi: `Daf Yomi`, the Gregorian and Hebrew dates
- ByMishnah: `Mishnah 13 of N`, `Perek 2, Mishnah 1`

File names: `Chullin_23b_daf.pdf`, `Chullin_23a-33b_daf.pdf`, `Chullin_Mishnah_13_of_N.pdf`, `Daf_Yomi_Chullin_122.pdf`.

The script uses wkhtmltopdf, Chrome/Chromium, or WeasyPrint, and stamps page numbers when pypdf and reportlab are present. Exit code 4 means no renderer exists: deliver the print-ready HTML it wrote and explain that it can be printed to PDF from a browser.

## Both at once

When both are requested, write any new addendum first, then produce the PDF and the audio from the same final content.
