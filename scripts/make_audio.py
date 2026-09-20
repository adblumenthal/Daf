#!/usr/bin/env python3
"""
Render a spoken shiur script to audio (MP3 when ffmpeg is present, else WAV).

Examples:
  python scripts/make_audio.py shiur.txt --out Chullin_23b_shiur.mp3 --title "Chullin 23b"
  python scripts/make_audio.py shiur.txt --out shiur.mp3 --engine piper --install
  python scripts/make_audio.py shiur.txt --prepare-only     # print the TTS-ready text

Engines, tried in order with --engine auto:
  piper   neural voice (pip package piper-tts + a voice model; --install fetches both)
  espeak  espeak-ng / espeak (robotic but offline)
  say     macOS built-in voice
If none is available the script exits 4 and leaves the prepared script, so the
agent can deliver the written shiur and explain what is missing.

Paragraphs are separated by blank lines. A line containing only [pause] adds a
longer pause. Hebrew-script characters are removed (English voices cannot read
them), so the script should already use transliteration.
"""

# Created by Adam Blumenthal in honor of David and Barbara Blumenthal,
# who always pushed him to keep asking questions.

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import wave
from pathlib import Path

VOICES = {
    "lessac": "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-lessac-medium.tar.gz",
    "ryan": "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-ryan-medium.tar.gz",
}
VOICE_DIR = Path(os.environ.get("DAF_VOICE_DIR", "~/.cache/daf/voices")).expanduser()

