import os
from pathlib import Path
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

CONFIG = {
    # === CAPITAL ===
    "STARTING_CAPITAL": 1000,

    # === AI ===
    "CONFIDENCE_THRESHOLD": 0.75,

    # === RISK ===
    "MAX_RISK_PER_TRADE": 0.02,
    "MAX_DRAWDOWN_PCT": 0.15,
    "MAX_TRADE_SIZE": int(os.getenv("MAX_TRADE_SIZE", "100")),
    "MAX_TRADES_PER_DAY": 20,
    "MAX_TRADES_PER_HOUR": 5,
    "MAX_CORRELATED_EXPOSURE": 0.06,
    "MAX_LOSS_STREAK": 5,
    "TRAILING_STOP_PCT": 0.05,

    # === FEES ===
    "MAKER_FEE": 0.00,
    "TAKER_FEE": 0.02,
    "BASE_SLIPPAGE": 0.005,
    "MAX_SLIPPAGE": 0.03,

    # === SCAN ===
    "SCAN_INTERVAL": 60,
    "MIN_SCAN_INTERVAL": 15,
    "MAX_SCAN_INTERVAL": 120,

    # === DATABASE ===
    "DB_PATH": "alpha_system/data/alpha_system.db",

    # === LOGGING ===
    "LOG_DIR": "alpha_system/data/logs",

    # === MODE ===
    "MODE": os.getenv("TRADING_MODE", "DRY"),

    # === API ===
    "OLLAMA_API_KEY": os.getenv("OLLAMA_API_KEY", ""),
    "POLYMARKET_PRIVATE_KEY": os.getenv("POLYMARKET_PRIVATE_KEY", ""),
}
