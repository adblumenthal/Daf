#!/usr/bin/env python3
"""
Export a Daf lesson (Markdown) to a formatted PDF.

Examples:
  python scripts/make_pdf.py lesson.md --out Chullin_23b.pdf \\
      --title "Chullin 23b" --subtitle "Perek 2 · Shechitah of the majority" --meta "Exact daf"
  python scripts/make_pdf.py lesson.md --out lesson.pdf --html-only   # print-ready HTML
  python scripts/make_pdf.py sheet.md --out sheet.pdf --title "Review" --compact  # denser handout

Renderers, tried in order: wkhtmltopdf, Chrome/Chromium headless, WeasyPrint.
If none exists, a print-ready HTML file is written and the script exits 4.

Supported Markdown: headings, paragraphs, bold, italic, inline code, links,
bullets (nested by indentation), numbered lists, checklists (- [ ] / - [x]),
blockquotes (rendered as callout boxes), tables, and horizontal rules.
Hebrew and Aramaic runs are detected and set right-to-left automatically.
"""

# Created by Adam Blumenthal in honor of David and Barbara Blumenthal,
# who always pushed him to keep asking questions.

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HEB = r"\u0590-\u05FF\uFB1D-\uFB4F"
HEB_RUN = re.compile(rf"[{HEB}](?:[{HEB}\s'\"\u05F3\u05F4.,:;()\-]*[{HEB}])?")

CSS = """
@page { size: Letter; margin: 0.8in 0.85in 0.9in 0.85in; }
html { -webkit-print-color-adjust: exact; }
body { font-family: "Libre Baskerville", "Georgia", "DejaVu Serif", "FreeSerif", serif;
       font-size: 10.6pt; line-height: 1.58; color: #1d1d1b; margin: 0; }
.he { font-family: "Frank Ruhl Libre", "SBL Hebrew", "Taamey Frank CLM", "David",
      "DejaVu Serif", "FreeSerif", serif; font-size: 1.12em;
      display: inline-block; max-width: 100%; }
.masthead { border-bottom: 2.5px solid #7a2e1d; padding-bottom: 12px; margin-bottom: 22px; }
.kicker { font-family: "Helvetica Neue", "Liberation Sans", "DejaVu Sans", sans-serif;
          font-size: 8pt; letter-spacing: 2.2px; text-transform: uppercase; color: #7a2e1d; }
.title { font-size: 25pt; line-height: 1.15; margin: 4px 0 2px 0; font-weight: bold; color: #151515; }
.subtitle { font-size: 12pt; font-style: italic; color: #4a4a48; }
.meta { font-family: "Helvetica Neue", "Liberation Sans", "DejaVu Sans", sans-serif;
        font-size: 8.3pt; color: #5b5b58; margin-top: 8px; }
.meta span { display: inline-block; border: 1px solid #d9cfc4; background: #f7f2ec;
             padding: 2px 8px; margin: 0 6px 4px 0; border-radius: 10px; }
h1 { font-size: 17pt; color: #151515; margin: 22px 0 8px; page-break-after: avoid; }
h2 { font-size: 13.2pt; color: #7a2e1d; margin: 22px 0 8px; padding-bottom: 4px;
     border-bottom: 1px solid #e3d8cc; page-break-after: avoid; }
h3 { font-size: 11.4pt; color: #2b2b29; margin: 16px 0 6px; page-break-after: avoid; }
h4 { font-size: 10.6pt; color: #4a4a48; margin: 12px 0 4px; font-style: italic; page-break-after: avoid; }
p { margin: 0 0 9px 0; text-align: left; orphans: 3; widows: 3; }
ul, ol { margin: 0 0 10px 0; padding-left: 22px; }
li { margin: 0 0 4px 0; }
li > ul, li > ol { margin-top: 4px; }
ul.check { list-style: none; padding-left: 4px; }
blockquote { margin: 12px 0; padding: 10px 14px; background: #f7f2ec;
             border-left: 3.5px solid #b5835a; page-break-inside: avoid; }
blockquote p:last-child { margin-bottom: 0; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 0.88em; background: #f1eeea; padding: 0 3px; }
a { color: #7a2e1d; text-decoration: none; border-bottom: 0.5px solid #d4b8a6; }
hr { border: 0; border-top: 1px solid #e3d8cc; margin: 18px 0; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 14px; font-size: 9.6pt; page-break-inside: avoid; }
th { background: #efe6dc; text-align: left; font-weight: bold; }
th, td { border: 1px solid #ddd2c6; padding: 5px 8px; vertical-align: top; }
.addendum { margin-top: 26px; padding-top: 6px; border-top: 2px solid #b5835a; }
.colophon { margin-top: 30px; font-family: "Helvetica Neue", "Liberation Sans", "DejaVu Sans", sans-serif;
            font-size: 7.8pt; color: #8a8a86; border-top: 1px solid #e3d8cc; padding-top: 8px; }
"""


