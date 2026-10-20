#!/bin/bash
# rasterise each figure at print size: the SVG is in mm, rendered at 4x CSS pixels (≈ 384 dpi)
cd "$(dirname "$0")"
B="${LOOMGROUND_CHROME:-/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge}"
for f in fig*.svg; do
  read w h < <(grep -o 'width="[0-9.]*mm" height="[0-9.]*mm"' "$f" | head -1 | tr -dc '0-9. ')
  pw=$(python3 -c "import math;print(math.ceil($w*96/25.4))"); ph=$(python3 -c "import math;print(math.ceil($h*96/25.4))")
  "$B" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=4 \
    --window-size="$pw,$ph" --screenshot="$PWD/${f%.svg}.png" "file://$PWD/$f" >/dev/null 2>&1
done
