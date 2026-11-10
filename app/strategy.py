from collections.abc import Sequence
from dataclasses import asdict, dataclass


@dataclass
class Signal:
    action: str
    strategy: str
    reason: str
    fast_ema: float | None = None
    slow_ema: float | None = None


def _ema(values: Sequence[float], period: int) -> float:
    alpha = 2.0 / (period + 1)
    result = float(values[0])
    for value in values[1:]:
        result = alpha * float(value) + (1 - alpha) * result
    return result


def analyze_closes(closes: Sequence[float], fast: int = 10, slow: int = 30,
                   max_recent_move_pct: float = 3.0) -> dict:
    if fast < 2 or slow <= fast:
        raise ValueError("EMA periods must satisfy 2 <= fast < slow")
    if len(closes) < slow:
        return asdict(Signal("WAIT", "ema_trend", f"Need at least {slow} bars; received {len(closes)}"))
    if any(float(c) <= 0 for c in closes):
        return asdict(Signal("WAIT", "ema_trend", "Invalid non-positive price data"))
    window = [float(c) for c in closes[-slow:]]
    move_pct = abs(window[-1] / window[0] - 1) * 100
    fast_value, slow_value = _ema(window[-fast:], fast), _ema(window, slow)
    if move_pct > max_recent_move_pct:
        action, reason = "WAIT", f"Volatility guard: recent move {move_pct:.2f}% exceeds limit"
    elif fast_value > slow_value:
        action, reason = "BUY", "Fast EMA is above slow EMA; sample trend condition only"
    elif fast_value < slow_value:
        action, reason = "SELL", "Fast EMA is below slow EMA; sample trend condition only"
    else:
        action, reason = "WAIT", "EMAs are equal; no directional edge"
    return asdict(Signal(action, "ema_trend", reason, round(fast_value, 8), round(slow_value, 8)))