COMPACT_CSS = """
body { font-size: 10.2pt; line-height: 1.55; }
.masthead { padding-bottom: 7px; margin-bottom: 10px; }
.title { font-size: 19pt; }
h2 { font-size: 12pt; margin: 16px 0 6px; padding-bottom: 3px; }
h3 { font-size: 10pt; margin: 8px 0 3px; }
p { margin: 0 0 5px 0; }
ul, ol { margin: 0 0 5px 0; }
li { margin: 0 0 3.5px 0; }
.colophon { margin-top: 10px; }
"""


def inline(text: str) -> str:
    t = html.escape(text, quote=False).replace("-&gt;", "\u2192")
    code_spans: list[str] = []

    def stash(m):
        code_spans.append(m.group(1))
        return f"\x00{len(code_spans) - 1}\x00"

    t = re.sub(r"`([^`]+)`", stash, t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])", r"<em>\1</em>", t)
    t = HEB_RUN.sub(lambda m: f'<span class="he" dir="rtl" lang="he">{m.group(0)}</span>', t)
    t = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{code_spans[int(m.group(1))]}</code>", t)
    return t


LIST_RE = re.compile(r"^(?P<indent>\s*)(?P<marker>[-*+]|\d+[.)])\s+(?P<body>.*)$")


def render_list(lines: list[str]) -> str:
    """Render consecutive list lines, nesting by indentation."""
    out: list[str] = []
    stack: list[tuple[int, str]] = []
    for line in lines:
        m = LIST_RE.match(line)
        indent = len(m.group("indent").expandtabs(4))
        ordered = m.group("marker")[0].isdigit()
        body = m.group("body")
        check = re.match(r"^\[( |x|X)\]\s+(.*)$", body)
        tag = "ol" if ordered else "ul"
        while stack and indent < stack[-1][0]:
            out.append(f"</li></{stack.pop()[1]}>")
        if not stack or indent > stack[-1][0]:
            cls = ' class="check"' if check else ""
            out.append(f"<{tag}{cls}>")
            stack.append((indent, tag))
        else:
            out.append("</li>")
        if check:
            box = "&#9745;" if check.group(1).lower() == "x" else "&#9744;"
            out.append(f"<li>{box} {inline(check.group(2))}")
        else:
            out.append(f"<li>{inline(body)}")
    while stack:
        out.append(f"</li></{stack.pop()[1]}>")
    return "".join(out)


def render_table(lines: list[str]) -> str:
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines]
    body = [r for r in rows if not all(re.fullmatch(r":?-{2,}:?", c) for c in r if c)]
    if not body:
        return ""
    head, rest = body[0], body[1:]
    h = "".join(f"<th>{inline(c)}</th>" for c in head)
    r = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>" for row in rest)
    return f"<table><thead><tr>{h}</tr></thead><tbody>{r}</tbody></table>"


