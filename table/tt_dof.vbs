' =============================================================================
' Threat Tide - cabinet feedback (DirectOutput Framework, DOF)
'
' The table sends numbered events; DOF turns them into contactor pulses,
' button lamps and LED effects according to the cabinet's DOF config (see
' docs/dof.md for the event list and a sample config). Events go through the
' B2S Backglass Server, which the table starts even when the browser page owns
' the back screen (hide the B2S window in its settings, see docs/dof.md).
'
' With TT_DofOn = False, or no B2S Server installed, every call is a no-op.
' =============================================================================

' Pulses (DOF config sets how long each output fires)
Const DOF_FLIPPER_L = 101       ' on while the left flipper is up
Const DOF_FLIPPER_R = 102       ' on while the right flipper is up
Const DOF_SLING_L = 103
Const DOF_SLING_R = 104
Const DOF_RELEASE = 105         ' ball into the plunger lane
Const DOF_KICKER = 106          ' Persistence / Impact scoop kick
Const DOF_DROPTARGET = 107      ' asset drop target hit
Const DOF_DROP_RESET = 108      ' asset bank reset
Const DOF_KNOCKER = 109         ' extra ball, path complete, jackpots
Const DOF_PLUNGER = 110         ' plunger released
Const DOF_DRAIN = 111
Const DOF_STAGE_HIT = 112       ' any stage shot collected (LED flash)
Const DOF_CARD = 113            ' technique card shown (LED flash)

' States (on until switched off)
Const DOF_ATTRACT = 120
Const DOF_GAME = 121            ' a game is running
Const DOF_MULTIBALL = 122       ' Expert Consensus
Const DOF_SURGE = 123           ' Storm Surge wizard mode
Const DOF_TILT = 124            ' Incident declared (until the next ball)
Const DOF_REPORT = 125          ' board report / initials after the game
Const DOF_START_LAMP = 140      ' Start button lamp (lit when a game can start)
Const DOF_LAUNCH_LAMP = 141     ' Launch button lamp (lit while a ball waits to launch)

Dim TTDofCtl : Set TTDofCtl = Nothing   ' B2S.Server, set by TTDofAttach
Dim TTDofStates : Set TTDofStates = CreateObject("Scripting.Dictionary")

Sub TTDofAttach(ctl)
    Set TTDofCtl = ctl
    TTDofStates.RemoveAll
End Sub

Function TTDofActive()
    TTDofActive = TT_DofOn And Not (TTDofCtl Is Nothing)
End Function

' state: 0 = off, 1 = on, 2 = pulse
Sub TTDof(ev, state)
    If Not TTDofActive() Then Exit Sub
    On Error Resume Next
    If state = 2 Then
        TTDofCtl.B2SSetData ev, 1
        TTDofCtl.B2SSetData ev, 0
    Else
        TTDofCtl.B2SSetData ev, state
    End If
    Err.Clear
    On Error GoTo 0
End Sub

Sub TTDofPulse(ev)
    TTDof ev, 2
End Sub

' On/off outputs: only send changes, so the per-tick state refresh is cheap.
Sub TTDofSet(ev, isOn)
    Dim v
    If isOn Then v = 1 Else v = 0
    If TTDofStates.Exists(ev) Then
        If TTDofStates(ev) = v Then Exit Sub
    End If
    TTDofStates(ev) = v
    TTDof ev, v
End Sub

' One place that maps the table's mode to the state outputs.
Sub TTDofMode(mode)
    TTDofSet DOF_ATTRACT, (mode = "attract" Or mode = "claim")
    TTDofSet DOF_GAME, (mode = "game" Or mode = "gameover_wait")
    TTDofSet DOF_REPORT, (mode = "report" Or mode = "initials")
    TTDofSet DOF_START_LAMP, (mode = "attract" Or mode = "claim")
    If mode <> "game" Then
        TTDofSet DOF_MULTIBALL, False
        TTDofSet DOF_SURGE, False
        TTDofSet DOF_TILT, False
        TTDofSet DOF_LAUNCH_LAMP, False
    End If
End Sub

' Rule events (from TTEmit) that drive feedback. Display and sound stay in TTEmit.
Sub TTDofEvent(kind, a)
    Select Case kind
        Case "ball"
            TTDofSet DOF_TILT, False
            TTDofSet DOF_LAUNCH_LAMP, True
        Case "collected"
            TTDofPulse DOF_STAGE_HIT
        Case "card"
            TTDofPulse DOF_CARD
        Case "path", "extraball", "agreement", "surge_tail", "airgap"
            TTDofPulse DOF_KNOCKER
        Case "tilt"
            TTDofSet DOF_TILT, True
            TTDofSet DOF_FLIPPER_L, False
            TTDofSet DOF_FLIPPER_R, False
        Case "multiball"
            TTDofSet DOF_MULTIBALL, True
        Case "multiball_end"
            TTDofSet DOF_MULTIBALL, False
        Case "surge_start"
            TTDofSet DOF_SURGE, True
        Case "surge_end"
            TTDofSet DOF_SURGE, False
    End Select
End Sub

' Ball left the plunger lane
Sub TTDofLaunched()
    TTDofSet DOF_LAUNCH_LAMP, False
End Sub

' Everything off (table exit), so no contactor or lamp is left on.
Sub TTDofAllOff()
    Dim k, keys
    keys = TTDofStates.Keys
    For Each k In keys
        TTDofSet k, False
    Next
End Sub
