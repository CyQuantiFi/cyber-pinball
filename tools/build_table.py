#!/usr/bin/env python3
"""Build dist/ThreatTide.vpx: the VPX blank table + the Threat Tide layout,
art, sounds and script.

    python3 tools/build_table.py            # needs vpxtool on PATH (or $VPXTOOL)

Steps
  1. Get VPX's own blank table (the File > New template) into .cache/.
  2. Extract it with vpxtool into build/table/.
  3. Add the playfield objects from tools/table_layout.py, Threat Tide
     materials, playfield + backglass images, the QR image, the sound effects
     and the bundled script (dist/ThreatTide_full.vbs).
  4. Assemble dist/ThreatTide.vpx, then run vpxtool verify and audit.

Before building, run: tools/bundle.py, tools/make_playfield_art.py,
node tools/render_art.js, tools/make_sfx.py (tools/build_all.sh does all of it).
"""
import copy
import json
import os
import pathlib
import shutil
import subprocess
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import table_layout as L  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"
BUILD = ROOT / "build" / "table"
OUT = ROOT / "dist" / "ThreatTide.vpx"
BASE_URL = "https://raw.githubusercontent.com/vpinball/vpinball/master/src/assets/blankTable.vpx"
VPXTOOL = os.environ.get("VPXTOOL") or shutil.which("vpxtool") or str(pathlib.Path.home() / ".cargo/bin/vpxtool")

# ---------------------------------------------------------------- item templates (vpin 0.39 expanded JSON)
T_WALL = {"hit_event": False, "is_droppable": False, "is_flipbook": False, "is_bottom_solid": False,
          "is_collidable": True, "is_timer_enabled": False, "timer_interval": 0, "threshold": 2.0, "image": "",
          "side_image": "", "side_material": "", "top_material": "", "slingshot_material": "",
          "height_bottom": 0.0, "height_top": 50.0, "name": "", "display_texture": False, "slingshot_force": 80.0,
          "slingshot_threshold": 0.0, "elasticity": 0.3, "elasticity_falloff": None, "friction": 0.3,
          "scatter": 0.0, "is_top_bottom_visible": True, "slingshot_animation": True, "is_side_visible": True,
          "disable_lighting_top": None, "disable_lighting_below": None, "is_reflection_enabled": None,
          "physics_material": None, "overwrite_physics": None, "drag_points": []}
T_TRIGGER = {"center": {"x": 0.0, "y": 0.0}, "radius": 25.0, "rotation": 0.0, "wire_thickness": None,
             "scale_x": 0.0, "scale_y": 0.0, "is_timer_enabled": False, "timer_interval": 0, "material": "",
             "surface": "", "is_visible": True, "is_enabled": True, "hit_height": 50.0, "name": "",
             "shape": "wire_a", "anim_speed": 0.0, "is_reflection_enabled": None, "drag_points": []}
T_KICKER = {"center": {"x": 0.0, "y": 0.0}, "radius": 25.0, "is_timer_enabled": False, "timer_interval": 0,
            "material": "", "surface": "", "is_enabled": True, "name": "", "kicker_type": "hole",
            "scatter": 0.0, "hit_accuracy": 0.7, "hit_height": None, "orientation": 0.0,
            "fall_through": False, "legacy_mode": True}
T_LIGHT = {"center": {"x": 0.0, "y": 0.0}, "height": None, "falloff_radius": 0.0, "falloff_power": 0.0,
           "state_u32": 0, "state": None, "color": "#ffa957", "color2": "#ffa957", "is_timer_enabled": False,
           "timer_interval": 0, "blink_pattern": "10", "image": "", "blink_interval": 0, "intensity": 1.0,
           "transmission_scale": 0.5, "surface": "", "name": "", "is_backglass": False, "depth_bias": 0.0,
           "fade_speed_up": 0.2, "fade_speed_down": 0.2, "is_bulb_light": False, "is_image_mode": False,
           "show_bulb_mesh": False, "has_static_bulb_mesh": None, "show_reflection_on_ball": True,
           "mesh_radius": 20.0, "bulb_modulate_vs_add": 0.9, "bulb_halo_height": 28.0, "shadows": None,
           "fader": None, "visible": None, "drag_points": []}