def markdown_to_html(md: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        if s.startswith("<!-- addendum -->"):
            out.append('<div class="addendum"></div>')
            i += 1
            continue
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", s):
            out.append("<hr>")
            i += 1
            continue
        h = re.match(r"^(#{1,4})\s+(.*)$", s)
        if h:
            lvl = len(h.group(1))
            out.append(f"<h{lvl}>{inline(h.group(2).strip())}</h{lvl}>")
            i += 1
            continue
        if s.startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            out.append(render_table(block))
            continue
        if s.startswith(">"):
            block = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                block.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append(f"<blockquote>{markdown_to_html(chr(10).join(block))}</blockquote>")
            continue
        if LIST_RE.match(line):
            block = []
            while i < len(lines) and (LIST_RE.match(lines[i]) or
                                      (lines[i].startswith("  ") and lines[i].strip() and block)):
                if LIST_RE.match(lines[i]):
                    block.append(lines[i])
                else:  # continuation line of the previous item
                    block[-1] = block[-1] + " " + lines[i].strip()
                i += 1
            out.append(render_list(block))
            continue
        para = [s]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^\s*(#{1,4}\s|>|\||[-*+]\s|\d+[.)]\s|-{3,}$)", lines[i]):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")
    return "\n".join(out)


def build_document(md: str, title: str, subtitle: str | None, meta: list[str],
                   kicker: str, colophon: str, compact: bool = False) -> str:
    # Drop a leading H1 that simply repeats the title.
    first = re.match(r"^\s*#\s+(.+)\n", md)
    if first and first.group(1).strip().lower() == title.strip().lower():
        md = md[first.end():]
    chips = "".join(f"<span>{inline(m)}</span>" for m in meta)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>{CSS}{COMPACT_CSS if compact else ""}</style></head><body>
<div class="masthead">
  <div class="kicker">{html.escape(kicker)}</div>
  <div class="title">{inline(title)}</div>
  {f'<div class="subtitle">{inline(subtitle)}</div>' if subtitle else ''}
  {f'<div class="meta">{chips}</div>' if chips else ''}
</div>
{markdown_to_html(md)}
<div class="colophon">{inline(colophon)}</div>
</body></html>"""


def stamp_footer(pdf_path: Path, footer: str) -> bool:
    """Add 'title ... page / total' to every page. Needs pypdf + reportlab; skipped otherwise."""
    try:
        import io
        from pypdf import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas
    except ImportError:
        return False
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()
    total = len(reader.pages)
    for n, page in enumerate(reader.pages, start=1):
        w, h = float(page.mediabox.width), float(page.mediabox.height)
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(w, h))
        c.setFont("Helvetica", 7)
        c.setFillColorRGB(0.52, 0.52, 0.5)
        c.drawString(56, 30, footer)
        c.drawRightString(w - 56, 30, f"{n} / {total}")
        c.save()
        buf.seek(0)
        page.merge_page(PdfReader(buf).pages[0])
        writer.add_page(page)
    writer.add_metadata({"/Title": footer, "/Creator": "Daf study skill"})
    with open(pdf_path, "wb") as fh:
        writer.write(fh)
    return True


def render(html_path: Path, pdf_path: Path, footer: str) -> str | None:
    wk = shutil.which("wkhtmltopdf")
    if wk:
        version = subprocess.run([wk, "--version"], capture_output=True, text=True).stdout
        patched = "patched qt" in version.lower()
        cmd = [wk, "--quiet", "--enable-local-file-access", "--encoding", "utf-8",
               "--page-size", "Letter", "-T", "18mm", "-B", "20mm", "-L", "20mm", "-R", "20mm"]
        if patched:
            cmd += ["--footer-font-name", "DejaVu Sans", "--footer-font-size", "7",
                    "--footer-left", footer, "--footer-right", "[page] / [topage]",
                    "--footer-spacing", "6"]
        env = {**os.environ, "XDG_RUNTIME_DIR": os.environ.get("XDG_RUNTIME_DIR", tempfile.gettempdir())}
        result = subprocess.run(cmd + [str(html_path), str(pdf_path)], env=env,
                                stderr=subprocess.DEVNULL)
        if result.returncode in (0, 1) and pdf_path.exists():
            if not patched:
                stamp_footer(pdf_path, footer)
            return "wkhtmltopdf"
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        exe = shutil.which(name)
        if exe:
            cmd = [exe, "--headless", "--disable-gpu", "--no-sandbox",
                   f"--print-to-pdf={pdf_path}", "--no-pdf-header-footer", html_path.as_uri()]
            if subprocess.run(cmd, capture_output=True).returncode == 0 and pdf_path.exists():
                stamp_footer(pdf_path, footer)
                return name
    try:
        from weasyprint import HTML  # type: ignore
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        stamp_footer(pdf_path, footer)
        return "weasyprint"
    except Exception:
        return None


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("markdown")
    p.add_argument("--out", default="lesson.pdf")
    p.add_argument("--title", required=True)
    p.add_argument("--subtitle")
    p.add_argument("--meta", action="append", default=[], help="Header chip; repeatable")
    p.add_argument("--kicker", default="Daf · Talmud study")
    p.add_argument("--colophon", default="Prepared with the Daf study skill. Sources: Sefaria.org; "
                                          "calendar data (Yomi mode): Hebcal.com.")
    p.add_argument("--html-only", action="store_true")
    p.add_argument("--compact", action="store_true", help="Tighter type and spacing, e.g. for one-page handouts")
    args = p.parse_args()

    md = Path(args.markdown).read_text(encoding="utf-8")
    doc = build_document(md, args.title, args.subtitle, args.meta, args.kicker, args.colophon, args.compact)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    html_path = out.with_suffix(".html") if args.html_only else Path(tempfile.mkdtemp()) / "lesson.html"
    html_path.write_text(doc, encoding="utf-8")
    if args.html_only:
        print(json.dumps({"ok": True, "file": str(html_path), "renderer": "html"}))
        return 0
    footer = re.sub(r"[\[\]]", "", args.title)
    renderer = render(html_path, out.with_suffix(".pdf"), footer)
    if not renderer:
        fallback = out.with_suffix(".html")
        shutil.copy(html_path, fallback)
        print(json.dumps({"ok": False, "reason": "no PDF renderer", "html": str(fallback)}), file=sys.stderr)
        return 4
    print(json.dumps({"ok": True, "file": str(out.with_suffix(".pdf")), "renderer": renderer}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
