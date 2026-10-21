' Threat Tide - rules tests (spec: "Scoring model" and "Modes and rules")

Sub RunRulesTests()
    RunTest "Test_LitStageFullValue"
    RunTest "Test_UnlitStageQuarterNoAdvance"
    RunTest "Test_PathAward"
    RunTest "Test_ImpactWithoutChainIsUnlit"
    RunTest "Test_MultiplierCapAndDrainReset"
    RunTest "Test_ComboInsideWindow"
    RunTest "Test_ComboWindowEdge"
    RunTest "Test_ComboExpired"
    RunTest "Test_EdrCutsPathInProgress"
    RunTest "Test_EdrChangesPathAward"
    RunTest "Test_DwellBonus"
    RunTest "Test_DwellBonusCap"
    RunTest "Test_BallSaveAtStart"
    RunTest "Test_BallSaveKeepsPath"
    RunTest "Test_BallSaveStartsAtLaunch"
    RunTest "Test_ReconTwiceRelightsSave"
    RunTest "Test_ExtraBallOnSecondPath"
    RunTest "Test_GameOverAfterLastBall"
    RunTest "Test_DrainLosesPathKeepsBanked"
    RunTest "Test_TiltWarningsThenTilt"
    RunTest "Test_TiltDebounce"
    RunTest "Test_TiltNoSaveNoBonus"
    RunTest "Test_AssetsRaiseImpact"
    RunTest "Test_PatchTuesday"
    RunTest "Test_PatchTuesdayOff"
    RunTest "Test_PatchTuesdayNothingLit"
    RunTest "Test_PatchTuesdayRandomPick"
    RunTest "Test_CardDrawMatchesStage"
    RunTest "Test_WorstPathKeepsLargest"
    RunTest "Test_NotActiveIgnoresHits"
End Sub

Sub Test_LitStageFullValue()
    Dim g : Set g = NewGame()
    Hit g, ST_RECON, "T1595", 1000
    AssertEq g.Score, 90000, "0.9 x $100K"
    AssertTrue g.StageDone(ST_RECON), "Recon collected"
    AssertEq g.NextLitStage(), ST_INITIAL_ACCESS, "Initial Access lit next"
    AssertEq T_Count("collected"), 1, "collected event"
End Sub

Sub Test_UnlitStageQuarterNoAdvance()
    Dim g : Set g = NewGame()
    Hit g, ST_EXECUTION, "T1059", 1000
    AssertEq g.Score, 20000, "25% of 0.8 x $100K"
    AssertEq g.StageDone(ST_EXECUTION), False, "not collected"
    AssertEq g.NextLitStage(), ST_RECON, "still on Recon"
    AssertEq T_Count("card"), 1, "card shown for unlit hit too"
End Sub

Sub Test_PathAward()
    Dim g, ev : Set g = NewGame()
    PlayPath g, 1000
    AssertEq g.Score, 1230000, "stages $410K + Path $410K x 2"
    AssertEq g.PathsCompleted, 1, "one Path"
    AssertEq g.PathMult, 3, "multiplier rises to 3"
    AssertEq g.NextLitStage(), ST_RECON, "chain resets"
    ev = T_Last("path")
    AssertEq ev(1), 820000, "path event award"
    AssertEq ev(2), 2, "path event multiplier used"
    AssertEq g.WorstPathValue, 820000, "worst day recorded"
    AssertEq g.WorstPathCard(ST_RECON), CardIdx(ST_RECON, "T1595"), "worst path card Recon"
    AssertEq g.WorstPathCard(ST_IMPACT), CardIdx(ST_IMPACT, "T1486"), "worst path card Impact"
End Sub

Sub Test_ImpactWithoutChainIsUnlit()
    Dim g : Set g = NewGame()
    Hit g, ST_RECON, "T1595", 1000
    Hit g, ST_IMPACT, "T1486", 2000
    AssertEq g.Score, 90000 + 7500, "Impact unlit pays 25%"
    AssertEq g.PathsCompleted, 0, "no Path"
    AssertTrue g.StageDone(ST_RECON), "chain kept"
End Sub

