# Booth runbook

## Booth flow

1. Player finishes and enters 3 initials on the cabinet.
2. The board report (15 s) and then the claim screen (20 s) show their initials, full $ score and the QR code.
3. Player scans the QR or uses the booth tablet: a HubSpot form where they enter their initials and score.
4. Staff use the board report as the opener for a 2-minute conversation: *"Your worst day was $X through phishing and valid accounts. Want that number for your real environment?"*

## HubSpot form

| Field | Required | Notes |
| --- | --- | --- |
| Name | Yes | |
| Work email | Yes | |
| Organisation | Yes | |
| Role | Yes | |
| Cabinet initials | Yes | For prize verification |
| Cabinet score | Yes | For prize verification |
| What's one system you can't scan? | No | Free text. Logged separately as validation data. |
| Enter today's contest | Yes, to win | Checkbox |
| Send me CyQuantiFi updates | No | Checkbox, **unticked by default** |

Add a collection notice above the submit button (see Privacy below) and a link to the contest terms. Point the QR code at the form URL and put the same URL in `TT_FormUrl` in `table/tt_config.vbs`.

## Contest rules (draft terms)

- Highest dollar score each day wins; ties go to the earlier entry (the cabinet's high-score table already orders ties this way).
- Winner is verified by matching cabinet initials and score to the form entry. The cabinet log `ThreatTide_games.jsonl` has the time of every game.
- One prize per person per event. Staff and their families cannot win.
- Written terms displayed at the booth and linked from the form.
- Scores are game-design numbers for fun, not real loss estimates.

## Installing on the cabinet

Needs Visual Pinball X 10.8, FlexDMD, and Chrome or Edge (standard on a virtual pinball cabinet). The B2S Backglass Server is only needed if you switch the back screen to the static image (`TT_BackglassMode = "b2s"`).

1. Download the **ThreatTide-table** artifact from the latest green CI run (Actions tab), or run `bash tools/build_all.sh`. Copy this whole repo to the cabinet too (e.g. `C:\ThreatTide\`): the back screen, leaderboard and launchers run from it.
2. Copy `ThreatTide.vpx` (and `ThreatTide.directb2s`, used only in `b2s` mode) into VPX's `Tables` folder.
3. Copy the repo's `dmd\` folder to `Tables\ThreatTide\` (the Comfortaa DMD fonts). Without it the DMD uses pixel fonts.
4. Copy the music (below).
5. Set the paths at the top of `start_booth.bat`, `backglass\start_backglass.bat` and (if used) `leaderboard\start_leaderboard.bat`, then start everything with `start_booth.bat`. If any table objects are missing, the DMD lists them for 20 seconds.

## Back screen: idle ad loop

The back screen is a browser page (`backglass/index.html`) that follows the table:

| Table is… | Back screen shows |
| --- | --- |
| Being played (game, board report, initials, QR) | Backglass art with ball number and live $ score |
| In attract mode for 60 s, or not running at all | Ad loop: your videos (or the built-in CyQuantiFi promo) → today's leaderboard (20 s) → repeat |

Pressing Start brings the art back within about a second.

**Your ad videos:** copy them into `backglass\media\`, copy `playlist.example.js` to `playlist.js` there and list the files. MP4 (H.264) works best. With no playlist the built-in promo plays (5 animated slides, 30 s: Threat Tide, $ counter, tagline, today's top score, QR code). The same promo is exported as `promo.mp4` (1920×1080) in the CI artifact, for socials or other booth screens. Videos play muted; add `&sound=1` to the page URL in `start_backglass.bat` for sound (it will mix with the table's music).

**Settings** (in `start_backglass.bat`): `SCREEN_POS` (where the back screen starts in Windows display settings), `IDLE_SECS`, `DATA_DIR` (same as `TT_DataDir`). A video that won't play is skipped after 8 s, so a bad file never freezes the screen.

**Start order matters:** the browser must open *before* Visual Pinball, or VPX loses keyboard focus and the flippers won't respond. `start_booth.bat` does this; if you start things by hand and the flippers are dead, click the playfield once.

**Preview:** kiosk mode has no developer tools, so preview on a laptop instead: open `backglass/index.html?idle=5` in Chrome. To watch the promo alone: `?promo=1`.

## Music (one-time cabinet setup)

Copy the background track (Pixabay `atlasaudio-cyberpunk-music-617559.mp3`, kept with CyQuantiFi's event files, not in the repo) to:

```
<VPX folder>\Music\ThreatTide\theme.mp3
```

It loops during games and stops in attract mode. Volume follows the F12 "Volume preset" (Booth: music at 35%, Quiet: 15%). The track is mastered loud (about -10.5 LUFS), so check it against the voice callouts on the real speakers.

## Leaderboard screen (second monitor)

One-time setup on the cabinet PC:
1. Set `TT_DataDir` in `table/tt_config.vbs` to a fixed folder, e.g. `C:\ThreatTide\data\`, and rebuild the bundle.
2. Copy the `leaderboard/` folder to the cabinet (e.g. `C:\ThreatTide\leaderboard\`).
3. Edit the top of `start_leaderboard.bat`: `DATA_DIR` (same folder as step 1) and `SCREEN_POS` (where the second monitor starts).
4. Double-click `start_leaderboard.bat`. It opens Chrome or Edge full screen. Alt+F4 closes it.

The page works offline. It checks for new scores every 3 seconds and highlights the newest entry. Preview it anywhere with `index.html?data=sample_data.js`.

## Daily routine

**Open**
- Power on, launch the table, confirm attract mode and today's empty high-score table (contest mode resets at midnight).
- Start the leaderboard screen; it shows "No losses yet today".
- Volume preset "Booth" for loud halls; "Quiet" for small rooms (F12 menu).
- Check the tablet is logged in to the form.

**Close**
- Photograph the high-score table on the DMD.
- Copy `ThreatTide_games.jsonl` and `ThreatTide_highscores.json` from the VPX `User` folder to the event folder.
- Pick the winner: top score, verified against the form entry.

## After each show

- Export form entries to HubSpot with an event tag.
- Log answers to "What's one system you can't scan?" separately; they feed the validation record, not just the lead list.

## Compliance checklist (each show)

- [ ] Spam Act 2003: marketing emails only to people who ticked the updates box; every email has an unsubscribe.
- [ ] Privacy: collection notice on the form saying what is collected, why, and how to opt out.
- [ ] Trade promotion: confirm the contest is a game of skill and check the rules for the event's state.
- [ ] Venue: confirm power, floor space and noise rules with the organiser.
- [ ] MITRE ATT&CK attribution present on backglass and attract mode.
