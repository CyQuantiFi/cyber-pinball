' Threat Tide - cabinet feedback (DOF) tests, with a fake B2S controller

Class T_FakeB2S
    Public Log
    Private Sub Class_Initialize()
        Log = ""
    End Sub
    Public Sub B2SSetData(ev, v)
        Log = Log & ev & "=" & v & ";"
    End Sub
End Class

Dim T_B2S

Sub RunDofTests()
    RunTest "Test_DofOffWithoutController"
    RunTest "Test_DofOffWhenDisabled"
    RunTest "Test_DofPulse"
    RunTest "Test_DofSetSendsChangesOnly"
    RunTest "Test_DofModes"
    RunTest "Test_DofTiltAndNextBall"
    RunTest "Test_DofKnockerEvents"
    RunTest "Test_DofAllOff"
End Sub

Sub T_DofFresh()
    TT_DofOn = True
    Set T_B2S = New T_FakeB2S
    TTDofAttach T_B2S
End Sub

Sub Test_DofOffWithoutController()
    TT_DofOn = True
    TTDofAttach Nothing
    TTDofPulse DOF_SLING_L          ' must not raise
    AssertEq TTDofActive(), False, "no controller = inactive"
End Sub

Sub Test_DofOffWhenDisabled()
    T_DofFresh
    TT_DofOn = False
    TTDofPulse DOF_SLING_L
    TTDofSet DOF_GAME, True
    AssertEq T_B2S.Log, "", "nothing sent when TT_DofOn is False"
    TT_DofOn = True
End Sub

Sub Test_DofPulse()
    T_DofFresh
    TTDofPulse DOF_SLING_R
    AssertEq T_B2S.Log, "104=1;104=0;", "pulse is on then off"
End Sub

Sub Test_DofSetSendsChangesOnly()
    T_DofFresh
    TTDofSet DOF_FLIPPER_L, True
    TTDofSet DOF_FLIPPER_L, True
    TTDofSet DOF_FLIPPER_L, False
    TTDofSet DOF_FLIPPER_L, False
    AssertEq T_B2S.Log, "101=1;101=0;", "repeats are not resent"
End Sub

Sub Test_DofModes()
    T_DofFresh
    TTDofMode "attract"
    AssertTrue InStr(T_B2S.Log, "120=1;") > 0, "attract on"
    AssertTrue InStr(T_B2S.Log, "140=1;") > 0, "start lamp on in attract"
    T_B2S.Log = ""
    TTDofMode "attract"
    AssertEq T_B2S.Log, "", "same mode sends nothing (safe to call every tick)"
    TTDofMode "game"
    AssertTrue InStr(T_B2S.Log, "120=0;") > 0, "attract off"
    AssertTrue InStr(T_B2S.Log, "121=1;") > 0, "game on"
    AssertTrue InStr(T_B2S.Log, "140=0;") > 0, "start lamp off in game"
    T_B2S.Log = ""
    TTDofMode "report"
    AssertTrue InStr(T_B2S.Log, "121=0;") > 0, "game off"
    AssertTrue InStr(T_B2S.Log, "125=1;") > 0, "report on"
End Sub

Sub Test_DofTiltAndNextBall()
    T_DofFresh
    TTDofMode "game"
    TTDofSet DOF_FLIPPER_R, True
    TTDofEvent "tilt", 0
    AssertTrue InStr(T_B2S.Log, "124=1;") > 0, "tilt on"
    AssertTrue InStr(T_B2S.Log, "102=0;") > 0, "held flipper released on tilt"
    T_B2S.Log = ""
    TTDofEvent "ball", 2
    AssertTrue InStr(T_B2S.Log, "124=0;") > 0, "tilt off at next ball"
    AssertTrue InStr(T_B2S.Log, "141=1;") > 0, "launch lamp on while the ball waits"
    TTDofLaunched
    AssertTrue InStr(T_B2S.Log, "141=0;") > 0, "launch lamp off after launch"
End Sub

Sub Test_DofKnockerEvents()
    Dim k
    For Each k In Array("path", "extraball", "agreement", "surge_tail", "airgap")
        T_DofFresh
        TTDofEvent k, 0
        AssertEq T_B2S.Log, "109=1;109=0;", "knocker on " & k
    Next
    T_DofFresh
    TTDofEvent "edr", 0
    AssertEq T_B2S.Log, "", "no knocker on an ordinary event"
End Sub

Sub Test_DofAllOff()
    T_DofFresh
    TTDofMode "game"
    TTDofEvent "multiball", 0
    TTDofSet DOF_FLIPPER_L, True
    T_B2S.Log = ""
    TTDofAllOff
    AssertTrue InStr(T_B2S.Log, "121=0;") > 0, "game off"
    AssertTrue InStr(T_B2S.Log, "122=0;") > 0, "multiball off"
    AssertTrue InStr(T_B2S.Log, "101=0;") > 0, "flipper off"
    AssertTrue InStr(T_B2S.Log, "=1;") = 0, "nothing left on"
End Sub
