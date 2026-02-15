import logging
import os
from datetime import datetime, UTC


class Logger:
    """Logger structuré — fichier + console."""

    def __init__(self, name="alpha_system", log_dir="alpha_system/data/logs"):

        os.makedirs(log_dir, exist_ok=True)

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Eviter les handlers dupliqués
        if self.logger.handlers:
            return

        # Format
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Fichier log principal
        file_handler = logging.FileHandler(
            os.path.join(log_dir, "alpha_system.log"),
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt)
        self.logger.addHandler(file_handler)

        # Fichier erreurs uniquement
        error_handler = logging.FileHandler(
            os.path.join(log_dir, "errors.log"),
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(fmt)
        self.logger.addHandler(error_handler)

        # Console (INFO+)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(fmt)
        self.logger.addHandler(console_handler)

    def info(self, msg):
        self.logger.info(msg)

    def debug(self, msg):
        self.logger.debug(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def critical(self, msg):
        self.logger.critical(msg)

    def trade(self, market, side, size, pnl, confidence):
        """Log spécifique pour les trades."""

        self.logger.info(
            f"TRADE | {market[:50]} | {side} | size:{size} | "
            f"pnl:{round(pnl,2)} | conf:{confidence}"
        )

    def risk(self, msg):
        self.logger.warning(f"RISK | {msg}")

    def audit(self, action, detail=""):
        self.logger.info(f"AUDIT | {action} | {detail}")
