#!/bin/bash
# paper.md → build/paper.html + build/paper.pdf (pandoc, then a Chromium-family browser)
# Fonts are local only. This script used to pull Archivo and IBM Plex from Google Fonts;
# no artefact here may do that, so paper.css names the faces and stops at a system stack.
set -euo pipefail
cd "$(dirname "$0")/.."
B="${LOOMGROUND_CHROME:-/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge}"
python3 - <<'PY'
import re
s = open("paper.md").read()
s = re.sub(r"```latex\n(.*?)\n```", lambda m: "$$" + m.group(1) + "$$", s, flags=re.S)
open("build/_paper.md", "w").write(s)
PY
pandoc build/_paper.md -f markdown+tex_math_dollars-implicit_figures -t html5 --standalone --mathml --wrap=none --syntax-highlighting=none \
  --metadata title="Whether an action may take effect" --metadata pagetitle="Whether an action may take effect" \
  --css paper.css \
  -o build/_paper.html
python3 - <<'PY'
import re
h = open("build/_paper.html").read()
h = re.sub(r'<header id="title-block-header">.*?</header>', "", h, flags=re.S)
h = re.sub(r'<p><img src="([^"]+)"\s+alt="([^"]*)"\s*/></p>',
           lambda m: f'<figure><img src="../{m.group(1)}" alt="{m.group(2)}"><figcaption>{m.group(2)}</figcaption></figure>', h)
open("build/paper.html", "w").write(h)
PY
rm build/_paper.md build/_paper.html
"$B" --headless=new --disable-gpu --no-pdf-header-footer --virtual-time-budget=8000 \
  --print-to-pdf="$PWD/build/paper.pdf" "file://$PWD/build/paper.html" >/dev/null 2>&1
ls -la build/paper.pdf
