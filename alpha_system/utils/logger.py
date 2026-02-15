import logging
import os
from logging.handlers import RotatingFileHandler


_logger_instance = None


def setup_logger(name="alpha_system", log_dir="alpha_system/data/logs"):
    """Crée et retourne le logger structuré avec rotation automatique."""

    global _logger_instance
    if _logger_instance is not None:
        return _logger_instance

    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        _logger_instance = Logger(logger)
        return _logger_instance

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Fichier principal — rotation 5 MB, 5 backups
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "alpha_system.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    # Fichier erreurs — rotation 2 MB, 3 backups
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, "errors.log"),
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(fmt)
    logger.addHandler(error_handler)

    # Console (INFO+)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    _logger_instance = Logger(logger)
    return _logger_instance


class Logger:
    """Wrapper logger structuré."""

    def __init__(self, logger=None, name="alpha_system", log_dir="alpha_system/data/logs"):

        if logger is not None:
            self.logger = logger
        else:
            # Fallback: utiliser setup_logger
            instance = setup_logger(name, log_dir)
            self.logger = instance.logger

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
        self.logger.info(
            f"TRADE | {market[:50]} | {side} | size:{size} | "
            f"pnl:{round(pnl,2)} | conf:{confidence}"
        )

    def risk(self, msg):
        self.logger.warning(f"RISK | {msg}")

    def audit(self, action, detail=""):
        self.logger.info(f"AUDIT | {action} | {detail}")
