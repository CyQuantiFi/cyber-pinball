' =============================================================================
' Threat Tide - FlexDMD display
'
' Screens: game (score, info, next target, 7 chain pips), callout overlay,
' board report, initials entry, claim (QR), attract, setup error.
' Every figure goes through TTMoney: no raw points anywhere.
' If FlexDMD is not installed the table still runs, without a display.
' =============================================================================

' FlexDMD alignment values
Const TTD_TOPLEFT = 0
Const TTD_TOP = 1
Const TTD_LEFT = 3
Const TTD_CENTER = 4
Const TTD_BOTTOM = 7

Dim FlexDMD, TTD_Ok
Dim TTD_ColOrange, TTD_ColPink, TTD_ColWhite, TTD_ColGrey, TTD_ColBg
Dim TTD_FBigO, TTD_FBigW, TTD_FMedO, TTD_FMedW, TTD_FSmallO, TTD_FSmallW, TTD_FSmallP, TTD_FTinyW, TTD_FTinyO, TTD_FTinyG

' Screens (groups)
Dim TTD_Game, TTD_Call, TTD_Report, TTD_Initials, TTD_Claim, TTD_Attract, TTD_Error

' Game screen
Dim TTD_lblScore, TTD_lblInfo, TTD_lblNext
Dim TTD_Pips(6)
Dim TTD_LastScoreText, TTD_LastInfoText, TTD_LastNextText

' Callout overlay + queue
Dim TTD_lblCall1, TTD_lblCall2
Dim TTD_CallActive, TTD_CallUntil, TTD_CallIsCard
Dim TTD_Q1(15), TTD_Q2(15), TTD_QMs(15), TTD_QHead, TTD_QCount
Dim TTD_PendCard1, TTD_PendCard2, TTD_PendCardAt, TTD_HasPendCard

' Report
Dim TTD_rTitle, TTD_rTotal, TTD_rWorst, TTD_rPath, TTD_rAssets, TTD_rClose1, TTD_rClose2

' Initials
Dim TTD_iTitle, TTD_iLetters, TTD_iHelp

' Claim
Dim TTD_cQr, TTD_cTitle, TTD_cLine1, TTD_cLine2, TTD_cLine3

' Attract
Dim TTD_aBig, TTD_aMed, TTD_aS(4)

' Error
Dim TTD_eLines(5)

' ---------------------------------------------------------------- setup

