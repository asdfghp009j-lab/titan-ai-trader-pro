# TITAN AI TRADER

Arabic-first, safety-focused starter for a MetaTrader 5 trading assistant. The current version provides a protected FastAPI service, MT5 **read-only** account/market access, a basic explainable signal, risk sizing, audit events, Telegram notifications, and a responsive Arabic dashboard.

> **Safety status:** no order-submission or withdrawal code is included. Real-account trading is not enabled. The MT5 adapter refuses non-demo accounts. Start with paper/demo testing; no signal or backtest guarantees profit.

## Current capabilities

- FastAPI REST API with bearer-token protection.
- Optional MT5 connection (Windows + installed/running MT5 terminal); account and rates are read-only.
- Basic EMA trend signal with a volatility guard and recorded explanation.
- Risk-based position-size proposal (not an order).
- Pause/resume/emergency-stop state controls, audit log in SQLite.
- Optional Telegram alert delivery.
- Arabic RTL dashboard served by the API.
- Unit tests for signal and risk calculations.

## Quick start (Windows VPS)

1. Install Python 3.11+ and MetaTrader 5 terminal. Log in to a **demo** account in the terminal.
2. Clone this repository and create an isolated environment:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```

3. Generate a long random API key and set `TITAN_API_KEY` in `.env`. Keep `.env` private and never commit it. The API binds to localhost by default.
4. Set `MT5_ENABLED=true` only after MT5 terminal is running and configure the optional MT5 fields in `.env`. Credentials are read from environment configuration; do not paste them into chat or source code. The adapter checks that the account is demo.
5. Run:

   ```powershell
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

6. Visit `http://127.0.0.1:8000/`. Enter the API key in the dashboard. API docs are at `/docs` (also bearer-protected).
7. Run tests with `pytest`.

### API authentication

Send `Authorization: Bearer <TITAN_API_KEY>` on API requests. Do not expose port 8000 directly to the internet. Use a VPN or properly configured HTTPS reverse proxy and firewall if remote access is needed. Rotate the key if exposed.

## Configuration

See `.env.example`. `MT5_ENABLED` defaults to false. `TRADING_ENABLED` is intentionally fixed to false in this starter; no trading endpoint exists. `EMERGENCY` pauses new proposals and is auditable; it does not close positions.

Telegram delivery is optional. Configure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as environment variables. Protect the bot and do not add Telegram trading commands until administrator identity checks, replay protection, and explicit confirmations are implemented and tested.

## Development and limitations

This is a safe foundation, not the full requested production system. The signal is educational and not an AI model or investment recommendation. There is no live execution, broker-side stop placement, economic-news feed, multi-account orchestration, withdrawal/deposit capability, or validated backtester. Before any future execution feature, add independent risk checks, idempotency, broker constraints, extensive demo/forward tests, operational monitoring, and an explicit human-controlled live activation flow. Never infer that a feature works until tested against the intended broker and terminal.

## Project layout

- `app/main.py` — API and dashboard routes
- `app/config.py` — environment settings
- `app/mt5_gateway.py` — demo-only, read-only MT5 access
- `app/strategy.py` — explainable sample signal
- `app/risk.py` — position-size proposal
- `app/audit.py` — SQLite event journal
- `app/telegram.py` — outbound Telegram alerts
- `app/static/` — Arabic RTL dashboard
- `tests/` — unit tests
