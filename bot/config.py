"""Configuration centrale du bot."""

from __future__ import annotations

import os
from pathlib import Path

# --- Chemins ---
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("BOT_DATA_DIR", ROOT_DIR / "bot" / "data"))
DB_PATH = Path(os.environ.get("BOT_DB_PATH", DATA_DIR / "bot.sqlite3"))

DATA_DIR.mkdir(parents=True, exist_ok=True)

# --- Marchés ---
# Mapping nom usuel -> symbole Binance
# Aligné sur paper_trading.py en prod (CRYPTOS).
MARKETS: dict[str, str] = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "SOL": "SOLUSDT",
    "BNB": "BNBUSDT",
    "XRP": "XRPUSDT",
}

# --- Données ---
DEFAULT_INTERVAL = os.environ.get("BOT_INTERVAL", "15m")  # 15m / 1h / 4h / 1d
DEFAULT_HISTORY_DAYS = int(os.environ.get("BOT_HISTORY_DAYS", "365"))

# --- Capital ---
CAPITAL_INITIAL = float(os.environ.get("BOT_CAPITAL", "3000"))
CAPITAL_PAR_MARCHE = float(os.environ.get("BOT_CAPITAL_PAR_MARCHE", "1000"))

# --- Frais & slippage (réalisme du backtest) ---
FRAIS_PCT = float(os.environ.get("BOT_FRAIS_PCT", "0.001"))      # 0.1 % par trade (Binance spot)
SLIPPAGE_PCT = float(os.environ.get("BOT_SLIPPAGE_PCT", "0.0005"))  # 0.05 %

# --- Anthropic ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
