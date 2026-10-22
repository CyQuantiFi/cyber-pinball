' =============================================================================
' Threat Tide - tuning and data block
'
' Every number a designer or operator might want to change lives here.
' All dollar values are game-design numbers for fun. They are not CyQuantiFi
' model outputs and must not be presented as real loss estimates.
'
' ATT&CK technique names and IDs: MITRE ATT&CK(R), https://attack.mitre.org
' =============================================================================

' ---- Stages (left to right across the playfield) ---------------------------
Const ST_RECON = 0
Const ST_INITIAL_ACCESS = 1
Const ST_EXECUTION = 2
Const ST_PERSISTENCE = 3
Const ST_PRIV_ESC = 4
Const ST_LATERAL = 5
Const ST_IMPACT = 6
Const TT_STAGE_COUNT = 7

Dim TT_StageNames
TT_StageNames = Array("Recon", "Initial Access", "Execution", "Persistence", _
                      "Privilege Escalation", "Lateral Movement", "Impact")

' ---- Technique decks ---------------------------------------------------------
' Each card: Array(stage, technique name, ATT&CK ID, probability)
' Stage value = probability x current Impact value.
Dim TT_Cards
TT_Cards = Array( _
    Array(ST_RECON,          "Active Scanning",                       "T1595", 0.9),  _
    Array(ST_RECON,          "Phishing for Information",              "T1598", 0.7),  _
    Array(ST_INITIAL_ACCESS, "Phishing",                              "T1566", 0.6),  _
    Array(ST_INITIAL_ACCESS, "Valid Accounts",                        "T1078", 0.5),  _
    Array(ST_INITIAL_ACCESS, "Exploit Public-Facing Application",     "T1190", 0.4),  _
    Array(ST_EXECUTION,      "Command and Scripting Interpreter",     "T1059", 0.8),  _
    Array(ST_EXECUTION,      "User Execution",                        "T1204", 0.6),  _
    Array(ST_PERSISTENCE,    "Scheduled Task/Job",                    "T1053", 0.6),  _
    Array(ST_PERSISTENCE,    "Create Account",                        "T1136", 0.5),  _
    Array(ST_PRIV_ESC,       "Exploitation for Privilege Escalation", "T1068", 0.4),  _
    Array(ST_PRIV_ESC,       "Valid Accounts",                        "T1078", 0.5),  _
    Array(ST_LATERAL,        "Remote Services",                       "T1021", 0.5),  _
    Array(ST_LATERAL,        "Lateral Tool Transfer",                 "T1570", 0.4),  _
    Array(ST_IMPACT,         "Data Encrypted for Impact",             "T1486", 0.3),  _
    Array(ST_IMPACT,         "Exfiltration Over C2 Channel",          "T1041", 0.35), _
    Array(ST_IMPACT,         "Data Destruction",                      "T1485", 0.2)   _
)

' ---- Scoring -----------------------------------------------------------------
Const TT_IMPACT_START = 100000        ' Impact value at game start ($)
Const TT_IMPACT_STEP = 50000          ' Impact rise per asset drop target ($)
Const TT_UNLIT_SHARE = 0.25           ' Unlit stage pays this share, no advance
Const TT_PATH_MULT_START = 2          ' Path multiplier at ball start
Const TT_PATH_MULT_STEP = 1           ' Added per completed Path
Const TT_PATH_MULT_MAX = 6            ' Cap
Const TT_COMBO_WINDOW_MS = 3000       ' Lateral Movement -> Initial Access window
Const TT_COMBO_MULT = 2               ' Combo multiplier on the second shot
Const TT_DWELL_PER_SEC = 5000         ' Drain bonus per second since last stage hit
Const TT_DWELL_CAP = 250000           ' Drain bonus cap
Const TT_EDR_CUT = 0.1                ' Each sling hit cuts Path in progress by this share
Const TT_EXTRA_BALL_AT_PATH = 2       ' Extra ball on this completed Path (per game)

' ---- Defences ----------------------------------------------------------------
Const TT_BALLSAVE_MS = 10000          ' IR retainer at ball start (from launch)
Const TT_RECON_FOR_RESAVE = 2         ' Recon collections per ball to re-arm IR retainer
Const TT_PATCH_TUESDAY_MS = 90000     ' Patch Tuesday interval
Const TT_TILT_WARNINGS = 2            ' Warnings before "Incident declared"
Const TT_TILT_DEBOUNCE_MS = 1000      ' Ignore repeat tilt-bob hits inside this window

