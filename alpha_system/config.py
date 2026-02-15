import os
from pathlib import Path
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

CONFIG = {
    # Capital
    "STARTING_CAPITAL": 1000,

    # AI
    "CONFIDENCE_THRESHOLD": 0.75,

    # Risk
    "MAX_RISK_PER_TRADE": 0.02,
    "MAX_DRAWDOWN_PCT": 0.15,
    "MAX_TRADE_SIZE": int(os.getenv("MAX_TRADE_SIZE", "100")),

    # Scan
    "SCAN_INTERVAL": 60,

    # Mode
    "MODE": os.getenv("TRADING_MODE", "DRY"),

    # Database
    "DB_PATH": "alpha_system/data/alpha_system.db",

    # API
    "OLLAMA_API_KEY": os.getenv("OLLAMA_API_KEY", ""),
    "POLYMARKET_PRIVATE_KEY": os.getenv("POLYMARKET_PRIVATE_KEY", ""),
}
