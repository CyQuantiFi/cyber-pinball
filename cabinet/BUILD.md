# Threat Tide cabinet: build guide

Part numbers (P01 to P29) match `out/drawings.pdf`, `out/cutlist.csv` and the DXF labels. Read it all once before cutting.

## 0. Before you cut

1. **Buy the screens first.** Measure the 32" and 24" monitors without their stands: outside size, depth, and the visible picture area. Set `TV`, `TV_VIEW`, `MON`, `MON_VIEW` in `geometry.py`. Do the same for the DMD (`DMD`, `DMD_VIEW`). The 32" must be no more than about 60 mm deep, or the crossbars won't fit.
2. **Measure the plywood** with calipers in a few places and set `T`. The dados follow it.
3. Check your plunger kit's mounting. The front panel has a 25 mm centre hole; drill the flange holes on assembly.
4. Run `python3 cabinet/make_cabinet.py`. It must say `clearance check: OK`.
5. Print the PDF page for the body side (P01) at 100% and check a dimension with a rule. This confirms the files are in mm.

## 1. CNC

Files: `out/sheets/ply18_1.dxf`, `ply18_2.dxf`, `ply6_1.dxf`, `mdf6_1.dxf`, `acrylic3_1.dxf`. The layer meanings are in [README.md](README.md#dxf-layers).

Order of operations per sheet:

1. `DRILL` (holes for tee nuts, inserts, screws).
2. `POCKET_6`, 6 mm deep: the dados and rebates. **Test the fit first.** Cut one short dado in an offcut and try a strip of the same sheet in it. It should slide in with hand pressure. Adjust `FIT` if needed.
3. `ENGRAVE` and `MARK`.
4. `CUT_INSIDE`, then `CUT_OUTSIDE` with tabs (3 to 4 per part, 6 mm wide, 3 mm high).

Back-face pockets: P21 (backbox top, bezel groove) and P22 (speaker / DMD panel, LCD recess). After cutting them out, flip each part. Square it to a fence and re-zero on a corner, then run the `POCKET_6_BACK` layer from that part's own DXF in `out/dxf/`, mirrored. If your CAM makes that awkward, cut these two grooves with a hand router and a fence.

Stopped dados leave round ends from the 6 mm bit. Ease the matching panel corners with a chisel or sanding block (3 mm). The mortises in the leg plates already have dog-bone corners.

Acrylic (P16/P17): leave the film on, use an O-flute, and engrave the `ENGRAVE` layer on the face that is up. The text is already mirrored, so it reads correctly from outside through the acrylic.

## 2. Body

Dry-fit everything first. Glue goes in the dados; 8g x 40 screws go through the sides into the panel edges (pre-drill and countersink 3 mm; fill and paint over the heads).

1. **Sides to floor.** Lay side L (P01) pockets-up. Glue the floor (P03) into its rebate, then the front (P04) and back (P06) panels. Add side R (P02) on top. Check the diagonals are equal, then screw.
2. **Rear deck** (P08) into its sloped rebate. Fit two M8 tee nuts into its underside holes first.
3. **Floor tee nuts.** Fit the 8 M8 tee nuts into the floor holes from the top, tapping them in with a hammer.
4. **Crossbar cleats** (P15 x 4): glue and screw to the sides, top edge on the red `MARK` lines (they are also on drawing P01). The TV crossbars (P13, P14) sit on them loose. Put 3 mm foam tape on top of each crossbar.
5. **Test the glass path.** Slide the mask (P10) and then the glass into the groove from the front. They should run smoothly all the way to the deck. Felt strip in the groove stops rattles.
6. **Lockbar.** Screw the stop strip (P12) under the lockbar (P11), 1 mm back from its front edge, on edge (see the side elevation). Drill M6 inserts into the top edge of each side, through the lockbar holes, then fit them. Round the lockbar front edge (R9) and wrap it in brushed-aluminium vinyl.
7. **Coin-door plate** (P05): paint silver or wrap it, then screw it to the front panel over the Exit hole.
8. **Back service cover** (P07): 4 x M4 screws or 8g screws into the back panel.

## 3. Backbox

1. Lay side L (P18) pockets-up. Glue in the bottom (P20), top (P21; its bezel groove goes underneath at the front) and speaker panel (P22; LCD recess at the back). Then slide in the monitor board (P24) from above, before the top goes on.
2. Slide the bezel (P23) down into its groove before the second side goes on. It sits between the speaker panel and the top.
3. Add side R (P19) and screw. Check it is square.
4. The back (P25) screws on with 8g x 25 screws and comes off for service.
5. Line up the 50 mm grommet holes in P20 and the deck (P08). The two bolt holes then line up with the deck tee nuts.

## 4. Legs

1. **Laminate** the plates (P26) in pairs. Glue them face to face with the edges flush; an offcut of 18 mm ply pushed through both mortises keeps them in register. Clamp, and screw from the inside face.
2. **Top plates** (P27): glue and screw down into the frame's top edge through the 4 countersunk holes. The 4 outer 9 mm holes are for the M8 knob bolts.
3. **Feet:** in the bottom edge of each leg, on the glue line, drill 14 mm x 40 deep and wind in an M10 hex-drive insert. Then screw in the levelling feet.
4. **Stretcher** (P28): slide its tenons through both frames' mortises and tap a wedge (P29) into each end. The wedges pull the frames tight with no tools.

## 5. Finish

Fill, sand 120 then 240, prime, and paint 2 coats of satin black (or wrap in vinyl). Leave the inside bare. Paint the mask (P10) and bezel (P23) matt black. Apply side-art vinyl if you are using it.

## 6. Fit-out

The layout matches `out/render/cabinet_inside.png`; every box there is clearance-checked.

| Where | What |
| --- | --- |
| Floor, rear (under the deck) | PC lying on its side, intake over the floor vents, rear I/O at the service cover |
| Floor, middle | Pinscape Pico + accelerometer **flat, centred, screwed down firmly** (nudge accuracy depends on it); 24 V brick; 5 V LED brick; amplifier; USB hub; power board; LED controller |
| Floor, front | Bass shakers (screwed hard to the floor), contactors (2 per side, near the flipper buttons) |
| Sides, front | Flipper buttons (28.6 mm holes) |
| Front panel | Start (left), Exit (centre, through the coin plate), Launch and plunger (right) |
| Under the glass | 32" monitor face-up on the crossbars, pressed against the mask |
| Backbox | 24" monitor on the VESA board, DMD bar in its recess, 4" speakers behind the grilles |

### Wiring

**Mains: no DIY mains wiring.** Everything plugs into one surge-protected power board inside the body. One lead leaves through the back-panel grommet. The PC, monitors, amplifier and the 24 V and 5 V bricks all use their own plug-in supplies. For events, have the power board and leads tested and tagged (most venues require it).

Low voltage:

- **Buttons and plunger** → Pinscape Pico inputs (follow the Pinscape wiring guide for your kit).
- **Contactors:** the 24 V brick feeds the contactor coils, switched by the Pinscape outputs. Fit a 1N4007 flyback diode across each coil (stripe to +24 V) unless your output board has them built in. The contactors' main contacts aren't used; the "thunk" is the coil pulling in.
- **LEDs:** Teensy → 74AHCT125 → 330 ohm → strip data in. Put a 1000 uF capacitor across 5 V/GND at the strip, inject 5 V at both ends of each run, and share ground with the Teensy.
- **Audio:** PC → amplifier. Left/right go to the backbox speakers, the sub channel to the two shakers.
- **Backbox:** one HDMI/DP lead each for the 24" and the DMD, plus the DMD's USB power and the speaker cable. All of it runs through the 50 mm grommet with a loop of slack, so the backbox can be lifted off after unplugging at the PC.

### Software

1. Windows 11, GPU driver, VPX 10.8, B2S server, DirectOutput (DOF), Pinscape config tool.
2. Displays: playfield = main display (VPX rotates the table for a cabinet), 24" = backglass, 12.3" = DMD. Turn off sleep and screen savers.
3. Table: install as per [`docs/booth-runbook.md`](../docs/booth-runbook.md#installing-on-the-cabinet). Start the booth with `start_booth.bat`.
4. Pinscape: calibrate the plunger and accelerometer, map the buttons to VPX keys, and enable the DOF outputs.
5. **Feedback (DOF):** the table sends events for the flippers, slings, knocker, button lamps and LED trim. Map them to your outputs as described in [`docs/dof.md`](../docs/dof.md), and set coil time limits first.

## Transport

Breakdown, about 10 minutes, 2 people:

1. Shut down Windows and unplug the mains lead.
2. Remove the backbox back (P25). Unplug the video, USB and speaker leads at the PC side and feed them up through the grommet. Undo the two M8 bolts.
3. Lift the backbox off (slots in its sides) and refit its back.
4. Tap the wedges out and pull the stretcher out.
5. Two people lift the body by its hand slots while a third undoes the 8 star knobs. Or: tip the cabinet back gently onto a blanket so the rear legs come off first, then the front.
6. Load the body **flat, glass up**, on a moving blanket, strapped down. Never stand it on its end with the monitor inside. Load the backbox upright, screens forward, strapped against the van wall. The leg frames lie flat.

Setup is the reverse. Level the playfield with the feet: a spirit level on the glass should read level across, and the slope comes from the cabinet itself. Bolt the backbox down before plugging in.

Tips:
- Keep the knobs, bolts and wedges in a labelled bag taped inside the backbox.
- A furniture dolly makes the body a one-person move on flat floors.
- The glass is toughened but its edges are vulnerable. Keep the lockbar bolted on in transit.
