#!/usr/bin/env bash
# Rebuild everything generated: script bundle, sounds, DMD fonts, art, table, backglass.
# Needs: python3 (Pillow, numpy), Node + Playwright with Chromium and the Comfortaa
# font installed (art/fonts) for the art step, and vpxtool (cargo install vpxtool).
# Set SKIP_ART=1 to reuse the committed PNGs in art/render/.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 tools/vbs_lint.py
python3 tools/bundle.py
python3 tools/make_sfx.py
python3 tools/make_dmd_fonts.py
python3 tools/make_playfield_art.py
if [ "${SKIP_ART:-0}" != "1" ]; then
  node tools/render_art.js
  python3 tools/make_qr.py
fi
python3 tools/build_table.py
python3 tools/make_directb2s.py
echo "done: dist/ThreatTide.vpx, dist/ThreatTide.directb2s"
