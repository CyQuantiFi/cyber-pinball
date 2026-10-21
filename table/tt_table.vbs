' =============================================================================
' Threat Tide - VPX glue
'
' Turns playfield events into rule calls and rule events into lights, display
' and sound. Object names here must match docs/object-contract.md.
' =============================================================================

Dim TTG                     ' TTGame (tt_rules.vbs)
Dim TTMode                  ' attract | game | gameover_wait | report | initials | claim | error
Dim TTTasks                 ' scheduled tasks: name -> due GameTime
Dim TTAttractPage, TTNextAttractMs
Dim TTInitialChars, TTInitialIdx, TTInitialPos, TTInitialsDone(2)
Dim TTLastInitials
Dim TTAssetDown(2)
Dim TTNudgeTimes(2), TTNudgeHead
Dim TTStageLightNames, TTStageLights(6), TTStageLightState(6)

' Phase 1 objects. Startup check reports any that are missing.
Function TTRequiredObjects()
    TTRequiredObjects = Array( _
        "LeftFlipper", "RightFlipper", "Plunger", "BallRelease", "Drain", "swPlungerLane", _
        "swRecon", "swInitialAccess", "swExecution", "kPersistence", "swPrivEsc", "swLateral", "kImpact", _
        "liRecon", "liInitialAccess", "liExecution", "liPersistence", "liPrivEsc", "liLateral", "liImpact", _
        "dtAsset1", "dtAsset2", "dtAsset3", "LeftSlingshot", "RightSlingshot", "tmrTick")
End Function

' ---------------------------------------------------------------- table events

Sub Table1_Init()
    Dim i
    Randomize
    Set TTG = New TTGame
    Set TTTasks = CreateObject("Scripting.Dictionary")
    TTInitialChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ<"
    TTStageLightNames = Array("liRecon", "liInitialAccess", "liExecution", "liPersistence", _
                              "liPrivEsc", "liLateral", "liImpact")
    For i = 0 To 6
        Set TTStageLights(i) = TTObj(TTStageLightNames(i))
        TTStageLightState(i) = -1
    Next
    For i = 0 To 2
        TTAssetDown(i) = False
        TTNudgeTimes(i) = -100000
    Next
    TTNudgeHead = 0

    TTScoresLoad
    TTDisplayInit
    tmrTick.Interval = 33
    tmrTick.Enabled = True

    If TTSelfCheck() Then
        TTEnterAttract
    Else
        TTMode = "error"
        TTSchedule "error_done", 20000
    End If
End Sub

Sub Table1_Exit()
    TTScoresSave
    TTDisplayExit
End Sub

' VPX 10.8 table options menu (operator settings). Ignored on older builds.
Sub Table1_OptionEvent(ByVal eventId)
    Dim v
    On Error Resume Next
    TT_BallsPerGame = Table1.Option("Balls per game", 3, 5, 2, 3, 0)
    v = Table1.Option("Patch Tuesday", 0, 1, 1, 1, 0, Array("Off", "On"))
    TT_PatchTuesdayOn = (v = 1)
    v = Table1.Option("Volume preset", 0, 1, 1, 0, 0, Array("Booth (loud hall)", "Quiet"))
    If v = 1 Then
        TT_VolumePreset = "quiet"
    Else
        TT_VolumePreset = "booth"
    End If
    v = Table1.Option("Contest mode (daily high-score reset)", 0, 1, 1, 1, 0, Array("Off", "On"))
    TT_ContestMode = (v = 1)
    Err.Clear
    On Error GoTo 0
End Sub

Sub tmrTick_Timer()
    Dim t : t = GameTime
    TTRunTasks t
    Select Case TTMode
        Case "game", "gameover_wait"
            TTG.Tick t
            TTUpdateLights
            TTDisplayUpdate TTG, t
        Case "attract"
            If t >= TTNextAttractMs Then
                TTAttractPage = (TTAttractPage + 1) Mod 5
                TTNextAttractMs = t + TT_ATTRACT_PAGE_MS
                TTDisplayAttract TTAttractPage
            End If
            TTAttractLights t
    End Select
