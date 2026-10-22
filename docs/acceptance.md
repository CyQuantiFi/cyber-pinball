# Acceptance tests

Run these on the booth cabinet (or an identical setup). Tick each box and note the date and who tested.

## Automated (every push)

- [ ] GitHub Actions **CI** is green: VBScript lint, bundle up to date, rules tests under `cscript`.

## Setup

- [ ] Table starts with no "SETUP: … OBJECT(S) MISSING" screen.
- [ ] FlexDMD shows the attract loop: title, today's high scores, "Put a dollar figure on every cyber risk", 3-line how-to-play, MITRE ATT&CK attribution.
- [ ] Backglass shows "THREAT TIDE", the CyQuantiFi wordmark and the MITRE ATT&CK attribution.
- [ ] Operator menu (F12) changes balls per game, Patch Tuesday, volume preset and contest mode, and the change sticks after restart.

## Phase 1 — Booth MVP

**Rules, checked by playing**

- [ ] Start → "BALL 1 / HIT THE LIT SHOT"; Recon insert blinks.
- [ ] Each stage hit shows the technique name and ATT&CK ID for 2 s with a $ value.
- [ ] Lit stage: insert goes solid, next insert blinks, chain pip fills. Unlit stage: smaller $ value, chain unchanged.
- [ ] Hitting Impact with stages 1–6 collected shows "PATH COMPLETE" with the award and multiplier; inserts reset.
- [ ] Lateral Movement → Initial Access inside 3 s shows "COMBO X2".
- [ ] Sling hit shows "DETECTED: EDR" and a lower Path value.
- [ ] Drain inside 10 s of launch: "IR RETAINER / BALL SAVED".
- [ ] Drain after that: "DWELL TIME" bonus, "EVICTED BY THE SOC", next ball.
- [ ] Second Path: "EXTRA BALL", shoot-again light, same ball number after the drain.
- [ ] Asset drop: "ASSET COMPROMISED", Impact rises on the info line.
- [ ] Patch Tuesday (on): after 90 s a collected insert goes dark and blinks as the next shot.
- [ ] Heavy nudging: two warnings, then "INCIDENT DECLARED", flippers dead, no bonus.

**Game over**

- [ ] Board report shows for 15 s on **every** game over: total realised loss, "Your worst day", the costliest Path as 7 ATT&CK IDs, assets compromised, closing line.
- [ ] Board report readable from 2 m (stand at 2 m and read it aloud).
- [ ] Initials entry works with flippers + start; times out after 45 s.
- [ ] Claim screen shows QR, initials and full $ score for 20 s.
- [ ] `ThreatTide_games.jsonl` gains one line per game and `ThreatTide_highscores.json` updates (VPX `User` folder unless `TT_DataDir` is set).
- [ ] Contest mode on: high scores reset after the date changes.

**Spec targets**

- [ ] Every score on every screen has $ formatting; no raw point values anywhere. Above $10M shows as `$12.4M`.
- [ ] A first-time player completes a Path within 3 games (test with at least 5 people who haven't played it).
- [ ] Average first-timer game lasts 3–5 minutes.
- [ ] No stuck balls in 50 consecutive test games.
- [ ] Runs a full day unattended in attract mode without crashing (leave it 8+ hours).
- [ ] No third-party IP in art, sound or layout; every asset listed in `docs/LICENSES.md`.

## Phase 2 — Modes

- [ ] Dropping all 3 asset targets shows "LOCK IS LIT"; a lock insert blinks; the DMD's next line adds "LOCK LIT".
- [ ] Shooting Impact with a lock lit shows "EXPERT 1 LOCKED"; the ball disappears and a new one is served. Same for lock 2.
- [ ] Lock 3 starts "EXPERT CONSENSUS": the held ball ejects, two more follow, the pink Air Gap insert blinks and the gate drops.
- [ ] Two different balls through the same shot inside 4 s: "AGREEMENT" with the jackpot; the jackpot on the info line rises $250K.
- [ ] Hits on different shots lower the jackpot on the info line.
- [ ] Shooting the captive ball: "AIR GAP BREACHED $X / QUANTIFIED THE ASSET YOU CAN'T SCAN" for jackpot × 3; the gate closes; a second hit pays nothing.
- [ ] Draining to one ball: "CONSENSUS CLOSED / AIR GAP SEALED", gate up, play continues on the same ball.
- [ ] A drain in the first 10 s of multiball is saved.
- [ ] Board report shows "AIR GAP BREACHED" when it was collected.
- [ ] Multiball eject: no ball collisions or stuck balls at the Impact scoop over 20 multiballs.
- [ ] Air Gap is reached in about 1 in 5 games by average players.

## Phase 3 — Wizard and leaderboard

- [ ] Third Path of a game starts "STORM SURGE": all stage inserts blink, info line shows seconds left, weather multiplier and peak.
- [ ] Weather multiplier changes every 5 s ("SHARED WEATHER X…").
- [ ] Centre ramp during the storm: "TAIL JACKPOT $X"; the mode ends.
- [ ] Timer running out: "STORM PASSED / TAIL JACKPOT MISSED".
- [ ] Storm Surge happens at most once per game.
- [ ] `leaderboard/start_leaderboard.bat` opens the board full screen on the second monitor, with no internet connection.
- [ ] Leaderboard updates within 10 s of initials entry (it checks every 3 s).
- [ ] The new entry is highlighted and the "Latest attack" panel shows the costliest Path with technique names.
- [ ] After midnight with contest mode on, the board shows "No losses yet today" until the first game.

## Back screen ad loop

- [ ] `start_booth.bat` opens the back screen, then VPX; the flippers work without clicking.
- [ ] While playing, the back screen shows the art with the ball number and live $ score; the MITRE ATT&CK attribution stays visible.
- [ ] After 60 s in attract mode the ad loop starts: video (or promo) → leaderboard → repeat.
- [ ] Pressing Start returns to the art within about a second, with the video stopped.
- [ ] With VPX closed, the back screen keeps looping the ads.
- [ ] A deliberately broken video file is skipped within 10 s.
- [ ] Runs a full day without the browser running out of memory (check Task Manager at close).
