' =============================================================================
' Threat Tide - table feel: GI, sling animation, ball shadows, rolling and
' contact sounds.
'
' Adapted from the Visual Pinball X blank table script (fuzzel, jimmyfingers,
' jpsalas, toxie, unclewilly; rolling sounds by jpsalas, ball shadow and
' flipper shadows by ninuzzu, ball drop sounds by rothbauerw). It drives the
' stock objects that come with the VPX blank table (GI lights, sling rubbers
' and arms, ball shadow primitives, the RollingTimer and BallShadowUpdate
' timers, and the Rubbers/Posts/Pins/... collections). Anything missing is
' skipped, so a table built without those objects still runs.
' =============================================================================

Const TTF_BALLSIZE = 25          ' ball radius
Const TTF_MAXBALLS = 5           ' rolling sound / shadow slots
Dim TTF_Rolling(5)
Dim TTF_RStep, TTF_LStep

Sub TTFeelInit()
    Dim xx, i
    For i = 0 To TTF_MAXBALLS
        TTF_Rolling(i) = False
    Next
    On Error Resume Next
    For Each xx In GI
        xx.State = 1
    Next
    Err.Clear
    On Error GoTo 0
End Sub

' ---------------------------------------------------------------- slings

' Called from the sling handlers in tt_table.vbs
Sub TTFeelSling(isRight)
    On Error Resume Next
    If isRight Then
        PlaySound "right_slingshot", 0, 1, 0.05, 0.05
        RSling.Visible = 0
        RSling1.Visible = 1
        Sling1.RotX = 20
        TTF_RStep = 0
        RightSlingShot.TimerEnabled = 1
        Gi1.State = 0 : Gi2.State = 0
    Else
        PlaySound "left_slingshot", 0, 1, -0.05, 0.05
        LSling.Visible = 0
        LSling1.Visible = 1
        Sling2.RotX = 20
        TTF_LStep = 0
        LeftSlingShot.TimerEnabled = 1
        Gi3.State = 0 : Gi4.State = 0
    End If
    Err.Clear
    On Error GoTo 0
End Sub

Sub RightSlingShot_Timer()
    On Error Resume Next
    Select Case TTF_RStep
        Case 3: RSling1.Visible = 0 : RSling2.Visible = 1 : Sling1.RotX = 10
        Case 4: RSling2.Visible = 0 : RSling.Visible = 1 : Sling1.RotX = 0 : RightSlingShot.TimerEnabled = 0 : Gi1.State = 1 : Gi2.State = 1
    End Select
    TTF_RStep = TTF_RStep + 1
    Err.Clear
    On Error GoTo 0
End Sub

Sub LeftSlingShot_Timer()
    On Error Resume Next
    Select Case TTF_LStep
        Case 3: LSling1.Visible = 0 : LSling2.Visible = 1 : Sling2.RotX = 10
        Case 4: LSling2.Visible = 0 : LSling.Visible = 1 : Sling2.RotX = 0 : LeftSlingShot.TimerEnabled = 0 : Gi3.State = 1 : Gi4.State = 1
    End Select
    TTF_LStep = TTF_LStep + 1
    Err.Clear
    On Error GoTo 0
End Sub

' ---------------------------------------------------------------- positional audio

Function AudioFade(tableobj)   ' front/back by Y position
    Dim tmp
    tmp = tableobj.y * 2 / Table1.height - 1
    If tmp > 0 Then
        AudioFade = CSng(tmp ^ 10)
    Else
        AudioFade = CSng(-((-tmp) ^ 10))
    End If
End Function

Function AudioPan(tableobj)    ' left/right by X position
    Dim tmp
    tmp = tableobj.x * 2 / Table1.width - 1
    If tmp > 0 Then
        AudioPan = CSng(tmp ^ 10)
    Else
        AudioPan = CSng(-((-tmp) ^ 10))
    End If
End Function

Function BallVel(ball)
    BallVel = Int(Sqr((ball.VelX ^ 2) + (ball.VelY ^ 2)))
End Function

Function Vol(ball)
    Vol = CSng(BallVel(ball) ^ 2 / 2000)
End Function

Function Pitch(ball)
    Pitch = BallVel(ball) * 20
End Function

Sub TTPlayAtBall(soundname)
    PlaySound soundname, 0, Vol(ActiveBall), AudioPan(ActiveBall), 0, Pitch(ActiveBall), 1, 0, AudioFade(ActiveBall)
End Sub

' ---------------------------------------------------------------- rolling sounds