End Sub

' ---------------------------------------------------------------- keys

Sub Table1_KeyDown(ByVal keycode)
    If keycode = PlungerKey Then Plunger.PullBack
    If keycode = LeftTiltKey Then Nudge 90, 2 : TTNudged
    If keycode = RightTiltKey Then Nudge 270, 2 : TTNudged
    If keycode = CenterTiltKey Then Nudge 0, 2 : TTNudged
    If keycode = MechanicalTilt Then TTTiltBob

    Select Case TTMode
        Case "game", "gameover_wait"
            If keycode = LeftFlipperKey And TTFlippersLive() Then
                LeftFlipper.RotateToEnd
                TTPlay "flipper"
            End If
            If keycode = RightFlipperKey And TTFlippersLive() Then
                RightFlipper.RotateToEnd
                TTPlay "flipper"
            End If
        Case "initials"
            TTInitialsKey keycode
        Case "attract", "claim", "error"
            If keycode = StartGameKey Then TTStartGame
            If keycode = LeftFlipperKey Or keycode = RightFlipperKey Then
                If TTMode = "attract" Then TTNextAttractMs = 0
            End If
    End Select
End Sub

Sub Table1_KeyUp(ByVal keycode)
    If keycode = PlungerKey Then Plunger.Fire
    If keycode = LeftFlipperKey Then LeftFlipper.RotateToStart
    If keycode = RightFlipperKey Then RightFlipper.RotateToStart
End Sub

Function TTFlippersLive()
    TTFlippersLive = (TTMode = "game") And TTG.IsActive And Not TTG.Tilted
End Function

' Three nudges inside 2 seconds count as one tilt-bob hit.
Sub TTNudged()
    Dim t : t = GameTime
    TTNudgeTimes(TTNudgeHead) = t
    TTNudgeHead = (TTNudgeHead + 1) Mod 3
    If t - TTNudgeTimes(TTNudgeHead) < 2000 Then TTTiltBob
End Sub

Sub TTTiltBob()
    If TTMode = "game" Then TTG.TiltBob GameTime
End Sub

' ---------------------------------------------------------------- playfield switches

Sub swPlungerLane_UnHit()
    If TTMode = "game" Then TTG.BallLaunched GameTime
End Sub

Sub swRecon_Hit()         : TTStage ST_RECON          : End Sub
Sub swInitialAccess_Hit() : TTStage ST_INITIAL_ACCESS : End Sub
Sub swExecution_Hit()     : TTStage ST_EXECUTION      : End Sub
Sub swPrivEsc_Hit()       : TTStage ST_PRIV_ESC       : End Sub
Sub swLateral_Hit()       : TTStage ST_LATERAL        : End Sub

Sub kPersistence_Hit()
    TTStage ST_PERSISTENCE
    TTSchedule "kickPersistence", TT_SAUCER_HOLD_MS
End Sub

Sub kImpact_Hit()
    TTStage ST_IMPACT
    TTSchedule "kickImpact", TT_SAUCER_HOLD_MS
End Sub

Sub TTStage(stage)
    If TTMode = "game" Then TTG.StageHit stage, GameTime
End Sub

Sub dtAsset1_Hit() : TTAssetHit 0 : End Sub
Sub dtAsset2_Hit() : TTAssetHit 1 : End Sub
Sub dtAsset3_Hit() : TTAssetHit 2 : End Sub

Sub TTAssetHit(n)
    If TTAssetDown(n) Then Exit Sub
    TTAssetDown(n) = True
    TTPlay "droptarget"
    If TTMode = "game" Then TTG.AssetDropped GameTime
    If TTAssetDown(0) And TTAssetDown(1) And TTAssetDown(2) Then
        TTSchedule "resetAssets", TT_ASSET_RESET_MS
    End If
