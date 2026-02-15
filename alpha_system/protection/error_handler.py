import traceback
import functools
from datetime import datetime, UTC


class ErrorHandler:
    """Capture toutes les exceptions — empêche le crash système.
    Shutdown automatique si erreurs critiques répétées."""

    def __init__(self, logger=None, db=None, max_critical=10):

        self.logger = logger
        self.db = db
        self.error_count = 0
        self.critical_errors = 0
        self.max_critical = max_critical
        self.shutdown_requested = False

    def handle(self, error, context=""):
        """Traite une erreur manuellement."""

        self.error_count += 1
        self._process_error(error, context)

    def wrap(self, func):
        """Décorateur — protège une fonction contre les exceptions."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.error_count += 1
                self._process_error(e, func.__name__)
                return None
        return wrapper

    def safe_execute(self, func, *args, default=None, context=""):
        """Exécute une fonction avec protection. Retourne default si erreur."""

        try:
            return func(*args)
        except Exception as e:
            self.error_count += 1
            self._process_error(e, context)
            return default

    def _process_error(self, error, context):

        error_msg = f"[ERROR] {context}: {type(error).__name__}: {error}"

        # Log
        if self.logger:
            self.logger.error(error_msg)

        # DB audit
        if self.db:
            try:
                self.db.log_audit("ERROR", error_msg)
            except Exception:
                pass

        # Console
        print(f"  {error_msg}")

        # Critical detection + shutdown automatique
        critical_types = (ConnectionError, TimeoutError, MemoryError, SystemError)
        if isinstance(error, critical_types):
            self.critical_errors += 1
            print(f"  !!! CRITICAL ERROR #{self.critical_errors}/{self.max_critical} !!!")

            if self.critical_errors >= self.max_critical:
                self.shutdown_requested = True
                if self.logger:
                    self.logger.critical("SHUTDOWN REQUESTED — too many critical errors")

    def is_system_healthy(self):
        """Le système est-il encore sain ?"""

        if self.shutdown_requested:
            return False
        return self.critical_errors < self.max_critical

    def reset(self):
        """Reset les compteurs (après maintenance)."""

        self.error_count = 0
        self.critical_errors = 0
        self.shutdown_requested = False

    def get_status(self):

        return {
            "total_errors": self.error_count,
            "critical_errors": self.critical_errors,
            "healthy": self.is_system_healthy(),
            "shutdown_requested": self.shutdown_requested,
        }
