"""Threat Tide cabinet: parametric geometry.

Every wooden part is a flat sheet: a 2D outline (with holes, pockets and engraving)
in the part's own (u, v) coordinates, extruded by its thickness along w, and placed in
the world by a frame (origin + three unit axes).

World axes (mm): x across the cabinet (0 = left outer face), y from the front
(0 = front face) to the rear, z up (0 = underside of the body floor; the legs sit
below it). The playfield slope is built into the body sides.

Change a number in P, run `python3 cabinet/make_cabinet.py`, and every output
(DXF, PDF, model, cut list) follows. The checks at the bottom catch parts that
collide with each other or with the bought components.
"""
import math
from dataclasses import dataclass, field

import numpy as np
from shapely import contains_xy
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

# ---------------------------------------------------------------- parameters
P = dict(
    T=18.0,          # structural plywood (measure yours: set the real thickness here)
    T6=6.0,          # thin sheet (mask, bezel, back, covers)
    DADO=6.0,        # dado / rebate depth into 18 mm sides
    FIT=0.3,         # extra dado width over the mating sheet
    W=600.0,         # body and backbox outer width
    L=1060.0,        # body length (floor plan)
    SLOPE=6.5,       # playfield angle, degrees
    HF=260.0,        # body side height at the front
    LEG_TOP=633.0,   # floor of the body above the ground (lockbar ~ 900 mm)
    FEET=25.0,       # levelling feet height at mid-adjustment
    DECK=250.0,      # rear deck length along the slope (backbox sits on it)
    GLASS=5.0,       # tempered glass thickness
    GROOVE_D0=14.0,  # glass groove starts this far below the side top edge
    LOCKBAR=100.0,   # lockbar depth along the slope
    TV=(735.0, 440.0, 60.0),   # 32" monitor envelope: length along slope, width, depth
    TV_VIEW=(708.0, 398.0),    # visible area (mask window)
    BB_DEPTH=236.0,  # backbox side depth (back panel adds 6)
    BB_FRONT=586.0,  # backbox height at the front
    SPK_PANEL=170.0, # speaker / DMD panel height
    MON=(540.0, 320.0, 50.0),  # 24" monitor envelope (no stand): w, h, depth
    MON_VIEW=(529.0, 298.0),   # bezel window
    DMD=(308.0, 127.0, 10.0),  # 12.3" 1920x720 bar LCD outline
    DMD_VIEW=(294.0, 111.0),
    SPK_CUT=93.0,    # 4" speaker cut-out
    TRESTLE_Y=(150.0, 910.0),  # leg frame centre lines
)
T, T6, DADO, FIT = P["T"], P["T6"], P["DADO"], P["FIT"]
W, L, HF = P["W"], P["L"], P["HF"]
A = math.radians(P["SLOPE"])
SA, CA, TA = math.sin(A), math.cos(A), math.tan(A)
IW = W - 2 * T              # interior width
PW = IW + 2 * DADO          # panels that sit in the side dados
X0 = T - DADO               # their left edge
S_END = L / CA              # slope length of the side top edge
S_DECK = S_END - P["DECK"]  # where the rear deck starts
GD0 = P["GROOVE_D0"]
GD1 = GD0 + P["GLASS"] + 1 + T6   # bottom of the glass + mask groove
MASK_D = (GD0 + P["GLASS"] + 1, GD1)
GLASS_D = (GD0, GD0 + P["GLASS"])
TV_LEN, TV_W, TV_DEP = P["TV"]
TV_S0 = P["LOCKBAR"] + 5 - (TV_LEN - P["TV_VIEW"][0]) / 2
TV_D = (MASK_D[1] + 1, MASK_D[1] + 1 + TV_DEP)
XC = W / 2


def top(y):
    """z of the side top edge (= glass line) at floor-plan position y."""
    return HF + y * TA


def slope_pt(s, d):
    """(y, z) of a point s along the slope from the front top edge, d below it."""
    return s * CA + d * SA, HF + s * SA - d * CA


# ---------------------------------------------------------------- frames
@dataclass
class Frame:
    o: tuple
    eu: tuple
    ev: tuple
    ew: tuple

    def mat(self):
        return np.array([self.eu, self.ev, self.ew], float).T   # columns

    @property
    def mirrored(self):
        return np.linalg.det(self.mat()) < 0

    def to_world(self, uvw):
        return np.asarray(uvw, float) @ self.mat().T + np.asarray(self.o, float)

    def to_local(self, xyz):
        return (np.asarray(xyz, float) - np.asarray(self.o, float)) @ self.mat()


def F_side(x_outer, inward):
    """Body/backbox side: u = y, v = z (absolute), w = into the cabinet."""
    return Frame((x_outer, 0, 0), (0, 1, 0), (0, 0, 1), (inward, 0, 0))


