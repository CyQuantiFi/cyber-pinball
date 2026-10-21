"""Threat Tide playfield layout, in VPX table units (952.94 x 2164.71, y down).

One source of truth for geometry. tools/build_table.py turns it into table
objects on top of the VPX blank table; tools/make_playfield_art.py draws the
playfield art from the same numbers so inserts and labels line up.

The blank table already supplies the outer walls, top arch, plunger lane,
slings, inlanes/outlanes, flippers (L 278,1803 / R 596,1803), ball release
and drain. This file adds the Threat Tide shots in the empty upper playfield.

Flow, left to right:
  Recon        left orbit (wire trigger in the orbit)
  Init Access  lane, aimed back at the left flipper (combo shot)
  Execution    lane, from the right flipper
  Persistence  lane with a saucer at the top; centre-ramp switch at its mouth
  Air Gap      channel: pink drop gate, captive ball on posts, switch at the top
  Priv Esc     lane, from the left flipper
  Lateral Mvt  right orbit: comes round the top and down the left orbit to the
               left inlane, so it feeds the left flipper for the IA combo
  Impact       scoop on the right, also the multiball lock
  Assets       3 drop targets on the left, facing the right flipper
"""
import math

TABLE_W = 952.94
TABLE_H = 2164.71
FLIP_L = (278.2, 1803.3)
FLIP_R = (595.9, 1803.3)
CENTRE_X = 437.0

LANE_IN = 64.0      # inner width of a lane (ball is 50)
WALL_T = 9.0        # guide wall thickness
LANE_LEN = 230.0

ORANGE = "#FF8818"
PINK = "#FF9AA3"
WHITE = "#FFFFFF"


def unit(dx, dy):
    n = math.hypot(dx, dy)
    return dx / n, dy / n


def lane(name, top, mouth):
    """A dead-end lane from a pointed cap at `top` to an open `mouth`."""
    ux, uy = unit(mouth[0] - top[0], mouth[1] - top[1])  # down the lane (toward mouth)
    px, py = -uy, ux                                     # perpendicular
    length = math.hypot(mouth[0] - top[0], mouth[1] - top[1])
    return dict(name=name, top=top, mouth=mouth, u=(ux, uy), p=(px, py), length=length,
                kick_angle=(math.degrees(math.atan2(ux, -uy)) + 360) % 360)


def at(l, t, side=0.0):
    """Point a fraction t from the lane top toward its mouth, offset sideways."""
    return (l["top"][0] + l["u"][0] * l["length"] * t + l["p"][0] * side,
            l["top"][1] + l["u"][1] * l["length"] * t + l["p"][1] * side)


# ---------------------------------------------------------------- lanes
LANES = {
    "initial_access": lane("InitialAccess", (190, 590), (205, 825)),
    "execution": lane("Execution", (300, 540), (325, 775)),
    "persistence": lane("Persistence", (420, 505), (420, 750)),
    "priv_esc": lane("PrivEsc", (640, 545), (615, 780)),
}
AIRGAP = lane("AirGap", (540, 300), (520, 640))

# Orbits: thin inner walls; the blank table's arch is the outer wall.
LEFT_ORBIT_WALL = [(122, 1150), (122, 520)]
RIGHT_ORBIT_WALL = [(762, 500), (762, 880)]

# Impact scoop pocket on the right, against the plunger-lane wall (x ~855).
IMPACT_KICKER = (812, 1190)
IMPACT_POCKET_TOP = [(742, 1146), (852, 1118)]      # slopes left so orbit balls roll off
IMPACT_POCKET_BOTTOM = [(742, 1236), (852, 1236)]


def impact_kick_angle():
    dx, dy = CENTRE_X - IMPACT_KICKER[0], FLIP_L[1] - 60 - IMPACT_KICKER[1]
    return round((math.degrees(math.atan2(dx, -dy)) + 360) % 360)


# ---------------------------------------------------------------- switches, kickers, targets
def switches():
    ia, ex, pe, pr = (LANES[k] for k in ("initial_access", "execution", "priv_esc", "persistence"))
    return {
        "swRecon": (70, 905),
        "swInitialAccess": at(ia, 0.30),
        "swExecution": at(ex, 0.30),
        "swPrivEsc": at(pe, 0.30),
        "swLateral": (811, 760),
        "swCentreRamp": at(pr, 0.82),
        "swAirGap": at(AIRGAP, 0.10),
    }


def kickers():
    pr = LANES["persistence"]
    return {
        "kPersistence": dict(center=at(pr, 0.10), kind="hole", angle=round(pr["kick_angle"])),
        "kImpact": dict(center=IMPACT_KICKER, kind="hole", angle=impact_kick_angle()),
        "kAirGapCaptive": dict(center=at(AIRGAP, 0.32), kind="invisible", angle=180),
    }


# Captive ball rests on two posts; the gap between them is narrower than a ball.
def airgap_posts():
    c = at(AIRGAP, 0.58)
    gap = 36.0
    size = 9.0
    out = []
    for s in (-1, 1):
        cx = c[0] + AIRGAP["p"][0] * s * (gap / 2 + size / 2)
        cy = c[1] + AIRGAP["p"][1] * s * (gap / 2 + size / 2)
        out.append(square(cx, cy, size))
    return out


def airgap_gate():
    """Pink drop wall across the channel mouth."""
    a = at(AIRGAP, 0.92, -LANE_IN / 2 - WALL_T)
    b = at(AIRGAP, 0.92, LANE_IN / 2 + WALL_T)
    return thick_line(a, b, 8)


DROP_TARGETS = [  # (name, x, y, rot_z) facing the right flipper
    ("dtAsset1", 168, 1215, -38),
    ("dtAsset2", 186, 1272, -38),
    ("dtAsset3", 204, 1329, -38),
]


