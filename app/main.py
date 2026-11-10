from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.audit import AuditLog
from app.config import settings
from app.mt5_gateway import MT5Gateway, MT5Unavailable
from app.risk import propose_position_size
from app.strategy import analyze_closes
from app.telegram import send_telegram

app = FastAPI(title="TITAN AI TRADER", version="0.1.0", description="Demo-only, read-only MT5 starter")
audit = AuditLog(settings.database_path)
mt5 = MT5Gateway(settings)
state = {"mode": "PAPER", "paused": True, "emergency": False, "mt5_connected": False}


def require_api_key(authorization: str | None = Header(default=None)) -> None:
    configured = settings.api_key.get_secret_value()
    if not configured or configured == "replace-with-a-long-random-secret":
        raise HTTPException(status_code=503, detail="Configure a strong TITAN_API_KEY before using the API")
    if authorization != f"Bearer {configured}":
        raise HTTPException(status_code=401, detail="Unauthorized")


class StateRequest(BaseModel):
    reason: str = Field(default="operator request", max_length=200)


class SizeRequest(BaseModel):
    equity: float = Field(gt=0)
    risk_pct: float = Field(gt=0, le=1.0)
    entry_price: float = Field(gt=0)
    stop_price: float = Field(gt=0)
    tick_size: float = Field(gt=0)
    tick_value: float = Field(gt=0)
    volume_step: float = Field(gt=0)


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/api/status", dependencies=[Depends(require_api_key)])
def get_status():
    return {**state, "execution_enabled": False, "note": "Order execution is not implemented"}


@app.post("/api/mt5/connect", dependencies=[Depends(require_api_key)])
def connect_mt5():
    try:
        account = mt5.connect()
        state["mt5_connected"] = True
        audit.write("mt5_connected", {"login": account["login"], "server": account["server"], "mode": "demo"})
        return {"connected": True, "account": account}
    except (MT5Unavailable, ValueError) as exc:
        state["mt5_connected"] = False
        audit.write("mt5_connect_failed", {"error": str(exc)})
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/mt5/account", dependencies=[Depends(require_api_key)])
def get_account():
    try:
        return mt5.account()
    except MT5Unavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/market/signal", dependencies=[Depends(require_api_key)])
def market_signal(symbol: str = Query(min_length=1, max_length=32), timeframe: str = "M15"):
    try:
        bars = mt5.rates(symbol, timeframe)
        signal = analyze_closes([bar["close"] for bar in bars])
        result = {"symbol": symbol, "timeframe": timeframe, "bars": len(bars), "signal": signal,
                  "execution": "not implemented"}
        audit.write("signal", result)
        return result
    except (MT5Unavailable, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/risk/size", dependencies=[Depends(require_api_key)])
def size_proposal(request: SizeRequest):
    if request.risk_pct > settings.max_risk_pct:
        raise HTTPException(status_code=422, detail=f"risk_pct exceeds configured cap ({settings.max_risk_pct}%)")
    try:
        proposal = propose_position_size(request.equity, request.risk_pct, request.entry_price,
            request.stop_price, request.tick_size, request.tick_value, request.volume_step,
            settings.max_position_lots)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    result = proposal.__dict__
    audit.write("risk_size_proposal", result)
    return result


@app.post("/api/control/pause", dependencies=[Depends(require_api_key)])
def pause(body: StateRequest):
    state["paused"] = True
    audit.write("paused", {"reason": body.reason})
    return {"paused": True}


@app.post("/api/control/resume", dependencies=[Depends(require_api_key)])
def resume(body: StateRequest):
    if state["emergency"]:
        raise HTTPException(status_code=409, detail="Clear emergency state before resuming")
    state["paused"] = False
    audit.write("resumed", {"reason": body.reason, "mode": state["mode"]})
    return {"paused": False, "execution_enabled": False, "note": "Resume only affects monitoring in this starter"}


@app.post("/api/control/emergency", dependencies=[Depends(require_api_key)])
def emergency(body: StateRequest):
    state["emergency"] = True
    state["paused"] = True
    audit.write("emergency", {"reason": body.reason})
    token = settings.telegram_bot_token.get_secret_value() if settings.telegram_bot_token else ""
    if token and settings.telegram_chat_id:
        send_telegram(token, settings.telegram_chat_id, f"TITAN EMERGENCY: {body.reason}")
    return {"emergency": True, "paused": True, "note": "No open positions were modified"}


@app.get("/api/audit", dependencies=[Depends(require_api_key)])
def get_audit(limit: int = 50):
    return audit.latest(limit)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "execution_enabled": False}
