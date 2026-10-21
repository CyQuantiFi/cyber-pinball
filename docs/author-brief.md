# Table author brief — Threat Tide (Phase 1)

You are building the playfield for an original Visual Pinball X 10.8 table that runs on a 3-screen virtual pinball cabinet at CyQuantiFi exhibition booths. The game rules, display, high scores and sound mapping are already written in this repo. Your job is the table itself.

Read first: the design spec (from CyQuantiFi), then [`object-contract.md`](object-contract.md).

## What you build

1. **Playfield geometry** in the VPX editor: walls, ramps, orbits, saucers, slings, flippers, plunger lane, drain, drop targets. Seven stage shots fanning left to right; Lateral Movement feeding the left flipper. Include the Phase 2/3 geometry listed in the object contract (lock, Air Gap gate + captive ball, centre ramp).
2. **Object names** exactly as in the object contract.
3. **Lights and inserts**: 7 orange stage inserts, pink Air Gap insert, white asset targets.
4. **Art placement**: playfield and backglass art from `art/` (SVG sources, brand palette, Comfortaa). Finish the art at print resolution; keep layered source files.
5. **B2S backglass** (`.directb2s`) from `art/backglass.svg`. Static image is fine for Phase 1.
6. **Sounds** imported into the Sound Manager using the names in `table/tt_sound.vbs` (e.g. `vo_path_complete`, `sfx_edr`). Original or royalty-free only. Missing sounds are skipped, so this can come last.
7. **Image `qr_form`** in the Image Manager: the QR code for the booth form (CyQuantiFi supplies it).

## Loading the script

- **Cabinet / release:** run `python3 tools/bundle.py` (or take the committed `dist/ThreatTide_full.vbs`) and paste the whole file into the table's script editor.
- **While iterating:** paste `table/ThreatTide_loader.vbs` instead and copy `table/*.vbs` into VPX's `Scripts` folder. Edits to the module files apply on the next table start. If your VPX build does not fire events from loaded files, use the bundle.

Do not edit game rules inside the .vpx. Change the files in `table/` and rebuild, so the repo stays the source of truth. Physical values you will tune (kicker angles and forces, saucer hold) are in the **Geometry** section at the bottom of `table/tt_config.vbs`.

## Requirements

- FlexDMD installed on the cabinet (the display uses a 256×64 full-colour FlexDMD canvas on the DMD screen).
- Tilt: VPX plumb tilt (`MechanicalTilt`) and nudge keys feed the script's warnings.
- Operator settings appear in the VPX 10.8 table options menu (F12): balls per game, Patch Tuesday, volume preset, contest mode.

## Deliverables

- `.vpx` table file, `.directb2s` backglass, any FlexDMD assets (e.g. Comfortaa BMFont files if you make them).
- Source files for playfield and backglass art (layered SVG/PSD/AI), so CyQuantiFi owns and can edit them.
- A completed `docs/LICENSES.md` row for every art, font and sound asset you add.

## Done for Phase 1 when

The checklist in [`acceptance.md`](acceptance.md) passes on the cabinet.

## Constraints

- Original table only: no reskin or recreation of a commercial machine, no third-party characters, logos or licensed music.
- MITRE ATT&CK attribution stays on the backglass and in attract mode.
