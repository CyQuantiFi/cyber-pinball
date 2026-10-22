' Threat Tide - high-score table and JSON output tests

Sub RunScoresTests()
    RunTest "Test_HighScoreOrderAndTies"
    RunTest "Test_HighScoreTableFull"
    RunTest "Test_ContestModeDailyReset"
    RunTest "Test_HighScoreLine"
    RunTest "Test_GameJson"
    RunTest "Test_GameJsonExportFields"
    RunTest "Test_GameJsonNoPath"
    RunTest "Test_GameSeqCounts"
    RunTest "Test_OffsetText"
    RunTest "Test_UtcOffsetSetting"
    RunTest "Test_JsonFrac"
    RunTest "Test_JsonEscaping"
    RunTest "Test_BackglassStateJs"
End Sub

Sub T_FreshTable()
    TTScoresClear
    TTHS_Day = TTToday()
End Sub

Sub Test_HighScoreOrderAndTies()
    T_FreshTable
    AssertEq TTScoresAdd("AAA", 100), 1, "first entry"
    AssertEq TTScoresAdd("BBB", 300), 1, "new leader"
    AssertEq TTScoresAdd("CCC", 200), 2, "middle"
    AssertEq TTScoresAdd("DDD", 200), 3, "tie goes to the earlier entry"
    AssertEq TTHS_Names(0) & TTHS_Names(1) & TTHS_Names(2) & TTHS_Names(3), "BBBCCCDDDAAA", "order"
End Sub

Sub Test_HighScoreTableFull()
    Dim i
    T_FreshTable
    For i = 1 To 10
        TTScoresAdd "P" & i, i * 1000
    Next
    AssertEq TTScoresAdd("LOW", 500), 0, "below tenth place is not placed"
    AssertEq TTScoresAdd("TOP", 50000), 1, "top still placed"
    AssertEq TTHS_Names(9), "P2", "lowest drops off"
End Sub

Sub Test_ContestModeDailyReset()
    T_FreshTable
    TTScoresAdd "OLD", 999
    TTHS_Day = "19990101"
    TT_ContestMode = True
    TTScoresCheckDay
    AssertEq TTHS_Scores(0), 0, "yesterday's table cleared"
    AssertEq TTHS_Day, TTToday(), "day moves on"

    TTScoresAdd "OLD", 999
    TTHS_Day = "19990101"
    TT_ContestMode = False
    TTScoresCheckDay
    AssertEq TTHS_Scores(0), 999, "contest mode off keeps the table"
    TT_ContestMode = True
End Sub

Sub Test_HighScoreLine()
    T_FreshTable
    TTScoresAdd "BBB", 300
    AssertEq TTHighScoreLine(1), "1. BBB  $300", "filled line"
    AssertEq TTHighScoreLine(2), "2. ---", "empty line"
End Sub