# ---------------------------------------------------------------- lights (inserts)
def lights():
    ia, ex, pe, pr = (LANES[k] for k in ("initial_access", "execution", "priv_esc", "persistence"))

    def below(l, d=58):
        return (l["mouth"][0] + l["u"][0] * d, l["mouth"][1] + l["u"][1] * d)

    return {
        "liRecon": dict(c=(70, 1080), color=ORANGE, label="RECON", n=1),
        "liInitialAccess": dict(c=below(ia), color=ORANGE, label="INITIAL ACCESS", n=2),
        "liExecution": dict(c=below(ex), color=ORANGE, label="EXECUTION", n=3),
        "liPersistence": dict(c=below(pr, 50), color=ORANGE, label="PERSISTENCE", n=4),
        "liPrivEsc": dict(c=below(pe), color=ORANGE, label="PRIVILEGE ESC.", n=5),
        "liLateral": dict(c=(811, 860), color=ORANGE, label="LATERAL MOVEMENT", n=6),
        "liImpact": dict(c=(690, 1190), color=ORANGE, label="IMPACT", n=7),
        "liLock1": dict(c=(668, 1262), color=WHITE, label="", r=11),
        "liLock2": dict(c=(704, 1282), color=WHITE, label="", r=11),
        "liLock3": dict(c=(740, 1302), color=WHITE, label="", r=11),
        "liAirGap": dict(c=below(AIRGAP, 46), color=PINK, label="AIR GAP", r=20),
        "liBallSave": dict(c=(CENTRE_X, 1630), color=PINK, label="IR", r=13),
        "liShootAgain": dict(c=(CENTRE_X, 1700), color=ORANGE, label="", r=13),
    }


# ---------------------------------------------------------------- wall shapes
def square(cx, cy, s):
    h = s / 2
    return [(cx - h, cy - h), (cx + h, cy - h), (cx + h, cy + h), (cx - h, cy + h)]


def thick_line(a, b, t=WALL_T):
    ux, uy = unit(b[0] - a[0], b[1] - a[1])
    px, py = -uy * t / 2, ux * t / 2
    return [(a[0] + px, a[1] + py), (b[0] + px, b[1] + py), (b[0] - px, b[1] - py), (a[0] - px, a[1] - py)]


def lane_walls(l, inner=LANE_IN):
    """Two side rails plus a pointed cap, as wall polygons."""
    half = inner / 2 + WALL_T / 2
    walls = []
    for s in (-1, 1):
        a = at(l, 0.0, s * half)
        b = at(l, 1.0, s * half)
        walls.append(thick_line(a, b))
    # pointed cap: a tent over the top so falling balls roll off
    peak = (l["top"][0] - l["u"][0] * 34, l["top"][1] - l["u"][1] * 34)
    left = at(l, 0.0, -half - WALL_T / 2)
    right = at(l, 0.0, half + WALL_T / 2)
    walls.append([left, peak, right, at(l, 0.04, half - WALL_T / 2), at(l, 0.04, -half + WALL_T / 2)])
    return walls


def all_walls():
    """name -> polygon for every guide wall."""
    walls = {}
    for key, l in list(LANES.items()) + [("airgap", AIRGAP)]:
        for i, poly in enumerate(lane_walls(l)):
            walls[f"Lane{l['name']}{i + 1}"] = poly
    walls["GuideLeftOrbit"] = thick_line(*LEFT_ORBIT_WALL)
    walls["GuideRightOrbit"] = thick_line(*RIGHT_ORBIT_WALL)
    walls["GuideImpactTop"] = thick_line(*IMPACT_POCKET_TOP)
    walls["GuideImpactBottom"] = thick_line(*IMPACT_POCKET_BOTTOM)
    for i, poly in enumerate(airgap_posts()):
        walls[f"PostAirGap{i + 1}"] = poly
    return walls


def rail_x(l, y, side):
    """x of the outer edge of a lane's left (-1) or right (+1) rail at height y, or None."""
    t = (y - l["top"][1]) / (l["u"][1] * l["length"])
    if not 0 <= t <= 1:
        return None
    half = LANE_IN / 2 + WALL_T
    x = l["top"][0] + l["u"][0] * l["length"] * t
    return x + side * half


def check():
    """Gaps between neighbouring guides must be < 48 (a ball can't get in)
    or > 75 (it rolls through). In between, a ball could wedge."""
    problems = []
    cols = [("orbitL", LEFT_ORBIT_WALL[0][0] + WALL_T / 2)] + [
        (l["name"], l) for l in (LANES["initial_access"], LANES["execution"], LANES["persistence"], AIRGAP, LANES["priv_esc"])
    ] + [("orbitR", RIGHT_ORBIT_WALL[0][0] - WALL_T / 2)]
    for y in range(300, 900, 10):
        edges = []
        for name, c in cols:
            if isinstance(c, float):
                edges.append((name, c, c))
            else:
                lx, rx = rail_x(c, y, -1), rail_x(c, y, 1)
                if lx is not None:
                    edges.append((name, lx, rx))
        for (n1, _, r1), (n2, l2, _) in zip(edges, edges[1:]):
            gap = l2 - r1
            if gap < 0:
                problems.append(f"{n1}/{n2} overlap at y={y}")
            elif 48 <= gap <= 75:
                problems.append(f"{n1}/{n2} gap {gap:.0f} at y={y}")
    return sorted(set(problems))


if __name__ == "__main__":
    for k, l in list(LANES.items()) + [("airgap", AIRGAP)]:
        print(f"{k:15} top={tuple(round(v) for v in l['top'])} mouth={tuple(round(v) for v in l['mouth'])} kick={l['kick_angle']:.0f}")
    print("impact kick", impact_kick_angle())
    print("problems:", check() or "none")