# Respellings that help English voices pronounce common learning terms.
LEXICON = {
    "gemara": "geh-mah-rah", "mishnah": "mish-nah", "mishnayot": "mish-nah-yote",
    "mishna": "mish-nah", "Rashi": "Rah-shee", "tosafot": "toe-sah-fote",
    "tosefot": "toe-sah-fote", "tosfos": "toss-fuss", "tosefta": "toe-sef-tah",
    "sugya": "soog-yah", "sugyot": "soog-yote", "sugyos": "soog-yose",
    "daf": "dahf", "dafim": "dah-feem", "amud": "ah-mood", "amudim": "ah-moo-deem",
    "perek": "peh-rek", "perakim": "peh-rah-keem", "masechet": "mah-seh-khet",
    "masechta": "mah-sekh-tah", "masechtot": "mah-sekh-tote",
    "halacha": "hah-lah-khah", "halachic": "hah-lah-khic", "halakha": "hah-lah-khah",
    "l'maaseh": "l'mah-ah-seh", "machloket": "makh-lo-ket", "machlokes": "makh-lo-kess",
    "rishonim": "ree-show-neem", "rishon": "ree-shone", "acharonim": "ah-khah-row-neem",
    "Rambam": "Rahm-bahm", "Ramban": "Rahm-bahn", "Rashba": "Rahsh-bah",
    "Ritva": "Reet-vah", "Rif": "Reef", "Rosh": "Roesh", "Ran": "Rahn", "Meiri": "May-ree",
    "Rashbam": "Rahsh-bahm", "Raavad": "Rah-ah-vahd", "Chananel": "Khah-nahn-el",
    "tanna": "tah-nah", "tannaim": "tah-nah-eem", "amora": "ah-more-ah",
    "amoraim": "ah-more-ah-eem", "bavli": "bahv-lee", "yerushalmi": "yeh-roo-shahl-mee",
    "shas": "shahss", "Chazal": "Khah-zahl", "beraita": "beh-rye-tah", "baraita": "bah-rye-tah",
    "kashya": "kahsh-yah", "teiku": "tay-koo", "peshat": "peh-shaht", "pshat": "p'shaht",
    "lomdus": "lom-duss", "siyum": "see-yoom", "shakla": "shahk-lah", "v'tarya": "veh-tar-yah",
    "Chullin": "Khoo-leen", "Berakhot": "Beh-rah-khote", "Berachot": "Beh-rah-khote",
    "Shabbat": "Shah-baht", "Eruvin": "Eh-roo-veen", "Pesachim": "Peh-sah-kheem",
    "Yoma": "Yo-mah", "Sukkah": "Soo-kah", "Beitzah": "Bay-tsah", "Taanit": "Tah-ah-neet",
    "Megillah": "Meh-gee-lah", "Chagigah": "Khah-gee-gah", "Yevamot": "Yeh-vah-mote",
    "Ketubot": "Keh-too-bote", "Nedarim": "Neh-dah-reem", "Nazir": "Nah-zeer",
    "Sotah": "So-tah", "Gittin": "Gee-teen", "Kiddushin": "Kee-doo-sheen",
    "Kamma": "Kah-mah", "Metzia": "Mets-ee-ah", "Batra": "Bahs-rah", "Bava": "Bah-vah",
    "Sanhedrin": "Sahn-hed-reen", "Makkot": "Mah-kote", "Shevuot": "Sheh-voo-ote",
    "Avodah": "Ah-vo-dah", "Zarah": "Zah-rah", "Horayot": "Ho-rah-yote",
    "Zevachim": "Zeh-vah-kheem", "Menachot": "Meh-nah-khote", "Bekhorot": "Beh-kho-rote",
    "Arakhin": "Ah-rah-kheen", "Temurah": "Teh-moo-rah", "Keritot": "Keh-ree-tote",
    "Meilah": "Meh-ee-lah", "Niddah": "Nee-dah", "Shekalim": "Sheh-kah-leem",
    "Rav": "Rahv", "Shmuel": "Shmoo-el", "Abaye": "Ah-bye-yay", "Rava": "Rah-vah",
    "Yochanan": "Yo-khah-nahn", "Reish": "Raysh", "Lakish": "Lah-keesh",
    "Shammai": "Shah-my", "Hillel": "Hill-el", "Beit": "Bait", "Akiva": "Ah-kee-vah",
    "Yehuda": "Yeh-hoo-dah", "Yehudah": "Yeh-hoo-dah", "Meir": "May-eer",
    "Shulchan": "Shool-khahn", "Arukh": "Ah-rookh", "Aruch": "Ah-rookh",
    "Mishneh": "Mish-neh", "shechita": "sheh-khee-tah", "shechitah": "sheh-khee-tah",
    "neveilah": "neh-vay-lah", "treifah": "tray-fah", "treif": "trayf",
    "kal": "kahl", "vachomer": "vah-kho-mer", "gezeirah": "geh-zay-rah", "shavah": "shah-vah",
    "din": "deen", "dinim": "dee-neem", "minhag": "min-hahg", "psak": "p'sahk",
    "dibbur": "dee-boor", "hamatchil": "hah-maht-kheel", "Hadran": "Hahd-rahn",
}
HEBREW = re.compile(r"[\u0590-\u05FF\uFB1D-\uFB4F]+")
UNITS = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen " \
        "fifteen sixteen seventeen eighteen nineteen".split()
TENS = "twenty thirty forty fifty sixty seventy eighty ninety".split()


def num_words(n: int) -> str:
    if n < 20:
        return UNITS[n]
    if n < 100:
        t, u = divmod(n, 10)
        return TENS[t - 2] + ("" if u == 0 else "-" + UNITS[u])
    h, r = divmod(n, 100)
    return UNITS[h] + " hundred" + ("" if r == 0 else " and " + num_words(r))


