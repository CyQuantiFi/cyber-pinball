' =============================================================================
' Threat Tide - minimal test harness for cscript
' Stands in for tt_table.vbs: records every TTEmit event.
' =============================================================================

Dim T_Pass, T_Fail, T_Current, T_Events
T_Pass = 0
T_Fail = 0
T_Current = ""
Set T_Events = CreateObject("Scripting.Dictionary")

' The rules call this; on the cabinet tt_table.vbs defines it.
Sub TTEmit(kind, a, b)
    T_Events.Add T_Events.Count, Array(kind, a, b)
End Sub

Sub T_ClearEvents()
    T_Events.RemoveAll
End Sub

Function T_Count(kind)
    Dim k, n, ev
    n = 0
    For Each k In T_Events.Keys
        ev = T_Events.Item(k)
        If ev(0) = kind Then n = n + 1
    Next
    T_Count = n
End Function

' Last event of this kind as Array(kind, a, b), or Array("", "", "")
Function T_Last(kind)
    Dim k, ev
    T_Last = Array("", "", "")
    For Each k In T_Events.Keys
        ev = T_Events.Item(k)
        If ev(0) = kind Then T_Last = ev
    Next
End Function

Sub AssertEq(actual, expected, msg)
    If CStr(actual) = CStr(expected) Then
        T_Pass = T_Pass + 1
    Else
        T_Fail = T_Fail + 1
        WScript.Echo "FAIL " & T_Current & ": " & msg & " - expected [" & CStr(expected) & "] got [" & CStr(actual) & "]"
    End If
End Sub

Sub AssertTrue(cond, msg)
    AssertEq CBool(cond), True, msg
End Sub

Sub RunTest(name)
    Dim f
    T_Current = name
    T_ClearEvents
    On Error Resume Next
    Set f = GetRef(name)
    If Err.Number = 0 Then Call f()
    If Err.Number <> 0 Then
        T_Fail = T_Fail + 1
        WScript.Echo "ERROR " & name & ": " & Err.Description & " (" & Err.Number & ")"
        Err.Clear
    End If
    On Error GoTo 0
End Sub

Sub T_Finish()
    WScript.Echo T_Pass & " passed, " & T_Fail & " failed"
    If T_Fail > 0 Then
        WScript.Quit 1
    Else
        WScript.Quit 0
    End If
End Sub

' ---------------------------------------------------------------- game helpers

' New game, ball 1 launched at t=0 (IR retainer runs to 10 s).
Function NewGame()
    Dim g
    Set g = New TTGame
    g.StartGame 0
    g.BallLaunched 0
    T_ClearEvents
    Set NewGame = g
End Function

Function CardIdx(stage, id)
    Dim i
    CardIdx = -1
    For i = 0 To UBound(TT_Cards)
        If TT_Cards(i)(0) = stage And TT_Cards(i)(2) = id Then
            CardIdx = i
            Exit Function
        End If
    Next
End Function

Sub Hit(g, stage, id, t)
    g.CardOverride = CardIdx(stage, id)
    g.StageHit stage, t
End Sub

' One full Attack Path at Impact $100K: stage values sum to $410,000.
'   Recon 90K, IA 60K, Exec 80K, Persist 60K, PrivEsc 40K, Lateral 50K, Impact 30K
Sub PlayPath(g, t0)
    Hit g, ST_RECON, "T1595", t0
    Hit g, ST_INITIAL_ACCESS, "T1566", t0 + 1000
    Hit g, ST_EXECUTION, "T1059", t0 + 2000
    Hit g, ST_PERSISTENCE, "T1053", t0 + 3000
    Hit g, ST_PRIV_ESC, "T1068", t0 + 4000
    Hit g, ST_LATERAL, "T1021", t0 + 5000
    Hit g, ST_IMPACT, "T1486", t0 + 6000
End Sub
