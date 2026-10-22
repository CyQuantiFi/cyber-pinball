"""Vinyl skins: print files, a template for client artwork, and livery previews.

    python3 cabinet/make_skins.py            print files + templates + preview renders
    python3 cabinet/make_skins.py --no-render

The skins are printed vinyl on 3 mm ACM panels (parts "Skin ..." in geometry.py),
swapped between hires. Every file is at 1:1 in mm with 5 mm bleed, drawn as seen
from the outside, so a sign shop can print it as is and route the matching DXF
from out/dxf/.

Liveries:
    threattide   CyQuantiFi / Threat Tide brand (dark, orange and pink tide lines)
    generic      neutral satin black, no branding (the "generic box" option)
    vendor-demo  example client reskin, to show vendors what they get
    template     white guide sheets for a client's designer: trim, bleed, safe
                 zone, holes, the light-panel zone (PDF + SVG)

Outputs go to cabinet/out/skins/<livery>/ and cabinet/out/render/livery_*.png.
"""
import math
import zlib
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.font_manager import FontProperties     # noqa: E402
from matplotlib.patches import Circle, PathPatch       # noqa: E402
import numpy as np                                     # noqa: E402
from PIL import Image                                  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
import geometry as G                                   # noqa: E402
import make_cabinet as M                               # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "skins")
FONT = FontProperties(fname=os.path.join(HERE, "..", "art", "fonts", "Comfortaa-VariableFont_wght.ttf"))
BLEED = 5.0
SAFE = 10.0
matplotlib.rcParams["pdf.fonttype"] = 42      # embed the font (OFL allows it)
matplotlib.rcParams["svg.fonttype"] = "path"

LIVERIES = {
    "threattide": dict(bg=("#0B0C0E", "#1A1B1C", "#101A24"), hot=("#FF8818", "#FF9AA3"), cool="#2C4458",
                       ink="#FFFFFF", accent="#FF8818", brand="CyQuantiFi", panels=True),
    "generic": dict(bg=("#111317", "#141619", "#111317"), hot=("#2A2E35", "#2A2E35"), cool="#22262C",
                    ink="#8A8F98", accent="#3A3F47", brand=None, panels=False),
    "vendor-demo": dict(bg=("#081C4A", "#0B3A6E", "#0E7C86"), hot=("#FFFFFF", "#7FE0E8"), cool="#5FB4FF",
                        ink="#FFFFFF", accent="#FFD23F", brand="YOUR BRAND", panels=False),
}


def skins(parts):
    return [p for p in parts if getattr(p, "skin", False)]


def to2d(p):
    """Part coords -> drawing coords (outer face view, outline from (0, 0))."""
    x0, y0, x1, y1 = p.outline.bounds
    mir = p.frame.mirrored

    def f(u, v):
        return ((x1 - x0) - (u - x0) if mir else u - x0), v - y0
    return f


def kind(p):
    n = p.name
    return "front" if n == "Skin front" else "bbfront" if "backbox front" in n else \
        "bbside" if "backbox side" in n else "side"


def new_sheet(w, h, dpi=72):
    fig = plt.figure(figsize=((w + 2 * BLEED) / 25.4, (h + 2 * BLEED) / 25.4), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-BLEED, w + BLEED)
    ax.set_ylim(-BLEED, h + BLEED)
    ax.axis("off")
    return fig, ax


def text(ax, x, y, s, size_mm, color, rot=0, ha="center", va="center", alpha=1.0, weight=None):
    # font size is in points; 1 pt = 0.3528 mm, cap height of Comfortaa ~0.7 em
    ax.text(x, y, s, fontproperties=FONT, fontsize=size_mm / 0.3528 / 0.72, color=color, rotation=rot,
            ha=ha, va=va, alpha=alpha, rotation_mode="anchor")


def waves(ax, w, h, colors, n, y0, y1, seed, lw=4, alpha=(0.12, 0.4)):
    rng = np.random.default_rng(seed)
    x = np.linspace(-BLEED, w + BLEED, 400)
    for i in range(n):
        f = i / max(n - 1, 1)
        base = y0 + (y1 - y0) * f
        amp = (y1 - y0) / n * 0.9
        y = base + sum(amp * a * np.sin(2 * np.pi * x / L + ph) for a, L, ph in
                       zip(rng.uniform(0.3, 0.7, 3), rng.uniform(180, 700, 3), rng.uniform(0, 6.3, 3)))
        ax.plot(x, y, color=colors[i % len(colors)], lw=lw, alpha=alpha[0] + (alpha[1] - alpha[0]) * f,
                solid_capstyle="round")