End Sub

Sub TTResetAssets()
    dtAsset1.IsDropped = False
    dtAsset2.IsDropped = False
    dtAsset3.IsDropped = False
    TTAssetDown(0) = False
    TTAssetDown(1) = False
    TTAssetDown(2) = False
End Sub

Sub LeftSlingshot_Slingshot()
    TTPlay "sling"
    If TTMode = "game" Then TTG.EdrHit GameTime
End Sub

Sub RightSlingshot_Slingshot()
    TTPlay "sling"
    If TTMode = "game" Then TTG.EdrHit GameTime
End Sub

Sub Drain_Hit()
    Drain.DestroyBall
    TTPlay "drain"
    If TTMode = "game" Then TTG.Drain GameTime
End Sub

Sub TTReleaseBall()
    BallRelease.CreateBall
    BallRelease.Kick TT_RELEASE_ANGLE, TT_RELEASE_FORCE
    TTPlay "release"
End Sub

' ---------------------------------------------------------------- rule events

Sub TTEmit(kind, a, b)
    Dim t : t = GameTime
    Select Case kind
        Case "ball"
            If b Then
                TTDisplayMessage "SHOOT AGAIN", "EXTRA BALL", TT_MSG_SHOW_MS, t
            Else
                TTDisplayMessage "BALL " & a, "HIT THE LIT SHOT", TT_MSG_SHOW_MS, t
            End If
            TTSchedule "release", 1500
        Case "card"
            TTDisplayCard UCase(TTCardName(a)), TTCardId(a) & "   +" & TTMoney(b), t
            TTPlay "card"
        Case "collected"
            If a = ST_INITIAL_ACCESS Then TTPlay "initial_access"
        Case "combo"
            TTDisplayMessage "COMBO X" & TT_COMBO_MULT, "LATERAL MOVEMENT > INITIAL ACCESS", TT_MSG_SHOW_MS, t
            TTPlay "combo"
        Case "path"
            TTDisplayMessage "PATH COMPLETE", TTMoney(a) & "   (X" & b & ")", 2500, t
            TTPlay "path"
        Case "extraball"
            TTDisplayMessage "EXTRA BALL", "SECOND ATTACK PATH", TT_MSG_SHOW_MS, t
            TTPlay "extraball"
        Case "edr"
            TTDisplayMessage "DETECTED: EDR", "PATH VALUE " & TTMoney(a), 1200, t
            TTPlay "edr"
        Case "asset"
            TTDisplayMessage "ASSET COMPROMISED", "IMPACT NOW " & TTMoney(b), TT_MSG_SHOW_MS, t
            TTPlay "asset"
        Case "patch"
            TTDisplayMessage "PATCH TUESDAY", UCase(TT_StageNames(a)) & " PATCHED", TT_MSG_SHOW_MS, t
            TTPlay "patch"
        Case "ballsave_relit"
            TTDisplayMessage "IR RETAINER RELIT", "NEXT DRAIN IS COVERED", TT_MSG_SHOW_MS, t
        Case "saved"
            TTDisplayMessage "IR RETAINER", "BALL SAVED", TT_MSG_SHOW_MS, t
            TTPlay "saved"
            TTSchedule "release", 1000
        Case "bonus"
            TTDisplayMessage "DWELL TIME", b & " SEC UNDETECTED  +" & TTMoney(a), TT_MSG_SHOW_MS, t
        Case "evicted"
            TTDisplayMessage "EVICTED BY THE SOC", "PATH IN PROGRESS LOST", TT_MSG_SHOW_MS, t
        Case "tilt_warning"
            TTDisplayMessage "WARNING", "THE SOC IS WATCHING", 1200, t
            TTPlay "tilt_warning"
        Case "tilt"
            TTDisplayMessage "INCIDENT DECLARED", "BONUS LOST", 2500, t
            TTPlay "tilt"
            LeftFlipper.RotateToStart
            RightFlipper.RotateToStart
        Case "gameover"
            TTMode = "gameover_wait"
            TTPlay "gameover"
            TTSchedule "report", 4000
    End Select
