' Threat Tide - high-score table and JSON output tests

Sub RunScoresTests()
    RunTest "Test_HighScoreOrderAndTies"
    RunTest "Test_HighScoreTableFull"
    RunTest "Test_ContestModeDailyReset"
    RunTest "Test_HighScoreLine"
    RunTest "Test_GameJson"
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
