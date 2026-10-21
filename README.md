# Threat Tide

An original Visual Pinball X table for CyQuantiFi exhibition booths. You play the attacker; your score is realised loss in dollars. Hit the lit shot, build the kill chain left to right, and Impact completes an Attack Path. Game over ends on a one-screen board report the booth staff can talk to.

All dollar values are game-design numbers for fun. They are not CyQuantiFi model outputs. ATT&CK technique names: [MITRE ATT&CK®](https://attack.mitre.org).

## What's here

| Path | What |
| --- | --- |
| `table/tt_config.vbs` | **All tuning values and the technique decks, in one block.** Start here to change the game. |
| `table/tt_rules.vbs` | Game rules (chain, Paths, multiplier, combos, defences, Expert Consensus, Air Gap, Storm Surge). No VPX objects, so it's unit-tested. |
| `table/tt_table.vbs` | VPX glue: switches, lights, keys, ball handling, game flow. |
| `table/tt_display.vbs` | FlexDMD: $ score, chain pips, card callouts, board report, initials, attract. |
| `table/tt_scores.vbs` | High scores (contest-mode daily reset) and the JSON game log. |
| `table/tt_money.vbs`, `tt_sound.vbs` | $ formatting; sound cue mapping and volume presets. |
| `dist/ThreatTide_full.vbs` | Everything above in one file, to paste into the .vpx. Built by `tools/bundle.py`. |
| `tests/` | Rules tests, run with Windows `cscript` in CI. |
| `tools/` | Bundler, VBScript lint, tuning simulator. |
| `art/` | Editable SVG sources: playfield, backglass, inserts, asset icons. |
| `leaderboard/` | Live leaderboard page for the booth's second screen. Runs from disk, no server or internet. |
| `docs/` | Object contract, author brief, tuning guide, acceptance tests, booth runbook, licences. |

The `.vpx` table file itself (playfield geometry) is built in the VPX editor by a table author against [`docs/object-contract.md`](docs/object-contract.md). See [`docs/author-brief.md`](docs/author-brief.md).

## Working on it

```sh
python3 tools/vbs_lint.py      # block structure + duplicate names
python3 tools/bundle.py        # rebuild dist/ThreatTide_full.vbs (commit it)
python3 tools/tune_sim.py      # what the current numbers do to scores and game length
```

On Windows: `cd tests && cscript //nologo run_tests.wsf`. CI runs all of these on every push.

## Roadmap

| Phase | Scope | Status |
| --- | --- | --- |
| 1 — Booth MVP | 7 stage shots, technique cards, $ scoring, Paths, defences, board report, initials, high scores + JSON log | Script done |
| 2 — Modes | Expert Consensus multiball (3-ball virtual lock at Impact), Air Gap captive ball | Script done |
| 3 — Wizard and leaderboard | Storm Surge, live leaderboard page, contest mode | Script and page done |

All three phases still need the table author's geometry, art and sound, then cabinet playtesting against [`docs/acceptance.md`](docs/acceptance.md).

Open questions from the spec: cabinet (buy, build or hire), author budget and deadline, first target show, daily prize.
