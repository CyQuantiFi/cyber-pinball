' Threat Tide - Phase 2 (Expert Consensus, Air Gap) and Phase 3 (Storm Surge) tests

Sub RunModesTests()
    RunTest "Test_AssetBankLightsLock"
    RunTest "Test_ImpactWithoutLockDoesNotLock"
    RunTest "Test_ThreeLocksStartMultiball"
    RunTest "Test_NoLockDuringMultiball"
    RunTest "Test_AgreementPaysJackpot"
    RunTest "Test_SameBallIsNotAgreement"
    RunTest "Test_AgreementWindow"
    RunTest "Test_ScatteredHitDecaysJackpot"
    RunTest "Test_JackpotDecayFloor"
    RunTest "Test_AirGapPaysTripleJackpot"
    RunTest "Test_AirGapClosedOutsideMultiball"
    RunTest "Test_MultiballBallSave"
    RunTest "Test_MultiballEndsAtOneBall"
    RunTest "Test_SurgeStartsOnThirdPath"
    RunTest "Test_SurgeScoringSwingAndTail"
    RunTest "Test_SurgeTimesOut"
    RunTest "Test_SurgeOncePerGame"
    RunTest "Test_CentreRampOutsideSurge"
    RunTest "Test_DrainEndsSurge"
    RunTest "Test_GameJsonModes"
End Sub

' Drop 9 assets (3 banks = 3 locks lit) and lock 3 balls at Impact from t.
Sub StartMultiballAt(g, t)
    Dim i
    For i = 1 To 9
        g.AssetDropped t
    Next
    For i = 1 To 3
        Hit g, ST_IMPACT, "T1486", t + i * 100
    Next
End Sub

Sub Test_AssetBankLightsLock()
    Dim g : Set g = NewGame()
    g.AssetDropped 1000
    g.AssetDropped 1100
    AssertEq g.LocksLit, 0, "two drops: no lock"
    g.AssetDropped 1200
    AssertEq g.LocksLit, 1, "full bank lights a lock"
    AssertEq T_Count("lock_lit"), 1, "lock_lit event"
End Sub

Sub Test_ImpactWithoutLockDoesNotLock()
    Dim g : Set g = NewGame()
    Hit g, ST_IMPACT, "T1486", 1000
    AssertEq g.BallsLocked, 0, "no lock lit, no lock"
    AssertEq T_Count("lock"), 0, "no lock event"
End Sub

Sub Test_ThreeLocksStartMultiball()
    Dim g : Set g = NewGame()
    StartMultiballAt g, 20000
    AssertEq T_Count("lock"), 2, "first two locks hold the ball"
    AssertEq T_Count("multiball"), 1, "third lock starts multiball"
    AssertEq T_Last("multiball")(1), 2, "two balls added to the one in play"
    AssertEq g.MultiballActive, True, "multiball running"
    AssertEq g.BallsInPlay, 3, "three experts"
    AssertEq g.AirGapOpen, True, "Air Gap gate opens"
    AssertEq g.Jackpot, TT_CONSENSUS_JACKPOT_START, "jackpot starts fresh"
    AssertEq g.BallsLocked, 0, "locks released"
End Sub

Sub Test_NoLockDuringMultiball()
    Dim g : Set g = NewGame()
    StartMultiballAt g, 20000
    g.AssetDropped 21000
    g.AssetDropped 21000
    g.AssetDropped 21000
    AssertEq g.LocksLit, 0, "banks don't light locks during multiball"
End Sub

Sub Test_AgreementPaysJackpot()
    Dim g, before : Set g = NewGame()
    StartMultiballAt g, 20000
    g.HitBallId = 1
    Hit g, ST_EXECUTION, "T1059", 21000
    before = g.Score
    g.HitBallId = 2
    Hit g, ST_EXECUTION, "T1059", 23000
    AssertEq T_Count("agreement"), 1, "two experts on the same stage inside 4 s"
    AssertEq T_Last("agreement")(1), 500000, "pays the current jackpot"
    AssertEq g.Jackpot, 750000, "jackpot +$250K"
    AssertEq g.AgreementCount, 1, "counted for the report"
    AssertTrue g.Score >= before + 500000, "jackpot added to the score"
End Sub

Sub Test_SameBallIsNotAgreement()
    Dim g : Set g = NewGame()
    StartMultiballAt g, 20000
    g.HitBallId = 1
    Hit g, ST_EXECUTION, "T1059", 21000
    Hit g, ST_EXECUTION, "T1059", 22000
    AssertEq T_Count("agreement"), 0, "one expert agreeing with itself"
End Sub

Sub Test_AgreementWindow()
    Dim g : Set g = NewGame()
    StartMultiballAt g, 20000
    g.HitBallId = 1
    Hit g, ST_EXECUTION, "T1059", 21000
    g.HitBallId = 2
    Hit g, ST_EXECUTION, "T1059", 25001
    AssertEq T_Count("agreement"), 0, "outside 4 s"
End Sub

Sub Test_ScatteredHitDecaysJackpot()
    Dim g : Set g = NewGame()
    StartMultiballAt g, 20000
    g.HitBallId = 1
    Hit g, ST_EXECUTION, "T1059", 21000
    AssertEq g.Jackpot, 500000, "first hit doesn't decay"
    g.HitBallId = 2
    Hit g, ST_PERSISTENCE, "T1053", 22000
    AssertEq g.Jackpot, 475000, "different stage: -5%"
End Sub

Sub Test_JackpotDecayFloor()
    Dim g, i : Set g = NewGame()
    StartMultiballAt g, 20000
    For i = 1 To 60
        g.HitBallId = i Mod 3
        Hit g, (i Mod 2) * 2, "", 21000 + i
    Next
    AssertEq g.Jackpot, TT_CONSENSUS_JACKPOT_MIN, "never below the floor"