def speakable(text: str) -> str:
    """Turn a markdown-ish script into clean text a voice can read."""
    t = text
    t = re.sub(r"```.*?```", "", t, flags=re.S)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)            # links -> text
    t = re.sub(r"^#{1,6}\s*", "", t, flags=re.M)               # headings
    t = re.sub(r"^\s*[-*+]\s+", "", t, flags=re.M)             # bullets
    t = re.sub(r"^\s*\d+[.)]\s+", "", t, flags=re.M)           # numbered items
    t = re.sub(r"[*_`>|]+", "", t)
    t = re.sub(r"\s*(->|\u2192)\s*", ", then ", t)
    t = re.sub(r"\b(Mishnah [A-Z][\w' ]*?) (\d+):(\d+)", r"\1, perek \2, mishnah \3", t)
    t = re.sub(r"\bs\.v\.", "at the words", t)
    t = re.sub(r"\bR\.\s", "Rabbi ", t)
    t = re.sub(r"(\d+[ab](?::\d+)?)\s*[-\u2013]\s*(\d+[ab](?::\d+)?)", r"\1 through \2", t)
    t = re.sub(r"(\d+)([ab]):(\d+)", lambda m: f"{m.group(1)}{m.group(2)}, line {m.group(3)}", t)
    t = re.sub(r"\b(\d+)([ab])\b",
               lambda m: f"{num_words(int(m.group(1)))}, amud {'aleph' if m.group(2) == 'a' else 'bet'}", t)
    t = re.sub(r"(\d+)\s*-\s*(\d+)", r"\1 to \2", t)
    t = re.sub(r"(\d+):(\d+)", lambda m: f"{m.group(1)}, {m.group(2)}", t)
    t = HEBREW.sub("", t)
    t = re.sub(r"\(\s*\)", "", t)
    for word, say in sorted(LEXICON.items(), key=lambda kv: -len(kv[0])):
        # Capitalized entries are names: match exactly, so English "ran" or "rosh" is untouched.
        # Lowercase entries are terms: also match a sentence-initial capital.
        forms = {word} if word[0].isupper() else {word, word[0].upper() + word[1:]}
        for form in forms:
            repl = say if form == word else say[0].upper() + say[1:]
            t = re.sub(rf"(?<![\w-]){re.escape(form)}(?![\w-])", repl, t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def paragraphs(text: str) -> list[str]:
    out = []
    for block in re.split(r"\n\s*\n", text):
        block = " ".join(line.strip() for line in block.splitlines() if line.strip())
        if block:
            out.append(block)
    return out


# ---------- engines ----------

def ensure_piper_voice(voice: str, install: bool) -> Path | None:
    model = next(VOICE_DIR.glob(f"*{voice}*.onnx"), None) if VOICE_DIR.exists() else None
    if model or not install:
        return model
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp()) / "voice.tgz"
    req = urllib.request.Request(VOICES[voice], headers={"User-Agent": "daf/3.0"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(tmp, "wb") as fh:
        shutil.copyfileobj(resp, fh)
    with tarfile.open(tmp) as tar:
        for m in tar.getmembers():
            if m.name.endswith((".onnx", ".onnx.json")):
                m.name = Path(m.name).name
                tar.extract(m, VOICE_DIR)
    return next(VOICE_DIR.glob(f"*{voice}*.onnx"), None)


def have_piper(install: bool) -> bool:
    try:
        import piper  # noqa: F401
        return True
    except ImportError:
        if not install:
            return False
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "piper-tts"]
                   + (["--break-system-packages"] if sys.platform.startswith("linux") else []),
                   check=False)
    try:
        import piper  # noqa: F401
        return True
    except ImportError:
        return False


def synth_piper(paras: list[str], wav_path: Path, voice: str, install: bool, rate: float) -> bool:
    if not have_piper(install):
        return False
    model = ensure_piper_voice(voice, install)
    if not model:
        return False
    from piper import PiperVoice, SynthesisConfig
    v = PiperVoice.load(str(model))
    cfg = SynthesisConfig(length_scale=1.0 / rate)
    with wave.open(str(wav_path), "wb") as w:
        first = True
        for p in paras:
            if p == "[pause]":
                if not first:
                    w.writeframes(b"\x00\x00" * int(w.getframerate() * 1.2))
                continue
            v.synthesize_wav(p, w, syn_config=cfg, set_wav_format=first)
            first = False
            w.writeframes(b"\x00\x00" * int(w.getframerate() * 0.55))
    return True