End Sub

' ---------------------------------------------------------------- modes

Sub TTStartGame()
    TTTasks.RemoveAll
    TTResetAssets
    TTMode = "game"
    TTDisplayStartGame
    TTMusic "theme.mp3"
    TTG.StartGame GameTime
End Sub

Sub TTEnterAttract()
    TTMode = "attract"
    TTAttractPage = 0
    TTNextAttractMs = GameTime + TT_ATTRACT_PAGE_MS
    TTScoresCheckDay
    TTDisplayAttract 0
    TTMusic ""
End Sub

Sub TTEnterReport()
    TTMode = "report"
    TTMusic ""
    TTAllLightsOff
    TTDisplayReport TTG
    TTSchedule "report_done", TT_REPORT_MS
End Sub

Sub TTEnterInitials()
    TTMode = "initials"
    TTInitialIdx = 0
    TTInitialPos = 0
    TTShowInitials
    TTSchedule "initials_timeout", TT_INITIALS_TIMEOUT_MS
End Sub

Sub TTShowInitials()
    Dim k, s
    s = ""
    For k = 0 To 2
        If k < TTInitialPos Then
            s = s & TTInitialsDone(k)
        ElseIf k = TTInitialPos Then
            s = s & Mid(TTInitialChars, TTInitialIdx + 1, 1)
        Else
            s = s & "_"
        End If
    Next
    TTDisplayInitials s
End Sub

Sub TTInitialsKey(keycode)
    Dim n, ch
    n = Len(TTInitialChars)
    If keycode = LeftFlipperKey Then
        TTInitialIdx = (TTInitialIdx + n - 1) Mod n
    ElseIf keycode = RightFlipperKey Then
        TTInitialIdx = (TTInitialIdx + 1) Mod n
    ElseIf keycode = StartGameKey Or keycode = PlungerKey Then
        ch = Mid(TTInitialChars, TTInitialIdx + 1, 1)
        If ch = "<" Then
            If TTInitialPos > 0 Then TTInitialPos = TTInitialPos - 1
        Else
            TTInitialsDone(TTInitialPos) = ch
            TTInitialPos = TTInitialPos + 1
            If TTInitialPos >= 3 Then
                TTFinishInitials
                Exit Sub
            End If
        End If
    Else
        Exit Sub
    End If
    TTShowInitials
End Sub

Sub TTFinishInitials()
    Dim k, rank
    If TTMode <> "initials" Then Exit Sub
    ' Timeout fills any blanks with the current letter, then A
    For k = TTInitialPos To 2
        If k = TTInitialPos Then
            TTInitialsDone(k) = Mid(TTInitialChars, TTInitialIdx + 1, 1)
            If TTInitialsDone(k) = "<" Then TTInitialsDone(k) = "A"
        Else
            TTInitialsDone(k) = "A"
        End If
    Next
    TTLastInitials = TTInitialsDone(0) & TTInitialsDone(1) & TTInitialsDone(2)
    If TTTasks.Exists("initials_timeout") Then TTTasks.Remove "initials_timeout"
    rank = TTScoresAdd(TTLastInitials, TTG.Score)
    TTScoresWriteFiles TTG, TTLastInitials, rank
    TTMode = "claim"
    TTDisplayClaim TTLastInitials, TTG.Score
    TTSchedule "claim_done", TT_CLAIM_MS
End Sub

' ---------------------------------------------------------------- tasks

Sub TTSchedule(name, delayMs)
    TTTasks(name) = GameTime + delayMs
End Sub

Sub TTRunTasks(t)
    Dim k
    For Each k In TTTasks.Keys
        If TTTasks.Exists(k) Then
            If t >= TTTasks(k) Then
                TTTasks.Remove k
                TTRunTask k
            End If
        End If
    Next
