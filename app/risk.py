from dataclasses import dataclass


@dataclass
class SizeProposal:
    lots: float
    risk_amount: float
    risk_pct: float
    note: str


def propose_position_size(
    equity: float,
    risk_pct: float,
    entry_price: float,
    stop_price: float,
    tick_size: float,
    tick_value: float,
    volume_step: float,
    max_lots: float,
) -> SizeProposal:
    """Estimate lots from stop distance and tick economics; this never submits an order."""
    values = (equity, risk_pct, entry_price, stop_price, tick_size, tick_value, volume_step, max_lots)
    if any(v <= 0 for v in values):
        raise ValueError("All sizing inputs must be positive")
    distance = abs(entry_price - stop_price)
    if distance <= 0:
        raise ValueError("Entry and stop must differ")
    risk_amount = equity * risk_pct / 100.0
    loss_per_lot = distance / tick_size * tick_value
    raw_lots = min(risk_amount / loss_per_lot, max_lots)
    lots = (raw_lots // volume_step) * volume_step
    if lots <= 0:
        return SizeProposal(0.0, 0.0, risk_pct, "Below broker volume step; do not trade")
    return SizeProposal(round(lots, 8), round(lots * loss_per_lot, 2), risk_pct,
                        "Proposal only; verify contract specifications and broker limits")
