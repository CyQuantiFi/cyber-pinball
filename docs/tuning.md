# Tuning guide

All values live in one block at the top of [`table/tt_config.vbs`](../table/tt_config.vbs). Change them there, run `python3 tools/tune_sim.py` to see the effect, rebuild the bundle, and playtest.

## Scoring

| Setting | Start | What it does |
| --- | --- | --- |
| `TT_Cards` | spec table | 16 technique cards: stage, name, ATT&CK ID, probability. Stage value = probability × Impact. A random card from the stage's deck is drawn on each stage hit. |
| `TT_IMPACT_START` | $100,000 | Impact at game start. |
| `TT_IMPACT_STEP` | $50,000 | Impact rise per asset drop target. *Not set by the spec; starting guess.* |
| `TT_UNLIT_SHARE` | 0.25 | An unlit stage pays 25% and doesn't advance the chain. |
| `TT_PATH_MULT_START` / `_STEP` / `_MAX` | 2 / 1 / 6 | Path multiplier. Resets to 2 on drain. |
| `TT_COMBO_WINDOW_MS` / `TT_COMBO_MULT` | 3000 / 2 | Lateral Movement → Initial Access combo. |
| `TT_DWELL_PER_SEC` / `TT_DWELL_CAP` | $5,000 / $250,000 | Drain bonus per second since the last stage hit. |
| `TT_EDR_CUT` | 0.10 | Each sling hit cuts the Path in progress. |
| `TT_EXTRA_BALL_AT_PATH` | 2 | Extra ball on the second completed Path. |

## Defences

| Setting | Start | What it does |
| --- | --- | --- |
| `TT_BALLSAVE_MS` | 10,000 | IR retainer from the moment the ball leaves the plunger lane. |
| `TT_RECON_FOR_RESAVE` | 2 | Collecting Recon twice in one ball arms one more save, held until the next drain. |
| `TT_PATCH_TUESDAY_MS` | 90,000 | Every 90 s of ball time, one random collected stage (never Impact) drops back to unlit. That stage is then the next lit shot. |
| `TT_TILT_WARNINGS` | 2 | Warnings before "Incident declared". |

## Expert Consensus multiball and Air Gap (Phase 2)

| Setting | Start | What it does |
| --- | --- | --- |
| `TT_ASSETS_PER_LOCK` | 3 | Asset drops per lit lock (one full bank). *Spec doesn't say how locks light; this is the lever for the "Air Gap in 1 in 5 games" target.* |
| `TT_LOCKS_FOR_MULTIBALL` | 3 | Balls locked at Impact to start multiball. |
| `TT_MB_BALLSAVE_MS` | 10,000 | IR retainer when multiball starts. |
| `TT_CONSENSUS_WINDOW_MS` | 4,000 | Same stage, different ball, inside this = agreement. |
| `TT_CONSENSUS_JACKPOT_START` | $500,000 | Jackpot at multiball start. *Not set by the spec.* |
| `TT_CONSENSUS_JACKPOT_STEP` | $250,000 | Added after each agreement. |
| `TT_CONSENSUS_DECAY` / `_MIN` | 5% / $100,000 | Scattered hit cuts the jackpot, never below the floor. |
| `TT_AIRGAP_MULT` | 3 | Air Gap pays the current jackpot × 3, once per multiball. |

## Storm Surge (Phase 3)

| Setting | Start | What it does |
| --- | --- | --- |
| `TT_WIZARD_AT_PATHS` | 3 | Completed Paths in one game to start it (once per game). |
| `TT_SURGE_MS` | 45,000 | Mode length. |
| `TT_SURGE_SWING_MS` | 5,000 | The shared multiplier changes this often. |
| `TT_SURGE_MULT_MIN` / `_MAX` | 1 / 10 | Range of the shared "weather" multiplier. |

## How rules were read from the spec

Where the spec left a choice, the script does this:

- **"In order"** means the lowest uncollected stage is the lit one. That makes Patch Tuesday clean: it opens a hole, and the hole is lit next.
- **Combo** doubles whatever Initial Access pays, lit or unlit.
- **EDR** cuts each collected stage value by 10%, so the Path award shrinks too. Dollars already scored stay.
- **Drain** loses the Path in progress and resets the multiplier; all dollars already scored stay.
- **Tilt** ends the ball's scoring, skips the IR retainer and pays no dwell bonus.
- **Impact** grows per game (not per ball).
- **Locks** light from full asset banks and are taken at the Impact scoop. They carry over between balls and reset after multiball.
- **Agreement** means the same stage as the previous multiball hit, inside 4 s, by a different ball. It pays the current jackpot, then the jackpot rises $250K. A **scattered** hit is one on a different stage from the previous hit: the jackpot drops 5%. Repeat hits by the same ball do neither.
- **Air Gap** is open from multiball start until one collect, the end of multiball or a tilt.
- **Storm Surge** starts the moment the 3rd Path completes. Every stage shot is lit and pays probability × Impact × the current weather. The chain is frozen and Patch Tuesday pauses. The centre ramp pays the tail jackpot (dollars scored in the mode × peak weather) and ends it. If the timer runs out first, there is no tail jackpot. A drain or tilt ends it too.

## Simulator baseline

`python3 tools/tune_sim.py` (5,000 games per profile, starting values):

| Profile | Median | p90 | Minutes | 1+ Path | Path within 3 games | Multiball | Air Gap | Storm Surge | Tail jackpot |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| First-timer | $1.5M | $5.1M | 3.5 | 28% | 62% | 4% | 2% | 2% | 1% |
| Average | $6.3M | $66.6M | 5.4 | 81% | 99% | 26% | 19% | 41% | 26% |
| Expert | $120.6M | $398.2M | 10.4 | 99% | 100% | 77% | 71% | 96% | 83% |

The player model is rough (fixed accuracy per shot, fixed drain rate, simple multiball and surge models), so read these as directions, not predictions.

**What it suggests before playtesting**

1. **Air Gap lands on target.** Average players reach it in about 19% of games, against the spec's "about 1 in 5". If playtests disagree, change `TT_ASSETS_PER_LOCK` first (2 makes multiball much more common).
2. **First-timers may miss the "Path within 3 games" target** (62%). Seven in-order shots is a lot for a novice. Levers, best first: make the early stages easy shots in the geometry (Recon and Initial Access off the flipper tips); lengthen `TT_BALLSAVE_MS`; a gentler `TT_EDR_CUT`. Changing the rules (e.g. keeping the chain on drain for ball 1) would need a spec change.
3. **Experts play for ~10 minutes.** Fine for a contest, slow for a queue. Levers: tighten outlanes; Patch Tuesday at 60 s.
4. **Storm Surge** is seen by ~40% of average players, and tail jackpots make the top of the leaderboard swing a lot (average-player p90 went from $28.6M before Phases 2 and 3 to $66.6M, mostly from multiball and tail jackpots). That's the spec's correlated tail risk in action; cap `TT_SURGE_MULT_MAX` if one lucky storm decides every day's contest.
