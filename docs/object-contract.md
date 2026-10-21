# Object contract

The table script finds playfield objects by name. Build the geometry however plays best, but give each object the name below. On table start the script checks every required name and, if any are missing, lists them on the DMD for 20 seconds.

The table object itself must be named **`Table1`**.

`tools/build_table.py` already creates every object below on the VPX blank table, positioned by `tools/table_layout.py`. This list is the contract for anyone editing the table by hand.

## Phase 1

### Core

| Name | VPX type | Notes |
| --- | --- | --- |
| `LeftFlipper`, `RightFlipper` | Flipper | |
| `Plunger` | Plunger | |
| `BallRelease` | Kicker | Creates the ball and kicks it into the plunger lane. Angle/force: `TT_RELEASE_*` in `tt_config.vbs`. |
| `swPlungerLane` | Trigger | In the plunger lane. Ball leaving it (`_UnHit`) starts the IR retainer clock. |
| `Drain` | Kicker | The SOC drain. Script destroys the ball. |
| `tmrTick` | Timer | Any interval; the script sets 33 ms. |
| `LeftSlingshot`, `RightSlingshot` | Wall with slingshot enabled | EDR kickers. `_Slingshot` event. |

### The seven stage shots (left to right)

Each shot needs a switch and an orange insert light. Any object with a `_Hit` event works as the switch (trigger at a ramp exit or orbit, standup target, etc.). Persistence and Impact are saucers (kickers) that hold the ball, then eject it.

| # | Stage | Switch | Type | Insert light |
| --- | --- | --- | --- | --- |
| 1 | Recon | `swRecon` | Trigger / target | `liRecon` |
| 2 | Initial Access | `swInitialAccess` | Trigger / target | `liInitialAccess` |
| 3 | Execution | `swExecution` | Trigger / target | `liExecution` |
| 4 | Persistence | `kPersistence` | Kicker (saucer) | `liPersistence` |
| 5 | Privilege Escalation | `swPrivEsc` | Trigger / target | `liPrivEsc` |
| 6 | Lateral Movement | `swLateral` | Trigger / target | `liLateral` |
| 7 | Impact | `kImpact` | Kicker (scoop) | `liImpact` |

Saucer hold time and eject angle/force: `TT_SAUCER_HOLD_MS`, `TT_KICK_PERSISTENCE_*`, `TT_KICK_IMPACT_*`.

**Flow requirements from the spec**
- The chain must read left to right across the upper playfield.
- Lateral Movement must feed back to the **left flipper** (e.g. a ramp or habitrail to the left inlane), with Initial Access makeable from the left flipper. That combo pays 2× within 3 seconds.
- Impact should be a hard-ish shot: it closes the Path.

Light states the script sets: `0` off, `1` collected, `2` blinking = shoot this next.

### Assets

| Name | VPX type | Notes |
| --- | --- | --- |
| `dtAsset1`, `dtAsset2`, `dtAsset3` | Hit target, drop type | White, with server / database / card-terminal icons. Each drop raises Impact. Bank resets 1.5 s after all three are down. |

### Optional lights (used if present)

| Name | Type | Lit when |
| --- | --- | --- |
| `liShootAgain` | Light | Extra ball pending |
| `liBallSave` | Light | IR retainer active |

## Phase 2: Expert Consensus and Air Gap

| Name | VPX type | Notes |
| --- | --- | --- |
| `kImpact` | Kicker | Same Impact scoop: it is also the lock. Locks are virtual: a locked ball is removed and a new one served to the plunger. When multiball starts, the held ball is kicked out and two more are created in `kImpact` and kicked out 1.5 s apart, so check the eject clears the next ball. |
| `liLock1`, `liLock2`, `liLock3` | Light | Lock inserts: blinking = lit, solid = locked. |
| `AirGapGate` | **Wall** | Pink gate in front of the captive ball. The script drops it (`IsDropped = True`) to open during multiball and raises it to close. |
| `liAirGap` | Light | Pink Air Gap insert: blinks while open, solid once breached. |
| `swAirGap` | Trigger or target | Hit by the captive SCADA / OT ball when the player shoots it. |
| `kAirGapCaptive` | Kicker (invisible) | Optional. On table start the script creates the captive ball here, drops it onto the two posts and switches the kicker off. |
| `PostAirGap1`, `PostAirGap2` | Wall | Posts the captive ball rests on; the gap between them is narrower than a ball, so the player's ball hits the captive ball but can't pass. |

Multiball needs at least 3 balls on the table at once; VPX creates them on demand, so there is no physical trough to size.

## Phase 3: Storm Surge

| Name | VPX type | Notes |
| --- | --- | --- |
| `swCentreRamp` | Trigger | Centre ramp exit. Collects the Storm Surge tail jackpot. Make it a clear, satisfying shot from either flipper. |

## Physics

Use VPX 10.8 standard physics (or nFozzy flipper physics if the author prefers). The acceptance test asks for 50 consecutive games with no stuck balls, so check saucer exits, ramp entrances and the plunger lane carefully.
