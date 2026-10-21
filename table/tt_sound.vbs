' =============================================================================
' Threat Tide - sound
'
' Logical cue names map to sounds imported into the table's Sound Manager.
' Missing sounds are skipped silently so the table runs before audio is final.
' Original or royalty-free audio only: record every file in docs/LICENSES.md.
' =============================================================================

' Logical cue -> VPX sound name
Function TTSoundName(cue)
    Select Case cue
        Case "initial_access": TTSoundName = "vo_initial_access"   ' "Initial access"
        Case "path":           TTSoundName = "vo_path_complete"    ' "Path complete"
        Case "air_gap":        TTSoundName = "vo_air_gap_breached" ' "Air gap breached" (Phase 2)
        Case "storm_surge":    TTSoundName = "vo_storm_surge"      ' "Storm surge" (Phase 3)
        Case "card":           TTSoundName = "sfx_card"
        Case "unlit":          TTSoundName = "sfx_unlit"
        Case "combo":          TTSoundName = "sfx_combo"
        Case "edr":            TTSoundName = "sfx_edr"
        Case "asset":          TTSoundName = "sfx_asset"
        Case "patch":          TTSoundName = "sfx_patch"
        Case "saved":          TTSoundName = "sfx_ballsave"
        Case "extraball":      TTSoundName = "vo_extra_ball"
        Case "lock_lit":       TTSoundName = "sfx_lock_lit"
        Case "lock":           TTSoundName = "vo_expert_locked"     ' "Expert locked"
        Case "multiball":      TTSoundName = "vo_expert_consensus"  ' "Expert consensus"
        Case "jackpot":        TTSoundName = "vo_jackpot"
        Case "tilt_warning":   TTSoundName = "sfx_tilt_warning"
        Case "tilt":           TTSoundName = "vo_incident_declared"
        Case "gameover":       TTSoundName = "sfx_gameover"
        ' Mechanical sounds: recorded samples that come with the VPX blank table
        Case "flipper":        TTSoundName = "fx_Flipperup"
        Case "flipper_down":   TTSoundName = "fx_Flipperdown"
        Case "plunger_pull":   TTSoundName = "plungerpull"
        Case "plunger":        TTSoundName = "plunger"
        Case "kicker":         TTSoundName = "popper_ball"
        Case "droptarget":     TTSoundName = "target"
        Case "release":        TTSoundName = "ballrelease"
        Case "drain":          TTSoundName = "drain"
        Case Else:             TTSoundName = ""
    End Select
End Function

' Volumes per preset. Halls are loud, so "booth" pushes callouts up.
Function TTVolume(kind)
    If TT_VolumePreset = "quiet" Then
        Select Case kind
            Case "voice": TTVolume = 0.5
            Case "music": TTVolume = 0.15
            Case Else:    TTVolume = 0.35
        End Select
    Else
        Select Case kind
            Case "voice": TTVolume = 1.0
            Case "music": TTVolume = 0.35
            Case Else:    TTVolume = 0.7
        End Select
    End If
End Function

Sub TTPlay(cue)
    Dim n, vol
    n = TTSoundName(cue)
    If n = "" Then Exit Sub
    If Left(n, 3) = "vo_" Then
        vol = TTVolume("voice")
    Else
        vol = TTVolume("sfx")
    End If
    On Error Resume Next
    PlaySound n, 0, vol
    On Error GoTo 0
End Sub

' Music files live in VPX's Music folder under ThreatTide\
' The current track loops: VPX calls Table1_MusicDone when it ends.
Dim TTMusicTrack : TTMusicTrack = ""

Sub TTMusic(track)
    If track = TTMusicTrack And track <> "" Then Exit Sub   ' already playing
    TTMusicTrack = track
    On Error Resume Next
    EndMusic
    If track <> "" Then PlayMusic "ThreatTide\" & track, TTVolume("music")
    On Error GoTo 0
End Sub

Sub TTMusicLoop()
    If TTMusicTrack = "" Then Exit Sub
    On Error Resume Next
    PlayMusic "ThreatTide\" & TTMusicTrack, TTVolume("music")
    On Error GoTo 0
End Sub
