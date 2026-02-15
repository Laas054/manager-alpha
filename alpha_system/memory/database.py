import sqlite3
import os
import shutil
from datetime import datetime, UTC


class DatabaseManager:
    """SQLite persistence — trades, capital_history, strategy_versions, backup, recovery."""

    def __init__(self, db_path="alpha_system/data/alpha_system.db"):

        self.db_path = db_path
        self.backup_dir = "alpha_system/data/backups"

        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):

        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                market TEXT NOT NULL,
                side TEXT NOT NULL,
                price REAL NOT NULL,
                size REAL NOT NULL,
                pnl REAL NOT NULL,
                confidence REAL NOT NULL,
                model TEXT DEFAULT '',
                source TEXT DEFAULT 'ai',
                status TEXT DEFAULT 'SIMULATED',
                fees REAL DEFAULT 0,
                slippage REAL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS capital_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                capital REAL NOT NULL,
                pnl REAL NOT NULL,
                drawdown_pct REAL NOT NULL,
                trade_count INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS strategy_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                version TEXT NOT NULL,
                confidence_threshold REAL NOT NULL,
                max_risk REAL NOT NULL,
                notes TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS system_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                capital REAL NOT NULL,
                starting_capital REAL NOT NULL,
                total_pnl REAL NOT NULL,
                total_trades INTEGER NOT NULL,
                wins INTEGER NOT NULL,
                losses INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                detail TEXT DEFAULT ''
            );
        """)
        self.conn.commit()
        self._migrate()

    def _migrate(self):
        """Ajoute les colonnes manquantes aux tables existantes."""

        migrations = [
            ("trades", "fees", "REAL DEFAULT 0"),
            ("trades", "slippage", "REAL DEFAULT 0"),
            ("trades", "model", "TEXT DEFAULT ''"),
            ("trades", "source", "TEXT DEFAULT 'ai'"),
            ("trades", "status", "TEXT DEFAULT 'SIMULATED'"),
        ]

        for table, column, col_type in migrations:
            try:
                self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                self.conn.commit()
            except Exception:
                pass  # Column already exists

    # === TRADES ===

    def record_trade(self, market, side, price, size, pnl, confidence,
                     model="", source="ai", status="SIMULATED",
                     fees=0, slippage=0):

        self.conn.execute("""
            INSERT INTO trades (timestamp, market, side, price, size, pnl,
                                confidence, model, source, status, fees, slippage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(UTC).isoformat(), market, side, price, size, pnl,
            confidence, model, source, status, fees, slippage
        ))
        self.conn.commit()

    def update_trade(self, trade_id, **kwargs):
        """Met à jour un trade existant."""

        allowed = {"pnl", "status", "fees", "slippage"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}

        if not updates:
            return

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [trade_id]

        self.conn.execute(
            f"UPDATE trades SET {set_clause} WHERE id = ?", values
        )
        self.conn.commit()

    def get_trades(self, limit=100):

        cursor = self.conn.execute(
            "SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_trade_count(self):

        cursor = self.conn.execute("SELECT COUNT(*) FROM trades")
        return cursor.fetchone()[0]

    def get_stats(self):

        cursor = self.conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losses,
                ROUND(SUM(pnl), 2) as total_pnl,
                ROUND(AVG(confidence), 4) as avg_confidence
            FROM trades
        """)
        row = cursor.fetchone()
        return dict(row) if row else {}

    # === CAPITAL HISTORY ===

    def record_capital(self, capital, pnl, drawdown_pct, trade_count):

        self.conn.execute("""
            INSERT INTO capital_history (timestamp, capital, pnl, drawdown_pct, trade_count)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.now(UTC).isoformat(), capital, pnl, drawdown_pct, trade_count))
        self.conn.commit()

    def get_capital_history(self, limit=500):

        cursor = self.conn.execute(
            "SELECT * FROM capital_history ORDER BY id DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]

    # === STRATEGY VERSIONS ===

    def save_strategy_version(self, version, confidence_threshold, max_risk, notes=""):

        self.conn.execute("""
            INSERT INTO strategy_versions (timestamp, version, confidence_threshold, max_risk, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.now(UTC).isoformat(), version, confidence_threshold, max_risk, notes))
        self.conn.commit()

    def get_strategy_versions(self):

        cursor = self.conn.execute("SELECT * FROM strategy_versions ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]

    # === STATE ===

    def save_state(self, capital, starting_capital, total_pnl,
                   total_trades, wins, losses):

        self.conn.execute("""
            INSERT INTO system_state (id, capital, starting_capital, total_pnl,
                                      total_trades, wins, losses, updated_at)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                capital=excluded.capital,
                starting_capital=excluded.starting_capital,
                total_pnl=excluded.total_pnl,
                total_trades=excluded.total_trades,
                wins=excluded.wins,
                losses=excluded.losses,
                updated_at=excluded.updated_at
        """, (
            capital, starting_capital, total_pnl,
            total_trades, wins, losses,
            datetime.now(UTC).isoformat()
        ))
        self.conn.commit()

    def load_state(self):

        cursor = self.conn.execute("SELECT * FROM system_state WHERE id = 1")
        row = cursor.fetchone()
        return dict(row) if row else None

    # === AUDIT ===

    def log_audit(self, action, detail=""):

        self.conn.execute("""
            INSERT INTO audit_log (timestamp, action, detail)
            VALUES (?, ?, ?)
        """, (datetime.now(UTC).isoformat(), action, detail))
        self.conn.commit()

    # === BACKUP ===

    def backup(self):

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"alpha_system_{timestamp}.db")

        self.conn.commit()
        shutil.copy2(self.db_path, backup_path)

        return backup_path

    def close(self):
        self.conn.close()