Sub Test_MultiplierCapAndDrainReset()
    Dim g, i, r : Set g = NewGame()
    For i = 0 To 5
        PlayPath g, 20000 + i * 10000
        ' The 3rd Path starts Storm Surge (chain frozen); end it with the ramp
        If g.SurgeActive Then g.CentreRampHit 20000 + i * 10000 + 7000
    Next
    AssertEq g.PathMult, 6, "capped at 6"
    AssertEq g.PathsCompleted, 6, "six Paths"
    r = g.Drain(100000)
    AssertEq r, 0, "IR retainer re-armed by Recon x2 catches the first drain"
    r = g.Drain(100500)
    AssertEq r, 1, "extra ball, not game over"
    AssertEq g.BallNum, 1, "extra ball keeps ball number"
    AssertEq g.PathMult, 2, "multiplier resets on drain"
    AssertEq T_Last("ball")(2), True, "ball event flagged extra"
End Sub

Sub Test_ComboInsideWindow()
    Dim g : Set g = NewGame()
    Hit g, ST_RECON, "T1595", 1000
    Hit g, ST_LATERAL, "T1021", 2000      ' unlit: 12,500
    Hit g, ST_INITIAL_ACCESS, "T1566", 4000 ' lit, combo: 60,000 x 2
    AssertEq g.Score, 90000 + 12500 + 120000, "combo doubles the second shot"
    AssertEq T_Count("combo"), 1, "combo event"
    AssertEq g.StageValue(ST_INITIAL_ACCESS), 120000, "Path carries the combo value"
End Sub

Sub Test_ComboWindowEdge()
    Dim g : Set g = NewGame()
    Hit g, ST_LATERAL, "T1021", 2000
    Hit g, ST_INITIAL_ACCESS, "T1566", 5000
    AssertEq g.Score, 12500 + 30000, "exactly 3 s still counts (unlit IA 15K x 2)"
End Sub

Sub Test_ComboExpired()
    Dim g : Set g = NewGame()
    Hit g, ST_RECON, "T1595", 1000
    Hit g, ST_LATERAL, "T1021", 2000
    Hit g, ST_INITIAL_ACCESS, "T1566", 5001
    AssertEq g.Score, 90000 + 12500 + 60000, "no combo after 3 s"
    AssertEq T_Count("combo"), 0, "no combo event"
End Sub

Sub Test_EdrCutsPathInProgress()
    Dim g : Set g = NewGame()
    Hit g, ST_RECON, "T1595", 1000
    Hit g, ST_INITIAL_ACCESS, "T1566", 2000
    AssertEq g.PathValue(), 150000, "before EDR"
    g.EdrHit 2500
    AssertEq g.PathValue(), 135000, "10% cut"
    AssertEq g.Score, 150000, "banked score untouched"
    AssertEq T_Count("edr"), 1, "edr event"
End Sub

Sub Test_EdrChangesPathAward()
    Dim g : Set g = NewGame()
    Hit g, ST_RECON, "T1595", 1000
    g.EdrHit 1500
    Hit g, ST_INITIAL_ACCESS, "T1566", 2000
    Hit g, ST_EXECUTION, "T1059", 3000
    Hit g, ST_PERSISTENCE, "T1053", 4000
    Hit g, ST_PRIV_ESC, "T1068", 5000
    Hit g, ST_LATERAL, "T1021", 6000
    Hit g, ST_IMPACT, "T1486", 7000
    AssertEq T_Last("path")(1), (81000 + 60000 + 80000 + 60000 + 40000 + 50000 + 30000) * 2, "award uses cut Recon value"
End Sub

Sub Test_DwellBonus()
    Dim g : Set g = NewGame()
    Hit g, ST_RECON, "T1595", 20000
    g.Drain 30000
    AssertEq T_Last("bonus")(1), 50000, "10 s x $5K"
    AssertEq g.Score, 140000, "bonus added"
    AssertEq g.BallNum, 2, "next ball"
    AssertEq g.NextLitStage(), ST_RECON, "chain lost"
    AssertEq T_Count("evicted"), 1, "evicted by the SOC"
End Sub

Sub Test_DwellBonusCap()
    Dim g : Set g = NewGame()
    g.Drain 200000
    AssertEq T_Last("bonus")(1), 250000, "capped"
End Sub