Sub TTDisplayInit()
    Dim i, x
    TTD_Ok = False
    TTD_CallActive = False
    TTD_QHead = 0
    TTD_QCount = 0
    TTD_HasPendCard = False
    TTD_LastScoreText = ""
    TTD_LastInfoText = ""
    TTD_LastNextText = ""

    On Error Resume Next
    Set FlexDMD = CreateObject("FlexDMD.FlexDMD")
    If Err.Number <> 0 Then
        Err.Clear
        On Error GoTo 0
        Exit Sub
    End If
    On Error GoTo 0

    TTD_ColOrange = RGB(255, 136, 24)
    TTD_ColPink = RGB(255, 154, 163)
    TTD_ColWhite = RGB(255, 255, 255)
    TTD_ColGrey = RGB(110, 110, 110)
    TTD_ColBg = RGB(26, 27, 28)

    With FlexDMD
        .GameName = "ThreatTide"
        .TableFile = Table1.Filename & ".vpx"
        .RenderMode = 2   ' full colour
        .Width = TT_DMD_W
        .Height = TT_DMD_H
        .Clear = True
    End With

    Set TTD_FBigO = FlexDMD.NewFont(TT_FONT_BIG, TTD_ColOrange, TTD_ColBg, 0)
    Set TTD_FBigW = FlexDMD.NewFont(TT_FONT_BIG, TTD_ColWhite, TTD_ColBg, 0)
    Set TTD_FMedO = FlexDMD.NewFont(TT_FONT_MED, TTD_ColOrange, TTD_ColBg, 0)
    Set TTD_FMedW = FlexDMD.NewFont(TT_FONT_MED, TTD_ColWhite, TTD_ColBg, 0)
    Set TTD_FSmallO = FlexDMD.NewFont(TT_FONT_SMALL, TTD_ColOrange, TTD_ColBg, 0)
    Set TTD_FSmallW = FlexDMD.NewFont(TT_FONT_SMALL, TTD_ColWhite, TTD_ColBg, 0)
    Set TTD_FSmallP = FlexDMD.NewFont(TT_FONT_SMALL, TTD_ColPink, TTD_ColBg, 0)
    Set TTD_FTinyW = FlexDMD.NewFont(TT_FONT_TINY, TTD_ColWhite, TTD_ColBg, 0)
    Set TTD_FTinyO = FlexDMD.NewFont(TT_FONT_TINY, TTD_ColOrange, TTD_ColBg, 0)
    Set TTD_FTinyG = FlexDMD.NewFont(TT_FONT_TINY, TTD_ColGrey, TTD_ColBg, 0)

    FlexDMD.LockRenderThread

    ' Game
    Set TTD_Game = TTDGroup("game")
    Set TTD_lblScore = TTDLabel(TTD_Game, "score", TTD_FBigW, "$0", TT_DMD_W / 2, 3, TTD_TOP)
    Set TTD_lblInfo = TTDLabel(TTD_Game, "info", TTD_FSmallW, "", TT_DMD_W / 2, 32, TTD_TOP)
    Set TTD_lblNext = TTDLabel(TTD_Game, "next", TTD_FSmallO, "", TT_DMD_W / 2, 42, TTD_TOP)
    For i = 0 To 6
        x = 16 + i * 32
        Set TTD_Pips(i) = FlexDMD.NewFrame("pip" & i)
        TTD_Pips(i).Thickness = 1
        TTD_Pips(i).BorderColor = TTD_ColGrey
        TTD_Pips(i).FillColor = TTD_ColOrange
        TTD_Pips(i).Fill = False
        TTD_Pips(i).SetBounds x, 55, 28, 6
        TTD_Game.AddActor TTD_Pips(i)
    Next

    ' Callout overlay (sits above the game screen)
    Set TTD_Call = TTDGroup("call")
    Set TTD_lblCall1 = TTDLabel(TTD_Call, "call1", TTD_FMedO, "", TT_DMD_W / 2, 14, TTD_TOP)
    Set TTD_lblCall2 = TTDLabel(TTD_Call, "call2", TTD_FSmallW, "", TT_DMD_W / 2, 36, TTD_TOP)

    ' Board report
    Set TTD_Report = TTDGroup("report")
    Set TTD_rTitle = TTDLabel(TTD_Report, "rtitle", TTD_FTinyG, "BOARD REPORT", TT_DMD_W / 2, 1, TTD_TOP)
    Set TTD_rTotal = TTDLabel(TTD_Report, "rtotal", TTD_FMedO, "", TT_DMD_W / 2, 8, TTD_TOP)
    Set TTD_rWorst = TTDLabel(TTD_Report, "rworst", TTD_FSmallW, "", TT_DMD_W / 2, 22, TTD_TOP)
    Set TTD_rPath = TTDLabel(TTD_Report, "rpath", TTD_FTinyO, "", TT_DMD_W / 2, 31, TTD_TOP)
    Set TTD_rAssets = TTDLabel(TTD_Report, "rassets", TTD_FSmallP, "", TT_DMD_W / 2, 38, TTD_TOP)
    Set TTD_rClose1 = TTDLabel(TTD_Report, "rclose1", TTD_FTinyW, "WANT THIS NUMBER FOR YOUR REAL ENVIRONMENT?", TT_DMD_W / 2, 50, TTD_TOP)
    Set TTD_rClose2 = TTDLabel(TTD_Report, "rclose2", TTD_FTinyO, "ASK US AT THE BOOTH.", TT_DMD_W / 2, 57, TTD_TOP)

    ' Initials
    Set TTD_Initials = TTDGroup("initials")
    Set TTD_iTitle = TTDLabel(TTD_Initials, "ititle", TTD_FSmallO, "ENTER YOUR INITIALS", TT_DMD_W / 2, 2, TTD_TOP)
    Set TTD_iLetters = TTDLabel(TTD_Initials, "iletters", TTD_FBigW, "A__", TT_DMD_W / 2, 14, TTD_TOP)
    Set TTD_iHelp = TTDLabel(TTD_Initials, "ihelp", TTD_FTinyG, "FLIPPERS CHANGE LETTER - START TO ENTER", TT_DMD_W / 2, 56, TTD_TOP)

    ' Claim (QR)
    Set TTD_Claim = TTDGroup("claim")
    On Error Resume Next
    Set TTD_cQr = FlexDMD.NewImage("qr", TT_QR_IMAGE)
    If Err.Number = 0 Then
        TTD_cQr.SetBounds 4, 4, 56, 56
        TTD_Claim.AddActor TTD_cQr
    End If
    Err.Clear
    On Error GoTo 0
    Set TTD_cTitle = TTDLabel(TTD_Claim, "ctitle", TTD_FMedO, "SCAN TO ENTER", 66, 4, TTD_TOPLEFT)
    Set TTD_cLine1 = TTDLabel(TTD_Claim, "cline1", TTD_FSmallW, "", 66, 22, TTD_TOPLEFT)
    Set TTD_cLine2 = TTDLabel(TTD_Claim, "cline2", TTD_FSmallW, TT_FormUrl, 66, 34, TTD_TOPLEFT)
    Set TTD_cLine3 = TTDLabel(TTD_Claim, "cline3", TTD_FTinyG, "OR ASK US AT THE BOOTH TABLET", 66, 48, TTD_TOPLEFT)

    ' Attract
    Set TTD_Attract = TTDGroup("attract")
    Set TTD_aBig = TTDLabel(TTD_Attract, "abig", TTD_FBigO, "", TT_DMD_W / 2, 4, TTD_TOP)
    Set TTD_aMed = TTDLabel(TTD_Attract, "amed", TTD_FMedW, "", TT_DMD_W / 2, 32, TTD_TOP)
    For i = 0 To 4
        Set TTD_aS(i) = TTDLabel(TTD_Attract, "as" & i, TTD_FTinyW, "", TT_DMD_W / 2, 6 + i * 11, TTD_TOP)
    Next

    ' Setup error
    Set TTD_Error = TTDGroup("error")
    For i = 0 To 5
        Set TTD_eLines(i) = TTDLabel(TTD_Error, "e" & i, TTD_FTinyW, "", 2, 2 + i * 10, TTD_TOPLEFT)
    Next

    TTDShowOnly ""
    FlexDMD.UnlockRenderThread
    FlexDMD.Run = True
    TTD_Ok = True
