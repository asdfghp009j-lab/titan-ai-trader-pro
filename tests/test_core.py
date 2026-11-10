import pytest
from app.risk import propose_position_size
from app.strategy import analyze_closes


def test_signal_waits_for_enough_data():
    result = analyze_closes([1.0] * 10)
    assert result["action"] == "WAIT"


def test_signal_reports_uptrend():
    closes = [100 + i * 0.2 for i in range(40)]
    assert analyze_closes(closes)["action"] == "BUY"


def test_risk_size_proposal():
    result = propose_position_size(10000, 0.5, 1.1, 1.09, 0.0001, 10, 0.01, 1.0)
    assert result.lots == pytest.approx(0.5)
    assert result.risk_amount == pytest.approx(50)


def test_invalid_risk_inputs_rejected():
    with pytest.raises(ValueError):
        propose_position_size(0, 0.5, 1.1, 1.09, 0.0001, 10, 0.01, 1.0)
