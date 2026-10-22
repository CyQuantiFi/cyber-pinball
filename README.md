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
| `tools/table_layout.py` | Playfield geometry (one source for both the table objects and the playfield art). |
| `art/` | SVG sources (`playfield_table.svg` is generated from the layout), renders, Comfortaa font. |
| `dmd/` | Comfortaa bitmap fonts for FlexDMD. |
| `sound/sfx/` | Game-cue sound effects, synthesized by `tools/make_sfx.py` (original, no licence to track). |
| `leaderboard/` | Live leaderboard page for the booth's second screen. Runs from disk, no server or internet. |
| `backglass/` | Browser backglass for the cabinet's back screen: art + live score while playing, ad video / promo + leaderboard when idle. |
| `cabinet/` | Wooden cabinet: parametric CAD (DXF cut files, A3 drawings, 3D model, renders), parts list and build guide. Start at [`cabinet/README.md`](cabinet/README.md). |
| `start_booth.bat` | Starts the back screen, leaderboard and table in the right order. |
| `docs/` | Object contract, author brief, tuning guide, acceptance tests, booth runbook, licences. |

**The playable table is built from this repo.** `tools/build_table.py` takes VPX's own blank table (the File > New template: cabinet, flippers, plunger lane, slings, apron), adds the Threat Tide shots from [`tools/table_layout.py`](tools/table_layout.py), the playfield and backglass art, sounds and the script, and writes `dist/ThreatTide.vpx` plus `dist/ThreatTide.directb2s`. CI builds both on every push: download them from the **ThreatTide-table** artifact on the Actions run. A table author then plays it on Windows and tunes the physics and art ([`docs/author-brief.md`](docs/author-brief.md)). Install steps: [`docs/booth-runbook.md`](docs/booth-runbook.md#installing-on-the-cabinet).

## Working on it

```sh
python3 tools/vbs_lint.py      # block structure + duplicate names
python3 tools/bundle.py        # rebuild dist/ThreatTide_full.vbs (commit it)
python3 tools/tune_sim.py      # what the current numbers do to scores and game length
bash tools/build_all.sh        # everything: sounds, fonts, art, .vpx, .directb2s
python3 tools/plot_table.py build/table map.png --bg art/render/playfield_table.png  # layout check
```

`build_all.sh` needs vpxtool (`cargo install vpxtool`), Pillow and numpy, and for the art step Node with Playwright and the Comfortaa font (`SKIP_ART=1` reuses the committed renders).

On Windows: `cd tests && cscript //nologo run_tests.wsf`. CI runs all of these on every push.

## Roadmap

| Phase | Scope | Status |
| --- | --- | --- |
| 1 — Booth MVP | 7 stage shots, technique cards, $ scoring, Paths, defences, board report, initials, high scores + JSON log | Script done |
| 2 — Modes | Expert Consensus multiball (3-ball virtual lock at Impact), Air Gap captive ball | Script done |
| 3 — Wizard and leaderboard | Storm Surge, live leaderboard page, contest mode | Script and page done |

What's left needs a Windows PC with VPX: play the built table, tune physics and shot geometry, finish the art, record voice callouts, then cabinet playtesting against [`docs/acceptance.md`](docs/acceptance.md).

Cabinet: a build-it-yourself design is in [`cabinet/`](cabinet/README.md).

Open questions from the spec: author budget and deadline, first target show, daily prize.

## Licence

Code, cabinet design files and original artwork are under the [MIT Licence](LICENSE). Third-party assets keep their own licences ([`docs/LICENSES.md`](docs/LICENSES.md)): Comfortaa is under the SIL OFL, and the VPX blank table is downloaded at build time under the VPX licence. The licence doesn't grant use of the CyQuantiFi name or logo as a trademark.
