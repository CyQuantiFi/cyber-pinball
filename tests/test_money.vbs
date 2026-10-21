' Threat Tide - dollar formatting tests

Sub RunMoneyTests()
    RunTest "Test_MoneyFull"
    RunTest "Test_MoneyShort"
    RunTest "Test_MoneyBeyondLong"
    RunTest "Test_Round"
End Sub

Sub Test_MoneyFull()
    AssertEq TTMoney(0), "$0", "zero"
    AssertEq TTMoney(999), "$999", "no separator under 1,000"
    AssertEq TTMoney(1000), "$1,000", "one separator"
    AssertEq TTMoney(1234500), "$1,234,500", "spec example"
    AssertEq TTMoney(9999999), "$9,999,999", "just under $10M stays full"
    AssertEq TTMoney(-5), "$0", "negative clamps to zero"
End Sub

Sub Test_MoneyShort()
    AssertEq TTMoney(10000000), "$10.0M", "$10M switches to short form"
    AssertEq TTMoney(12400000), "$12.4M", "spec example"
    AssertEq TTMoney(12449999), "$12.4M", "rounds down"
    AssertEq TTMoney(12450000), "$12.5M", "rounds up"
    AssertEq TTMoney(999000000), "$999.0M", "under $1B"
    AssertEq TTMoney(3000000000), "$3.0B", "billions"
    AssertEq TTMoney(1234000000000), "$1,234.0B", "trillions stay in B with separators"
End Sub

Sub Test_MoneyBeyondLong()
    AssertEq TTMoneyFull(3000000000), "$3,000,000,000", "above Long range"
    AssertEq TTMoneyFull(123456789012), "$123,456,789,012", "12 digits"
End Sub

Sub Test_Round()
    AssertEq TTRound(0.6 * 100000), 60000, "0.6 x 100K"
    AssertEq TTRound(0.35 * 100000), 35000, "0.35 x 100K"
    AssertEq TTRound(12.5), 13, "half rounds up"
End Sub
