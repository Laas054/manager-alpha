"""
ALPHA QUEUE — File d'attente persistée SQLite pour AlphaDecision.
Garantit la livraison des décisions aux équipes externes.
Le payload JSON est IMMUTABLE une fois enqueué.
"""

import json
import os
import sqlite3

from config import DATA_DIR, QUEUE_DB_PATH, QUEUE_MAX_RETRIES, utc_now


class AlphaDecisionQueue:
    """File d'attente SQLite pour AlphaDecision. Payload immutable."""

    def __init__(self, db_path: str | None = None):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._db_path = db_path or QUEUE_DB_PATH
        self._init_db()

    def _init_db(self) -> None:
        """Crée la table si elle n'existe pas."""
        with self._connect() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS alpha_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT NOT NULL UNIQUE,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    created_at TEXT NOT NULL,
                    delivered_at TEXT,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    max_retries INTEGER NOT NULL DEFAULT {int(QUEUE_MAX_RETRIES)}
                )
            """)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def enqueue(self, decision: dict) -> str:
        """
        Insère une AlphaDecision dans la queue.
        Le payload est sérialisé en JSON immutable.
        Retourne le decision_id.
        """
        decision_id = decision.get("decision_id", "UNKNOWN")
        payload = json.dumps(decision, ensure_ascii=False)
        created_at = utc_now().isoformat()

        with self._connect() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO alpha_decisions
                   (decision_id, payload, status, created_at, max_retries)
                   VALUES (?, ?, 'PENDING', ?, ?)""",
                (decision_id, payload, created_at, QUEUE_MAX_RETRIES),
            )

        return decision_id

    def fetch_pending(self, limit: int = 10) -> list[dict]:
        """Récupère les décisions en attente (FIFO)."""
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT id, decision_id, payload, status, created_at,
                          retry_count, max_retries
                   FROM alpha_decisions
                   WHERE status = 'PENDING'
                   ORDER BY id ASC
                   LIMIT ?""",
                (limit,),
            ).fetchall()

        return [
            {
                "id": row["id"],
                "decision_id": row["decision_id"],
                "payload": json.loads(row["payload"]),
                "status": row["status"],
                "created_at": row["created_at"],
                "retry_count": row["retry_count"],
            }
            for row in rows
        ]

    def mark_delivered(self, decision_id: str) -> bool:
        """Marque une décision comme livrée. NE modifie PAS le payload."""
        delivered_at = utc_now().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """UPDATE alpha_decisions
                   SET status = 'DELIVERED', delivered_at = ?
                   WHERE decision_id = ? AND status = 'PENDING'""",
                (delivered_at, decision_id),
            )
        return cursor.rowcount > 0

    def mark_failed(self, decision_id: str) -> bool:
        """Marque une décision comme échouée et incrémente le compteur."""
        with self._connect() as conn:
            cursor = conn.execute(
                """UPDATE alpha_decisions
                   SET status = 'FAILED', retry_count = retry_count + 1
                   WHERE decision_id = ? AND status = 'PENDING'""",
                (decision_id,),
            )
        return cursor.rowcount > 0

    def retry_failed(self) -> int:
        """Remet en PENDING les décisions FAILED si retry_count < max_retries."""
        with self._connect() as conn:
            cursor = conn.execute(
                """UPDATE alpha_decisions
                   SET status = 'PENDING'
                   WHERE status = 'FAILED' AND retry_count < max_retries""",
            )
        return cursor.rowcount

    def count_pending(self) -> int:
        """Nombre de décisions en attente."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM alpha_decisions WHERE status = 'PENDING'"
            ).fetchone()
        return row[0] if row else 0

    def count_all(self) -> dict:
        """Compteurs par statut."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) FROM alpha_decisions GROUP BY status"
            ).fetchall()
        return {row[0]: row[1] for row in rows}
