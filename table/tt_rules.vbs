' =============================================================================
' Threat Tide - game rules
'
' Pure rules: no VPX objects, so this file runs under Windows cscript for tests.
' Time is passed in as milliseconds (VPX GameTime). The rules report what
' happened by calling a global Sub TTEmit(kind, a, b), which tt_table.vbs
' (on the cabinet) or tests/test_lib.vbs (in CI) defines.
'
' Events emitted (kind, a, b):
'   "ball"           ball number, extra-ball flag   new ball ready to release
'   "card"           card index, dollars             any stage shot scored
'   "collected"      stage, dollars                  lit stage collected (not Impact)
'   "combo"          dollars, -                       LM -> IA combo paid
'   "path"           award, multiplier used           Attack Path complete
'   "extraball"      -, -
'   "edr"            Path value after cut, -
'   "asset"          assets dropped, new Impact
'   "patch"          stage un-lit, -                   Patch Tuesday
'   "ballsave_relit" -, -
'   "saved"          -, -                              drain saved by IR retainer
'   "bonus"          dollars, seconds                  dwell bonus at drain
'   "evicted"        -, -                              ball ended
'   "tilt_warning"   warning number, -
'   "tilt"           -, -
'   "gameover"       final score, -
' =============================================================================

Class TTGame
    ' ---- Public state (read by display and report) ----
    Public IsActive          ' game running
    Public Score             ' Double, dollars
    Public BallNum
    Public BallsPerGame
    Public ExtraBalls        ' pending extra balls
    Public ExtraBallAwarded
    Public Impact            ' Double, current Impact value
    Public AssetsDropped
    Public AirGapBreached    ' Phase 2
    Public PathMult
    Public PathsCompleted
    Public WorstPathValue
    Public Tilted
    Public TiltWarnings
    Public Launched          ' ball has left the plunger lane
    Public BallSaveUntilMs
    Public BallSaveArmed     ' relit IR retainer, used on next drain
    Public PatchTuesdayOn

    ' ---- Test hooks: force the next random pick (-1 = random) ----
    Public CardOverride
    Public PatchOverride

    ' ---- Private state ----
    Private m_done()
    Private m_value()
    Private m_card()
    Private m_worstCards()
    Private m_lastStageMs
    Private m_lastLateralMs
    Private m_lastTiltMs
    Private m_reconCount
    Private m_resaveGiven
    Private m_nextPatchMs

    Private Sub Class_Initialize()
        ReDim m_done(TT_STAGE_COUNT - 1)
        ReDim m_value(TT_STAGE_COUNT - 1)
        ReDim m_card(TT_STAGE_COUNT - 1)
        ReDim m_worstCards(TT_STAGE_COUNT - 1)
        IsActive = False
        Score = 0
        BallNum = 0
        ExtraBalls = 0
        ExtraBallAwarded = False
        Impact = CDbl(TT_IMPACT_START)
        AssetsDropped = 0
        AirGapBreached = False
        PathMult = TT_PATH_MULT_START
        PathsCompleted = 0
        Tilted = False
        TiltWarnings = 0
        Launched = False
        BallSaveUntilMs = 0
        BallSaveArmed = False
        m_lastStageMs = 0
        m_lastLateralMs = -1
        m_lastTiltMs = -100000
        m_reconCount = 0
        m_resaveGiven = False
        m_nextPatchMs = 0
        CardOverride = -1
        PatchOverride = -1
        BallsPerGame = TT_BallsPerGame
        PatchTuesdayOn = TT_PatchTuesdayOn
        ResetChain
        ClearWorst
    End Sub

    ' ======================== Game / ball flow ========================

    Public Sub StartGame(nowMs)
        IsActive = True
        Score = 0
        BallNum = 1
        BallsPerGame = TT_BallsPerGame
        PatchTuesdayOn = TT_PatchTuesdayOn
        ExtraBalls = 0
        ExtraBallAwarded = False
        Impact = CDbl(TT_IMPACT_START)
        AssetsDropped = 0
        AirGapBreached = False
        PathsCompleted = 0
        ClearWorst
        StartBall nowMs, False
    End Sub

    Private Sub StartBall(nowMs, isExtra)
        ResetChain
        PathMult = TT_PATH_MULT_START
        Tilted = False
        TiltWarnings = 0
        m_lastTiltMs = -100000
        Launched = False
        BallSaveUntilMs = 0
        BallSaveArmed = False
        m_reconCount = 0
        m_resaveGiven = False
        m_lastStageMs = nowMs
        m_lastLateralMs = -1
        m_nextPatchMs = nowMs + TT_PATCH_TUESDAY_MS
        TTEmit "ball", BallNum, isExtra
    End Sub

    ' Ball has left the plunger lane. Starts the IR retainer and the clocks once per ball.
    Public Sub BallLaunched(nowMs)
        If Not IsActive Or Launched Then Exit Sub
        Launched = True
        BallSaveUntilMs = nowMs + TT_BALLSAVE_MS
        m_lastStageMs = nowMs
        m_nextPatchMs = nowMs + TT_PATCH_TUESDAY_MS
    End Sub

    Public Function BallSaveActive(nowMs)
        BallSaveActive = (Launched And nowMs < BallSaveUntilMs) Or BallSaveArmed
    End Function

    ' Returns 0 = saved, 1 = next ball (or extra ball), 2 = game over.
    Public Function Drain(nowMs)
        Dim secs, bonus
        Drain = 2
        If Not IsActive Then Exit Function

        If Not Tilted Then
            If Launched And nowMs < BallSaveUntilMs Then
                BallSaveUntilMs = 0
                TTEmit "saved", 0, 0
                Drain = 0
                Exit Function
            ElseIf BallSaveArmed Then
                BallSaveArmed = False
                TTEmit "saved", 0, 0
                Drain = 0
                Exit Function
            End If
        End If

        ' Dwell time bonus (lost on tilt)
        If Tilted Then
            bonus = 0
            secs = 0
        Else
            secs = Int((nowMs - m_lastStageMs) / 1000)
            If secs < 0 Then secs = 0
            bonus = CDbl(secs) * TT_DWELL_PER_SEC
            If bonus > TT_DWELL_CAP Then bonus = CDbl(TT_DWELL_CAP)
        End If
        Score = Score + bonus
        TTEmit "bonus", bonus, secs
        TTEmit "evicted", 0, 0

        ' The Path in progress is lost; banked Paths stay in the score.
        ResetChain

        If ExtraBalls > 0 Then
            ExtraBalls = ExtraBalls - 1
            StartBall nowMs, True
            Drain = 1
        ElseIf BallNum < BallsPerGame Then
            BallNum = BallNum + 1
            StartBall nowMs, False
            Drain = 1
        Else
            IsActive = False
            TTEmit "gameover", Score, 0
            Drain = 2
        End If
    End Function

    ' Call every frame. Runs Patch Tuesday.
    Public Sub Tick(nowMs)
        If Not IsActive Or Not Launched Or Tilted Then Exit Sub
        If Not PatchTuesdayOn Then Exit Sub
        If nowMs < m_nextPatchMs Then Exit Sub
        m_nextPatchMs = nowMs + TT_PATCH_TUESDAY_MS
        PatchOne
    End Sub

    ' ======================== Shots ========================

    Public Sub StageHit(stage, nowMs)
        Dim c, value, isLit
        If Not IsActive Or Tilted Then Exit Sub
        If stage < 0 Or stage >= TT_STAGE_COUNT Then Exit Sub

        c = DrawCard(stage)
        isLit = (stage = NextLitStage())
        value = TT_Cards(c)(3) * Impact
        If Not isLit Then value = value * TT_UNLIT_SHARE

        If stage = ST_INITIAL_ACCESS And m_lastLateralMs >= 0 Then
            If nowMs - m_lastLateralMs <= TT_COMBO_WINDOW_MS Then
                value = value * TT_COMBO_MULT
                TTEmit "combo", TTRound(value), 0
            End If
            m_lastLateralMs = -1
        End If
        If stage = ST_LATERAL Then m_lastLateralMs = nowMs

        value = TTRound(value)
        Score = Score + value
        m_lastStageMs = nowMs
        TTEmit "card", c, value

        If isLit Then
            m_done(stage) = True
            m_value(stage) = value
            m_card(stage) = c
            If stage = ST_IMPACT Then
                CompletePath
            Else
                TTEmit "collected", stage, value
                If stage = ST_RECON Then ReconCollected
            End If
        End If
    End Sub

    ' Slingshot: "Detected: EDR"
    Public Sub EdrHit(nowMs)
        Dim i
        If Not IsActive Or Tilted Then Exit Sub
        For i = 0 To TT_STAGE_COUNT - 1
            If m_done(i) Then m_value(i) = m_value(i) * (1 - TT_EDR_CUT)
        Next
        TTEmit "edr", PathValue(), 0
    End Sub

    ' Asset drop target
    Public Sub AssetDropped(nowMs)
        If Not IsActive Or Tilted Then Exit Sub
        AssetsDropped = AssetsDropped + 1
        Impact = Impact + TT_IMPACT_STEP
        TTEmit "asset", AssetsDropped, Impact
    End Sub

    ' Tilt bob / plumb hit
    Public Sub TiltBob(nowMs)
        If Not IsActive Or Tilted Then Exit Sub
        If nowMs - m_lastTiltMs < TT_TILT_DEBOUNCE_MS Then Exit Sub
        m_lastTiltMs = nowMs
        TiltWarnings = TiltWarnings + 1
        If TiltWarnings > TT_TILT_WARNINGS Then
            Tilted = True
            TTEmit "tilt", 0, 0
        Else
            TTEmit "tilt_warning", TiltWarnings, 0
        End If
    End Sub

    ' ======================== Queries ========================

    ' Lowest stage not yet collected. In-order means "this one next".
    Public Function NextLitStage()
        Dim i
        For i = 0 To TT_STAGE_COUNT - 1
            If Not m_done(i) Then
                NextLitStage = i
                Exit Function
            End If
        Next
        NextLitStage = TT_STAGE_COUNT
    End Function

    Public Function StageDone(i)
        StageDone = m_done(i)
    End Function

    Public Function StageValue(i)
        StageValue = m_value(i)
    End Function

    Public Function StageCard(i)
        StageCard = m_card(i)
    End Function

    ' Sum of collected stage values in the Path in progress.
    Public Function PathValue()
        Dim i, s
        s = 0
        For i = 0 To TT_STAGE_COUNT - 1
            If m_done(i) Then s = s + m_value(i)
        Next
        PathValue = s
    End Function

    ' Card index for each stage of the costliest Path (-1 if none).
    Public Function WorstPathCard(i)
        WorstPathCard = m_worstCards(i)
    End Function

    ' ======================== Internals ========================

    Private Sub CompletePath()
        Dim award, i, multUsed
        multUsed = PathMult
        award = TTRound(PathValue() * multUsed)
        Score = Score + award
        PathsCompleted = PathsCompleted + 1

        If award > WorstPathValue Then
            WorstPathValue = award
            For i = 0 To TT_STAGE_COUNT - 1
                m_worstCards(i) = m_card(i)
            Next
        End If

        TTEmit "path", award, multUsed

        PathMult = PathMult + TT_PATH_MULT_STEP
        If PathMult > TT_PATH_MULT_MAX Then PathMult = TT_PATH_MULT_MAX

        If PathsCompleted = TT_EXTRA_BALL_AT_PATH And Not ExtraBallAwarded Then
            ExtraBallAwarded = True
            ExtraBalls = ExtraBalls + 1
            TTEmit "extraball", 0, 0
        End If

        ResetChain
    End Sub

    Private Sub ReconCollected()
        m_reconCount = m_reconCount + 1
        If m_reconCount >= TT_RECON_FOR_RESAVE And Not m_resaveGiven Then
            m_resaveGiven = True
            BallSaveArmed = True
            TTEmit "ballsave_relit", 0, 0
        End If
    End Sub

    ' Patch Tuesday: one random collected stage (never Impact) drops back to unlit.
    Private Sub PatchOne()
        Dim i, n, pick, picked
        n = 0
        For i = 0 To TT_STAGE_COUNT - 2
            If m_done(i) Then n = n + 1
        Next
        If n = 0 Then Exit Sub

        If PatchOverride >= 0 Then
            picked = PatchOverride
            PatchOverride = -1
        Else
            pick = Int(Rnd * n)
            picked = -1
            For i = 0 To TT_STAGE_COUNT - 2
                If m_done(i) Then
                    If pick = 0 Then
                        picked = i
                        Exit For
                    End If
                    pick = pick - 1
                End If
            Next
        End If
        If picked < 0 Then Exit Sub
        If Not m_done(picked) Then Exit Sub

        m_done(picked) = False
        m_value(picked) = 0
        m_card(picked) = -1
        TTEmit "patch", picked, 0
    End Sub

    Private Function DrawCard(stage)
        Dim i, n, pick
        If CardOverride >= 0 Then
            DrawCard = CardOverride
            CardOverride = -1
            Exit Function
        End If
        n = 0
        For i = 0 To UBound(TT_Cards)
            If TT_Cards(i)(0) = stage Then n = n + 1
        Next
        pick = Int(Rnd * n)
        For i = 0 To UBound(TT_Cards)
            If TT_Cards(i)(0) = stage Then
                If pick = 0 Then
                    DrawCard = i
                    Exit Function
                End If
                pick = pick - 1
            End If
        Next
        DrawCard = 0
    End Function

    Private Sub ResetChain()
        Dim i
        For i = 0 To TT_STAGE_COUNT - 1
            m_done(i) = False
            m_value(i) = 0
            m_card(i) = -1
        Next
    End Sub

    Private Sub ClearWorst()
        Dim i
        WorstPathValue = 0
        For i = 0 To TT_STAGE_COUNT - 1
            m_worstCards(i) = -1
        Next
    End Sub
End Class

' Card helpers (shared by display, report and tests)
Function TTCardName(c)
    If c < 0 Then
        TTCardName = ""
    Else
        TTCardName = TT_Cards(c)(1)
    End If
End Function

Function TTCardId(c)
    If c < 0 Then
        TTCardId = ""
    Else
        TTCardId = TT_Cards(c)(2)
    End If
End Function

Function TTCardStage(c)
    TTCardStage = TT_Cards(c)(0)
End Function
