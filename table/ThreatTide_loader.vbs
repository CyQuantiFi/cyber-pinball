' =============================================================================
' Threat Tide - development loader
'
' For fast iteration: paste this into the .vpx script editor and keep the
' table\*.vbs files in VPX's Scripts folder (or next to the .vpx). Edits to
' the module files then apply on the next table start, no re-paste needed.
'
' For the booth cabinet, paste dist/ThreatTide_full.vbs instead (built by
' tools/bundle.py). It is the same code in one file with no external files.
' =============================================================================

Sub TTLoadModule(fileName)
    Dim code
    code = ""
    On Error Resume Next
    code = GetTextFile(fileName)
    Err.Clear
    On Error GoTo 0
    If code = "" Then
        MsgBox "Threat Tide could not load " & fileName & vbCrLf & _
               "Copy the table\*.vbs files into VPX's Scripts folder, or use dist\ThreatTide_full.vbs."
        Exit Sub
    End If
    ExecuteGlobal code
End Sub

' Order matters: config first, glue last.
TTLoadModule "tt_config.vbs"
TTLoadModule "tt_money.vbs"
TTLoadModule "tt_rules.vbs"
TTLoadModule "tt_sound.vbs"
TTLoadModule "tt_display.vbs"
TTLoadModule "tt_scores.vbs"
TTLoadModule "tt_table.vbs"