End Sub

Sub TTDisplayExit()
    If Not TTD_Ok Then Exit Sub
    On Error Resume Next
    FlexDMD.Run = False
    On Error GoTo 0
End Sub

Function TTDGroup(name)
    Dim g, bg
    Set g = FlexDMD.NewGroup(name)
    Set bg = FlexDMD.NewFrame(name & "_bg")
    bg.Thickness = 0
    bg.Fill = True
    bg.FillColor = TTD_ColBg
    bg.SetBounds 0, 0, TT_DMD_W, TT_DMD_H
    g.AddActor bg
    g.Visible = False
    FlexDMD.Stage.AddActor g
    Set TTDGroup = g
End Function

Function TTDLabel(group, name, font, text, x, y, align)
    Dim l
    Set l = FlexDMD.NewLabel(name, font, text)
    l.SetAlignedPosition x, y, align
    group.AddActor l
    Set TTDLabel = l
End Function

' Set label text and re-anchor (FlexDMD aligns once, at the current size)
Sub TTDSet(lbl, text, x, y, align)
    lbl.Text = text
    lbl.SetAlignedPosition x, y, align
End Sub

Sub TTDSetC(lbl, text, y)
    TTDSet lbl, text, TT_DMD_W / 2, y, TTD_TOP
End Sub

' Show one screen ("game", "report", ...). Callout overlay is managed separately.
Sub TTDShowOnly(name)
    TTD_Game.Visible = (name = "game")
    TTD_Report.Visible = (name = "report")
    TTD_Initials.Visible = (name = "initials")
    TTD_Claim.Visible = (name = "claim")
    TTD_Attract.Visible = (name = "attract")
    TTD_Error.Visible = (name = "error")
    If name <> "game" Then
        TTD_Call.Visible = False
        TTD_CallActive = False
        TTD_QCount = 0
        TTD_HasPendCard = False
    End If
End Sub

Sub TTDisplayShow(name)
    If Not TTD_Ok Then Exit Sub
    FlexDMD.LockRenderThread
    TTDShowOnly name
    FlexDMD.UnlockRenderThread
End Sub

' ---------------------------------------------------------------- game screen

Sub TTDisplayStartGame()
    If Not TTD_Ok Then Exit Sub
    TTD_LastScoreText = ""
    TTD_LastInfoText = ""
    TTD_LastNextText = ""
    TTDisplayShow "game"
End Sub

