# Table author brief — Threat Tide

You are building the playfield for an original Visual Pinball X 10.8 table that runs on a 3-screen virtual pinball cabinet at CyQuantiFi exhibition booths. The game rules, display, high scores and sound mapping are already written in this repo. Your job is the table itself.

Read first: the design spec (from CyQuantiFi), then [`object-contract.md`](object-contract.md).

## What's already built

`dist/ThreatTide.vpx` (from CI, or `bash tools/build_all.sh`) is a complete, scripted table built on the VPX blank table:

- All seven stage shots, the Air Gap channel (drop gate, captive ball on posts, switch), the Impact scoop/lock, asset drop targets, orbits and every insert light, laid out in [`tools/table_layout.py`](../tools/table_layout.py).
- Playfield art generated from the same layout, so inserts and labels line up; the backglass (`ThreatTide.directb2s`); Comfortaa DMD fonts; game-cue sound effects.
- The full script for all three phases, plus the blank table's ball shadows, rolling sounds and sling animations.

It has not been played yet: it was built on Linux, where VPX can't run.

## What you do

1. **Play it and fix the flow.** Shot angles, lane widths, kicker eject angles and forces, the captive ball's travel, and the Impact scoop are first guesses. Change geometry in `tools/table_layout.py` and rebuild, or adjust in the VPX editor and port the numbers back so the repo stays the source of truth. Kicker values live in the **Geometry** block of `table/tt_config.vbs`.
2. **Lateral Movement → left flipper.** It's the right orbit: the ball goes round the top and down the left orbit to the left inlane. Check that it reliably reaches the left flipper; a habitrail or ramp would do it better.
3. **Art polish.** Finish `art/playfield_table.svg` and `art/backglass.svg` at print quality (keep the layered sources), and replace the blank table's generic apron art.
4. **Voice callouts** (`vo_*` in `table/tt_sound.vbs`). Original or royalty-free only. Missing sounds are skipped.
5. **Music**: `<VPX folder>\Music\ThreatTide\theme.mp3` (CyQuantiFi supplies the file; it isn't in this repo for licence reasons).
6. **QR code**: set `TT_FormUrl` in `tt_config.vbs` to the real form URL and run `python3 tools/make_qr.py`.

## Loading the script

- **Cabinet / release:** the built `.vpx` already contains the script. To update only the script, paste `dist/ThreatTide_full.vbs` into the table's script editor.
- **While iterating:** paste `table/ThreatTide_loader.vbs` instead and copy `table/*.vbs` into VPX's `Scripts` folder. Edits to the module files apply on the next table start. If your VPX build does not fire events from loaded files, use the bundle.

Do not edit game rules inside the .vpx. Change the files in `table/` and rebuild, so the repo stays the source of truth. Physical values you will tune (kicker angles and forces, saucer hold) are in the **Geometry** section at the bottom of `table/tt_config.vbs`.

## Requirements

- FlexDMD installed on the cabinet (the display uses a 256×64 full-colour FlexDMD canvas on the DMD screen).
- Tilt: VPX plumb tilt (`MechanicalTilt`) and nudge keys feed the script's warnings.
- Operator settings appear in the VPX 10.8 table options menu (F12): balls per game, Patch Tuesday, volume preset, contest mode.

## Deliverables

- Layout and config changes committed back to this repo, so `tools/build_all.sh` reproduces your table.
- Source files for playfield and backglass art (layered SVG/PSD/AI), so CyQuantiFi owns and can edit them.
- A completed `docs/LICENSES.md` row for every art, font and sound asset you add.

## Done when

The checklist in [`acceptance.md`](acceptance.md) passes on the cabinet. Phase 1 alone is enough for a first show; the Phase 2 and 3 checks can follow.

## Constraints

- Original table only: no reskin or recreation of a commercial machine, no third-party characters, logos or licensed music.
- MITRE ATT&CK attribution stays on the backglass and in attract mode.
