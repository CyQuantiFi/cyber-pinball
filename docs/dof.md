# Cabinet feedback (DOF)

The table sends numbered events to DirectOutput Framework (DOF). DOF then fires the contactors, the button lamps and the LED trim. The code is in `table/tt_dof.vbs` and is switched on by `TT_DofOn` in `tt_config.vbs`.

The bass shakers don't use DOF: they run off the amplifier's sub channel, so they follow the game sound.

## Setup on the cabinet

1. Install the B2S Backglass Server and DirectOutput. DOF sees the table through B2S.
2. Keep `ThreatTide.directb2s` next to `ThreatTide.vpx`.
3. **Hide the B2S window**, because the browser page owns the back screen. Start the table once, right-click the B2S backglass, open Settings, and tick **Hide B2S backglass** (also hide the grill and DMD if offered). B2S saves this per table, and DOF keeps working with the window hidden.
4. Tell DOF what each output does, using one of these:
   - **DOF Config Tool** (configtool.vpuniverse.com): register your Pinscape Pico and Teensy LED controller, add a table config named `ThreatTide`, and map the events below to your outputs. Download the generated config into DOF's `Config` folder.
   - **Hand edit**: in your device's `directoutputconfig*.ini`, add a `ThreatTide` line under the device section. Each comma-separated column is one output port in order. The sample below assumes ports 1 to 7 are wired as in the table further down:

     ```
     ThreatTide,E101,E102,E103,E104,E109,E140,E141
     ```
5. **Set a time limit on every contactor output** in the Pinscape config, about 1 s for the flippers and 50 to 100 ms for the others. A stuck event then can't cook a coil.

## Events

**Pulses**: DOF sets how long the output fires.

| Event | When | Suggested output |
| --- | --- | --- |
| E101 | Left flipper up (on while held) | Contactor 1 |
| E102 | Right flipper up (on while held) | Contactor 2 |
| E103 | Left slingshot | Contactor 3 (feature) |
| E104 | Right slingshot | Contactor 4 (feature) |
| E105 | Ball into the plunger lane | — |
| E106 | Persistence / Impact scoop kick | Contactor 3 or 4, if you have them |
| E107 | Asset drop target hit | — |
| E108 | Asset bank reset | — |
| E109 | Knocker: path complete, extra ball, jackpots, Air Gap | Contactor (or a shared one) + white LED flash |
| E110 | Plunger released | — |
| E111 | Drain | Short red LED flash |
| E112 | Stage shot collected | Cyan LED flash |
| E113 | Technique card shown | Orange LED flash |

**States**: on until switched off.

| Event | On while | Suggested LED trim |
| --- | --- | --- |
| E120 | Attract mode | Slow teal/blue colour cycle |
| E121 | Game in progress | Steady dim cyan |
| E122 | Expert Consensus multiball | Orange chase |
| E123 | Storm Surge | Purple strobe |
| E124 | Incident declared (tilt), until the next ball | Solid red |
| E125 | Board report and initials | Steady amber |
| E140 | A game can start | Start button lamp |
| E141 | A ball is waiting to launch | Launch button lamp |

Event numbers are constants at the top of `tt_dof.vbs`. If you renumber one, change it in your DOF config too.

## Testing without a game

The Pinscape config tool and DOF's own test tools can fire each output by hand. Do that first, with the coil time limits set, before starting the table.
