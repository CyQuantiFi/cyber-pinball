"""Build every cabinet output from geometry.py.

    python3 cabinet/make_cabinet.py           everything (about 3 minutes, mostly the renders)
    python3 cabinet/make_cabinet.py --check   clearance check + nesting only (seconds)
    SKIP_RENDER=1 python3 cabinet/make_cabinet.py   keep the existing PNG renders

Needs: pip install -r cabinet/requirements.txt

Writes to cabinet/out/:
    dxf/P##_<part>.dxf        one file per part, mm, cut-face up
    sheets/<material>_#.dxf   parts nested on 2400 x 1200 sheets (for the CNC)
    drawings.pdf              A3 dimensioned drawings: overview, elevations, every part, sheet layouts
    cabinet.glb               full 3D model (opens in Windows 3D Viewer, Blender, online viewers)
    stl/<module>.stl          one mesh per transport module (body, backbox, legs)
    render/*.png              shaded views
    cutlist.csv               part, material, size, qty, area, weight
Exits non-zero if the clearance check finds a collision.
"""
import csv
import math
import os
import sys

import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                     # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.patches import Polygon as MplPoly     # noqa: E402
import numpy as np                                   # noqa: E402
import trimesh                                       # noqa: E402
from PIL import Image                                # noqa: E402
from shapely import affinity                         # noqa: E402
from shapely.geometry import MultiPolygon, Polygon   # noqa: E402
from shapely.ops import unary_union                  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
import geometry as G                                 # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
SHEET = dict(ply18=(2400, 1200), ply6=(2400, 1200), mdf6=(2400, 1200), acrylic3=(1200, 600))
MAT_NAME = dict(ply18="18 mm plywood", ply6="6 mm plywood", mdf6="6 mm MDF", glass5="5 mm toughened glass",
                acrylic3="3 mm clear cast acrylic")
GAP, MARGIN = 14.0, 15.0     # spacing between nested parts (6 mm bit + tabs) and sheet edge margin
PAINTED = {"Body side L", "Body side R", "Body front", "Body back", "Backbox side L", "Backbox side R",
           "Backbox top", "Backbox back", "Leg frame plate", "Leg top plate", "Leg stretcher", "Wedge",
           "Speaker / DMD panel", "Rear deck", "Backbox bottom", "Body floor", "Lockbar stop strip",
           "Back service cover"}
BACKBOX_COMPS = ("24in", "DMD", "4in speaker")


def comp_module(c):
    return "backbox" if any(k in c.name for k in BACKBOX_COMPS) else "body"


def slug(s):
    return "".join(c.lower() if c.isalnum() else "_" for c in s).strip("_").replace("__", "_")


# ---------------------------------------------------------------- 2D (cut face up)
def polys(geom):
    if geom.is_empty:
        return []
    return list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]


def part2d(p):
    """All 2D geometry of a part as seen from its cut face, moved so the outline starts at (0, 0)."""
    mir = p.frame.mirrored
    x0, y0, x1, y1 = p.outline.bounds

    def tf(g):
        g = affinity.translate(g, -x0, -y0)
        return affinity.scale(g, -1, 1, origin=((x1 - x0) / 2, 0)) if mir else g

    def tp(u, v):
        u, v = u - x0, v - y0
        return ((x1 - x0) - u if mir else u), v

    return dict(
        outline=tf(p.outline),
        cuts=[tf(c) for c in p.cuts],
        circles=[(*tp(cx, cy), d, layer) for cx, cy, d, layer in p.circles],
        pockets=[(tf(pk[0]), pk[1], pk[2] if len(pk) > 2 else "top") for pk in p.pockets],
        engrave=[[tp(u, v) for u, v in line] for line in p.engrave],
        marks=[[tp(u, v) for u, v in line] for line in p.marks],
        size=(x1 - x0, y1 - y0), mirrored=mir)


def add_poly(msp, poly, layer, dx=0.0, dy=0.0, rot=False, H=0.0):
    for ring in [poly.exterior, *poly.interiors]:
        pts = [xf(u, v, dx, dy, rot, H) for u, v in ring.coords]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})


def xf(u, v, dx, dy, rot, H):
    """Place a part point on a sheet: optional 90 degree turn, then shift."""
    if rot:
        u, v = H - v, u
    return (u + dx, v + dy)


LAYERS = [("CUT_OUTSIDE", 1), ("CUT_INSIDE", 5), ("DRILL", 3), ("POCKET_6", 6), ("POCKET_6_BACK", 30),
          ("ENGRAVE", 4), ("MARK", 8), ("NOTES", 7)]


def new_doc():
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    for name, col in LAYERS:
        doc.layers.add(name, color=col)
    return doc