Sub Test_BallSaveAtStart()
    Dim g, r : Set g = NewGame()
    r = g.Drain(5000)
    AssertEq r, 0, "saved inside 10 s"
    AssertEq g.BallNum, 1, "same ball"
    AssertEq T_Count("saved"), 1, "saved event"
    r = g.Drain(6000)
    AssertEq r, 1, "second drain ends the ball"
    AssertEq g.BallNum, 2, "ball 2"
End Sub

Sub Test_BallSaveKeepsPath()
    Dim g : Set g = NewGame()
    Hit g, ST_RECON, "T1595", 1000
    g.Drain 2000
    AssertTrue g.StageDone(ST_RECON), "saved ball keeps the chain"
End Sub

Sub Test_BallSaveStartsAtLaunch()
    Dim g, r
    Set g = New TTGame
    g.StartGame 0
    g.BallLaunched 30000
    r = g.Drain(39000)
    AssertEq r, 0, "save runs 10 s from launch, not from ball start"
End Sub

Sub Test_ReconTwiceRelightsSave()
    Dim g, r : Set g = NewGame()
    PlayPath g, 20000
    AssertEq g.BallSaveArmed, False, "one Recon is not enough"
    Hit g, ST_RECON, "T1595", 30000
    AssertEq g.BallSaveArmed, True, "second Recon arms IR retainer"
    AssertEq T_Count("ballsave_relit"), 1, "relit event"
    r = g.Drain(60000)
    AssertEq r, 0, "armed save catches the drain"
    AssertEq g.BallSaveArmed, False, "save used"
    r = g.Drain(61000)
    AssertEq r, 1, "next drain ends the ball"
End Sub

Sub Test_ExtraBallOnSecondPath()
    Dim g : Set g = NewGame()
    PlayPath g, 20000
    AssertEq g.ExtraBalls, 0, "none after first Path"
    PlayPath g, 30000
    AssertEq g.ExtraBalls, 1, "extra ball on second Path"
    PlayPath g, 40000
    AssertEq g.ExtraBalls, 1, "only one per game"
    AssertEq T_Count("extraball"), 1, "one event"
End Sub

Sub Test_GameOverAfterLastBall()
    Dim g, r : Set g = NewGame()
    r = g.Drain(20000)
    AssertEq r, 1, "ball 1 ends"
    r = g.Drain(30000)
    AssertEq r, 1, "ball 2 ends (never launched, no save)"
    r = g.Drain(40000)
    AssertEq r, 2, "ball 3 ends the game"
    AssertEq g.IsActive, False, "game over"
    AssertEq T_Count("gameover"), 1, "gameover event"
End Sub

Sub Test_DrainLosesPathKeepsBanked()
    Dim g, before : Set g = NewGame()
    Hit g, ST_RECON, "T1595", 20000
    Hit g, ST_INITIAL_ACCESS, "T1566", 21000
    before = g.Score
    g.Drain 21000
    AssertEq g.Score, before, "dollars already scored stay (0 s dwell)"
    AssertEq g.PathValue(), 0, "Path in progress lost"
    AssertEq g.NextLitStage(), ST_RECON, "chain starts again"
End Sub

Sub Test_TiltWarningsThenTilt()
    Dim g : Set g = NewGame()
    g.TiltBob 1000
    g.TiltBob 3000
    AssertEq g.Tilted, False, "two warnings"
    AssertEq T_Count("tilt_warning"), 2, "warning events"
    g.TiltBob 5000
    AssertEq g.Tilted, True, "third hit tilts"
    Hit g, ST_RECON, "T1595", 6000
    AssertEq g.Score, 0, "no scoring while tilted"
End Sub

Sub Test_TiltDebounce()
    Dim g : Set g = NewGame()
    g.TiltBob 1000
    g.TiltBob 1500
    AssertEq g.TiltWarnings, 1, "bounce inside 1 s ignored"
End Sub

Sub Test_TiltNoSaveNoBonus()
    Dim g, r : Set g = NewGame()
    g.TiltBob 1000
    g.TiltBob 2500
    g.TiltBob 4000
    r = g.Drain(6000)
    AssertEq r, 1, "IR retainer does not cover a tilt"
    AssertEq T_Last("bonus")(1), 0, "bonus lost"
    AssertEq g.Tilted, False, "tilt clears for the next ball"