' ---- Display timing ----------------------------------------------------------
Const TT_CARD_SHOW_MS = 2000          ' Technique card callout
Const TT_MSG_SHOW_MS = 1800           ' Other callouts
Const TT_REPORT_MS = 15000            ' Board report before initials entry
Const TT_INITIALS_TIMEOUT_MS = 45000  ' Auto-accept initials after this
Const TT_CLAIM_MS = 20000             ' "Scan to claim" screen after initials
Const TT_ATTRACT_PAGE_MS = 5000       ' Attract page rotation

' ---- Phase 2: Expert Consensus multiball and Air Gap -------------------------
Const TT_ASSETS_PER_LOCK = 3            ' Asset drops per lit lock (one full bank)
Const TT_LOCKS_FOR_MULTIBALL = 3        ' Balls locked at Impact to start multiball
Const TT_MB_BALLSAVE_MS = 10000         ' IR retainer at multiball start
Const TT_CONSENSUS_WINDOW_MS = 4000     ' Same stage, different ball, inside this = agreement
Const TT_CONSENSUS_JACKPOT_START = 500000 ' Jackpot at multiball start
Const TT_CONSENSUS_JACKPOT_STEP = 250000  ' Added after each agreement
Const TT_CONSENSUS_DECAY = 0.05         ' Scattered hit (different stage) cuts the jackpot
Const TT_CONSENSUS_JACKPOT_MIN = 100000 ' Decay floor
Const TT_AIRGAP_MULT = 3                ' Air Gap pays current jackpot x this

' ---- Phase 3: Storm Surge wizard -----------------------------------------------
Const TT_WIZARD_AT_PATHS = 3            ' Completed Paths in one game to start it
Const TT_SURGE_MS = 45000
Const TT_SURGE_SWING_MS = 5000          ' Shared multiplier changes this often
Const TT_SURGE_MULT_MIN = 1
Const TT_SURGE_MULT_MAX = 10

' ---- Operator settings -------------------------------------------------------
Dim TT_BallsPerGame : TT_BallsPerGame = 3
Dim TT_PatchTuesdayOn : TT_PatchTuesdayOn = True
Dim TT_VolumePreset : TT_VolumePreset = "booth"   ' "booth" (loud hall) or "quiet"
Dim TT_ContestMode : TT_ContestMode = True        ' High scores reset each day
Dim TT_DataDir : TT_DataDir = ""                  ' "" = VPX user folder
' Back screen: "page" = browser backglass (backglass/index.html: art while
' playing, ad video + leaderboard when idle); "b2s" = static ThreatTide.directb2s
Dim TT_BackglassMode : TT_BackglassMode = "page"
Dim TT_FormUrl : TT_FormUrl = "cyquantifi.com/play" ' Shown under the QR code

' ---- Music (files in VPX's Music\ThreatTide\ folder, see docs/LICENSES.md) ----
Dim TT_MusicTheme : TT_MusicTheme = "theme.mp3"   ' Loops during play
Dim TT_MusicSurge : TT_MusicSurge = ""            ' Storm Surge track; "" keeps the theme playing

' ---- Display -----------------------------------------------------------------
Const TT_DMD_W = 256
Const TT_DMD_H = 64
' FlexDMD assets folder, relative to the .vpx (copy the repo's dmd\ folder here)
Const TT_DMD_ASSETS = "./ThreatTide/"
' Brand fonts (Comfortaa BMFonts from tools/make_dmd_fonts.py). If they're
' missing, the built-in pixel fonts below are used instead.
Const TT_FONT_BRAND_BIG = "comfortaa_bold_24.fnt"
Const TT_FONT_BRAND_HEAD = "comfortaa_bold_14.fnt"
Const TT_FONT_BIG = "FlexDMD.Resources.udmd-f12by24.fnt"
Const TT_FONT_MED = "FlexDMD.Resources.udmd-f6by12.fnt"
Const TT_FONT_SMALL = "FlexDMD.Resources.udmd-f5by7.fnt"
Const TT_FONT_TINY = "FlexDMD.Resources.udmd-f4by5.fnt"
Const TT_QR_IMAGE = "VPX.qr_form"   ' Image named qr_form in the table's image manager

' ---- Geometry (set by the table author) --------------------------------------
' Kicker eject: angle in degrees (0 = up), force.
Const TT_KICK_PERSISTENCE_ANGLE = 180
Const TT_KICK_PERSISTENCE_FORCE = 12
Const TT_KICK_IMPACT_ANGLE = 214
Const TT_KICK_IMPACT_FORCE = 10
Const TT_RELEASE_ANGLE = 90
Const TT_RELEASE_FORCE = 7
Const TT_SAUCER_HOLD_MS = 900
Const TT_ASSET_RESET_MS = 1500