def draw_part_dxf(msp, g, label, dx=0.0, dy=0.0, rot=False):
    H = g["size"][1]
    for poly in polys(g["outline"]):
        add_poly(msp, Polygon(poly.exterior), "CUT_OUTSIDE", dx, dy, rot, H)
    for c in g["cuts"]:
        for poly in polys(c):
            add_poly(msp, Polygon(poly.exterior), "CUT_INSIDE", dx, dy, rot, H)
    for cx, cy, d, layer in g["circles"]:
        msp.add_circle(xf(cx, cy, dx, dy, rot, H), d / 2, dxfattribs={"layer": layer})
    for poly, depth, face in g["pockets"]:
        for pp in polys(poly):
            add_poly(msp, pp, f"POCKET_{depth:g}" + ("_BACK" if face == "bottom" else ""), dx, dy, rot, H)
    for line in g["engrave"]:
        msp.add_lwpolyline([xf(u, v, dx, dy, rot, H) for u, v in line], close=True, dxfattribs={"layer": "ENGRAVE"})
    for line in g["marks"]:
        msp.add_lwpolyline([xf(u, v, dx, dy, rot, H) for u, v in line], dxfattribs={"layer": "MARK"})
    w, h = g["size"]
    cx, cy = xf(w / 2, h / 2, dx, dy, rot, H)
    msp.add_text(label, height=12, dxfattribs={"layer": "NOTES"}).set_placement(
        (cx, cy), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)


# ---------------------------------------------------------------- nesting
def nest(items, sheet):
    """MaxRects packing (best short-side fit) of (key, w, h) rectangles; parts may turn 90 degrees.

    Returns a list of sheets, each a list of (key, x, y, rotated)."""
    SW, SH = sheet
    UW, UH = SW - 2 * MARGIN + GAP, SH - 2 * MARGIN + GAP
    order = sorted(items, key=lambda it: (-it[1] * it[2], -max(it[1], it[2])))
    sheets = []     # dict(free=[(x, y, w, h)], parts=[])

    def split(free, px, py, pw, ph):
        out = []
        for fx, fy, fw, fh in free:
            if px >= fx + fw or px + pw <= fx or py >= fy + fh or py + ph <= fy:
                out.append((fx, fy, fw, fh))
                continue
            if px > fx:
                out.append((fx, fy, px - fx, fh))
            if px + pw < fx + fw:
                out.append((px + pw, fy, fx + fw - px - pw, fh))
            if py > fy:
                out.append((fx, fy, fw, py - fy))
            if py + ph < fy + fh:
                out.append((fx, py + ph, fw, fy + fh - py - ph))
        keep = []
        for i, r in enumerate(out):
            if r[2] <= 0 or r[3] <= 0:
                continue
            if any(j != i and q[0] <= r[0] and q[1] <= r[1] and q[0] + q[2] >= r[0] + r[2]
                   and q[1] + q[3] >= r[1] + r[3] and (q != r or j < i) for j, q in enumerate(out)):
                continue
            keep.append(r)
        return keep

    for key, w, h in order:
        best = None
        for si, sh in enumerate(sheets + [dict(free=[(0, 0, UW, UH)], parts=[])]):
            for rot, (pw, ph) in ((False, (w + GAP, h + GAP)), (True, (h + GAP, w + GAP))):
                for fx, fy, fw, fh in sh["free"]:
                    if pw <= fw and ph <= fh:
                        score = (si, min(fw - pw, fh - ph), max(fw - pw, fh - ph))
                        if best is None or score < best[0]:
                            best = (score, si, fx, fy, pw, ph, rot)
            if best is not None and best[1] == si:
                break
        if best is None:
            raise SystemExit(f"part {key} does not fit a {SW} x {SH} sheet")
        _, si, fx, fy, pw, ph, rot = best
        if si == len(sheets):
            sheets.append(dict(free=[(0, 0, UW, UH)], parts=[]))
        sh = sheets[si]
        sh["parts"].append((key, fx + MARGIN, fy + MARGIN, rot))
        sh["free"] = split(sh["free"], fx, fy, pw, ph)
    return [sh["parts"] for sh in sheets]


# ---------------------------------------------------------------- meshes
def part_meshes(p):
    out = []
    sol = p.solid()
    for fr in G.placements(p):
        for poly in polys(sol):
            m = trimesh.creation.extrude_polygon(poly, p.t)
            v = fr.to_world(m.vertices)
            f = m.faces[:, ::-1] if fr.mirrored else m.faces
            out.append(trimesh.Trimesh(v, f, process=False))
    return out


def comp_mesh(c):
    m = trimesh.creation.box(extents=np.array(c.hi) - np.array(c.lo))
    m.apply_translation((np.array(c.hi) + np.array(c.lo)) / 2)
    v = c.frame.to_world(m.vertices)
    f = m.faces[:, ::-1] if c.frame.mirrored else m.faces
    return trimesh.Trimesh(v, f, process=False)


def part_color(p, painted=True):
    if painted and p.name in PAINTED:
        return G.PAINT
    return p.color if tuple(p.color) != G.COL["ply18"] else G.COL[p.material]


def part_bias(p):
    """Sides lose depth ties against the panels that sit in their dados (no z-fighting)."""
    return 0.4 if "side" in p.name.lower() else 0.0


