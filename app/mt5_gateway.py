from typing import Any


class MT5Unavailable(RuntimeError):
    pass


class MT5Gateway:
    """Read-only MT5 adapter. Deliberately contains no order_send method."""

    def __init__(self, settings):
        self.settings = settings
        self.mt5 = None

    def connect(self) -> dict[str, Any]:
        if not self.settings.mt5_enabled:
            raise MT5Unavailable("MT5 is disabled; set TITAN_MT5_ENABLED=true to enable read-only access")
        try:
            import MetaTrader5 as mt5
        except ImportError as exc:
            raise MT5Unavailable("MetaTrader5 package is unavailable; install on Windows with MT5 terminal") from exc
        self.mt5 = mt5
        kwargs = {}
        if self.settings.mt5_login is not None:
            kwargs["login"] = self.settings.mt5_login
        if self.settings.mt5_password:
            kwargs["password"] = self.settings.mt5_password.get_secret_value()
        if self.settings.mt5_server:
            kwargs["server"] = self.settings.mt5_server
        if self.settings.mt5_path:
            kwargs["path"] = self.settings.mt5_path
        if not mt5.initialize(**kwargs):
            raise MT5Unavailable(f"MT5 initialize failed: {mt5.last_error()}")
        account = mt5.account_info()
        if account is None:
            mt5.shutdown()
            raise MT5Unavailable(f"Cannot read MT5 account: {mt5.last_error()}")
        if account.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
            mt5.shutdown()
            raise MT5Unavailable("Safety guard: this starter accepts demo accounts only")
        self.mt5 = mt5
        return self.account()

    def account(self) -> dict[str, Any]:
        if self.mt5 is None:
            raise MT5Unavailable("MT5 is not connected")
        info = self.mt5.account_info()
        if info is None:
            raise MT5Unavailable(f"Account read failed: {self.mt5.last_error()}")
        return {"login": info.login, "server": info.server, "currency": info.currency,
                "balance": info.balance, "equity": info.equity, "margin": info.margin,
                "margin_free": info.margin_free, "leverage": info.leverage,
                "trade_mode": "demo"}

    def rates(self, symbol: str, timeframe: str = "M15", count: int = 200) -> list[dict[str, float]]:
        if self.mt5 is None:
            raise MT5Unavailable("MT5 is not connected")
        if not self.mt5.symbol_select(symbol, True):
            raise MT5Unavailable(f"Symbol unavailable: {symbol}")
        tf = getattr(self.mt5, f"TIMEFRAME_{timeframe}", None)
        if tf is None:
            raise ValueError("Unsupported timeframe")
        rows = self.mt5.copy_rates_from_pos(symbol, tf, 0, min(max(count, 30), 1000))
        if rows is None or len(rows) == 0:
            raise MT5Unavailable(f"No rates returned: {self.mt5.last_error()}")
        return [{"time": int(r["time"]), "open": float(r["open"]), "high": float(r["high"]),
                 "low": float(r["low"]), "close": float(r["close"]), "tick_volume": int(r["tick_volume"])}
                for r in rows]

    def disconnect(self) -> None:
        if self.mt5 is not None:
            self.mt5.shutdown()
            self.mt5 = None