' Called every tick while a game is running.
Sub TTDisplayUpdate(g, nowMs)
    Dim s, info, nxt, i, nextLit, blinkOn
    If Not TTD_Ok Then Exit Sub
    FlexDMD.LockRenderThread

    s = TTMoney(g.Score)
    If s <> TTD_LastScoreText Then
        TTDSetC TTD_lblScore, s, 3
        TTD_LastScoreText = s
    End If

    If g.SurgeActive Then
        info = "STORM SURGE " & g.SurgeSecondsLeft(nowMs) & "S  WEATHER X" & g.SurgeMult & "  PEAK X" & g.SurgePeak
    ElseIf g.MultiballActive Then
        info = "CONSENSUS JACKPOT " & TTMoney(g.Jackpot) & "  EXPERTS " & g.BallsInPlay
    Else
        info = "BALL " & g.BallNum & "  PATH X" & g.PathMult & "  IMPACT " & TTMoney(g.Impact)
        If g.BallSaveActive(nowMs) Then info = info & "  IR"
    End If
    If info <> TTD_LastInfoText Then
        TTDSetC TTD_lblInfo, info, 32
        TTD_LastInfoText = info
    End If

    nextLit = g.NextLitStage()
    If g.Tilted Then
        nxt = "INCIDENT DECLARED"
    ElseIf g.SurgeActive Then
        nxt = "CENTRE RAMP: TAIL JACKPOT " & TTMoney(g.SurgeSum * g.SurgePeak)
    ElseIf g.AirGapOpen Then
        nxt = "AIR GAP OPEN: " & TTMoney(g.Jackpot * TT_AIRGAP_MULT)
    ElseIf nextLit < TT_STAGE_COUNT Then
        nxt = "NEXT: " & UCase(TT_StageNames(nextLit))
        If g.LocksLit > 0 And Not g.MultiballActive Then nxt = nxt & " - LOCK LIT"
    Else
        nxt = ""
    End If
    If nxt <> TTD_LastNextText Then
        TTDSetC TTD_lblNext, nxt, 42
        TTD_LastNextText = nxt
    End If

    blinkOn = ((Int(nowMs / 250) Mod 2) = 0)
    For i = 0 To 6
        If g.StageDone(i) Then
            TTD_Pips(i).Fill = True
            TTD_Pips(i).BorderColor = TTD_ColOrange
        ElseIf i = nextLit And blinkOn Then
            TTD_Pips(i).Fill = False
            TTD_Pips(i).BorderColor = TTD_ColOrange
        Else
            TTD_Pips(i).Fill = False
            TTD_Pips(i).BorderColor = TTD_ColGrey
        End If
    Next

    TTDCalloutTick nowMs
    FlexDMD.UnlockRenderThread
End Sub

' ---------------------------------------------------------------- callouts

' Card callouts replace each other; other messages queue so none are lost.
Sub TTDisplayCard(line1, line2, nowMs)
    If Not TTD_Ok Then Exit Sub
    FlexDMD.LockRenderThread
    If Not TTD_CallActive Or TTD_CallIsCard Then
        TTDShowCallout line1, line2, TT_CARD_SHOW_MS, nowMs, True
    Else
        TTD_PendCard1 = line1
        TTD_PendCard2 = line2
        TTD_PendCardAt = nowMs
        TTD_HasPendCard = True
    End If
    FlexDMD.UnlockRenderThread
End Sub

Sub TTDisplayMessage(line1, line2, ms, nowMs)
    Dim slot
    If Not TTD_Ok Then Exit Sub
    FlexDMD.LockRenderThread
    If Not TTD_CallActive Or TTD_CallIsCard Then
        TTDShowCallout line1, line2, ms, nowMs, False
    ElseIf TTD_QCount < 16 Then
        slot = (TTD_QHead + TTD_QCount) Mod 16
        TTD_Q1(slot) = line1
        TTD_Q2(slot) = line2
        TTD_QMs(slot) = ms
        TTD_QCount = TTD_QCount + 1
    End If
    FlexDMD.UnlockRenderThread
End Sub

Sub TTDShowCallout(line1, line2, ms, nowMs, isCard)
    TTDSetC TTD_lblCall1, line1, 14
    TTDSetC TTD_lblCall2, line2, 36
    TTD_Call.Visible = True
    TTD_CallActive = True
    TTD_CallIsCard = isCard
    TTD_CallUntil = nowMs + ms
End Sub

Sub TTDCalloutTick(nowMs)
    If Not TTD_CallActive Then Exit Sub
    If nowMs < TTD_CallUntil Then Exit Sub
    If TTD_QCount > 0 Then
        TTDShowCallout TTD_Q1(TTD_QHead), TTD_Q2(TTD_QHead), TTD_QMs(TTD_QHead), nowMs, False
        TTD_QHead = (TTD_QHead + 1) Mod 16
        TTD_QCount = TTD_QCount - 1
    ElseIf TTD_HasPendCard And nowMs - TTD_PendCardAt < TT_CARD_SHOW_MS Then
        TTD_HasPendCard = False
        TTDShowCallout TTD_PendCard1, TTD_PendCard2, TT_CARD_SHOW_MS, nowMs, True
    Else
        TTD_HasPendCard = False
        TTD_Call.Visible = False
        TTD_CallActive = False
    End If
