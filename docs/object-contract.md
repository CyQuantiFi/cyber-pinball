# Object contract

The table script finds playfield objects by name. Build the geometry however plays best, but give each object the name below. On table start the script checks every **Phase 1** name and, if any are missing, lists them on the DMD for 20 seconds.

The table object itself must be named **`Table1`**.

## Phase 1 (required now)

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

## Phase 2 and 3 (build the geometry now, script comes later)

Build these into the first layout so the table is only laid out once. The Phase 1 script ignores them.

| Name | VPX type | Phase | Notes |
| --- | --- | --- | --- |
| `kImpactLock` *(or reuse `kImpact`)* | Kicker | 2 | Impact lock: holds balls for Expert Consensus multiball. |
| `liLock1`, `liLock2`, `liLock3` | Light | 2 | Locked-ball inserts. |
| `AirGapGate` | Gate or diverter wall | 2 | Pink gate, closed except during multiball. |
| `liAirGap` | Light | 2 | Pink Air Gap insert. |
| `swAirGap` | Trigger / target | 2 | Behind the gate: hit by the captive SCADA / OT ball. |
| `CaptiveAirGap` | Captive ball setup (kicker + ball) | 2 | The unscannable asset. |
| `swCentreRamp` | Trigger | 3 | Centre ramp: Storm Surge final shot. |

## Physics

Use VPX 10.8 standard physics (or nFozzy flipper physics if the author prefers). The acceptance test asks for 50 consecutive games with no stuck balls, so check saucer exits, ramp entrances and the plunger lane carefully.