def synth_cli(paras: list[str], wav_path: Path, engine: str, rate: float) -> bool:
    text = "\n\n".join(p for p in paras if p != "[pause]")
    tmp = Path(tempfile.mkdtemp()) / "script.txt"
    tmp.write_text(text, encoding="utf-8")
    if engine == "espeak":
        exe = shutil.which("espeak-ng") or shutil.which("espeak")
        if not exe:
            return False
        cmd = [exe, "-v", "en-us", "-s", str(int(165 * rate)), "-g", "6", "-f", str(tmp), "-w", str(wav_path)]
    elif engine == "say":
        exe = shutil.which("say")
        if not exe:
            return False
        aiff = wav_path.with_suffix(".aiff")
        subprocess.run([exe, "-r", str(int(175 * rate)), "-f", str(tmp), "-o", str(aiff)], check=True)
        if shutil.which("ffmpeg"):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(aiff), str(wav_path)], check=True)
        else:
            shutil.move(aiff, wav_path)
        return True
    else:
        return False
    return subprocess.run(cmd).returncode == 0


def encode(wav_path: Path, out: Path, title: str | None) -> Path:
    if out.suffix.lower() == ".wav" or not shutil.which("ffmpeg"):
        final = out.with_suffix(".wav")
        shutil.move(str(wav_path), final)
        return final
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_path),
           "-af", "loudnorm=I=-18:TP=-2", "-codec:a", "libmp3lame", "-b:a", "64k", "-ac", "1"]
    if title:
        cmd += ["-metadata", f"title={title}", "-metadata", "artist=Daf shiur", "-metadata", "genre=Speech"]
    subprocess.run(cmd + [str(out)], check=True)
    return out


def duration(path: Path) -> float | None:
    try:
        if path.suffix == ".wav":
            with wave.open(str(path)) as w:
                return w.getnframes() / w.getframerate()
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(path)], capture_output=True, text=True)
        return float(r.stdout.strip())
    except Exception:
        return None


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("script", help="Shiur script (plain text or light markdown)")
    p.add_argument("--out", default="shiur.mp3")
    p.add_argument("--title")
    p.add_argument("--engine", choices=["auto", "piper", "espeak", "say"], default="auto")
    p.add_argument("--voice", choices=sorted(VOICES), default="lessac")
    p.add_argument("--rate", type=float, default=1.0, help="1.0 normal, 0.9 slower, 1.1 faster")
    p.add_argument("--install", action="store_true", help="Allow installing piper-tts and a voice")
    p.add_argument("--lexicon", help="JSON file of extra {word: respelling} entries")
    p.add_argument("--prepare-only", action="store_true")
    args = p.parse_args()

    if args.lexicon:
        LEXICON.update(json.loads(Path(args.lexicon).read_text(encoding="utf-8")))
    raw = Path(args.script).read_text(encoding="utf-8")
    prepared = speakable(raw)
    if args.prepare_only:
        print(prepared)
        return 0
    paras = paragraphs(prepared)
    if not paras:
        print("Script is empty after preparation", file=sys.stderr)
        return 2

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    wav = Path(tempfile.mkdtemp()) / "shiur.wav"
    order = ["piper", "espeak", "say"] if args.engine == "auto" else [args.engine]
    used, notes = None, []
    for engine in order:
        try:
            ok = (synth_piper(paras, wav, args.voice, args.install, args.rate) if engine == "piper"
                  else synth_cli(paras, wav, engine, args.rate))
        except Exception as exc:
            ok = False
            notes.append(f"{engine}: {exc}")
        if ok and wav.exists() and wav.stat().st_size > 1000:
            used = engine
            break
        notes.append(f"{engine}: unavailable")
    if not used:
        print(json.dumps({"ok": False, "reason": "no TTS engine available", "tried": notes}), file=sys.stderr)
        return 4

    final = encode(wav, out, args.title)
    secs = duration(final)
    print(json.dumps({
        "ok": True, "file": str(final), "engine": used,
        "voice": args.voice if used == "piper" else None,
        "minutes": round(secs / 60, 1) if secs else None,
        "words": len(prepared.split()),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
