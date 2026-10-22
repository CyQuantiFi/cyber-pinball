# Asset licences

> **Check before the first show: Visual Pinball X licence.** VPX has been moving to GPLv3+ since 2020, but files without a GPL marker are still under its older licence, which says redistributions "may not be sold, nor may they be used in a commercial product or activity". A booth used for marketing could count as commercial activity, both for running VPX and for the blank-table parts inside `ThreatTide.vpx`. Get a view from legal, or ask the VPX team (github.com/vpinball/vpinball), before the first show.

Every font, image, sound and music file in the table, backglass or display must have a row here before it goes to a show. Original table only: no third-party characters, logos or licensed music.

| Asset | Used in | Source / author | Licence | Notes |
| --- | --- | --- | --- | --- |
| Comfortaa (font), `art/fonts/` | Playfield, backglass, DMD (`dmd/*.fnt`), leaderboard | The Comfortaa Project Authors, from google/fonts | SIL Open Font License 1.1 (`art/fonts/OFL.txt`) | Embedding and bitmap conversion allowed; keep OFL.txt with the font. |
| FlexDMD built-in fonts (`udmd-*.fnt`) | DMD small text | FlexDMD (vbousquet) | Bundled with FlexDMD | |
| VPX blank table (`blankTable.vpx`) | Base of `ThreatTide.vpx`: cabinet, apron, flippers, slings, plunger lane, stock images and mechanical sounds | Visual Pinball X team | VPX licence (see below) | Downloaded at build time, not stored in this repo. |
| Game-cue sound effects (`sound/sfx/*.wav`) | Game | Synthesized by `tools/make_sfx.py` | Owned by CyQuantiFi | Original, generated from code. |
| Table-feel script (`table/tt_feel.vbs`) | Ball shadows, rolling sounds, sling animation | Adapted from the VPX blank table script (fuzzel, jimmyfingers, jpsalas, toxie, unclewilly, ninuzzu, rothbauerw) | VPX licence | Credited in the file header. |
| `art/playfield.svg`, `art/backglass.svg`, `art/icons/*`, `art/inserts/*` | Art sources | CyQuantiFi (made for this table) | Owned by CyQuantiFi | |
| MITRE ATT&CK technique names and IDs | Display, report, backglass | The MITRE Corporation | ATT&CK Terms of Use (attribution required) | Attribution on backglass and attract mode. |
| CyQuantiFi wordmark | Backglass | CyQuantiFi | Owned | |
| Built-in promo loop and `promo.mp4` | Back screen ad loop | Made for CyQuantiFi (`backglass/index.html`, `tools/render_promo.js`) | Owned by CyQuantiFi | Comfortaa (OFL). |
| *Ad videos in `backglass/media/`* | Back screen ad loop | *CyQuantiFi* | *Record the source of any stock footage or music in them* | Not stored in this repo. |
| Music: `theme.mp3` (background, loops) | Game, incl. Storm Surge | "Cyberpunk music" by atlasaudio, Pixabay track 617559 (file `atlasaudio-cyberpunk-music-617559.mp3`) | [Pixabay Content License](https://pixabay.com/service/license-summary/) | Free for commercial use, no attribution required. Do not redistribute the file on its own, so it is **not** committed to this public repo. Keep the original download and a screenshot of the track page with the event records. |
| *Music: `surge.mp3` (optional)* | Storm Surge | *TBD* | *TBD* | Only if `TT_MusicSurge` is set. Original or royalty-free only. |
| *Voice callouts (`vo_*`)* | Game | *TBD* | *TBD* | "Initial access", "Path complete", "Air gap breached", "Storm surge", "Extra ball", "Incident declared", "Expert locked", "Expert consensus", "Jackpot". |
| Comfortaa via Google Fonts | Leaderboard page | Google Fonts | SIL OFL 1.1 | Falls back to the system font when offline. |
| *Sound effects (`sfx_*`)* | Game | *TBD* | *TBD* | |
