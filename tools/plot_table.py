#!/usr/bin/env python3
"""Draw a top-down map of an extracted .vpx (vpxtool extract) for layout checks.

    python3 tools/plot_table.py <extracted_dir> <out.png> [--bg playfield.png]

Walls grey, rubbers white, triggers green, kickers blue, targets yellow,
lights orange, flippers red, ramps purple. Names are printed next to items.
"""
import json
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

COL = dict(Wall=(150, 150, 150), Rubber=(240, 240, 240), Trigger=(60, 220, 90), Kicker=(80, 150, 255),
           HitTarget=(255, 220, 60), Light=(255, 136, 24), Flipper=(255, 70, 70), Ramp=(190, 110, 255),
           Gate=(0, 220, 220), Plunger=(255, 255, 255), Bumper=(255, 154, 163))


def main(src, out, bg=None):
    src = pathlib.Path(src)
    gd = json.load(open(src / "gamedata.json"))
    W, H = gd["right"], gd["bottom"]
    S = 0.6
    if bg:
        img = Image.open(bg).convert("RGB").resize((int(W * S), int(H * S)))
        img = Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), 0.55)
    else:
        img = Image.new("RGB", (int(W * S), int(H * S)), (20, 22, 26))
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    order = json.load(open(src / "gameitems.json"))
    for entry in order:
        f = src / "gameitems" / entry["file_name"]
        if not f.exists():
            continue
        item = json.load(open(f))
        kind = next(iter(item))
        v = item[kind]
        name = v.get("name", "")
        c = COL.get(kind)
        if c is None:
            continue
        pts = [(p["x"] * S, p["y"] * S) for p in v.get("drag_points", [])]
        if kind in ("Wall", "Rubber", "Ramp") and len(pts) > 1:
            if kind == "Ramp":
                d.line(pts, fill=c, width=max(2, int(v.get("width_bottom", 20) * S / 3)))
            else:
                d.line(pts + ([pts[0]] if kind == "Wall" else []), fill=c, width=2)
            if v.get("is_droppable") or name.startswith(("AirGap", "Lane", "Guide", "TT")):
                d.text(pts[0], name, fill=c, font=font)
        elif kind == "Flipper":
            cx, cy = v["center"]["x"], v["center"]["y"]
            import math
            a = math.radians(v["start_angle"])
            r = v["flipper_radius_max"]
            d.line([(cx * S, cy * S), ((cx + r * math.sin(a)) * S, (cy - r * math.cos(a)) * S)], fill=c, width=6)
        elif "center" in v:
            cx, cy = v["center"]["x"] * S, v["center"]["y"] * S
            r = max(4, v.get("radius", 12) * S)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=2)
            d.text((cx + r + 2, cy - 5), name, fill=c, font=font)
        elif "position" in v:
            cx, cy = v["position"]["x"] * S, v["position"]["y"] * S
            d.rectangle([cx - 10, cy - 4, cx + 10, cy + 4], fill=c)
            d.text((cx + 12, cy - 5), name, fill=c, font=font)
    img.save(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    bg = a[a.index("--bg") + 1] if "--bg" in a else None
    main(a[0], a[1], bg)
