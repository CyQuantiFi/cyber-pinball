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

## How rules were read from the spec

Where the spec left a choice, the script does this:

- **"In order"** means the lowest uncollected stage is the lit one. That makes Patch Tuesday clean: it opens a hole, and the hole is lit next.
- **Combo** doubles whatever Initial Access pays, lit or unlit.
- **EDR** cuts each collected stage value by 10%, so the Path award shrinks too. Dollars already scored stay.
- **Drain** loses the Path in progress and resets the multiplier; all dollars already scored stay.
- **Tilt** ends the ball's scoring, skips the IR retainer and pays no dwell bonus.
- **Impact** grows per game (not per ball).

## Simulator baseline

`python3 tools/tune_sim.py` (5,000 games per profile, starting values):

| Profile | Median | p90 | Minutes | 1+ Path | Path within 3 games | 3+ Paths |
| --- | --- | --- | --- | --- | --- | --- |
| First-timer | $1.5M | $5.0M | 3.4 | 28% | 62% | 1% |
| Average | $6.6M | $28.6M | 5.1 | 81% | 99% | 40% |
| Expert | $87.1M | $316.9M | 9.9 | 99% | 100% | 97% |

The player model is rough (fixed accuracy per shot, fixed drain rate), so read these as directions, not predictions.

**What it suggests before playtesting**

1. **First-timers may miss the "Path within 3 games" target** (62% vs. the spec's expectation). Seven in-order shots is a lot for a novice. Levers, best first: make the early stages easy shots in the geometry (Recon and Initial Access off the flipper tips); lengthen `TT_BALLSAVE_MS`; a gentler `TT_EDR_CUT`. Changing the rules (e.g. keeping the chain on drain for ball 1) would need a spec change.
2. **Experts play for ~10 minutes.** Fine for a contest, slow for a queue. Levers: 3 balls is already the floor; tighten outlanes; Patch Tuesday at 60 s.
3. **Storm Surge (3 Paths)** would be seen by ~40% of average players. That fits a wizard mode that's earned, but check it in playtesting before Phase 3.