T_TARGET = {"position": {"x": 0.0, "y": 0.0, "z": 0.0}, "size": {"x": 32.0, "y": 32.0, "z": 32.0},
            "rot_z": 0.0, "image": "", "target_type": "drop_target_simple", "name": "", "material": "",
            "is_visible": True, "is_legacy": False, "use_hit_event": True, "threshold": 2.0, "elasticity": 0.0,
            "elasticity_falloff": 0.0, "friction": 0.0, "scatter": 0.0, "is_collidable": True,
            "disable_lighting_top": None, "disable_lighting_below": None, "depth_bias": 0.0,
            "is_reflection_enabled": True, "is_dropped": False, "drop_speed": 0.5, "is_timer_enabled": False,
            "timer_interval": 0, "raise_delay": None, "physics_material": None, "overwrite_physics": None}
T_TIMER = {"center": {"x": 0.0, "y": 0.0}, "is_timer_enabled": False, "timer_interval": 0, "name": "",
           "backglass": False}
LAYER = "Threat Tide"


def dp(x, y, slingshot=None):
    return {"x": float(x), "y": float(y), "z": 0.0, "smooth": False, "is_slingshot": slingshot,
            "has_auto_texture": True, "tex_coord": 0.0, "is_locked": False}


def circle(cx, cy, r, n=12):
    import math
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def make(template, **kw):
    v = copy.deepcopy(template)
    v.update(kw)
    v["part_group_name"] = None
    v["editor_layer_name"] = LAYER
    return v


# ---------------------------------------------------------------- steps
def run(*args):
    print("$", " ".join(str(a) for a in args))
    subprocess.run([str(a) for a in args], check=True)


def get_base():
    CACHE.mkdir(exist_ok=True)
    base = CACHE / "blankTable.vpx"
    if not base.exists():
        print("downloading the VPX blank table ...")
        urllib.request.urlretrieve(BASE_URL, base)
    return base


def extract(base):
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.parent.mkdir(parents=True, exist_ok=True)
    run(VPXTOOL, "extract", "-f", "-o", BUILD, base)


def load(name):
    return json.loads((BUILD / name).read_text())


def save(name, data):
    (BUILD / name).write_text(json.dumps(data, indent=2))


class Items:
    def __init__(self):
        self.index = load("gameitems.json")
        self.names = {e["file_name"] for e in self.index}

    def add(self, kind, value):
        fname = f"{kind}.{value['name']}.json"
        assert fname not in self.names, f"duplicate item {fname}"
        (BUILD / "gameitems" / fname).write_text(json.dumps({kind: value}, indent=2))
        self.index.append({"file_name": fname, "is_locked": False})
        self.names.add(fname)

    def rename(self, kind, old, new):
        src = BUILD / "gameitems" / f"{kind}.{old}.json"
        data = json.loads(src.read_text())
        data[kind]["name"] = new
        src.unlink()
        dst = f"{kind}.{new}.json"
        (BUILD / "gameitems" / dst).write_text(json.dumps(data, indent=2))
        for e in self.index:
            if e["file_name"] == f"{kind}.{old}.json":
                e["file_name"] = dst
        self.names.discard(f"{kind}.{old}.json")
        self.names.add(dst)

    def save(self):
        save("gameitems.json", self.index)


def add_materials():
    mats = load("materials.json")
    base = next(m for m in mats if m["name"] == "Plastic White")
    metal = next(m for m in mats if m["name"] == "Metal0.8")
    for name, src, colour in [("TT Orange", base, "#ff8818"), ("TT Pink", base, "#ff9aa3"),
                              ("TT Dark", base, "#2a2c2e"), ("TT Rail", metal, "#c8ccd2")]:
        m = copy.deepcopy(src)
        m["name"] = name
        m["base_color"] = colour
        mats.append(m)
    save("materials.json", mats)