End Sub

Sub Test_AirGapPaysTripleJackpot()
    Dim g, before : Set g = NewGame()
    StartMultiballAt g, 20000
    before = g.Score
    g.AirGapHit 21000
    AssertEq T_Last("airgap")(1), 1500000, "jackpot x3"
    AssertEq g.Score, before + 1500000, "added to the score"
    AssertEq g.AirGapBreached, True, "for the board report"
    AssertEq g.AirGapOpen, False, "one collect per multiball"
    g.AirGapHit 22000
    AssertEq T_Count("airgap"), 1, "second hit pays nothing"
End Sub

Sub Test_AirGapClosedOutsideMultiball()
    Dim g : Set g = NewGame()
    g.AirGapHit 1000
    AssertEq T_Count("airgap"), 0, "gate closed"
    AssertEq g.Score, 0, "no award"
End Sub

Sub Test_MultiballBallSave()
    Dim g, r : Set g = NewGame()
    StartMultiballAt g, 20000
    r = g.Drain(25000)
    AssertEq r, 0, "IR retainer at multiball start"
    AssertEq g.BallsInPlay, 3, "still three experts"
End Sub

Sub Test_MultiballEndsAtOneBall()
    Dim g, r : Set g = NewGame()
    StartMultiballAt g, 20000
    r = g.Drain(40000)
    AssertEq r, 3, "a ball lost, others in play"
    AssertEq g.BallsInPlay, 2, "two left"
    AssertEq g.MultiballActive, True, "still multiball"
    r = g.Drain(41000)
    AssertEq g.BallsInPlay, 1, "one left"
    AssertEq g.MultiballActive, False, "multiball ends at one ball"
    AssertEq g.AirGapOpen, False, "gate closes"
    AssertEq T_Count("multiball_end"), 1, "end event"
    AssertEq g.BallNum, 1, "same ball continues"
    r = g.Drain(42000)
    AssertEq r, 1, "last ball drains normally"
    AssertEq g.BallNum, 2, "next ball"
End Sub

Sub Test_SurgeStartsOnThirdPath()
    Dim g : Set g = NewGame()
    PlayPath g, 20000
    PlayPath g, 30000
    AssertEq g.SurgeActive, False, "not after two"
    g.SurgeOverride = 4
    PlayPath g, 40000
    AssertEq g.SurgeActive, True, "Storm Surge on the third Path"
    AssertEq T_Last("surge_start")(1), 4, "first weather multiplier"
    AssertEq g.SurgeSecondsLeft(46000), 45, "45 s timer"
End Sub

Sub Test_SurgeScoringSwingAndTail()
    Dim g, before : Set g = NewGame()
    PlayPath g, 20000
    PlayPath g, 30000
    g.SurgeOverride = 4
    PlayPath g, 40000                         ' surge starts at 46,000
    before = g.Score
    Hit g, ST_EXECUTION, "T1059", 47000       ' 0.8 x 100K x 4
    AssertEq g.Score - before, 320000, "every shot lit, x weather"
    AssertEq g.StageDone(ST_EXECUTION), False, "chain frozen during the storm"
    g.SurgeOverride = 9
    g.Tick 51000
    AssertEq g.SurgeMult, 9, "weather swings every 5 s"
    AssertEq g.SurgePeak, 9, "peak tracked"
    Hit g, ST_PERSISTENCE, "T1053", 52000     ' 0.6 x 100K x 9
    AssertEq g.SurgeSum, 860000, "sum of the mode"
    g.CentreRampHit 53000
    AssertEq T_Last("surge_tail")(1), 7740000, "tail jackpot = sum x peak"
    AssertEq g.SurgeActive, False, "final shot ends the mode"
    AssertEq T_Last("surge_end")(1), True, "collected"
End Sub

Sub Test_SurgeTimesOut()
    Dim g : Set g = NewGame()
    PlayPath g, 20000
    PlayPath g, 30000
    PlayPath g, 40000
    g.Tick 90999
    AssertEq g.SurgeActive, True, "still running at 44.9 s"
    g.Tick 91000
    AssertEq g.SurgeActive, False, "ends at 45 s"
    AssertEq T_Last("surge_end")(1), False, "tail missed"
    g.CentreRampHit 92000
    AssertEq T_Count("surge_tail"), 0, "too late"
End Sub

Sub Test_SurgeOncePerGame()
    Dim g : Set g = NewGame()
    PlayPath g, 20000
    PlayPath g, 30000
    PlayPath g, 40000
    g.Tick 91000
    PlayPath g, 100000
    AssertEq T_Count("surge_start"), 1, "once per game"
End Sub

Sub Test_CentreRampOutsideSurge()
    Dim g : Set g = NewGame()
    g.CentreRampHit 1000
    AssertEq g.Score, 0, "nothing outside Storm Surge"
End Sub

Sub Test_DrainEndsSurge()
    Dim g : Set g = NewGame()
    PlayPath g, 20000
    PlayPath g, 30000
    PlayPath g, 40000
    g.Drain 50000      ' Recon x2 armed a save: this one is caught
    g.Drain 50500
    AssertEq g.SurgeActive, False, "storm ends with the ball"
    AssertEq T_Count("surge_end"), 1, "end event"
End Sub

Sub Test_GameJsonModes()
    Dim g, j : Set g = NewGame()
    StartMultiballAt g, 20000
    g.AirGapHit 21000
    j = TTGameJson(g, "ABC", 1)
    AssertTrue InStr(j, """multiballs"":1,") > 0, "multiballs"
    AssertTrue InStr(j, """storm_surge"":false,") > 0, "storm surge flag"
    AssertTrue InStr(j, """air_gap"":true}") > 0, "air gap"
End Sub