Sub RollingTimer_Timer()
    Dim BOT, b
    BOT = GetBalls
    For b = UBound(BOT) + 1 To TTF_MAXBALLS
        TTF_Rolling(b) = False
        StopSound "fx_ballrolling" & b
    Next
    If UBound(BOT) = -1 Then Exit Sub
    For b = 0 To UBound(BOT)
        If b > TTF_MAXBALLS Then Exit For
        If BallVel(BOT(b)) > 1 And BOT(b).z < 30 Then
            TTF_Rolling(b) = True
            PlaySound "fx_ballrolling" & b, -1, Vol(BOT(b)), AudioPan(BOT(b)), 0, Pitch(BOT(b)), 1, 0, AudioFade(BOT(b))
        ElseIf TTF_Rolling(b) Then
            StopSound "fx_ballrolling" & b
            TTF_Rolling(b) = False
        End If
        If BOT(b).VelZ < -1 And BOT(b).z < 55 And BOT(b).z > 27 Then
            PlaySound "fx_ball_drop" & b, 0, Abs(BOT(b).VelZ) / 17, AudioPan(BOT(b)), 0, Pitch(BOT(b)), 1, 0, AudioFade(BOT(b))
        End If
    Next
End Sub

Sub OnBallBallCollision(ball1, ball2, velocity)
    PlaySound "fx_collide", 0, CSng(velocity) ^ 2 / 2000, AudioPan(ball1), 0, Pitch(ball1), 0, 0, AudioFade(ball1)
End Sub

' ---------------------------------------------------------------- shadows

Sub LeftFlipper_Animate()
    On Error Resume Next
    FlipperLSh.RotZ = LeftFlipper.CurrentAngle
    On Error GoTo 0
End Sub

Sub RightFlipper_Animate()
    On Error Resume Next
    FlipperRSh.RotZ = RightFlipper.CurrentAngle
    On Error GoTo 0
End Sub

Sub BallShadowUpdate_Timer()
    Dim BOT, b, shadows
    On Error Resume Next
    shadows = Array(BallShadow1, BallShadow2, BallShadow3, BallShadow4, BallShadow5)
    If Err.Number <> 0 Then
        Err.Clear
        On Error GoTo 0
        Exit Sub
    End If
    BOT = GetBalls
    For b = UBound(BOT) + 1 To TTF_MAXBALLS - 1
        shadows(b).Visible = 0
    Next
    For b = 0 To UBound(BOT)
        If b >= TTF_MAXBALLS Then Exit For
        shadows(b).X = BOT(b).X + (BOT(b).X - (Table1.Width / 2)) * 1.25 / TTF_BALLSIZE
        shadows(b).Y = BOT(b).Y + 12
        shadows(b).Size_X = 5
        shadows(b).Size_Y = 5
        If BOT(b).Z > 20 Then
            shadows(b).Visible = 1
        Else
            shadows(b).Visible = 0
        End If
    Next
    Err.Clear
    On Error GoTo 0
End Sub

' ---------------------------------------------------------------- contact sounds (collections)

Sub Pins_Hit(idx)          : TTPlayAtBall "pinhit_low"      : End Sub
Sub Targets_Hit(idx)       : TTPlayAtBall "target"          : End Sub
Sub Metals_Thin_Hit(idx)   : TTPlayAtBall "metalhit_thin"   : End Sub
Sub Metals_Medium_Hit(idx) : TTPlayAtBall "metalhit_medium" : End Sub
Sub Metals2_Hit(idx)       : TTPlayAtBall "metalhit2"       : End Sub
Sub Gates_Hit(idx)         : TTPlayAtBall "gate4"           : End Sub

Sub Rubbers_Hit(idx)
    TTRubberSound 20
End Sub

Sub Posts_Hit(idx)
    TTRubberSound 16
End Sub

Sub TTRubberSound(hard)
    Dim speed
    speed = Sqr(ActiveBall.VelX * ActiveBall.VelX + ActiveBall.VelY * ActiveBall.VelY)
    If speed > hard Then
        TTPlayAtBall "fx_rubber2"
    ElseIf speed >= 6 Then
        TTPlayAtBall "rubber_hit_" & (Int(Rnd * 3) + 1)
    End If
End Sub

Sub LeftFlipper_Collide(parm)
    TTPlayAtBall "flip_hit_" & (Int(Rnd * 3) + 1)
End Sub

Sub RightFlipper_Collide(parm)
    TTPlayAtBall "flip_hit_" & (Int(Rnd * 3) + 1)
End Sub