End Sub

Sub TTRunTask(name)
    Select Case name
        Case "release":          TTReleaseBall
        Case "kickPersistence":  kPersistence.Kick TT_KICK_PERSISTENCE_ANGLE, TT_KICK_PERSISTENCE_FORCE : TTPlay "kicker"
        Case "kickImpact":       kImpact.Kick TT_KICK_IMPACT_ANGLE, TT_KICK_IMPACT_FORCE : TTPlay "kicker"
        Case "resetAssets":      TTResetAssets
        Case "report":           TTEnterReport
        Case "report_done":      TTEnterInitials
        Case "initials_timeout": TTFinishInitials
        Case "claim_done":       TTEnterAttract
        Case "error_done":       TTEnterAttract
    End Select
End Sub

' ---------------------------------------------------------------- lights

Sub TTSetStageLight(i, state)
    If TTStageLightState(i) = state Then Exit Sub
    TTStageLightState(i) = state
    If IsObject(TTStageLights(i)) Then
        If Not TTStageLights(i) Is Nothing Then TTStageLights(i).State = state
    End If
End Sub

' Collected = on, next lit = blinking, rest off.
Sub TTUpdateLights()
    Dim i, nextLit
    nextLit = TTG.NextLitStage()
    For i = 0 To 6
        If TTG.Tilted Then
            TTSetStageLight i, 0
        ElseIf TTG.StageDone(i) Then
            TTSetStageLight i, 1
        ElseIf i = nextLit Then
            TTSetStageLight i, 2
        Else
            TTSetStageLight i, 0
        End If
    Next
    TTSetOptionalLight "liShootAgain", TTG.ExtraBalls > 0
    TTSetOptionalLight "liBallSave", TTG.BallSaveActive(GameTime)
End Sub

' Left-to-right sweep: the chain reads left to right.
Sub TTAttractLights(t)
    Dim i, lit
    lit = Int(t / 180) Mod 9
    For i = 0 To 6
        If i = lit Then
            TTSetStageLight i, 1
        Else
            TTSetStageLight i, 0
        End If
    Next
End Sub

Sub TTAllLightsOff()
    Dim i
    For i = 0 To 6
        TTSetStageLight i, 0
    Next
    TTSetOptionalLight "liShootAgain", False
    TTSetOptionalLight "liBallSave", False
End Sub

Sub TTSetOptionalLight(name, isOn)
    Dim o
    Set o = TTObj(name)
    If o Is Nothing Then Exit Sub
    If isOn Then
        If o.State <> 1 Then o.State = 1
    Else
        If o.State <> 0 Then o.State = 0
    End If
End Sub

' ---------------------------------------------------------------- setup check

' Returns the named table object, or Nothing.
Function TTObj(name)
    Dim o
    Set TTObj = Nothing
    On Error Resume Next
    Set o = Eval(name)
    If Err.Number = 0 Then
        If IsObject(o) Then Set TTObj = o
    End If
    Err.Clear
    On Error GoTo 0
End Function

Function TTSelfCheck()
    Dim n, missing, lines(5), li, cur
    missing = 0
    li = 1
    cur = ""
    For li = 0 To 5
        lines(li) = ""
    Next
    li = 1
    For Each n In TTRequiredObjects()
        If TTObj(n) Is Nothing Then
            missing = missing + 1
            If Len(cur) + Len(n) + 1 > 50 Then
                If li <= 5 Then lines(li) = cur
                li = li + 1
                cur = ""
            End If
            cur = cur & n & " "
        End If
    Next
    If cur <> "" And li <= 5 Then lines(li) = cur
    TTSelfCheck = (missing = 0)
    If missing > 0 Then
        lines(0) = "SETUP: " & missing & " OBJECT(S) MISSING - SEE OBJECT-CONTRACT.MD"
        TTDisplayError lines
    End If
End Function