Sub Test_GameJson()
    Dim g, j : Set g = NewGame()
    PlayPath g, 20000
    j = TTGameJson(g, "ABC", 1)
    AssertTrue InStr(j, """initials"":""ABC""") > 0, "initials"
    AssertTrue InStr(j, """score"":1230000,") > 0, "score as plain number"
    AssertTrue InStr(j, """score_text"":""$1,230,000""") > 0, "score as text"
    AssertTrue InStr(j, """worst_path"":820000,") > 0, "worst path"
    AssertTrue InStr(j, """id"":""T1595""") > 0, "first technique"
    AssertTrue InStr(j, """technique"":""Data Encrypted for Impact""") > 0, "last technique"
    AssertTrue InStr(j, """air_gap"":false}") > 0, "air gap flag closes the object"
End Sub

Sub Test_GameJsonExportFields()
    Dim g, j, n
    Set g = NewGame()
    PlayPath g, 20000
    n = DateSerial(2026, 10, 22) + TimeSerial(14, 3, 11)
    TT_CabinetId = "TT-07"
    TT_EventId = "aisa-melb-2026"
    TT_EventName = "AISA Melbourne"
    j = TTGameJsonAt(g, "ABC", 1, n, 42, 660)
    AssertTrue Left(j, 20) = "{""schema_version"":1,", "schema version leads"
    AssertTrue InStr(j, """game_id"":""TT-07-20261022T140311-42""") > 0, "game id"
    AssertTrue InStr(j, """cabinet_id"":""TT-07""") > 0, "cabinet"
    AssertTrue InStr(j, """event_id"":""aisa-melb-2026"",""event_name"":""AISA Melbourne""") > 0, "event"
    AssertTrue InStr(j, """ts"":""2026-10-22T14:03:11+11:00""") > 0, "time with offset"
    AssertTrue InStr(j, """id"":""T1595"",""technique"":""Active Scanning"",""probability"":0.900}") > 0, "probability"
    AssertTrue InStr(j, """probability"":0.300}") > 0, "last stage probability"
    AssertTrue InStr(j, """air_gap"":false}") > 0, "still closes the object"

    TT_EventName = ""
    j = TTGameJsonAt(g, "ABC", 1, n, 1, Empty)
    AssertEq InStr(j, "event_name"), 0, "no event name when unset"
    AssertTrue InStr(j, """ts"":""2026-10-22T14:03:11""") > 0, "unknown offset leaves the time bare"
    TT_CabinetId = "TT-01"
    TT_EventId = "booth"
End Sub

Sub Test_GameJsonNoPath()
    Dim g, j : Set g = NewGame()
    j = TTGameJsonAt(g, "ZZZ", 0, Now, 1, 0)
    AssertTrue InStr(j, """worst_path"":0,") > 0, "no path value"
    AssertTrue InStr(j, """worst_path_techniques"":[]") > 0, "no techniques"
End Sub

Sub Test_GameSeqCounts()
    Dim a, b
    a = TTNextGameSeq()
    b = TTNextGameSeq()
    AssertEq b, a + 1, "each game gets the next number"
End Sub

Sub Test_OffsetText()
    AssertEq TTOffsetText(660), "+11:00", "east"
    AssertEq TTOffsetText(-210), "-03:30", "west, half hour"
    AssertEq TTOffsetText(0), "+00:00", "UTC"
    AssertEq TTOffsetText(Empty), "", "unknown"
End Sub

Sub Test_UtcOffsetSetting()
    TT_UtcOffsetMin = 600
    AssertEq TTUtcOffsetMin(), 600, "setting wins"
    TT_UtcOffsetMin = "abc"
    AssertTrue IsEmpty(TTUtcOffsetMin()), "a bad setting is unknown, not a guess"
    TT_UtcOffsetMin = ""
    AssertTrue Not IsEmpty(TTUtcOffsetMin()), "read from Windows"
End Sub

Sub Test_JsonFrac()
    AssertEq TTJsonFrac(0.35), "0.350", "two places"
    AssertEq TTJsonFrac(1), "1.000", "one"
    AssertEq TTJsonFrac(0), "0.000", "zero"
    AssertEq TTJsonFrac(0.0004), "0.000", "rounds down"
    AssertEq TTJsonFrac(0.0006), "0.001", "rounds up"
End Sub

Sub Test_JsonEscaping()
    AssertEq TTJsonStr("a""b\c"), """a\""b\\c""", "quotes and backslashes"
End Sub

Sub Test_BackglassStateJs()
    Dim g, j : Set g = NewGame()
    PlayPath g, 20000
    j = TTStateJs("game", g)
    AssertTrue Left(j, 18) = "window.TT_STATE = ", "assigns the page's global"
    AssertTrue InStr(j, """mode"":""game""") > 0, "mode"
    AssertTrue InStr(j, """score"":1230000,") > 0, "score as plain number"
    AssertTrue InStr(j, """score_text"":""$1,230,000""") > 0, "score as display text"
    AssertTrue InStr(j, """ball"":1,""balls"":3}") > 0, "ball and balls per game"
End Sub
