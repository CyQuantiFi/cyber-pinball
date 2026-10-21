' =============================================================================
' Threat Tide - dollar formatting
'
' Dollars are always Doubles. VBScript Long overflows at $2.1B, and Mod / \
' convert to Long, so this file avoids both. Formatting is done by hand so the
' cabinet's Windows locale can't change separators.
' =============================================================================

' Round to whole dollars.
Function TTRound(v)
    TTRound = Int(CDbl(v) + 0.5)
End Function

' Whole-number digits with no grouping, e.g. 1234500 -> "1234500".
Function TTDigits(v)
    Dim n : n = TTRound(v)
    If n < 0 Then n = 0
    TTDigits = FormatNumber(n, 0, -1, 0, 0)
End Function

' Insert thousands separators into a digit string.
Function TTGroup(digits)
    Dim s, out, i, count
    s = digits
    out = ""
    count = 0
    For i = Len(s) To 1 Step -1
        If count = 3 Then
            out = "," & out
            count = 0
        End If
        out = Mid(s, i, 1) & out
        count = count + 1
    Next
    TTGroup = out
End Function

' Full figure: $1,234,500
Function TTMoneyFull(v)
    TTMoneyFull = "$" & TTGroup(TTDigits(v))
End Function

' One decimal place in units of `unitSize`, e.g. 12400000 / 1e6 -> "12.4"
Function TTOneDecimal(v, unitSize)
    Dim tenths, whole, frac
    tenths = Int(CDbl(v) / (unitSize / 10) + 0.5)
    whole = Int(tenths / 10)
    frac = tenths - whole * 10
    TTOneDecimal = TTGroup(TTDigits(whole)) & "." & CStr(frac)
End Function

' Display figure: full below $10M, then $12.4M, then $1.2B.
Function TTMoney(v)
    Dim d : d = CDbl(v)
    If d >= 1000000000 Then
        TTMoney = "$" & TTOneDecimal(d, 1000000000) & "B"
    ElseIf d >= 10000000 Then
        TTMoney = "$" & TTOneDecimal(d, 1000000) & "M"
    Else
        TTMoney = TTMoneyFull(d)
    End If
End Function
