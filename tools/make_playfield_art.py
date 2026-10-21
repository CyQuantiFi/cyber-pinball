#!/usr/bin/env python3
"""Draw the playfield art from tools/table_layout.py, in VPX table units.

    python3 tools/make_playfield_art.py     # writes art/playfield_table.svg

Because the art uses the same coordinates as the table objects, the inserts,
lane arrows and labels line up with the real shots. Render it to PNG with
node tools/render_art.js. Fonts: Comfortaa (art/fonts, SIL OFL).
"""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import table_layout as L  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "art" / "playfield_table.svg"
W, H = L.TABLE_W, L.TABLE_H
BG, OR, PK, WH = "#1A1B1C", "#FF8818", "#FF9AA3", "#FFFFFF"


def wave(y, amp, wl, phase, x0=0, x1=W, step=8):
    pts = []
    x = x0
    while x <= x1 + step:
        yy = y + amp * math.sin(x / wl * 2 * math.pi + phase) + amp * 0.35 * math.sin(x / (wl * 0.43) * 2 * math.pi + phase * 1.7)
        pts.append(f"{x:.0f},{yy:.1f}")
        x += step
    return "M" + " L".join(pts)


def poly(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def lane_fill(l, colour, op=0.22):
    half = L.LANE_IN / 2
    pts = [L.at(l, 0.0, -half), L.at(l, 0.0, half), L.at(l, 1.0, half), L.at(l, 1.0, -half)]
    return f'<polygon points="{poly(pts)}" fill="{colour}" fill-opacity="{op}"/>'


def arrow(x0, y0, x1, y1, colour=OR, width=10, op=0.9):
    return (f'<path d="M{x0:.0f},{y0:.0f} L{x1:.0f},{y1:.0f}" stroke="{colour}" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-opacity="{op}" marker-end="url(#arrow)" fill="none"/>')


def text(x, y, s, size=20, colour=WH, weight=700, anchor="middle", op=1.0, rot=0, spacing=1):
    tr = f' transform="rotate({rot:.1f} {x:.0f} {y:.0f})"' if rot else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{colour}" '
            f'fill-opacity="{op}" text-anchor="{anchor}" letter-spacing="{spacing}"{tr}>{s}</text>')


