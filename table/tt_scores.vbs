' =============================================================================
' Threat Tide - high scores and game log
'
' High-score table: top 10, kept in VPX's settings store (SaveValue/LoadValue).
' Contest mode: the table resets when the date changes.
' Each game also writes, in the data folder:
'   ThreatTide_games.jsonl       one JSON line per game (append)
'   ThreatTide_highscores.json   today's table (rewritten)
'   ThreatTide_leaderboard.js    today's table + last game, for leaderboard/index.html
' =============================================================================

Const TTHS_COUNT = 10
Dim TTHS_Names(9), TTHS_Scores(9), TTHS_Day

Function TTToday()
    TTToday = CStr(Year(Date)) & TTPad2(Month(Date)) & TTPad2(Day(Date))
End Function

Function TTPad2(n)
    TTPad2 = Right("0" & CStr(n), 2)
End Function

Function TTIsoNow()
    TTIsoNow = TTIsoTime(Now)
End Function

' Local time as 2026-10-22T14:03:11 (no zone).
Function TTIsoTime(n)
    TTIsoTime = Year(n) & "-" & TTPad2(Month(n)) & "-" & TTPad2(Day(n)) & "T" & _
                TTPad2(Hour(n)) & ":" & TTPad2(Minute(n)) & ":" & TTPad2(Second(n))
End Function

' Local time as 20261022T140311, for game ids.
Function TTStamp(n)
    TTStamp = Year(n) & TTPad2(Month(n)) & TTPad2(Day(n)) & "T" & _
              TTPad2(Hour(n)) & TTPad2(Minute(n)) & TTPad2(Second(n))
End Function

Sub TTScoresClear()
    Dim i
    For i = 0 To TTHS_COUNT - 1
        TTHS_Names(i) = "---"
        TTHS_Scores(i) = 0
    Next
End Sub

Sub TTScoresLoad()
    Dim i, v
    TTScoresClear
    TTHS_Day = ""
    On Error Resume Next
    TTHS_Day = CStr(LoadValue("ThreatTide", "HS_Day"))
    For i = 0 To TTHS_COUNT - 1
        v = LoadValue("ThreatTide", "HS_N" & i)
        If v <> "" Then TTHS_Names(i) = v
        v = LoadValue("ThreatTide", "HS_S" & i)
        If v <> "" Then TTHS_Scores(i) = CDbl(v)
    Next
    Err.Clear
    On Error GoTo 0
    TTScoresCheckDay
End Sub

Sub TTScoresSave()
    Dim i
    On Error Resume Next
    SaveValue "ThreatTide", "HS_Day", TTHS_Day
    For i = 0 To TTHS_COUNT - 1
        SaveValue "ThreatTide", "HS_N" & i, TTHS_Names(i)
        SaveValue "ThreatTide", "HS_S" & i, TTDigits(TTHS_Scores(i))
    Next
    Err.Clear
    On Error GoTo 0
End Sub

' Contest mode: new day, new table.
Sub TTScoresCheckDay()
    Dim today : today = TTToday()
    If TTHS_Day = today Then Exit Sub
    If TT_ContestMode Then TTScoresClear
    TTHS_Day = today
    TTScoresSave
End Sub

' Returns rank 1..10, or 0 if not placed. Ties go to the earlier entry.
Function TTScoresAdd(initials, score)
    Dim i, j
    TTScoresCheckDay
    TTScoresAdd = 0
    For i = 0 To TTHS_COUNT - 1
        If score > TTHS_Scores(i) Then
            For j = TTHS_COUNT - 1 To i + 1 Step -1
                TTHS_Names(j) = TTHS_Names(j - 1)
                TTHS_Scores(j) = TTHS_Scores(j - 1)
            Next
            TTHS_Names(i) = initials
            TTHS_Scores(i) = CDbl(score)
            TTScoresAdd = i + 1
            TTScoresSave
            Exit Function
        End If
    Next
End Function

' "1. ABC  $12.4M" for attract mode; rank is 1-based.
Function TTHighScoreLine(rank)
    Dim i : i = rank - 1
    If i < 0 Or i >= TTHS_COUNT Then
        TTHighScoreLine = ""
    ElseIf TTHS_Scores(i) <= 0 Then
        TTHighScoreLine = rank & ". ---"
    Else
        TTHighScoreLine = rank & ". " & TTHS_Names(i) & "  " & TTMoney(TTHS_Scores(i))
    End If
End Function

' ---------------------------------------------------------------- JSON output