End Sub

Sub Test_AssetsRaiseImpact()
    Dim g : Set g = NewGame()
    g.AssetDropped 1000
    g.AssetDropped 2000
    AssertEq g.Impact, 200000, "+$50K per asset"
    AssertEq g.AssetsDropped, 2, "count for the report"
    Hit g, ST_RECON, "T1595", 3000
    AssertEq g.Score, 180000, "0.9 x $200K"
End Sub

Sub Test_PatchTuesday()
    Dim g : Set g = NewGame()
    Hit g, ST_RECON, "T1595", 1000
    Hit g, ST_INITIAL_ACCESS, "T1566", 2000
    Hit g, ST_EXECUTION, "T1059", 3000
    g.PatchOverride = ST_INITIAL_ACCESS
    g.Tick 89999
    AssertEq T_Count("patch"), 0, "not yet"
    g.Tick 90000
    AssertEq T_Count("patch"), 1, "patched at 90 s"
    AssertEq g.StageDone(ST_INITIAL_ACCESS), False, "Initial Access dropped back"
    AssertEq g.NextLitStage(), ST_INITIAL_ACCESS, "the hole is lit next"
    AssertEq g.PathValue(), 90000 + 80000, "its value leaves the Path"
    g.Tick 90001
    AssertEq T_Count("patch"), 1, "next one in another 90 s"
End Sub

Sub Test_PatchTuesdayOff()
    Dim g : Set g = NewGame()
    g.PatchTuesdayOn = False
    Hit g, ST_RECON, "T1595", 1000
    g.Tick 100000
    AssertEq T_Count("patch"), 0, "operator setting off"
End Sub

Sub Test_PatchTuesdayNothingLit()
    Dim g : Set g = NewGame()
    g.Tick 100000
    AssertEq T_Count("patch"), 0, "nothing to patch"
End Sub

Sub Test_PatchTuesdayRandomPick()
    Dim g, i, cleared : Set g = NewGame()
    Hit g, ST_RECON, "T1595", 1000
    Hit g, ST_INITIAL_ACCESS, "T1566", 2000
    Hit g, ST_EXECUTION, "T1059", 3000
    g.Tick 90000
    cleared = 0
    For i = 0 To 2
        If Not g.StageDone(i) Then cleared = cleared + 1
    Next
    AssertEq cleared, 1, "exactly one collected stage dropped"
End Sub

Sub Test_CardDrawMatchesStage()
    Dim g, i, ev, ok : Set g = NewGame()
    ok = True
    For i = 1 To 50
        g.StageHit ST_INITIAL_ACCESS, 1000 + i
        ev = T_Last("card")
        If TTCardStage(ev(1)) <> ST_INITIAL_ACCESS Then ok = False
    Next
    AssertTrue ok, "random draws stay in the stage's deck"
End Sub

Sub Test_WorstPathKeepsLargest()
    Dim g : Set g = NewGame()
    PlayPath g, 20000                 ' 410K x 2 = 820K
    g.AssetDropped 26500
    g.Drain 27000                     ' multiplier back to 2, ball 2
    g.BallLaunched 28000
    Hit g, ST_RECON, "T1598", 29000   ' different Recon card, Impact now $150K
    Hit g, ST_INITIAL_ACCESS, "T1566", 30000
    Hit g, ST_EXECUTION, "T1059", 31000
    Hit g, ST_PERSISTENCE, "T1053", 32000
    Hit g, ST_PRIV_ESC, "T1068", 33000
    Hit g, ST_LATERAL, "T1021", 34000
    Hit g, ST_IMPACT, "T1486", 35000
    AssertTrue g.WorstPathValue > 820000, "bigger Path replaces worst day"
    AssertEq g.WorstPathCard(ST_RECON), CardIdx(ST_RECON, "T1598"), "cards follow the worst Path"
End Sub

Sub Test_NotActiveIgnoresHits()
    Dim g
    Set g = New TTGame
    g.StageHit ST_RECON, 1000
    g.EdrHit 1000
    g.AssetDropped 1000
    AssertEq g.Score, 0, "no game, no score"
    AssertEq T_Count("card"), 0, "no events"
End Sub