def insert(x, y, r, colour, num=None):
    out = [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * 2.6:.1f}" fill="url(#glow)" />' if colour == OR else
           f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * 2.6:.1f}" fill="url(#pinkglow)" />' if colour == PK else "",
           f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{colour}" fill-opacity="0.85" stroke="{WH}" stroke-width="2"/>']
    if num:
        out.append(text(x, y + r * 0.42, str(num), size=r * 1.15, colour=BG))
    return "".join(out)


def build():
    lights = L.lights()
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         f'font-family="Comfortaa, sans-serif">',
         "<title>Threat Tide playfield (generated from tools/table_layout.py)</title>",
         "<defs>",
         f'<linearGradient id="sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0B0C0E"/>'
         f'<stop offset="0.38" stop-color="{BG}"/><stop offset="1" stop-color="#101A24"/></linearGradient>',
         f'<radialGradient id="glow"><stop offset="0" stop-color="{OR}" stop-opacity="0.5"/>'
         f'<stop offset="1" stop-color="{OR}" stop-opacity="0"/></radialGradient>',
         f'<radialGradient id="pinkglow"><stop offset="0" stop-color="{PK}" stop-opacity="0.55"/>'
         f'<stop offset="1" stop-color="{PK}" stop-opacity="0"/></radialGradient>',
         f'<marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" '
         f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{OR}"/></marker>',
         "</defs>",
         f'<rect width="{W}" height="{H}" fill="url(#sea)"/>']

    # storm at the top, waves rising from the bottom
    s.append('<g id="storm" fill="none">')
    for k in range(7):
        s.append(f'<path d="{wave(70 + k * 48, 18 + k * 3, 380 - k * 22, k * 0.9)}" stroke="{PK if k % 2 else OR}" '
                 f'stroke-opacity="{0.08 + 0.04 * k:.2f}" stroke-width="{2 + k % 3}"/>')
    s.append('</g><g id="waves" fill="none">')
    for k in range(16):
        y = H - 40 - k * 90
        s.append(f'<path d="{wave(y, 12 + (k % 4) * 4, 280 + (k % 5) * 40, k * 1.3)}" stroke="#2C4458" '
                 f'stroke-opacity="{max(0.05, 0.32 - k * 0.018):.2f}" stroke-width="3"/>')
    s.append("</g>")

    # lanes
    s.append('<g id="lanes">')
    for key, l in L.LANES.items():
        s.append(lane_fill(l, OR))
    s.append(lane_fill(L.AIRGAP, PK, 0.25))
    # orbits
    s.append(f'<rect x="22" y="520" width="98" height="640" fill="{OR}" fill-opacity="0.12"/>')
    s.append(f'<rect x="766" y="500" width="88" height="380" fill="{OR}" fill-opacity="0.12"/>')
    s.append("</g>")

    # arrows from each insert into its shot
    s.append('<g id="arrows">')
    for key, li in (("initial_access", "liInitialAccess"), ("execution", "liExecution"),
                    ("persistence", "liPersistence"), ("priv_esc", "liPrivEsc")):
        l = L.LANES[key]
        a = L.at(l, 0.97)
        b = L.at(l, 0.80)
        s.append(arrow(a[0], a[1], b[0], b[1], width=8))
    s.append(arrow(70, 1040, 70, 960))                     # Recon up the left orbit
    s.append(arrow(811, 900, 811, 820))                    # Lateral Movement up the right orbit
    s.append(arrow(735, 1190, 772, 1190))                  # Impact into the scoop
    a = L.at(L.AIRGAP, 0.97)
    b = L.at(L.AIRGAP, 0.75)
    s.append(arrow(a[0], a[1], b[0], b[1], PK))
    s.append("</g>")

    # inserts and labels
    s.append('<g id="inserts">')
    for name, li in lights.items():
        x, y = li["c"]
        s.append(insert(x, y, li.get("r", 17), li["color"], li.get("n")))
    s.append("</g><g id=\"labels\">")
    # lane labels run up the inside of each lane
    for key, label in (("initial_access", "INITIAL ACCESS"), ("execution", "EXECUTION"),
                       ("persistence", "PERSISTENCE"), ("priv_esc", "PRIV ESCALATION")):
        l = L.LANES[key]
        x, y = L.at(l, 0.40)
        ang = math.degrees(math.atan2(l["u"][1], l["u"][0])) + 180
        s.append(text(x, y + 5, label, size=13, rot=ang, spacing=1.5))
    # orbit labels run up the orbits; Impact sits beside its scoop
    s.append(text(70, 830, "RECON", size=16, rot=-90, spacing=3))
    s.append(text(811, 690, "LATERAL MOVEMENT", size=13, rot=-90, spacing=2))
    s.append(text(690, 1234, "IMPACT", size=17))
    ag = lights["liAirGap"]["c"]
    s.append(text(ag[0], ag[1] + 52, "AIR GAP", size=19, colour=PK))
    s.append(text(ag[0], ag[1] + 72, "SCADA / OT", size=12, colour=PK, weight=400))
    top = L.AIRGAP["top"]
    s.append(text(top[0], top[1] - 46, "THE ASSET YOU CAN'T SCAN", size=13, colour=PK, weight=400))
    s.append(text(704, 1330, "LOCK", size=14, colour=WH, op=0.8))
    s.append(text(L.CENTRE_X, 1634 + 32, "IR RETAINER", size=11, colour=PK, weight=400))
    s.append(text(L.CENTRE_X, 1700 + 32, "SHOOT AGAIN", size=11, colour=OR, weight=400))
    # assets
    for name, x, y, rot in L.DROP_TARGETS:
        s.append(f'<circle cx="{x + 42}" cy="{y + 12}" r="6" fill="{WH}" fill-opacity="0.7"/>')
    s.append(text(150, 1390, "ASSETS", size=16, colour=WH, op=0.85))
    s.append(text(150, 1410, "RAISE IMPACT", size=11, colour=WH, weight=400, op=0.75))
    s.append("</g>")

    # title block between the lane mouths and the slings
    s.append('<g id="title">')
    s.append(text(L.CENTRE_X, 1000, "THREAT TIDE", size=74, colour=OR, spacing=5))
    s.append(text(L.CENTRE_X, 1042, "HIT THE LIT SHOT. BUILD THE CHAIN.", size=20, colour=WH, weight=400, spacing=2))
    s.append(text(L.CENTRE_X, 1072, "LATERAL MOVEMENT FEEDS INITIAL ACCESS: COMBO X2", size=13, colour=PK, weight=400))
    s.append(text(L.CENTRE_X, 1440, "EVERY SHOT IS A DOLLAR FIGURE", size=15, colour=WH, weight=400, op=0.55, spacing=3))
    s.append("</g>")
    s.append("</svg>")
    return "\n".join(s)


if __name__ == "__main__":
    OUT.write_text(build())
    print("wrote", OUT.relative_to(ROOT))
