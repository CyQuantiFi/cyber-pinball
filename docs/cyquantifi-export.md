# CyQuantiFi export (plan)

Status: plan, not built. The full plan lives in `cyquantifi-core` at
`docs/game-results-export-plan.md`.

## Summary

- Every finished game is sent to one shared CyQuantiFi organisation,
  "Threat Tide Arcade", and recorded as a risk register entry labelled as from the game.
- The table itself never calls the network. It keeps appending to
  `ThreatTide_games.jsonl` as today.
- A separate `tools/uploader.py` reads new lines and posts them to
  `POST /api/game/results` with a cabinet API key, retrying while offline.
- Only initials are sent. Names and emails stay in the HubSpot form.

## Changes in this repo

1. `TTGameJson` (`table/tt_scores.vbs`) gains `schema_version`, `game_id`,
   `cabinet_id`, `event_id`, a time-zone offset, and each technique's probability.
   New settings `TT_CabinetId` and `TT_EventId` in `table/tt_config.vbs`.
   Tests in `tests/test_scores.vbs`; rebuild with `tools/bundle.py`.
2. `tools/uploader.py`: tails the jsonl, remembers the sent offset in
   `ThreatTide_upload_state.json`, logs rejected lines to
   `ThreatTide_upload_errors.jsonl`. Config from `ThreatTide_upload.ini` or
   `CYQ_API_URL` / `CYQ_API_KEY` (never committed).
3. `start_booth.bat`: start the uploader when `USE_UPLOAD=1`.
4. `docs/booth-runbook.md`: getting a key, checking the upload, re-sending a day.
