#!/usr/bin/env python3
"""Make art/render/qr_form.png from TT_FormUrl in table/tt_config.vbs.
Needs: pip install qrcode. The table shows it on the claim screen (image qr_form)."""
import pathlib
import re

import qrcode

ROOT = pathlib.Path(__file__).resolve().parent.parent
url = re.search(r'TT_FormUrl = "([^"]+)"', (ROOT / "table" / "tt_config.vbs").read_text()).group(1)
if not url.startswith("http"):
    url = "https://" + url
img = qrcode.make(url, border=2, box_size=8).convert("RGB")
img.save(ROOT / "art" / "render" / "qr_form.png")
print("wrote art/render/qr_form.png for", url)
