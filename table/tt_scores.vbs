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
    Dim n : n = Now
    TTIsoNow = Year(n) & "-" & TTPad2(Month(n)) & "-" & TTPad2(Day(n)) & "T" & _
               TTPad2(Hour(n)) & ":" & TTPad2(Minute(n)) & ":" & TTPad2(Second(n))
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

' One game as a JSON object (single line).
Function TTGameJson(g, initials, rank)
    Dim i, c, path, j
    path = ""
    If g.WorstPathValue > 0 Then
        For i = 0 To TT_STAGE_COUNT - 1
            c = g.WorstPathCard(i)
            If i > 0 Then path = path & ","
            path = path & "{""stage"":" & TTJsonStr(TT_StageNames(i)) & _
                          ",""id"":" & TTJsonStr(TTCardId(c)) & _
                          ",""technique"":" & TTJsonStr(TTCardName(c)) & "}"
        Next
    End If
    j = "{""ts"":" & TTJsonStr(TTIsoNow()) & _
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
    TTGameJson = j
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
