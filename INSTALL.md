# Installing Daf

Daf is a set of instructions and small Python scripts. It needs no account, API key, or network settings.

Two files are published with each release:

- `daf.skill` for Claude (a zip file with a different extension)
- the source zip, for everything else

Use `daf.skill` for Claude where you can. The two archives have the same structure (a single `daf` folder holding `SKILL.md`), so renaming a copy of the source zip to `daf.skill` should also work; it just carries extra files that Claude does not need, such as the tests and the checklist.

## Claude (web or desktop app)

1. Download `daf.skill` from the Releases page.
2. In Claude, open Settings and find the Skills section (under Capabilities).
3. Upload `daf.skill`.
4. Start a new chat and type `/daf yomi`.

Menu names move between versions. If you cannot find Skills, search Claude's help site for "skills" or ask Claude in the app where to upload a skill.

## Claude Code, Cowork, or another local agent

Unzip the source zip and put the folder where your agent looks for skills, keeping `SKILL.md` at the top of the folder:

```bash
unzip daf-v3.1.1-github.zip
mkdir -p ~/.claude/skills
cp -R daf ~/.claude/skills/daf
```

Then start a session and type `/daf yomi`. In these environments the progress log is a file at `~/.daf/learning-log.json`, so it carries over between sessions on its own.

## ChatGPT

ChatGPT has no skills system, so Daf runs there as a project with the instructions attached.

1. Unzip the source zip.
2. Create a new Project in ChatGPT and name it Daf.
3. Upload these files to the project: `SKILL.md`, everything in `references/`, and, if you want mishnah-by-mishnah learning, `data/mishnah_maps.json`.
4. In the project's instructions, paste: "Follow the attached SKILL.md exactly when I use /daf commands or ask to learn a daf, a mishnah, or the Daf Yomi."
5. Start a chat in that project and type `/daf yomi`.

What works and what does not:

- **Teaching, structure, follow-ups, and study modes** work, since these are instructions.
- **Daf Yomi dates** rely on ChatGPT's own knowledge or its web search, not the bundled calculator, so confirm the date before relying on it.
- **Live Sefaria text** depends on ChatGPT's browsing, since its code tool has no internet access.
- **Audio shiurim and PDF export** do not work; those need the bundled scripts to run with network access.
- **The progress log** does not save itself. Ask for your position at the end of a session and paste it back next time, or keep it in the project's instructions.

## Other agents

Any agent that can read a folder of instructions can use Daf. Point it at `SKILL.md`; the scripts in `scripts/` are plain Python 3 with no installed dependencies. Audio generation is the one exception: it installs a speech package on first use.

## Checking it works

```
/daf yomi
```

You should get today's Daf Yomi assignment with its Hebrew date and a full lesson. Then try `/daf Chullin 23b`, `/daf bymishnah Berakhot`, and `/daf log`.
