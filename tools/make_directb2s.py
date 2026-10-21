#!/usr/bin/env python3
"""Build dist/ThreatTide.directb2s: the B2S backglass for the cabinet's
backglass screen, from art/render/backglass.png.

    python3 tools/make_directb2s.py

Static image only (no lamps or score reels): the score and board report live on
the FlexDMD screen. Put the file next to ThreatTide.vpx with the same base name.
The table script starts the B2S server itself (see TTBackglassStart).
"""
import base64
import io
import pathlib
from xml.sax.saxutils import quoteattr

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "art" / "render" / "backglass.png"
OUT = ROOT / "dist" / "ThreatTide.directb2s"

# Fixed GUIDs so rebuilds produce the same file
GUIDS = ("7D2C1E54-3B1A-4E0D-9C51-2F6A9E3B0C11", "0F4B8A27-6C3D-4E19-A2B5-8D7E1C9F3A22",
         "B9E3D640-1A7C-4F25-8E06-3C4D5A6B7E33")


def b64png(img):
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def build():
    bg = Image.open(SRC).convert("RGB")
    thumb = bg.copy()
    thumb.thumbnail((200, 160))
    v = lambda tag, val: f"  <{tag} Value={quoteattr(str(val))}/>"
    lines = [
        '<DirectB2SData Version="1.2">',
        v("Name", "Threat Tide"),
        v("TableType", 4),
        v("DMDType", 1),
        '  <DMDDefaultLocation LocX="0" LocY="0"/>',
        v("GrillHeight", 0),
        v("ProjectGUID", GUIDS[0]),
        v("ProjectGUID2", GUIDS[1]),
        v("AssemblyGUID", GUIDS[2]),
        v("VSName", "Threat Tide"),
        v("DualBackglass", 0),
        v("Author", "CyQuantiFi"),
        v("Artwork", "CyQuantiFi"),
        v("GameName", "ThreatTide"),
        v("AddEMDefaults", 0),
        v("CommType", 1),
        v("DestType", 1),
        v("NumberOfPlayers", 1),
        v("B2SDataCount", 5),
        v("ReelType", ""),
        v("UseDream7LEDs", 1),
        v("D7Glow", 1500),
        v("D7Thickness", 2000),
        v("D7Shear", 10),
        v("ReelRollingDirection", 0),
        v("ReelRollingInterval", 20),
        v("ReelIntermediateImageCount", 0),
        "  <Animations/>",
        '  <Scores ReelCountOfIntermediates="0" ReelRollingDirection="Up" ReelRollingInterval="20"/>',
        "  <Illumination/>",
        "  <Images>",
        f'    <BackglassImage Value="{b64png(bg)}" FileName="backglass.png"/>',
        f'    <ThumbnailImage Value="{b64png(thumb)}"/>',
        "  </Images>",
        "</DirectB2SData>",
    ]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e3:.0f} KB)")


if __name__ == "__main__":
    build()