def background(ax, w, h, stops):
    g = np.linspace(0, 1, 256)[:, None]
    cols = np.array([matplotlib.colors.to_rgb(c) for c in stops])
    t = np.linspace(0, 1, len(stops))
    img = np.stack([np.interp(g[:, 0], t, cols[:, k]) for k in range(3)], -1)[:, None, :]
    ax.imshow(img[::-1], extent=(-BLEED, w + BLEED, -BLEED, h + BLEED), aspect="auto", zorder=-10)


def pips(ax, x, y, n, step, r, lv):
    for i in range(n):
        c = lv["hot"][1] if i == n - 1 else lv["hot"][0]
        ax.add_patch(Circle((x + i * step, y), r, color=c, alpha=0.9, lw=0))
        if i < n - 1:
            ax.plot([x + i * step + r * 1.3, x + (i + 1) * step - r * 1.3], [y, y], color=lv["hot"][0], lw=3,
                    alpha=0.6)


def draw_livery(p, name, lv):
    g = M.part2d(p)
    w, h = g["size"]
    f = to2d(p)
    fig, ax = new_sheet(w, h)
    background(ax, w, h, lv["bg"])
    k = kind(p)
    seed = zlib.crc32(p.name.encode()) % 1000
    slope = math.degrees(G.A) * (-1 if p.frame.mirrored else 1)
    if k == "side":
        waves(ax, w, h, [lv["cool"]], 6, h * 0.08, h * 0.45, seed, lw=5, alpha=(0.5, 0.2))
        waves(ax, w, h, list(lv["hot"]), 7, h * 0.5, h * 0.92, seed + 1, lw=4)
        if name == "vendor-demo":
            text(ax, *f(540, 150), lv["brand"], 70, lv["ink"], rot=slope)
            text(ax, *f(540, 75), "yourbrand.com.au", 22, lv["accent"], rot=slope)
        elif lv["brand"]:
            yy = 560
            text(ax, *f(yy, G.top(yy) - 28), "PUT A DOLLAR FIGURE ON EVERY CYBER RISK", 13, lv["ink"], rot=slope,
                 alpha=0.85)
            text(ax, *f(935, G.top(935) - 75), lv["brand"], 22, lv["ink"], rot=slope)
            px, py = f(935, G.top(935) - 120)
            pips(ax, px - 37, py, 3, 37, 6, lv)
    elif k == "bbside":
        waves(ax, w, h, list(lv["hot"]), 6, h * 0.55, h * 0.95, seed, lw=4)
        waves(ax, w, h, [lv["cool"]], 5, h * 0.05, h * 0.45, seed + 3, lw=5, alpha=(0.5, 0.2))
        if lv["brand"]:
            text(ax, w / 2, h * 0.42, lv["brand"], 30 if name != "vendor-demo" else 34, lv["ink"], rot=90)
    elif k == "front":
        waves(ax, w, h, [lv["cool"]], 4, h * 0.1, h * 0.5, seed, lw=4, alpha=(0.5, 0.25))
        sx, sz = f(90, 150)
        text(ax, sx, sz + 30, "START", 11, lv["ink"])
        lx, lz = f(G.W - 120, 120)
        text(ax, lx, lz - 30, "LAUNCH", 11, lv["ink"])
        if name == "threattide":
            pips(ax, *f(90, 216), 7, 70, 4, lv)
        if name == "vendor-demo":
            text(ax, w / 2, 22, lv["brand"], 12, lv["accent"])
    elif k == "bbfront":
        waves(ax, w, h, [lv["cool"]], 3, h * 0.2, h * 0.8, seed, lw=4, alpha=(0.35, 0.2))
        x0, y0, x1, y1 = [c.bounds for c in g["cuts"]][0]
        ax.plot([x0 - 8, x1 + 8, x1 + 8, x0 - 8, x0 - 8], [y0 - 8, y0 - 8, y1 + 8, y1 + 8, y0 - 8],
                color=lv["accent"], lw=3, alpha=0.9)
    return fig, ax, g


