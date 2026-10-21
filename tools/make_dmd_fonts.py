#!/usr/bin/env python3
"""Render Comfortaa into BMFont files (.fnt + .png) for FlexDMD.

FlexDMD can't use .ttf directly. This draws each printable ASCII glyph in
white with an alpha channel (FlexDMD tints it at run time) and writes the
text BMFont format FlexDMD reads.

    python3 tools/make_dmd_fonts.py        # writes dmd/*.fnt and dmd/*.png

Font: art/fonts/Comfortaa-VariableFont_wght.ttf (SIL OFL 1.1).
"""
import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
TTF = ROOT / "art" / "fonts" / "Comfortaa-VariableFont_wght.ttf"
OUT = ROOT / "dmd"

# (file stem, pixel size, weight axis value)
FONTS = [
    ("comfortaa_bold_24", 24, 700),   # score, attract title
    ("comfortaa_bold_14", 14, 700),   # callout headline, report total
]
CHARS = [chr(c) for c in range(32, 127)]


def render(stem, size, weight):
    font = ImageFont.truetype(str(TTF), size)
    try:
        font.set_variation_by_axes([weight])
    except Exception:
        pass
    ascent, descent = font.getmetrics()
    line_h = ascent + descent
    pad = 1
    # Pack glyphs left to right into rows
    sheet_w = 512
    x = y = 0
    row_h = line_h + pad * 2
    boxes = []
    for ch in CHARS:
        l, t, r, b = font.getbbox(ch)
        w = max(0, r - l)
        h = max(0, b - t)
        if x + w + pad * 2 > sheet_w:
            x = 0
            y += row_h
        boxes.append((ch, x, y, w, h, l, t, font.getlength(ch)))
        x += w + pad * 2
    sheet_h = 1
    while sheet_h < y + row_h:
        sheet_h *= 2
    img = Image.new("RGBA", (sheet_w, sheet_h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    lines = []
    for ch, gx, gy, w, h, l, t, adv in boxes:
        if w and h:
            draw.text((gx + pad - l, gy + pad - t), ch, font=font, fill=(255, 255, 255, 255))
        lines.append(
            f"char id={ord(ch)} x={gx + pad} y={gy + pad} width={w} height={h} "
            f"xoffset={l} yoffset={t} xadvance={round(adv)} page=0 chnl=15"
        )
    OUT.mkdir(exist_ok=True)
    png = f"{stem}.png"
    img.save(OUT / png)
    fnt = [
        f'info face="Comfortaa" size={size} bold={1 if weight >= 600 else 0} italic=0 charset="" unicode=1 '
        f"stretchH=100 smooth=1 aa=1 padding=0,0,0,0 spacing=1,1 outline=0",
        f"common lineHeight={line_h} base={ascent} scaleW={sheet_w} scaleH={sheet_h} pages=1 packed=0 "
        f"alphaChnl=0 redChnl=4 greenChnl=4 blueChnl=4",
        f'page id=0 file="{png}"',
        f"chars count={len(lines)}",
        *lines,
    ]
    (OUT / f"{stem}.fnt").write_text("\n".join(fnt) + "\n")
    return stem


if __name__ == "__main__":
    made = [render(*f) for f in FONTS]
    print("wrote", ", ".join(f"dmd/{m}.fnt" for m in made))