End Sub

' ---------------------------------------------------------------- board report

Sub TTDisplayReport(g)
    Dim i, ids, worst, assets
    If Not TTD_Ok Then Exit Sub
    FlexDMD.LockRenderThread
    TTDSetC TTD_rTotal, "REALISED LOSS " & TTMoneyFull(g.Score), 8

    If g.WorstPathValue > 0 Then
        worst = "YOUR WORST DAY " & TTMoney(g.WorstPathValue)
        ids = ""
        For i = 0 To TT_STAGE_COUNT - 1
            If i > 0 Then ids = ids & ">"
            ids = ids & TTCardId(g.WorstPathCard(i))
        Next
    Else
        worst = "NO ATTACK PATH COMPLETED"
        ids = "HIT THE LIT SHOT. BUILD THE CHAIN."
    End If
    TTDSetC TTD_rWorst, worst, 22
    TTDSetC TTD_rPath, ids, 31

    assets = "ASSETS COMPROMISED: " & g.AssetsDropped
    If g.AirGapBreached Then assets = assets & "   AIR GAP BREACHED"
    TTDSetC TTD_rAssets, assets, 38

    TTDShowOnly "report"
    FlexDMD.UnlockRenderThread
End Sub

' ---------------------------------------------------------------- initials / claim

Sub TTDisplayInitials(letters)
    If Not TTD_Ok Then Exit Sub
    FlexDMD.LockRenderThread
    TTDSetC TTD_iLetters, letters, 14
    TTDShowOnly "initials"
    FlexDMD.UnlockRenderThread
End Sub

Sub TTDisplayClaim(initials, score)
    If Not TTD_Ok Then Exit Sub
    FlexDMD.LockRenderThread
    TTDSet TTD_cLine1, initials & "  " & TTMoneyFull(score), 66, 22, TTD_TOPLEFT
    TTDShowOnly "claim"
    FlexDMD.UnlockRenderThread
End Sub

' ---------------------------------------------------------------- attract

' page: 0 title, 1 high scores, 2 tagline, 3 how to play, 4 attribution
Sub TTDisplayAttract(page)
    Dim i, lines(4)
    If Not TTD_Ok Then Exit Sub
    For i = 0 To 4
        lines(i) = ""
    Next
    FlexDMD.LockRenderThread
    TTDSetC TTD_aBig, "", 4
    TTDSetC TTD_aMed, "", 32
    Select Case page
        Case 0
            TTDSetC TTD_aBig, "THREAT TIDE", 4
            TTDSetC TTD_aMed, "PRESS START", 36
        Case 1
            lines(0) = "TODAY'S BIGGEST LOSSES"
            For i = 1 To 4
                lines(i) = TTHighScoreLine(i)
            Next
        Case 2
            lines(1) = "PUT A DOLLAR FIGURE"
            lines(2) = "ON EVERY CYBER RISK"
            lines(4) = "CYQUANTIFI"
        Case 3
            lines(0) = "HOW TO PLAY"
            lines(1) = "1. HIT THE LIT SHOT"
            lines(2) = "2. BUILD THE CHAIN LEFT TO RIGHT"
            lines(3) = "3. IMPACT COMPLETES THE ATTACK PATH"
        Case 4
            lines(0) = "TECHNIQUE NAMES FROM"
            lines(1) = "MITRE ATT&CK(R)"
            lines(2) = "ATTACK.MITRE.ORG"
            lines(4) = "DOLLAR VALUES ARE FOR FUN, NOT ESTIMATES"
    End Select
    For i = 0 To 4
        TTDSetC TTD_aS(i), lines(i), 6 + i * 11
    Next
    TTDShowOnly "attract"
    FlexDMD.UnlockRenderThread
End Sub

' ---------------------------------------------------------------- setup error

Sub TTDisplayError(lines)
    Dim i
    If Not TTD_Ok Then Exit Sub
    FlexDMD.LockRenderThread
    For i = 0 To 5
        If i <= UBound(lines) Then
            TTDSet TTD_eLines(i), lines(i), 2, 2 + i * 10, TTD_TOPLEFT
        Else
            TTDSet TTD_eLines(i), "", 2, 2 + i * 10, TTD_TOPLEFT
        End If
    Next
    TTDShowOnly "error"
    FlexDMD.UnlockRenderThread
End Sub