def draw_template(p):
    g = M.part2d(p)
    w, h = g["size"]
    f = to2d(p)
    fig, ax = new_sheet(w, h)
    outline = g["outline"]
    ax.add_patch(PathPatch(M.patch(outline.buffer(BLEED, join_style=2)).get_path(), fc="#FCE4E4", ec="none"))
    ax.add_patch(PathPatch(M.patch(outline).get_path(), fc="white", ec="black", lw=0.8))
    safe = outline.buffer(-SAFE, join_style=2)
    for poly in M.polys(safe):
        ax.add_patch(PathPatch(M.patch(poly).get_path(), fc="none", ec="#1B9E3E", lw=0.6, ls="--"))
    holes = list(g["cuts"]) + [G.Point(cx, cy).buffer(d / 2, 32) for cx, cy, d, _ in g["circles"]]
    for hp in holes:
        ax.add_patch(PathPatch(M.patch(hp.buffer(5)).get_path(), fc="none", ec="#C0392B", lw=0.4, ls=":"))
        ax.add_patch(PathPatch(M.patch(hp).get_path(), fc="#BBBBBB", ec="#C0392B", lw=0.6))
    if kind(p) == "side":
        x0, z0 = f(190, 30)
        x1, z1 = f(880, 230)
        ax.add_patch(matplotlib.patches.Rectangle((min(x0, x1), z0), abs(x1 - x0), z1 - z0, fc="#E8F6FA",
                                                  ec="#2C8FB0", lw=0.6, hatch="///", alpha=0.6))
        text(ax, (x0 + x1) / 2, (z0 + z1) / 2, "EDGE-LIT LOGO PANEL ZONE\n(art shows through clear acrylic; "
             "keep it dark if a panel is fitted)", 7, "#2C8FB0")
    cy = h - 18 if kind(p) != "side" else 250
    text(ax, w / 2, cy, f"{p.name}  |  trim {w:.0f} x {h:.0f} mm  |  bleed 5 mm",
         5, "#333333")
    fig.text(0.5, 0.01, "Black = trim/cut line. Pink = bleed (extend art to here). Green dashed = safe zone "
             "(keep text/logos inside). Grey = cut-outs, red dotted = 5 mm keep-clear. Seen from outside. 1:1 mm.",
             fontsize=4, ha="center", color="#555555", fontproperties=FONT)
    return fig, ax, g


def texture(path_png, p):
    """Texture spec for the renderer, mapping the skin art onto its outer face."""
    im = Image.open(path_png).convert("RGB")
    if p.frame.mirrored:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    x0, y0, x1, y1 = p.outline.bounds
    return dict(img=np.asarray(im, float) / 255, frame=p.frame, axes=(0, 1), face=(2, p.t),
                rect=(x0 - BLEED, y0 - BLEED, x1 + BLEED, y1 + BLEED))


def main():
    parts, comps = G.build()
    sk = skins(parts)
    previews = {}
    for name, lv in LIVERIES.items():
        d = os.path.join(OUT, name)
        os.makedirs(d, exist_ok=True)
        for p in sk:
            fig, ax, g = draw_livery(p, name, lv)
            base = os.path.join(d, M.slug(p.name))
            fig.savefig(base + ".pdf")
            fig.savefig(base + "_preview.png", dpi=40)
            plt.close(fig)
            previews[(name, p.name)] = base + "_preview.png"
        print("livery", name, "done")
    d = os.path.join(OUT, "template")
    os.makedirs(d, exist_ok=True)
    for p in sk:
        fig, ax, g = draw_template(p)
        base = os.path.join(d, M.slug(p.name))
        fig.savefig(base + ".pdf")
        fig.savefig(base + ".svg")
        plt.close(fig)
    print("templates done")
    if "--no-render" in sys.argv:
        return 0

    # ---- livery preview renders
    tex = M.screen_textures(comps)
    for c in comps:
        if c.name in tex:
            tex[c.name]["frame"] = c.frame
    shown = [c for c in comps if c.name in tex or "Plunger knob" in c.name or "speaker" in c.name]
    screen_objs = [(M.comp_mesh(c), c.color, -0.2, tex.get(c.name)) for c in shown]
    acr = M.acrylic_textures(parts)
    rd = os.path.join(HERE, "out", "render")
    imgs = []
    for name, lv in LIVERIES.items():
        objs = []
        for p in parts:
            if p.material == "glass5" or (p.material == "acrylic3" and not lv["panels"]):
                continue
            t = texture(previews[(name, p.name)], p) if getattr(p, "skin", False) else acr.get(p.name)
            for m in M.part_meshes(p):
                objs.append((m, M.part_color(p), M.part_bias(p) - (0.3 if getattr(p, "skin", False) else 0), t))
        path = os.path.join(rd, f"livery_{name}.png")
        M.render(objs + screen_objs, path, az=-35, el=22, size=(1000, 1200))
        imgs.append(Image.open(path))
        print("render", name)
    W_ = sum(i.width for i in imgs)
    sheet = Image.new("RGB", (W_, imgs[0].height), (244, 245, 248))
    x = 0
    for i in imgs:
        sheet.paste(i, (x, 0))
        x += i.width
    sheet.save(os.path.join(rd, "livery_options.png"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