def F_xz(y_face, t):
    """Vertical panel across the cabinet: u = x, v = z, w = 0 at y_face + t, t at y_face."""
    return Frame((0, y_face + t, 0), (1, 0, 0), (0, 0, 1), (0, -1, 0))


def F_xy(z_bottom):
    return Frame((0, 0, z_bottom), (1, 0, 0), (0, 1, 0), (0, 0, 1))


def F_slope(d_bottom):
    """Plane parallel to the playfield: u = x, v = s; w = 0 at depth d_bottom."""
    return Frame((0, d_bottom * SA, HF - d_bottom * CA), (1, 0, 0), (0, CA, SA), (0, -SA, CA))


# ---------------------------------------------------------------- parts
@dataclass
class Part:
    name: str
    module: str          # body / backbox / legs / loose
    material: str        # ply18 / mdf6 / ply6 / glass5 / acrylic3
    t: float
    outline: Polygon
    frame: Frame
    qty: int = 1
    cuts: list = field(default_factory=list)      # inner profile cuts (polygons)
    circles: list = field(default_factory=list)   # (cx, cy, d, layer)
    pockets: list = field(default_factory=list)   # (polygon, depth[, "bottom"]) from the w = t face
    engrave: list = field(default_factory=list)   # polylines [(u, v), ...]
    marks: list = field(default_factory=list)     # layout lines for assembly [(u, v), ...]
    notes: str = ""
    color: tuple = (0.80, 0.66, 0.46)
    cnc: bool = True     # False = bought / cut by the supplier

    def solid(self):
        """Outline minus every through cut (for meshes and checks)."""
        holes = list(self.cuts) + [Point(cx, cy).buffer(d / 2, 32) for cx, cy, d, _ in self.circles]
        return self.outline.difference(unary_union(holes)) if holes else self.outline

    def area_m2(self):
        return self.solid().area / 1e6


DENS = dict(ply18=600, ply6=650, mdf6=750, glass5=2500, acrylic3=1190)
COL = dict(ply18=(0.80, 0.66, 0.46), ply6=(0.78, 0.68, 0.52), mdf6=(0.12, 0.12, 0.14),
           glass5=(0.70, 0.85, 0.95), acrylic3=(0.55, 0.95, 1.0))
PAINT = (0.07, 0.09, 0.14)   # cabinet paint / vinyl colour for renders


def rect(u0, v0, u1, v1):
    return box(min(u0, u1), min(v0, v1), max(u0, u1), max(v0, v1))


def slot(cx, cy, length, width):
    r = width / 2
    return Point(cx - length / 2 + r, cy).buffer(r, 32).union(
        Point(cx + length / 2 - r, cy).buffer(r, 32)).convex_hull


def dogbone_rect(u0, v0, u1, v1, r=3.2):
    """Rectangle cut-out with dog-bone corners so a square tenon seats fully."""
    rr = rect(u0, v0, u1, v1)
    d = r * 0.7071
    bones = [Point(u + su * d, v + sv * d).buffer(r, 16)
             for u, su in ((u0, 1), (u1, -1)) for v, sv in ((v0, 1), (v1, -1))]
    return unary_union([rr] + bones)


def slope_band(s0, s1, d0, d1):
    """Polygon in side (y, z) coords for a band parallel to the playfield."""
    return Polygon([slope_pt(s0, d0), slope_pt(s1, d0), slope_pt(s1, d1), slope_pt(s0, d1)])