Function TTJsonStr(s)
    Dim r
    r = Replace(CStr(s), "\", "\\")
    r = Replace(r, """", "\""")
    TTJsonStr = """" & r & """"
End Function

Function TTJsonBool(b)
    If b Then
        TTJsonBool = "true"
    Else
        TTJsonBool = "false"
    End If
End Function

Function TTDataPath(fileName)
    Dim d, fso
    d = TT_DataDir
    If d = "" Then
        On Error Resume Next
        d = UserDirectory
        If Err.Number <> 0 Then d = ""
        Err.Clear
        On Error GoTo 0
    End If
    If d = "" Then
        Set fso = CreateObject("Scripting.FileSystemObject")
        d = fso.GetAbsolutePathName(".")
    End If
    If Right(d, 1) <> "\" Then d = d & "\"
    TTDataPath = d & fileName
End Function

' ------------------------------------------------------- CyQuantiFi export
' Each game line is also what tools/uploader.py sends to CyQuantiFi, so it
' carries a schema version, a unique game id, the cabinet and event, and a
' timestamp with its UTC offset. See docs/cyquantifi-export.md.

Const TT_RESULT_SCHEMA = 1
Dim TTGameSeq : TTGameSeq = -1

' Next game number on this cabinet. Kept in VPX's settings store so a restart
' never reuses a game id. Outside VPX (the tests) it just counts from 1.
Function TTNextGameSeq()
    Dim v
    If TTGameSeq < 0 Then
        TTGameSeq = 0
        v = ""
        On Error Resume Next
        v = CStr(LoadValue("ThreatTide", "GameSeq"))
        Err.Clear
        On Error GoTo 0
        If IsNumeric(v) Then TTGameSeq = CLng(v)
    End If
    TTGameSeq = TTGameSeq + 1
    On Error Resume Next
    SaveValue "ThreatTide", "GameSeq", CStr(TTGameSeq)
    Err.Clear
    On Error GoTo 0
    TTNextGameSeq = TTGameSeq
End Function

' Minutes east of UTC right now, or Empty if it can't be found.
' TT_UtcOffsetMin wins; otherwise Windows' ActiveTimeBias (which includes
' daylight saving) is read from the registry.
Function TTUtcOffsetMin()
    Dim sh, bias
    TTUtcOffsetMin = Empty
    If CStr(TT_UtcOffsetMin) <> "" Then
        If IsNumeric(TT_UtcOffsetMin) Then TTUtcOffsetMin = CLng(TT_UtcOffsetMin)
        Exit Function
    End If
    bias = Empty
    On Error Resume Next
    Set sh = CreateObject("WScript.Shell")
    bias = sh.RegRead("HKLM\SYSTEM\CurrentControlSet\Control\TimeZoneInformation\ActiveTimeBias")
    Err.Clear
    On Error GoTo 0
    ' IsNumeric(Empty) is True in VBScript, so a failed read must be ruled out first.
    If IsEmpty(bias) Then Exit Function
    If IsNumeric(bias) Then
        bias = CDbl(bias)
        ' A REG_DWORD can come back unsigned.
        If bias > 2147483647 Then bias = bias - 4294967296
        TTUtcOffsetMin = -CLng(bias)
    End If
End Function

' +11:00 / -03:30 / +00:00, or "" if the offset is unknown.
Function TTOffsetText(m)
    Dim sign, a
    TTOffsetText = ""
    If IsEmpty(m) Then Exit Function
    sign = "+"
    If m < 0 Then sign = "-"
    a = Abs(m)
    TTOffsetText = sign & TTPad2(a \ 60) & ":" & TTPad2(a Mod 60)
End Function

' 0..1 as "0.350". Built from whole numbers so a PC that writes decimals with
' a comma still produces valid JSON.
Function TTJsonFrac(p)
    Dim n
    n = Int(CDbl(p) * 1000 + 0.5)
    If n < 0 Then n = 0
    TTJsonFrac = CStr(n \ 1000) & "." & Right("00" & CStr(n Mod 1000), 3)
End Function

Function TTCardProb(c)
    If c < 0 Then
        TTCardProb = 0
    Else
        TTCardProb = TT_Cards(c)(3)
    End If
End Function

' One game as a JSON object (single line), stamped now.
Function TTGameJson(g, initials, rank)
    TTGameJson = TTGameJsonAt(g, initials, rank, Now, TTNextGameSeq(), TTUtcOffsetMin())
End Function

' The same, with the clock, game number and UTC offset passed in (for tests).
Function TTGameJsonAt(g, initials, rank, n, seq, offsetMin)
    Dim i, c, path, j, ev
    path = ""
    If g.WorstPathValue > 0 Then
        For i = 0 To TT_STAGE_COUNT - 1
            c = g.WorstPathCard(i)
            If i > 0 Then path = path & ","
            path = path & "{""stage"":" & TTJsonStr(TT_StageNames(i)) & _
                          ",""id"":" & TTJsonStr(TTCardId(c)) & _
                          ",""technique"":" & TTJsonStr(TTCardName(c)) & _
                          ",""probability"":" & TTJsonFrac(TTCardProb(c)) & "}"
        Next
    End If
    ev = ""
    If TT_EventName <> "" Then ev = ",""event_name"":" & TTJsonStr(TT_EventName)
    j = "{""schema_version"":" & TT_RESULT_SCHEMA & _
        ",""game_id"":" & TTJsonStr(TT_CabinetId & "-" & TTStamp(n) & "-" & seq) & _
        ",""cabinet_id"":" & TTJsonStr(TT_CabinetId) & _
        ",""event_id"":" & TTJsonStr(TT_EventId) & ev & _
        ",""ts"":" & TTJsonStr(TTIsoTime(n) & TTOffsetText(offsetMin)) & _
        ",""day"":" & TTJsonStr(TTHS_Day) & _
        ",""initials"":" & TTJsonStr(initials) & _
        ",""score"":" & TTDigits(g.Score) & _
        ",""score_text"":" & TTJsonStr(TTMoneyFull(g.Score)) & _
        ",""rank"":" & rank & _
        ",""worst_path"":" & TTDigits(g.WorstPathValue) & _
        ",""worst_path_techniques"":[" & path & "]" & _
        ",""paths"":" & g.PathsCompleted & _
        ",""assets"":" & g.AssetsDropped & _
        ",""multiballs"":" & g.MultiballsPlayed & _
        ",""agreements"":" & g.AgreementCount & _
        ",""storm_surge"":" & TTJsonBool(g.SurgePlayed) & _
        ",""tail_jackpot"":" & TTDigits(g.SurgeTail) & _
        ",""air_gap"":" & TTJsonBool(g.AirGapBreached) & "}"
    TTGameJsonAt = j
End Function

Function TTHighScoresJson()
    Dim i, rows
    rows = ""
    For i = 0 To TTHS_COUNT - 1
        If TTHS_Scores(i) > 0 Then
            If rows <> "" Then rows = rows & ","
            rows = rows & vbCrLf & "  {""rank"":" & (i + 1) & _
                   ",""initials"":" & TTJsonStr(TTHS_Names(i)) & _
                   ",""score"":" & TTDigits(TTHS_Scores(i)) & _
                   ",""score_text"":" & TTJsonStr(TTMoneyFull(TTHS_Scores(i))) & "}"
        End If
    Next
    TTHighScoresJson = "{""day"":" & TTJsonStr(TTHS_Day) & _
                       ",""updated"":" & TTJsonStr(TTIsoNow()) & _
                       ",""scores"":[" & rows & vbCrLf & "]}" & vbCrLf
End Function

' ---------------------------------------------------------------- backglass page state

' ThreatTide_state.js tells backglass/index.html what the table is doing, so
' it can show the art while someone plays and the ad loop when nobody does.
Dim TTStateSeq : TTStateSeq = 0
Dim TTStateKey : TTStateKey = ""

Function TTStateJs(mode, g)
    TTStateJs = "window.TT_STATE = {""seq"":" & TTStateSeq & _
                ",""mode"":" & TTJsonStr(mode) & _
                ",""ts"":" & TTJsonStr(TTIsoNow()) & _
                ",""score"":" & TTDigits(g.Score) & _
                ",""score_text"":" & TTJsonStr(TTMoney(g.Score)) & _
                ",""ball"":" & g.BallNum & _
                ",""balls"":" & g.BallsPerGame & "};" & vbCrLf
End Function

' Writes only when something changed. Never lets a disk error stop play.
Sub TTWriteState(mode, g)
    Dim key, fso, f
    key = mode & "|" & TTDigits(g.Score) & "|" & g.BallNum
    If key = TTStateKey Then Exit Sub
    TTStateKey = key
    TTStateSeq = TTStateSeq + 1
    On Error Resume Next
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set f = fso.CreateTextFile(TTDataPath("ThreatTide_state.js"), True)
    f.Write TTStateJs(mode, g)
    f.Close
    Err.Clear
    On Error GoTo 0
End Sub

' Data for leaderboard/index.html. A .js file (not .json) so the page can load
' it straight from disk with a <script> tag: no web server needed.
Function TTLeaderboardJs(gameJson)
    TTLeaderboardJs = "window.TT_LEADERBOARD = {""board"":" & TTHighScoresJson() & _
                      ",""last_game"":" & gameJson & "};" & vbCrLf
End Function

' Append the game and rewrite today's table. Never lets a disk error stop play.
Sub TTScoresWriteFiles(g, initials, rank)
    Dim fso, f, j
    On Error Resume Next
    j = TTGameJson(g, initials, rank)
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set f = fso.OpenTextFile(TTDataPath("ThreatTide_games.jsonl"), 8, True)
    f.WriteLine j
    f.Close
    Set f = fso.CreateTextFile(TTDataPath("ThreatTide_highscores.json"), True)
    f.Write TTHighScoresJson()
    f.Close
    Set f = fso.CreateTextFile(TTDataPath("ThreatTide_leaderboard.js"), True)
    f.Write TTLeaderboardJs(j)
    f.Close
    Err.Clear
    On Error GoTo 0
End Sub
