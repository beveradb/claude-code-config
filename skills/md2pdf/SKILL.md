---
name: md2pdf
description: Render a Markdown file to a clean, watermark-free, professionally-styled PDF (headless Chrome via md-to-pdf). Use whenever the user asks for a PDF version of a Markdown document, or says "make a PDF", "export to PDF", "convert this markdown to PDF", "render as PDF", "md to pdf", or wants a nicely-formatted PDF of notes/docs/reports/READMEs.
---

# md2pdf — Markdown to styled PDF

Render any Markdown file to a clean, watermark-free PDF using the bundled theme
(styled like markdowntopdf.com). Everything travels with this skill, so it works on
any machine that has this repo cloned plus Node.js and a Chrome/Chromium browser.

## Usage

```bash
SCRIPT=~/.claude/skills/md2pdf/scripts/md2pdf

bash $SCRIPT input.md                 # -> input.pdf (beside the source)
bash $SCRIPT input.md output.pdf      # -> explicit output path
bash $SCRIPT --css other.css in.md    # override the stylesheet for one run
```

That's the whole tool — run it and report the output path to the user.

## How it works

- Uses `md-to-pdf` (fetched on demand via `npx -y`, no global install needed).
- Default theme is `~/.claude/skills/md2pdf/style.css`, bundled with this skill.
  Edit that file to restyle output globally, or pass `--css`/`MD2PDF_CSS` per run.
- Auto-detects a system browser (Chrome, Chromium, or Edge) on macOS/Linux and
  reuses it (no Chromium download). If none is found, it falls back to Puppeteer's
  own Chromium. Force a specific binary with `MD2PDF_CHROME=/path/to/chrome`.
- PDF defaults: A4, sensible margins, backgrounds printed.

## Requirements

- **Node.js** (`node`/`npx`) — `brew install node` (macOS) or your platform's package.
- **A Chromium-based browser** (Google Chrome, Chromium, or Edge) recommended; if
  absent, the first run downloads a Chromium via Puppeteer automatically.

## Optional: put `md2pdf` on your PATH

For terminal use outside Claude, symlink it once per machine:

```bash
ln -sf ~/.claude/skills/md2pdf/scripts/md2pdf ~/.local/bin/md2pdf
```
