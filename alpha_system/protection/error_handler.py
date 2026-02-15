import traceback
from datetime import datetime, UTC


class ErrorHandler:
    """Capture toutes les exceptions — empêche le crash système."""

    def __init__(self, logger=None, db=None):

        self.logger = logger
        self.db = db
        self.error_count = 0
        self.critical_errors = 0
        self.max_critical = 10

    def safe_execute(self, func, *args, default=None, context=""):
        """Exécute une fonction avec protection. Retourne default si erreur."""

        try:
            return func(*args)
        except Exception as e:
            self.error_count += 1
            self._handle_error(e, context)
            return default

    def handle(self, error, context=""):
        """Traite une erreur manuellement."""

        self.error_count += 1
        self._handle_error(error, context)

    def _handle_error(self, error, context):

        error_msg = f"[ERROR] {context}: {type(error).__name__}: {error}"
        tb = traceback.format_exc()

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

        # Critical detection
        critical_types = (ConnectionError, TimeoutError, MemoryError, SystemError)
        if isinstance(error, critical_types):
            self.critical_errors += 1
            print(f"  !!! CRITICAL ERROR #{self.critical_errors} !!!")

    def is_system_healthy(self):
        """Le système est-il encore sain ?"""

        return self.critical_errors < self.max_critical

    def get_status(self):

        return {
            "total_errors": self.error_count,
            "critical_errors": self.critical_errors,
            "healthy": self.is_system_healthy(),
        }