def text_paths(txt, size, cx, cy, mirror=False):
    """Text as closed polylines (for the ENGRAVE layer), centred on (cx, cy)."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath
    import os
    font = os.path.join(os.path.dirname(__file__), "..", "art", "fonts", "Comfortaa-VariableFont_wght.ttf")
    tp = TextPath((0, 0), txt, size=size, prop=FontProperties(fname=font))
    polys = [np.asarray(p) for p in tp.to_polygons() if len(p) > 2]
    allp = np.vstack(polys)
    mx, my = (allp.min(0) + allp.max(0)) / 2
    out = []
    for p in polys:
        q = p - [mx, my]
        if mirror:
            q[:, 0] *= -1
        out.append([(cx + a, cy + b) for a, b in q])
    return out


def build():
    """Return (parts, components)."""
    parts = []
    add = parts.append
    FL = 18 + 0.0      # floor top
    yb = L - T         # back panel front face
    front_top = slope_pt(0, MASK_D[1])[1] - 5    # front panel stays under the mask
    deck_under_back = top(yb) - T / CA

    # --------------------------------------------------------------- body
    side_outline = Polygon([(0, 0), (L, 0), (L, top(L)), (0, HF)])
    btn_v = top(85) - 60
    hand_y = (120.0, 960.0)
    hand_z = 95.0
    for nm, xo, inw in (("Body side L", 0, 1), ("Body side R", W, -1)):
        sp = Part(nm, "body", "ply18", T, side_outline, F_side(xo, inw))
        sp.pockets += [
            (rect(0, 0, L, T + FIT), DADO),                                   # floor
            (rect(0, T, T + FIT, front_top), DADO),                           # front panel
            (rect(L - T - FIT, T, L, deck_under_back + 2), DADO),             # back panel
            (slope_band(-20, S_DECK + 0.5, GD0, GD1).intersection(side_outline), DADO),   # glass + mask
            (slope_band(S_DECK - 0.5, S_END + 20, 0, T + FIT).intersection(side_outline), DADO),  # deck
        ]
        sp.circles += [(85, btn_v, 28.6, "CUT_INSIDE")]
        sp.cuts += [slot(y, hand_z, 130, 36) for y in hand_y]
        # standoffs for the edge-lit side panel (outer face)
        sp.circles += [(y, z, 5.0, "DRILL") for y in (260, 840) for z in (60, 200)]
        for sc in (250.0, 680.0):     # crossbar cleat positions (layout marks)
            y0, z0 = slope_pt(sc - 50, TV_D[1] + 1 + T)
            y1, z1 = slope_pt(sc + 50, TV_D[1] + 1 + T)
            sp.marks.append([(y0, z0), (y1, z1)])
        sp.notes = "Pockets are on the inside face. R is the mirror of L."
        add(sp)

    floor = Part("Body floor", "body", "ply18", T, rect(X0, 0, X0 + PW, L), F_xy(0))
    for yc in P["TRESTLE_Y"]:
        floor.circles += [(x, yc + dy, 10.0, "DRILL") for x in (60, W - 60) for dy in (-50, 50)]
    floor.cuts += [slot(XC, y, 220, 14) for y in range(720, 1000, 40)]       # PC intake vents
    floor.circles += [(XC - 60, 160, 6.5, "DRILL"), (XC + 60, 160, 6.5, "DRILL")]   # cable-tie anchors
    floor.notes = "Tee nuts (M8) pressed in from the top for the leg bolts."
    add(floor)

    fh = front_top
    front = Part("Body front", "body", "ply18", T, rect(X0, FL, X0 + PW, fh), F_xz(0, T))
    plunger = (W - 55, 175.0)
    front.circles += [(90, 150, 30.0, "CUT_INSIDE"),          # Start (30 mm snap-in arcade button)
                      (W - 120, 120, 30.0, "CUT_INSIDE"),     # Launch
                      (plunger[0], plunger[1], 25.0, "CUT_INSIDE"),
                      (XC, 150, 30.0, "CUT_INSIDE")]          # Exit (through the coin door)
    front.notes = "Plunger flange holes: drill to your plunger kit on assembly."
    add(front)

    coin = Part("Coin door overlay", "body", "ply6", T6, rect(XC - 110, 40, XC + 110, 205), F_xz(-T6, T6))
    coin.circles += [(XC, 150, 24.0, "CUT_INSIDE")]
    coin.circles += [(XC + dx, 75 + dy, 4.0, "DRILL") for dx in (-95, 95) for dy in (0, 110)]
    coin.cuts += [rect(XC - 70, 85, XC - 64, 125), rect(XC + 64, 85, XC + 70, 125)]    # coin slots
    coin.engrave += text_paths("INSERT CREDIT", 9, XC, 60)
    coin.color = (0.75, 0.75, 0.78)
    coin.notes = "Paint silver or wrap in brushed vinyl. Slots are decorative."
    add(coin)

    back = Part("Body back", "body", "ply18", T, rect(X0, FL, X0 + PW, deck_under_back - 1), F_xz(yb, T))
    back.cuts += [rect(XC - 160, 30, XC + 160, 215)]                    # PC / service opening
    back.circles += [(XC + dx, z, 4.0, "DRILL") for dx in (-180, 180) for z in (45, 220)]
    back.circles += [(W - 90, 285, 114, "CUT_INSIDE")]                 # 120 mm exhaust fan
    back.circles += [(W - 90 + dx, 285 + dy, 4.5, "DRILL") for dx in (-52.5, 52.5) for dy in (-52.5, 52.5)]
    back.circles += [(90, 100, 50.0, "CUT_INSIDE")]                    # power lead grommet
    add(back)

    cover = Part("Back service cover", "body", "ply6", T6, rect(XC - 195, 20, XC + 195, 240), F_xz(L, T6))
    cover.cuts += [slot(XC, z, 260, 10) for z in range(60, 200, 22)]
    cover.circles += [(XC + dx, z, 4.5, "DRILL") for dx in (-180, 180) for z in (45, 220)]
    cover.notes = "Screws on with 4 x M4 into the back panel. Vents for the PC."
    add(cover)

    deck = Part("Rear deck", "body", "ply18", T, rect(X0, S_DECK, X0 + PW, S_END - 2.5), F_slope(T))
    bb_bolt_s = (950 / CA)
    deck.circles += [(150, bb_bolt_s, 10.0, "DRILL"), (W - 150, bb_bolt_s, 10.0, "DRILL"),
                     (XC, 1000 / CA, 50.0, "CUT_INSIDE")]
    deck.notes = "Tee nuts on the underside for the backbox bolts."
    add(deck)

    glass = Part("Playfield glass", "body", "glass5", P["GLASS"],
                 rect(T - DADO + 1, 20, W - T + DADO - 1, S_DECK - 1), F_slope(GLASS_D[1]), cnc=False)
    glass.notes = "5 mm toughened, edges arrised. Order cut to size from a glazier."
    add(glass)

    tvx0, tvx1 = XC - P["TV_VIEW"][1] / 2, XC + P["TV_VIEW"][1] / 2
    ms0 = P["LOCKBAR"] + 5
    mask = Part("Playfield mask", "body", "mdf6", T6, rect(T - DADO + 1, 20, W - T + DADO - 1, S_DECK - 1),
                F_slope(MASK_D[1]))
    mask.cuts += [rect(tvx0, ms0, tvx1, ms0 + P["TV_VIEW"][0])]
    mask.notes = "Paint matt black. Window = TV visible area; check against your TV and adjust TV_VIEW."
    add(mask)

    # sits ON the side tops: its w = 0 face is the top edge line (d = 0)
    lockbar = Part("Lockbar", "body", "ply18", T, rect(0, 0, W, P["LOCKBAR"]), F_slope(0.0))
    lockbar.circles += [(T / 2, 50, 7.0, "DRILL"), (W - T / 2, 50, 7.0, "DRILL")]
    lockbar.color = (0.75, 0.75, 0.78)
    lockbar.notes = "Round over the front edge (R9) and wrap in brushed vinyl or cap with aluminium angle."
    add(lockbar)
    # on edge under the lockbar: u = x, v = depth below the top line, w = along the slope (s 1..19)
    stop = Part("Lockbar stop strip", "body", "ply18", T, rect(T + 0.5, 0.5, W - T - 0.5, MASK_D[1] + 1),
                Frame(slope_pt_xyz(1, 0), (1, 0, 0), (0, SA, -CA), (0, CA, SA)))
    stop.notes = "Glued and screwed under the lockbar; holds the glass and mask in."
    add(stop)

    for i, sc in enumerate((250.0, 680.0)):
        cb = Part(f"TV crossbar {i + 1}", "body", "ply18", T, rect(T + 1, sc - 40, W - T - 1, sc + 40),
                  F_slope(TV_D[1] + 1 + T))
        cb.notes = "Lift-out. 3 mm foam tape on top presses the TV up against the mask."
        add(cb)
    cleat = Part("Crossbar cleat", "body", "ply18", T, rect(T, -50, T + 40, 50), None, qty=4)
    cleat.frames = []
    for sc in (250.0, 680.0):
        base = F_slope(TV_D[1] + 1 + 2 * T)
        for x in (0, W - 2 * T - 40):
            o = base.to_world([x, sc, 0])
            cleat.frames.append(Frame(tuple(o), base.eu, base.ev, base.ew))
    cleat.frame = cleat.frames[0]
    cleat.notes = "Glue and screw to the sides on the layout marks."
    add(cleat)

    # Edge-lit acrylic side panels (outer face of each side)
    for nm, x, inw, mir in (("Side light panel L", -12 - 3, 1, True), ("Side light panel R", W + 12 + 3, -1, False)):
        ap = Part(nm, "body", "acrylic3", 3.0, rect(190, 30, 880, 230), F_side(x, inw))
        ap.circles += [(y, z, 5.0, "CUT_INSIDE") for y in (260, 840) for z in (60, 200)]
        ap.engrave += text_paths("THREAT TIDE", 76, 535, 130, mirror=mir)
        ap.color = COL["acrylic3"]
        ap.notes = ("3 mm clear cast acrylic, engraved on the face against the cabinet "
                    "(text is pre-mirrored). 12 mm standoffs; LED strip in a channel under the bottom edge.")
        add(ap)

    # --------------------------------------------------------------- backbox
    y0b = 818.0
    y1b = y0b + P["BB_DEPTH"]
    zt = top(y0b) + P["BB_FRONT"]
    bb_out = Polygon([(y0b, top(y0b)), (y1b, top(y1b)), (y1b, zt), (y0b, zt)])
    bot_t = T / CA

    def bb_bot_top(y):
        return top(y) + bot_t

    zsp0 = bb_bot_top(y0b + T)
    zsp1 = zsp0 + P["SPK_PANEL"]
    zbz1 = zt - T
    ymon = y0b + T6 + 1
    ybrd = ymon + P["MON"][2] + 3
    for nm, xo, inw in (("Backbox side L", 0, 1), ("Backbox side R", W, -1)):
        bs = Part(nm, "backbox", "ply18", T, bb_out, F_side(xo, inw))
        bs.pockets += [
            (Polygon([(y0b, top(y0b)), (y1b, top(y1b)), (y1b, bb_bot_top(y1b) + FIT),
                      (y0b, bb_bot_top(y0b) + FIT)]), DADO),                     # bottom
            (rect(y0b, zt - T - FIT, y1b, zt), DADO),                           # top
            (rect(y0b, top(y0b), y0b + T + FIT, zsp1), DADO),                   # speaker panel
            (rect(y0b, zsp1 - 1, y0b + T6 + FIT, zt - T + 1), DADO),           # bezel
            (rect(ybrd, zsp1, ybrd + T + FIT, zt - T + 1), DADO),              # monitor board (stopped)
        ]
        bs.cuts += [slot((y0b + y1b) / 2, zt - 70, 120, 36)]                    # carry handle
        bs.notes = "Pockets on the inside face. R is the mirror of L."
        add(bs)

    bbb = Part("Backbox bottom", "backbox", "ply18", T, rect(X0, y0b / CA, X0 + PW, y1b / CA - 0.5),
               F_slope(0.0))
    bbb.circles += [(150, bb_bolt_s, 10.0, "DRILL"), (W - 150, bb_bolt_s, 10.0, "DRILL"),
                    (XC, 1000 / CA, 50.0, "CUT_INSIDE")]
    bbb.notes = "M8 bolts down through here into the deck tee nuts."
    add(bbb)

    bbt = Part("Backbox top", "backbox", "ply18", T, rect(X0, y0b, X0 + PW, y1b), F_xy(zt - T))
    bbt.cuts += [slot(XC + dx, y1b - 60, 140, 12) for dx in (-170, 0, 170)]    # warm-air vents
    bbt.pockets += [(rect(X0 - 1, y0b - 1, X0 + PW + 1, y0b + T6 + FIT), DADO, "bottom")]   # bezel groove
    bbt.notes = "Bezel groove is on the underside (flip the part for that op)."
    add(bbt)

    spk = Part("Speaker / DMD panel", "backbox", "ply18", T, rect(X0, zsp0, X0 + PW, zsp1), F_xz(y0b, T))
    zmid = (zsp0 + zsp1) / 2
    dvw, dvh = P["DMD_VIEW"]
    spk.cuts += [rect(XC - dvw / 2, zmid - dvh / 2, XC + dvw / 2, zmid + dvh / 2)]
    spx = (T + XC - P["DMD"][0] / 2) / 2
    for x in (spx, W - spx):
        spk.circles.append((x, zmid, P["SPK_CUT"], "CUT_INSIDE"))
        spk.circles += [(x + dx, zmid + dy, 4.0, "DRILL") for dx in (-41, 41) for dy in (-41, 41)]
    spk.pockets += [(rect(XC - P["DMD"][0] / 2 - 1, zmid - P["DMD"][1] / 2 - 1,
                          XC + P["DMD"][0] / 2 + 1, zmid + P["DMD"][1] / 2 + 1), 6.0, "bottom")]
    spk.notes = "DMD pocket is on the BACK face (flip the part for that op): the LCD sits in it."
    add(spk)

    bez = Part("Monitor bezel", "backbox", "mdf6", T6, rect(X0, zsp1, X0 + PW, zbz1 + DADO - 0.5), F_xz(y0b, T6))
    mvw, mvh = P["MON_VIEW"]
    zmon = (zsp1 + zbz1) / 2
    bez.cuts += [rect(XC - mvw / 2, zmon - mvh / 2, XC + mvw / 2, zmon + mvh / 2)]
    bez.notes = "Paint matt black. Window = 24\" visible area; check against your monitor."
    add(bez)

    brd = Part("Monitor board", "backbox", "ply18", T, rect(X0, zsp1, X0 + PW, zbz1 - 0.5), F_xz(ybrd, T))
    brd.circles += [(XC + dx, zmon + dy, 5.0, "DRILL") for dx in (-50, 50) for dy in (-50, 50)]
    brd.cuts += [slot(XC, zmon - 110, 120, 40), slot(XC, zmon + 110, 200, 30)]
    brd.notes = "VESA 100 holes; slots for cables and airflow."
    add(brd)

    bback = Part("Backbox back", "backbox", "ply6", T6, rect(0, top(y1b), W, zt), F_xz(y1b, T6))
    bback.cuts += [slot(XC + dx, zt - 60, 140, 12) for dx in (-170, 0, 170)]
    bback.circles += [(x, z, 4.5, "DRILL") for x in (9, W - 9) for z in (top(y1b) + 60, (top(y1b) + zt) / 2, zt - 40)]
    bback.notes = "Removable for bolting the backbox down and for service."
    add(bback)

    # --------------------------------------------------------------- legs
    zl0 = -P["LEG_TOP"] + P["FEET"]
    zl1 = -T
    win = rect(120, zl0 + 110, W - 120, zl1 - 160).buffer(-20).buffer(20)
    mort = dogbone_rect(XC - (T + FIT) / 2, zl0 + 20, XC + (T + FIT) / 2, zl0 + 100)
    lp = Part("Leg frame plate", "legs", "ply18", T, rect(0, zl0, W, zl1), None, qty=4)
    lp.cuts += [win, mort]
    lp.frames = [F_xz(yf, T) for yc in P["TRESTLE_Y"] for yf in (yc - T, yc)]
    lp.frame = lp.frames[0]
    lp.notes = "Glue two plates face to face for each leg frame (4 plates make 2 frames)."
    add(lp)
    tp = Part("Leg top plate", "legs", "ply18", T, rect(0, -80, W, 80), None, qty=2)
    tp.frames = [Frame((0, yc, zl1), (1, 0, 0), (0, 1, 0), (0, 0, 1)) for yc in P["TRESTLE_Y"]]
    tp.frame = tp.frames[0]
    tp.circles += [(x, dy, 9.0, "DRILL") for x in (60, W - 60) for dy in (-50, 50)]
    tp.circles += [(x, 0, 4.5, "DRILL") for x in (100, 250, 350, 500)]
    tp.notes = "Glue and screw down into the frame edge. M8 knob bolts go up through the outer holes."
    add(tp)
    yf_in, yr_in = P["TRESTLE_Y"][0] + T, P["TRESTLE_Y"][1] - T
    tz0, tz1 = zl0 + 20.15, zl0 + 99.85
    st_out = unary_union([rect(yf_in, tz0 - 15, yr_in, tz1 + 40),
                          rect(yf_in - 2 * T - 45, tz0, yr_in + 2 * T + 45, tz1)])
    stretch = Part("Leg stretcher", "legs", "ply18", T, st_out, F_side(XC - T / 2, 1))
    for yo, sgn in ((P["TRESTLE_Y"][0] - T, -1), (P["TRESTLE_Y"][1] + T, 1)):
        u0 = yo - sgn * 2       # wedge bears 2 mm inside the frame face
        stretch.cuts.append(dogbone_rect(min(u0, u0 + sgn * 24), (tz0 + tz1) / 2 - 10,
                                         max(u0, u0 + sgn * 24), (tz0 + tz1) / 2 + 10))
    stretch.notes = "Through-tenons pass the leg frames; a wedge in each end locks it. No tools."
    add(stretch)
    zc = (tz0 + tz1) / 2
    wd = Part("Wedge", "legs", "ply18", T, Polygon([(0, 0), (110, 0), (110, 24), (0, 13)]), None, qty=2)
    wd.frames = [Frame((XC - 55, yo, zc - T / 2), (1, 0, 0), (0, sgn, 0), (0, 0, 1))
                 for yo, sgn in ((P["TRESTLE_Y"][0] - T, -1), (P["TRESTLE_Y"][1] + T, 1))]
    wd.frame = wd.frames[0]
    wd.notes = "Tap in from either side to pull the leg frame tight."
    add(wd)

    comps = components(dict(btn_v=btn_v, plunger=plunger, hand_y=hand_y, hand_z=hand_z, zsp0=zsp0,
                            zsp1=zsp1, zmid=zmid, zmon=zmon, ymon=ymon, spx=spx, y0b=y0b, zl0=zl0))
    return parts, comps


def slope_pt_xyz(s, d):
    y, z = slope_pt(s, d)
    return (0.0, y, z)


# ---------------------------------------------------------------- bought components
@dataclass
class Comp:
    name: str
    frame: Frame
    lo: tuple   # local box min (u, v, w)
    hi: tuple
    color: tuple = (0.35, 0.37, 0.42)
    clear: bool = True    # include in the clearance check

    def corners(self):
        lo, hi = np.array(self.lo), np.array(self.hi)
        c = np.array([[lo[0] if i & 1 == 0 else hi[0], lo[1] if i & 2 == 0 else hi[1],
                       lo[2] if i & 4 == 0 else hi[2]] for i in range(8)])
        return self.frame.to_world(c)


WORLD = Frame((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))


def wbox(name, x0, x1, y0, y1, z0, z1, **kw):
    return Comp(name, WORLD, (x0, y0, z0), (x1, y1, z1), **kw)


def components(g):
    S = Frame((0, 0, HF), (1, 0, 0), (0, CA, SA), (0, SA, -CA))   # u = x, v = s, w = depth below top
    c = []
    c.append(Comp("32in monitor (playfield)", S, (XC - TV_W / 2, TV_S0, TV_D[0]),
                  (XC + TV_W / 2, TV_S0 + TV_LEN, TV_D[1]), color=(0.05, 0.05, 0.06)))
    c.append(wbox("Mini-ITX PC (NR200P class, on its side)", XC - 146, XC + 146, 660, 1036, 18, 203,
                  color=(0.25, 0.27, 0.3)))
    px, pz = g["plunger"]
    c.append(wbox("Plunger mechanism", px - 20, px + 20, 18, 190, pz - 20, pz + 20, color=(0.7, 0.7, 0.72)))
    c.append(wbox("Plunger knob", px - 12, px + 12, -95, 0, pz - 12, pz + 12, color=(0.9, 0.2, 0.2), clear=False))
    bv = g["btn_v"]
    c.append(wbox("Flipper button L", T, T + 45, 85 - 16, 85 + 16, bv - 16, bv + 16, color=(0.2, 0.9, 0.95)))
    c.append(wbox("Flipper button R", W - T - 45, W - T, 85 - 16, 85 + 16, bv - 16, bv + 16, color=(0.2, 0.9, 0.95)))
    for nm, x, z in (("Start button", 90, 150), ("Launch button", W - 120, 120), ("Exit button", XC, 150)):
        c.append(wbox(nm, x - 16, x + 16, 18, 63, z - 16, z + 16, color=(0.95, 0.6, 0.1)))
    for i, x in enumerate((40, 90, W - 140, W - 90)):
        c.append(wbox(f"Contactor {i + 1}", x, x + 45, 330, 405, 18, 93, color=(0.3, 0.5, 0.3)))
    c.append(wbox("Bass shaker L", 165, 285, 120, 240, 18, 73, color=(0.2, 0.2, 0.2)))
    c.append(wbox("Bass shaker R", W - 285, W - 165, 120, 240, 18, 73, color=(0.2, 0.2, 0.2)))
    c.append(wbox("Pinscape Pico + accelerometer", 250, 350, 300, 380, 18, 45, color=(0.1, 0.5, 0.2)))
    c.append(wbox("24 V supply", 380, 555, 420, 492, 18, 53, color=(0.6, 0.6, 0.6)))
    c.append(wbox("5 V LED supply", 45, 220, 420, 492, 18, 53, color=(0.6, 0.6, 0.6)))
    c.append(wbox("Amplifier", 245, 345, 420, 520, 18, 58, color=(0.3, 0.3, 0.6)))
    c.append(wbox("USB relay + LED controller", 60, 220, 560, 620, 18, 45, color=(0.1, 0.4, 0.6)))
    c.append(wbox("Power board", 380, 560, 560, 620, 18, 58, color=(0.9, 0.9, 0.9)))
    for y in g["hand_y"]:
        for x0, x1 in ((T, T + 70), (W - T - 70, W - T)):
            c.append(wbox("Hand room", x0, x1, y - 65, y + 65, g["hand_z"] - 40, g["hand_z"] + 30,
                          color=(1, 0.8, 0.6), clear=True))
    mw, mh, md = P["MON"]
    c.append(wbox("24in monitor (backglass)", XC - mw / 2, XC + mw / 2, g["ymon"], g["ymon"] + md,
                  g["zmon"] - mh / 2, g["zmon"] + mh / 2, color=(0.05, 0.05, 0.06)))
    dw, dh, dd = P["DMD"]
    c.append(wbox("12.3in DMD bar LCD", XC - dw / 2, XC + dw / 2, g["y0b"] + T - 6 + 0.5, g["y0b"] + T - 6 + 0.5 + dd,
                  g["zmid"] - dh / 2, g["zmid"] + dh / 2, color=(0.05, 0.05, 0.06)))
    for x in (g["spx"], W - g["spx"]):
        c.append(wbox("4in speaker", x - 52, x + 52, g["y0b"] + T, g["y0b"] + T + 60, g["zmid"] - 52, g["zmid"] + 52,
                      color=(0.15, 0.15, 0.15)))
    return c


# ---------------------------------------------------------------- placements / checks
def placements(p):
    return getattr(p, "frames", None) or [p.frame]


def _sample_part(p, step=7.0, layers=3):
    sol = p.solid().buffer(-0.6)
    if sol.is_empty:
        return np.zeros((0, 3))
    u0, v0, u1, v1 = sol.bounds
    uu, vv = np.meshgrid(np.arange(u0 + step / 2, u1, step), np.arange(v0 + step / 2, v1, step))
    uu, vv = uu.ravel(), vv.ravel()
    m = contains_xy(sol, uu, vv)
    uu, vv = uu[m], vv[m]
    pts = np.vstack([np.column_stack([uu, vv, np.full(len(uu), p.t * (k + 0.5) / layers)])
                     for k in range(layers)])
    keep = np.ones(len(pts), bool)
    for pk in p.pockets:
        inz = _pocket_w(p, pk, pts[:, 2], 0.0)
        keep &= ~(inz & contains_xy(pk[0], pts[:, 0], pts[:, 1]))
    return pts[keep]


def _pocket_w(p, pk, w, tol):
    depth = pk[1]
    if len(pk) > 2 and pk[2] == "bottom":
        return w < depth + tol
    return w > p.t - depth - tol


def _inside_part(p, fr, pts, tol=0.4):
    """Mask of world points strictly inside part p's material (pockets count as empty)."""
    loc = fr.to_local(pts)
    m = (loc[:, 2] > tol) & (loc[:, 2] < p.t - tol)
    if not m.any():
        return m
    sol = p.solid().buffer(-tol)
    m[m] = contains_xy(sol, loc[m, 0], loc[m, 1])
    for pk in p.pockets:
        mm = m & _pocket_w(p, pk, loc[:, 2], tol)
        if mm.any():
            hit = contains_xy(pk[0].buffer(tol), loc[mm, 0], loc[mm, 1])
            idx = np.where(mm)[0][hit]
            m[idx] = False
    return m


