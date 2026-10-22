# CyQuantiFi export

Every finished game can be sent to CyQuantiFi, into the shared **Threat Tide
Arcade** organisation. Each game with a completed attack path also becomes a
risk register entry labelled as from the game. The full design is in
`cyquantifi-core` at `docs/game-results-export-plan.md`.

- The table never calls the network. It appends one line per game to
  `ThreatTide_games.jsonl`, as it always has.
- `tools/uploader.py` reads new lines and sends them, retrying while the booth
  is offline. The jsonl file stays the master copy.
- Only initials are sent. Names and emails stay in the HubSpot form.
- The dollar figures are game-design numbers, and CyQuantiFi says so on every
  entry.

## One-time setup

**In CyQuantiFi** (an admin of Threat Tide Arcade):

1. Register the cabinet: `POST /api/game/cabinets` with
   `{"code": "TT-01", "name": "Booth cabinet 1"}`.
2. Mint its key: `POST /api/api-keys` with `scopes: ["game.ingest"]`,
   `subject_type: "game_cabinet"` and the cabinet's `id`. Copy the key; it is
   shown once.

**On the booth PC:**

1. Install Python 3.10 or later (python.org; tick "Add to PATH").
2. In `table/tt_config.vbs` set `TT_CabinetId` to the code from step 1, and
   `TT_DataDir` to a fixed folder such as `C:\ThreatTide\data\`. Rebuild the
   bundle (`python3 tools/bundle.py`).
3. Copy `tools/ThreatTide_upload.example.ini` to
   `ThreatTide_upload.ini` in that data folder and paste in the URL and key.
4. In `start_booth.bat` set `USE_UPLOAD=1` and `UPLOAD_DATA_DIR` to the same
   folder.
5. Check it: `python tools\uploader.py --data-dir C:\ThreatTide\data --dry-run`.

## Each event

Set `TT_EventId` (e.g. `aisa-melb-2026`) and, if you like, `TT_EventName`
(`AISA Melbourne 2026`) in `table/tt_config.vbs`, and rebuild. CyQuantiFi makes
one project per event.

The table reads the PC's time zone from Windows. If the clock or time zone is
wrong, fix Windows, or set `TT_UtcOffsetMin` (minutes east of UTC, e.g. `660`
for AEDT).

## What each line carries

On top of the fields the leaderboard already used:

| Field | Example | Notes |
| --- | --- | --- |
| `schema_version` | `1` | Bumped when the line changes shape |
| `game_id` | `TT-01-20261022T140311-42` | Cabinet, local time, game number. The number survives restarts. |
| `cabinet_id` | `TT-01` | `TT_CabinetId` |
| `event_id` | `aisa-melb-2026` | `TT_EventId` |
| `event_name` | `AISA Melbourne 2026` | Only when `TT_EventName` is set |
| `ts` | `2026-10-22T14:03:11+11:00` | With the UTC offset. Without one (unknown time zone) CyQuantiFi refuses the line. |
| `worst_path_techniques[].probability` | `0.900` | The game's per-stage probability |

## Checking on it

Files in the data folder:

| File | What it is |
| --- | --- |
| `ThreatTide_upload.log` | What was sent and when, and any connection trouble |
| `ThreatTide_upload_errors.jsonl` | Lines CyQuantiFi refused, with the reason. Games from before this change land here (no `schema_version`). |
| `ThreatTide_upload_state.json` | How far through the games file it has got |

To send a whole file again (say, after restoring a backup):
`python tools\uploader.py --data-dir C:\ThreatTide\data --once --resend`.
Games CyQuantiFi already has are skipped.