def screen_textures(comps):
    """Screen art for the renders: dict component name -> texture spec."""
    from PIL import ImageDraw, ImageFont
    root = os.path.join(HERE, "..")

    def letterbox(src, w, h, px=4):
        im = Image.open(src).convert("RGB")
        W_, H_ = int(w * px), int(h * px)
        k = min(W_ / im.width, H_ / im.height)
        im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
        out = Image.new("RGB", (W_, H_), (0, 0, 0))
        out.paste(im, ((W_ - im.width) // 2, (H_ - im.height) // 2))
        return np.asarray(out, float) / 255

    tv_w, tv_l = G.P["TV_VIEW"][1], G.P["TV_VIEW"][0]
    ms0 = G.P["LOCKBAR"] + 5
    tex = {}
    tex["32in monitor (playfield)"] = dict(
        img=letterbox(os.path.join(root, "art/render/playfield.png"), tv_w, tv_l), axes=(0, 1), face=(2, G.TV_D[0]),
        rect=(G.XC - tv_w / 2, ms0, G.XC + tv_w / 2, ms0 + tv_l))
    mon = [c for c in comps if c.name.startswith("24in")][0]
    mw, mh = G.P["MON_VIEW"]
    zc = (mon.lo[2] + mon.hi[2]) / 2
    tex[mon.name] = dict(img=letterbox(os.path.join(root, "art/render/backglass.png"), mw, mh), axes=(0, 2),
                         face=(1, mon.lo[1]), rect=(G.XC - mw / 2, zc - mh / 2, G.XC + mw / 2, zc + mh / 2))
    dmd = [c for c in comps if "DMD" in c.name][0]
    dw, dh = G.P["DMD_VIEW"]
    im = Image.new("RGB", (int(dw * 4), int(dh * 4)), (0, 0, 0))
    font = ImageFont.truetype(os.path.join(root, "art/fonts/Comfortaa-VariableFont_wght.ttf"), int(dh * 1.3))
    ImageDraw.Draw(im).text((im.width / 2, im.height / 2), "THREAT TIDE", font=font, fill=(255, 120, 20), anchor="mm")
    zc = (dmd.lo[2] + dmd.hi[2]) / 2
    tex[dmd.name] = dict(img=np.asarray(im, float) / 255, axes=(0, 2), face=(1, dmd.lo[1]),
                         rect=(G.XC - dw / 2, zc - dh / 2, G.XC + dw / 2, zc + dh / 2))
    return tex


# ---------------------------------------------------------------- rasteriser
def look(az, el):
    """Rotation for an orthographic camera: azimuth around z, elevation (degrees)."""
    a, e = math.radians(az), math.radians(el)
    fwd = np.array([math.cos(e) * math.sin(a), math.cos(e) * math.cos(a), -math.sin(e)])   # view direction
    right = np.cross(fwd, [0, 0, 1])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return np.array([right, up, fwd])


def render(objs, path, az=-35, el=24, size=(1600, 1200), ss=2, light=(-0.4, -0.6, 0.7), bg=(244, 245, 248)):
    """objs: list of (trimesh, rgb[, bias[, texture]]). Z-buffered orthographic render with outline edges.

    texture: dict(img, frame, axes=(i, j), face=(k, value), rect=(u0, v0, u1, v1)) maps an image onto the
    pixels of that object lying on the face local[k] == value (frame local coords; default world)."""
    R = look(az, el)
    tris, cols, ids, bias = [], [], [], []
    for i, o in enumerate(objs):
        m, c = o[0], o[1]
        t = m.vertices[m.faces]
        tris.append(t)
        cols.append(np.tile(c, (len(t), 1)))
        ids.append(np.full(len(t), i))
        bias.append(np.full(len(t), o[2] if len(o) > 2 else 0.0))
    tris = np.concatenate(tris)
    cols = np.concatenate(cols)
    ids = np.concatenate(ids)
    bias = np.concatenate(bias)
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    ln = np.linalg.norm(n, axis=1)
    ok = ln > 1e-9
    tris, cols, ids, bias, n = tris[ok], cols[ok], ids[ok], bias[ok], n[ok] / ln[ok, None]
    Ld = np.array(light) / np.linalg.norm(light)
    shade = 0.42 + 0.58 * np.abs(n @ Ld)
    rgb = np.clip(cols * shade[:, None], 0, 1)
    v = tris @ R.T             # x right, y up, z depth (towards the scene)
    W, H = size[0] * ss, size[1] * ss
    lo, hi = v[..., :2].reshape(-1, 2).min(0), v[..., :2].reshape(-1, 2).max(0)
    sc = 0.9 * min(W / (hi[0] - lo[0]), H / (hi[1] - lo[1]))
    mid = (lo + hi) / 2
    px = (v[..., 0] - mid[0]) * sc + W / 2
    py = H / 2 - (v[..., 1] - mid[1]) * sc
    pz = v[..., 2]
    zbuf = np.full((H, W), np.inf)
    img = np.ones((H, W, 3)) * np.array(bg) / 255
    idb = np.full((H, W), -1)
    nrm = np.zeros((H, W, 3))
    pos = np.zeros((H, W, 3))
    for k in range(len(px)):
        x, y, z = px[k], py[k], pz[k]
        x0, x1 = max(int(x.min()), 0), min(int(x.max()) + 1, W - 1)
        y0, y1 = max(int(y.min()), 0), min(int(y.max()) + 1, H - 1)
        if x0 > x1 or y0 > y1:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(d) < 1e-12:
            continue
        a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d
        b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
        c = 1 - a - b
        inside = (a >= -1e-6) & (b >= -1e-6) & (c >= -1e-6)
        if not inside.any():
            continue
        zz = a * z[0] + b * z[1] + c * z[2] + bias[k]
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        win = inside & (zz < sub)
        sub[win] = zz[win]
        img[y0:y1 + 1, x0:x1 + 1][win] = rgb[k]
        idb[y0:y1 + 1, x0:x1 + 1][win] = ids[k]
        nrm[y0:y1 + 1, x0:x1 + 1][win] = n[k]
        T3 = tris[k]
        pos[y0:y1 + 1, x0:x1 + 1][win] = (a[win, None] * T3[0] + b[win, None] * T3[1] + c[win, None] * T3[2])
    for i, o in enumerate(objs):
        if len(o) < 4 or o[3] is None:
            continue
        tx = o[3]
        msk = idb == i
        loc = tx.get("frame", G.WORLD).to_local(pos[msk])
        k, val = tx["face"]
        on = np.abs(loc[:, k] - val) < 1.0
        u0, v0, u1, v1 = tx["rect"]
        uu = (loc[:, tx["axes"][0]] - u0) / (u1 - u0)
        vv = (loc[:, tx["axes"][1]] - v0) / (v1 - v0)
        on &= (uu >= 0) & (uu <= 1) & (vv >= 0) & (vv <= 1)
        ih, iw = tx["img"].shape[:2]
        col = tx["img"][np.clip(((1 - vv) * ih).astype(int), 0, ih - 1), np.clip((uu * iw).astype(int), 0, iw - 1)]
        sel = img[msk]
        sel[on] = col[on]
        img[msk] = sel
    # outline edges: object change, crease, or depth step
    edge = np.zeros((H, W), bool)
    for dy, dx in ((0, 1), (1, 0)):
        a_id, b_id = idb[:H - dy, :W - dx], idb[dy:, dx:]
        a_n, b_n = nrm[:H - dy, :W - dx], nrm[dy:, dx:]
        a_z, b_z = zbuf[:H - dy, :W - dx], zbuf[dy:, dx:]
        e = ((a_id != b_id) | (np.abs((a_n * b_n).sum(-1)) < 0.95)) & ((a_id >= 0) | (b_id >= 0))
        with np.errstate(invalid="ignore"):
            e |= np.abs(a_z - b_z) > 6
        edge[:H - dy, :W - dx] |= e
    img[edge] = img[edge] * 0.25
    im = Image.fromarray((img * 255).astype(np.uint8)).resize(size, Image.LANCZOS)
    im.save(path)


# ---------------------------------------------------------------- PDF helpers
A3 = (16.535, 11.693)


def axes_mm(fig, x_mm, y_mm, w_mm, h_mm):
    """Axes placed in page millimetres (A3 landscape 420 x 297)."""
    return fig.add_axes([x_mm / 420, y_mm / 297, w_mm / 420, h_mm / 297])


def scaled_axes(fig, bounds, box_mm, scales=(1, 2, 2.5, 4, 5, 8, 10, 15, 20)):
    """Axes at a true print scale 1:N that fits bounds (x0, y0, x1, y1) into box (x, y, w, h) mm."""
    x0, y0, x1, y1 = bounds
    bx, by, bw, bh = box_mm
    for s in scales:
        if (x1 - x0) / s <= bw and (y1 - y0) / s <= bh:
            break
    w, h = bw * s, bh * s
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    ax = axes_mm(fig, bx, by, bw, bh)
    ax.set_xlim(cx - w / 2, cx + w / 2)
    ax.set_ylim(cy - h / 2, cy + h / 2)
    ax.set_aspect("equal")
    ax.axis("off")
    return ax, s


def dim(ax, p1, p2, off, text=None, fs=7, color="#204080"):
    """Linear dimension between p1 and p2, drawn `off` mm to the left of the p1->p2 direction."""
    p1, p2 = np.array(p1, float), np.array(p2, float)
    d = p2 - p1
    L = np.linalg.norm(d)
    if L < 1e-6:
        return
    nrm = np.array([-d[1], d[0]]) / L
    a, b = p1 + nrm * off, p2 + nrm * off
    ext = np.sign(off) * nrm * 3 * abs(off) / max(abs(off), 1e-9)
    ax.plot([p1[0], a[0] + ext[0]], [p1[1], a[1] + ext[1]], lw=0.3, color=color)
    ax.plot([p2[0], b[0] + ext[0]], [p2[1], b[1] + ext[1]], lw=0.3, color=color)
    ax.annotate("", a, b, arrowprops=dict(arrowstyle="<->", lw=0.5, color=color, shrinkA=0, shrinkB=0))
    ang = math.degrees(math.atan2(d[1], d[0]))
    if ang > 90 or ang < -90:
        ang += 180
    m = (a + b) / 2 + nrm * np.sign(off) * 0.0
    ax.text(m[0], m[1], text or f"{L:.0f}", fontsize=fs, rotation=ang, ha="center", va="center", color=color,
            bbox=dict(fc="white", ec="none", pad=0.6))


def title_block(fig, title, sub="", page=None):
    fig.text(0.02, 0.965, title, fontsize=16, weight="bold")
    if sub:
        fig.text(0.02, 0.94, sub, fontsize=9, color="#444")
    fig.text(0.98, 0.015, "Threat Tide cabinet  |  all dimensions mm  |  generated by cabinet/make_cabinet.py"
             + (f"  |  sheet {page}" if page else ""), fontsize=7, ha="right", color="#666")


def patch(poly, **kw):
    """Matplotlib patch for a shapely polygon including its holes."""
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch
    verts, codes = [], []
    for ring in [poly.exterior, *poly.interiors]:
        c = np.asarray(ring.coords)
        verts += c.tolist()
        codes += [Path.MOVETO] + [Path.LINETO] * (len(c) - 2) + [Path.CLOSEPOLY]
    return PathPatch(Path(verts, codes), **kw)


def draw_geom(ax, g, hatch_pockets=True, lw=1.0):
    for poly in polys(g["outline"]):
        ax.add_patch(MplPoly(np.array(poly.exterior.coords), closed=True, fc="#f6efe2", ec="black", lw=lw))
    for poly, depth, face in g["pockets"]:
        for pp in polys(poly):
            ax.add_patch(MplPoly(np.array(pp.exterior.coords), closed=True, fc="#d9c7a7" if face == "top" else "#c8d4e6",
                                 ec="#806040", lw=0.4, hatch="////" if hatch_pockets else None))
    for c in g["cuts"]:
        for poly in polys(c):
            ax.add_patch(MplPoly(np.array(poly.exterior.coords), closed=True, fc="white", ec="black", lw=lw * 0.8))
    for cx, cy, d, layer in g["circles"]:
        ax.add_patch(plt.Circle((cx, cy), d / 2, fc="white", ec="black" if layer == "CUT_INSIDE" else "#007000",
                                lw=lw * 0.7))
        if layer == "DRILL":
            ax.plot([cx - d, cx + d], [cy, cy], lw=0.25, color="#007000")
            ax.plot([cx, cx], [cy - d, cy + d], lw=0.25, color="#007000")
    for line in g["engrave"]:
        a = np.array(line + [line[0]])
        ax.plot(a[:, 0], a[:, 1], lw=0.3, color="#0090a0")
    for line in g["marks"]:
        a = np.array(line)
        ax.plot(a[:, 0], a[:, 1], lw=0.6, color="#b00000", ls="--")


def project(meshes, axes):
    """Silhouette polygon of meshes projected on two world axes (e.g. (1, 2) = side view)."""
    tris = np.concatenate([m.vertices[m.faces][:, :, axes] for m in meshes])
    a = (tris[:, 1, 0] - tris[:, 0, 0]) * (tris[:, 2, 1] - tris[:, 0, 1]) - \
        (tris[:, 2, 0] - tris[:, 0, 0]) * (tris[:, 1, 1] - tris[:, 0, 1])
    tris = tris[np.abs(a) > 1e-6]
    return unary_union([Polygon(t) for t in tris]).buffer(0.01).buffer(-0.01)


# ---------------------------------------------------------------- main
def main():
    os.makedirs(OUT, exist_ok=True)
    for d in ("dxf", "sheets", "stl", "render"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
        for f in os.listdir(os.path.join(OUT, d)):
            os.remove(os.path.join(OUT, d, f))
    parts, comps = G.build()
    problems = G.check(parts, comps)
    print("clearance check:", "OK" if not problems else "\n  " + "\n  ".join(problems))
    if "--check" in sys.argv:
        for p in parts:
            p.g2 = part2d(p)
        for mat in G.DENS:
            items = [((p.name, k), *p.g2["size"]) for p in parts if p.cnc and p.material == mat
                     for k in range(len(G.placements(p)))]
            if items:
                print(f"{mat}: {len(nest(items, SHEET[mat]))} sheet(s)")
        return 1 if problems else 0
    mods = G.modules(parts)

    # ---- per-part DXF + cut list
    rows = []
    for i, p in enumerate(parts, 1):
        p.pid = f"P{i:02d}"
        p.g2 = part2d(p)
        qty = len(G.placements(p)) if getattr(p, "frames", None) else p.qty
        p.qty = qty
        w, h = p.g2["size"]
        kg = p.area_m2() * p.t / 1000 * G.DENS[p.material]
        rows.append([p.pid, p.name, p.module, MAT_NAME[p.material], f"{w:.1f}", f"{h:.1f}", qty,
                     "CNC" if p.cnc else "supplier", f"{kg * qty:.1f}", p.notes])
        if not p.cnc:
            continue
        doc = new_doc()
        draw_part_dxf(doc.modelspace(), p.g2, f"{p.pid} {p.name}")
        doc.saveas(os.path.join(OUT, "dxf", f"{p.pid}_{slug(p.name)}.dxf"))
    with open(os.path.join(OUT, "cutlist.csv"), "w", newline="") as f:
        cw = csv.writer(f)
        cw.writerow(["id", "part", "module", "material", "width_mm", "height_mm", "qty", "made_by", "kg_total", "notes"])
        cw.writerows(rows)

    # ---- nested sheets
    by_mat = {}
    for p in parts:
        if p.cnc:
            for k in range(p.qty):
                w, h = p.g2["size"]
                by_mat.setdefault(p.material, []).append(((p.pid, k), w, h))
    layouts = {}
    for mat, items in by_mat.items():
        lay = nest(items, SHEET[mat])
        layouts[mat] = lay
        pmap = {p.pid: p for p in parts}
        for si, sh in enumerate(lay, 1):
            doc = new_doc()
            msp = doc.modelspace()
            SW, SH = SHEET[mat]
            msp.add_lwpolyline([(0, 0), (SW, 0), (SW, SH), (0, SH)], close=True, dxfattribs={"layer": "NOTES"})
            for (pid, k), x, y, rot in sh:
                p = pmap[pid]
                draw_part_dxf(msp, p.g2, f"{pid} {p.name}", x, y, rot)
            doc.saveas(os.path.join(OUT, "sheets", f"{mat}_{si}.dxf"))
    print("sheets:", {m: len(v) for m, v in layouts.items()})

    # ---- meshes, GLB, STL
    scene = trimesh.Scene()
    mod_meshes = {}
    objs_parts = []
    for p in parts:
        for m in part_meshes(p):
            col = part_color(p)
            rgba = (np.array(list(col) + [0.35 if p.material == "glass5" else 1.0]) * 255).astype(np.uint8)
            mm = m.copy()
            mm.visual.face_colors = rgba
            scene.add_geometry(mm, node_name=f"{p.pid} {p.name}")
            mod_meshes.setdefault(p.module, []).append(m)
            objs_parts.append((p, m))
    for c in comps:
        m = comp_mesh(c)
        if c.name == "Hand room":
            continue
        mm = m.copy()
        mm.visual.face_colors = (np.array(list(c.color) + [1]) * 255).astype(np.uint8)
        scene.add_geometry(mm, node_name=c.name)
    ground = np.array([0, 0, -G.P["LEG_TOP"]])
    scene.apply_translation(-ground)
    scene.export(os.path.join(OUT, "cabinet.glb"))
    for mod, ms in mod_meshes.items():
        trimesh.util.concatenate(ms).export(os.path.join(OUT, "stl", f"{mod}.stl"))

    # ---- renders
    tex = screen_textures(comps)
    for c in comps:
        if c.name in tex:
            tex[c.name]["frame"] = c.frame
    shown = [c for c in comps if c.name != "Hand room"]
    comp_objs = [(comp_mesh(c), c.color, -0.2, tex.get(c.name)) for c in shown]
    screens = [o for o, c in zip(comp_objs, shown) if c.name in tex or "Plunger knob" in c.name or "speaker" in c.name]
    from PIL import ImageDraw, ImageFilter, ImageFont
    font = ImageFont.truetype(os.path.join(HERE, "..", "art/fonts/Comfortaa-VariableFont_wght.ttf"), 300)
    acr = {}
    for p in parts:
        if p.material == "acrylic3":
            x0, y0, x1, y1 = p.outline.bounds
            im = Image.new("RGB", (int((x1 - x0) * 4), int((y1 - y0) * 4)), (60, 140, 150))
            glow = Image.new("RGB", im.size, (0, 0, 0))
            ImageDraw.Draw(glow).text((im.width / 2, im.height / 2), "THREAT TIDE", font=font, fill=(120, 255, 255),
                                      anchor="mm")
            im = Image.fromarray(np.clip(np.asarray(im, float) + np.asarray(glow.filter(ImageFilter.GaussianBlur(14)), float)
                                         + np.asarray(glow, float) * 0.8, 0, 255).astype(np.uint8))
            if not p.frame.mirrored:
                im = im.transpose(Image.FLIP_LEFT_RIGHT)
            acr[p.name] = dict(img=np.asarray(im, float) / 255, frame=p.frame, axes=(0, 1), face=(2, 0.0),
                               rect=(x0, y0, x1, y1))
    vis = [(m, part_color(p), part_bias(p), acr.get(p.name)) for p, m in objs_parts if p.material != "glass5"]
    rd = os.path.join(OUT, "render")
    if os.environ.get("SKIP_RENDER") != "1":
        render(vis + screens, os.path.join(rd, "cabinet_front.png"), az=-35, el=22)
        render(vis + screens, os.path.join(rd, "cabinet_rear.png"), az=145, el=22)
        hide = {"Body side L", "Side light panel L", "Playfield mask", "Backbox side L", "Lockbar",
                "Lockbar stop strip", "Leg frame plate", "Leg top plate", "Leg stretcher", "Wedge"}
        inside = [(m, part_color(p, painted=False), part_bias(p)) for p, m in objs_parts
                  if p.name not in hide and p.material != "glass5"]
        render(inside + [o for o, c in zip(comp_objs, shown) if "32in" not in c.name],
               os.path.join(rd, "cabinet_inside.png"), az=-58, el=48)
        # transport: modules pulled apart
        off = dict(body=np.array([0, 0, 0]), backbox=np.array([0, 500, -250]), legs=np.array([900, 0, 0]))
        expl = []
        for p, m in objs_parts:
            if p.material == "glass5":
                continue
            mm = m.copy()
            mm.apply_translation(off[p.module])
            t = acr.get(p.name)
            if t:
                f = t["frame"]
                t = dict(t, frame=G.Frame(tuple(np.array(f.o) + off[p.module]), f.eu, f.ev, f.ew))
            expl.append((mm, part_color(p), part_bias(p), t))
        for (m, col, b, t), c in zip(screens, [c for c in shown if c.name in tex or "Plunger knob" in c.name
                                               or "speaker" in c.name]):
            o = off[comp_module(c)]
            mm = m.copy()
            mm.apply_translation(o)
            if t:
                t = dict(t, frame=G.Frame(tuple(np.array(c.frame.o) + o), c.frame.eu, c.frame.ev, c.frame.ew))
            expl.append((mm, col, b, t))
        render(expl, os.path.join(rd, "transport_modules.png"), az=-40, el=26)
    print("renders done")

    # ---- PDF
    pdf_path = os.path.join(OUT, "drawings.pdf")
    with PdfPages(pdf_path) as pdf:
        page = 1
        # overview
        fig = plt.figure(figsize=A3)
        title_block(fig, "Threat Tide pinball cabinet", "32\" playfield, 24\" backglass + 12.3\" DMD bar, "
                    "18 mm plywood, knock-down for van / ute transport", page)
        for k, (img, x) in enumerate((("cabinet_front.png", 8), ("cabinet_inside.png", 145), ("transport_modules.png", 282))):
            ax = axes_mm(fig, x, 105, 130, 165)
            ax.imshow(Image.open(os.path.join(OUT, "render", img)))
            ax.set_title(["Assembled", "Inside (left side hidden)", "Transport modules"][k], fontsize=10)
            ax.axis("off")
        hl = G.P["LEG_TOP"]
        lines = [
            f"Overall: {G.W:.0f} W x {G.L + 95:.0f} D (incl. plunger) x {hl + 939:.0f} H mm",
            f"Lockbar height {hl + G.HF + 18:.0f} mm, playfield slope {G.P['SLOPE']} deg (built into the sides)",
            "",
            "Transport modules (empty weight estimate, plywood 600 kg/m3):",
        ]
        for mod in ("body", "backbox", "legs"):
            d = mods[mod]
            sz = d["hi"] - d["lo"]
            lines.append(f"  {mod:8s} {sz[0]:5.0f} x {sz[1]:5.0f} x {sz[2]:5.0f} mm   ~{d['kg']:4.1f} kg wood")
        lines += ["  + components: body ~13 kg (monitor, PC, contactors, shakers), backbox ~6 kg",
                  "",
                  "Clearance check: " + ("passed - no part or component collisions" if not problems
                                         else f"{len(problems)} problems (see console)"),
                  "",
                  "Sheets: " + ", ".join(f"{len(v)} x {MAT_NAME[m]}" for m, v in layouts.items()),
                  "DXF layers: CUT_OUTSIDE, CUT_INSIDE, DRILL, POCKET_6 (6 deep), POCKET_6_BACK (other face),",
                  "            ENGRAVE, MARK (layout lines, do not cut), NOTES"]
        fig.text(0.03, 0.30, "\n".join(lines), fontsize=9, family="monospace", va="top")
        pdf.savefig(fig)
        plt.close(fig)

        # elevations
        page += 1
        fig = plt.figure(figsize=A3)
        title_block(fig, "General arrangement", "Side, front and plan views at 1:10 on A3. Ground = 0.", page)
        allm = [m.copy() for p, m in objs_parts]
        for m in allm:
            m.apply_translation(-ground)
        compm = [comp_mesh(c) for c in comps if c.name != "Hand room"]
        for m in compm:
            m.apply_translation(-ground)
        views = [((1, 2), (15, 30, 150, 230), "Side elevation (from left)"),
                 ((0, 2), (180, 30, 90, 230), "Front elevation"),
                 ((0, 1), (290, 60, 90, 150), "Plan")]
        for axes_ij, box_mm, name in views:
            ax, s = scaled_axes(fig, (-150, -60, 1200, 1700) if axes_ij == (1, 2) else
                                ((-60, -60, 660, 1700) if axes_ij == (0, 2) else (-60, -150, 660, 1200)),
                                box_mm, scales=(10,))
            sil = [project([m], axes_ij) for m in allm]
            for sp in sil:
                for poly in polys(sp):
                    ax.add_patch(patch(poly, fc="#efe6d6", ec="black", lw=0.4))
            for m in compm:
                for poly in polys(project([m], axes_ij)):
                    ax.add_patch(MplPoly(np.array(poly.exterior.coords), closed=True, fc="none", ec="#3060c0",
                                         lw=0.4, ls="--"))
            ax.set_title(name + f"  1:{s}", fontsize=9)
            ax.plot([-100, 1200], [0, 0], color="#888", lw=0.5) if axes_ij != (0, 1) else None
            if axes_ij == (1, 2):
                dim(ax, (0, 0), (0, hl + G.HF), 60, f"{hl + G.HF:.0f} side top / {hl + G.HF + 18:.0f} lockbar")
                dim(ax, (G.L, 0), (G.L, hl + G.top(G.L)), -40)
                zt = hl + G.top(818) + G.P["BB_FRONT"]
                dim(ax, (1100, 0), (1100, zt), -60, f"{zt:.0f}")
                dim(ax, (0, -30), (G.L, -30), 0, f"{G.L:.0f}")
                y0, y1 = G.P["TRESTLE_Y"]
                dim(ax, (y0, 40), (y1, 40), 0, f"leg frames {y1 - y0:.0f} apart")
                dim(ax, (818, zt + 20), (1060, zt + 20), 0, "242")
            elif axes_ij == (0, 2):
                dim(ax, (0, -30), (G.W, -30), 0, f"{G.W:.0f}")
                dim(ax, (0, hl), (0, hl + G.HF), 40, f"{G.HF:.0f}")
                dim(ax, (G.W + 10, 0), (G.W + 10, hl), -30, f"{hl:.0f}")
            else:
                dim(ax, (0, -110), (G.W, -110), 0, f"{G.W:.0f}")
                dim(ax, (-30, 0), (-30, G.L), -0.01, f"{G.L:.0f}")
        fig.text(0.70, 0.12, "Blue dashed = bought components (monitor, PC, buttons, plunger, contactors,\n"
                 "shakers, supplies, speakers). Clearances are checked automatically in code.", fontsize=8)
        pdf.savefig(fig)
        plt.close(fig)

        # one page per part
        for p in parts:
            page += 1
            fig = plt.figure(figsize=A3)
            g = p.g2
            title_block(fig, f"{p.pid}  {p.name}",
                        f"{MAT_NAME[p.material]}  |  qty {p.qty}  |  module: {p.module}"
                        + ("  |  supplier cut" if not p.cnc else "")
                        + ("  |  drawn mirrored: shows the cut face (same as the DXF)" if g["mirrored"] else ""), page)
            w, h = g["size"]
            ax, s = scaled_axes(fig, (-60, -60, w + 60, h + 60), (15, 30, 285, 235))
            draw_geom(ax, g)
            dim(ax, (0, -25), (w, -25), 0)
            dim(ax, (-25, 0), (-25, h), 0.001)
            # ordinate dims for every hole
            for k, (cx, cy, d, layer) in enumerate(g["circles"], 1):
                ax.text(cx + d / 2 + 2, cy + d / 2 + 2, str(k), fontsize=6, color="#007000" if layer == "DRILL" else "black")
            for poly, depth, face in g["pockets"]:
                for pp in polys(poly):
                    c = pp.representative_point()
                    ax.text(c.x, c.y, f"{depth:g} deep" + (" (back)" if face == "bottom" else ""), fontsize=6,
                            ha="center", color="#604020")
            for c in g["cuts"]:
                b = c.bounds
                ax.text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, f"{b[2] - b[0]:.0f} x {b[3] - b[1]:.0f}",
                        fontsize=5.5, ha="center", va="center", color="#555")
            ax.set_title(f"scale 1:{s} at A3 (origin = lower-left corner)", fontsize=8, loc="left")
            info = [p.notes, ""] if p.notes else []
            if g["circles"]:
                info.append(" #   dia     X       Y     op")
                for k, (cx, cy, d, layer) in enumerate(g["circles"], 1):
                    info.append(f"{k:2d} {d:6.1f} {cx:7.1f} {cy:7.1f}  {'drill' if layer == 'DRILL' else 'profile'}")
            if g["pockets"]:
                info.append("")
                info.append("Pockets (bounding boxes):")
                for poly, depth, face in g["pockets"]:
                    b = poly.bounds
                    info.append(f"  {b[0]:.1f},{b[1]:.1f} to {b[2]:.1f},{b[3]:.1f}  {depth:g} deep {face}")
            import textwrap
            out = []
            for line in info:
                out += textwrap.wrap(line, 52) or [""]
            fig.text(0.735, 0.88, "\n".join(out[:60]), fontsize=7, family="monospace", va="top")
            pdf.savefig(fig)
            plt.close(fig)

        # sheet layouts
        pmap = {p.pid: p for p in parts}
        for mat, lay in layouts.items():
            for si, sh in enumerate(lay, 1):
                page += 1
                fig = plt.figure(figsize=A3)
                SW, SH = SHEET[mat]
                title_block(fig, f"Sheet layout: {MAT_NAME[mat]}  #{si} of {len(lay)}",
                            f"{SW} x {SH} sheet, {GAP:.0f} mm between parts. File: sheets/{mat}_{si}.dxf", page)
                ax, s = scaled_axes(fig, (-20, -20, SW + 20, SH + 20), (15, 25, 390, 245), scales=(5, 6, 8, 10, 12))
                ax.add_patch(MplPoly(np.array([(0, 0), (SW, 0), (SW, SH), (0, SH)]), fc="#fbf7ef", ec="black", lw=0.8))
                for (pid, k), x, y, rot in sh:
                    p = pmap[pid]
                    g = p.g2
                    H = g["size"][1]

                    def mv(geom):
                        if rot:
                            geom = affinity.affine_transform(geom, [0, -1, 1, 0, H, 0])
                        return affinity.translate(geom, x, y)
                    g2 = dict(outline=mv(g["outline"]), cuts=[mv(c) for c in g["cuts"]],
                              circles=[(*xf(cx, cy, x, y, rot, H), d, l) for cx, cy, d, l in g["circles"]],
                              pockets=[(mv(pk), d, f) for pk, d, f in g["pockets"]],
                              engrave=[[xf(u, v, x, y, rot, H) for u, v in line] for line in g["engrave"]],
                              marks=[])
                    draw_geom(ax, g2, hatch_pockets=False, lw=0.6)
                    c = g2["outline"].centroid
                    ax.text(c.x, c.y, f"{pid}\n{p.name}", fontsize=6, ha="center", va="center", weight="bold")
                pdf.savefig(fig)
                plt.close(fig)
    print("wrote", os.path.relpath(pdf_path))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