def _inside_comp(c, pts, tol=0.4):
    loc = c.frame.to_local(pts)
    lo, hi = np.array(c.lo) + tol, np.array(c.hi) - tol
    return np.all((loc > lo) & (loc < hi), axis=1)


def _bbox(pts):
    return pts.min(0), pts.max(0)


def check(parts, comps):
    """Return a list of problems: overlapping material, components hitting parts or each other."""
    probs = []
    inst = []
    for p in parts:
        for fr in placements(p):
            q = _sample_part(p)
            wp = fr.to_world(q)
            corners = fr.to_world(np.array([[a, b, w] for a, b in p.outline.exterior.coords for w in (0, p.t)]))
            inst.append((p, fr, wp, _bbox(corners)))
    for i, (p, fr, wp, bb) in enumerate(inst):
        for j, (p2, fr2, wp2, bb2) in enumerate(inst):
            if j <= i or np.any(bb[1] < bb2[0]) or np.any(bb2[1] < bb[0]):
                continue
            n = _inside_part(p2, fr2, wp).sum() + _inside_part(p, fr, wp2).sum()
            if n:
                probs.append(f"parts overlap: {p.name} / {p2.name} ({n} sample points)")
    for c in comps:
        if not c.clear:
            continue
        lo, hi = np.array(c.lo), np.array(c.hi)
        g = [np.linspace(lo[k] + 1, hi[k] - 1, max(3, int((hi[k] - lo[k]) / 8))) for k in range(3)]
        loc = np.stack(np.meshgrid(*g, indexing="ij"), -1).reshape(-1, 3)
        wp = c.frame.to_world(loc)
        for p, fr, _, bb in inst:
            if np.any(wp.max(0) < bb[0]) or np.any(bb[1] < wp.min(0)):
                continue
            n = _inside_part(p, fr, wp).sum()
            if n:
                probs.append(f"component hits part: {c.name} / {p.name} ({n})")
        for c2 in comps:
            if c2 is c or not c2.clear or c.name == c2.name == "Hand room":
                continue
            n = _inside_comp(c2, wp).sum()
            if n:
                probs.append("components overlap: " + " / ".join(sorted([c.name, c2.name])))
    return sorted(set(probs))


def modules(parts):
    """Transport modules with mass (kg) and bounding size (mm)."""
    out = {}
    for p in parts:
        for fr in placements(p):
            pts = fr.to_world(np.array([[a, b, w] for a, b in p.outline.exterior.coords for w in (0, p.t)]))
            m = p.area_m2() * p.t / 1000 * DENS[p.material]
            d = out.setdefault(p.module, dict(kg=0.0, lo=pts.min(0), hi=pts.max(0)))
            d["kg"] += m
            d["lo"] = np.minimum(d["lo"], pts.min(0))
            d["hi"] = np.maximum(d["hi"], pts.max(0))
    return out
