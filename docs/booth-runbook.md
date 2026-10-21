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

## Daily routine

**Open**
- Power on, launch the table, confirm attract mode and today's empty high-score table (contest mode resets at midnight).
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