def add_playfield(items):
    for name, poly in L.all_walls().items():
        rail = name.startswith(("Lane", "Guide"))
        items.add("Wall", make(T_WALL, name=name, drag_points=[dp(x, y) for x, y in poly],
                               top_material="TT Rail" if rail else "TT Dark",
                               side_material="TT Rail" if rail else "TT Dark",
                               height_top=40.0 if rail else 30.0, elasticity=0.3, friction=0.2))
    # Air Gap gate: pink drop wall the script lowers during multiball
    items.add("Wall", make(T_WALL, name="AirGapGate", is_droppable=True,
                           drag_points=[dp(x, y) for x, y in L.airgap_gate()],
                           top_material="TT Pink", side_material="TT Pink", height_top=45.0))
    for name, (x, y) in L.switches().items():
        shape = "none" if name in ("swCentreRamp",) else "wire_a"
        items.add("Trigger", make(T_TRIGGER, name=name, center={"x": x, "y": y}, radius=22.0, shape=shape,
                                  material="Metal0.8",
                                  drag_points=[dp(px, py) for px, py in circle(x, y, 22, 8)]))
    for name, k in L.kickers().items():
        x, y = k["center"]
        items.add("Kicker", make(T_KICKER, name=name, center={"x": x, "y": y}, kicker_type=k["kind"],
                                 material="Metal0.8", radius=25.0, orientation=float(k["angle"])))
    for name, x, y, rot in L.DROP_TARGETS:
        items.add("HitTarget", make(T_TARGET, name=name, position={"x": x, "y": y, "z": 0.0}, rot_z=float(rot),
                                    target_type="drop_target_beveled", material="Plastic White"))
    for name, li in L.lights().items():
        x, y = li["c"]
        r = li.get("r", 17)
        items.add("Light", make(T_LIGHT, name=name, center={"x": x, "y": y}, color=li["color"],
                                color2=li["color"], falloff_radius=r * 3.2, falloff_power=2.0, intensity=8.0,
                                blink_pattern="10", blink_interval=125,
                                drag_points=[dp(px, py) for px, py in circle(x, y, r, 16)]))
    items.add("Timer", make(T_TIMER, name="tmrTick", center={"x": 1000.0, "y": 60.0}, timer_interval=33))
    # Plunger lane switch: the blank table's Trigger1 sits in the lane already
    items.rename("Trigger", "Trigger1", "swPlungerLane")


def add_images():
    images = load("images.json")
    imgdir = BUILD / "images"

    def put(name, src):
        from PIL import Image
        w, h = Image.open(src).size
        for old in list(imgdir.glob(f"{name}.*")):
            old.unlink()
        shutil.copy(src, imgdir / f"{name}.png")
        entry = {"name": name, "path": f"{name}.png", "width": w, "height": h, "alpha_test_value": 1.0,
                 "is_opaque": True}
        for i, e in enumerate(images):
            if e["name"] == name:
                images[i] = entry
                return
        images.append(entry)

    put("tt_playfield", ROOT / "art" / "render" / "playfield_table.png")
    put("Backglass", ROOT / "art" / "render" / "backglass.png")     # blank table's backbox image
    qr = ROOT / "art" / "render" / "qr_form.png"
    if qr.exists():
        put("qr_form", qr)
    save("images.json", images)
    gd = load("gamedata.json")
    gd["image"] = "tt_playfield"
    save("gamedata.json", gd)


def add_sounds():
    sounds = load("sounds.json")
    sdir = BUILD / "sounds"
    for wav in sorted((ROOT / "sound" / "sfx").glob("*.wav")):
        shutil.copy(wav, sdir / wav.name)
        sounds.append({"name": wav.stem, "path": wav.name, "internal_name": "", "fade": 0, "volume": 0,
                       "balance": 0, "output_target": "table"})
    save("sounds.json", sounds)


def set_script_and_info():
    (BUILD / "script.vbs").write_bytes((ROOT / "dist" / "ThreatTide_full.vbs").read_bytes())
    info = load("info.json")
    info.update(table_name="Threat Tide", author_name="CyQuantiFi", table_version="0.1",
                table_blurb="You are the attacker. Your score is realised loss in dollars.",
                table_description="Original CyQuantiFi exhibition table. ATT&CK technique names from MITRE "
                                  "ATT&CK(R). Dollar values are game-design numbers, not loss estimates. "
                                  "Built on the Visual Pinball X blank table.",
                table_rules="Hit the lit shot, build the chain left to right, Impact completes the Attack Path.")
    save("info.json", info)


def main():
    if not pathlib.Path(VPXTOOL).exists():
        sys.exit("vpxtool not found: cargo install vpxtool, or set VPXTOOL")
    problems = L.check()
    if problems:
        sys.exit("layout problems:\n  " + "\n  ".join(problems))
    extract(get_base())
    items = Items()
    add_materials()
    add_playfield(items)
    items.save()
    add_images()
    add_sounds()
    set_script_and_info()
    OUT.parent.mkdir(exist_ok=True)
    if OUT.exists():
        OUT.unlink()
    run(VPXTOOL, "assemble", BUILD, OUT)
    run(VPXTOOL, "verify", OUT)
    print(f"built {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
