"""
AGENT ALPHA — Gestion des agents et registre.
Séparation stricte Candidate / Agent actif / Exclu.
"""

import json
import os
import uuid
from collections import OrderedDict

from config import (
    AGENT_CACHE_MAX_SIZE,
    AGENT_STATUS_ACTIVE,
    AGENT_STATUS_CANDIDATE,
    AGENT_STATUS_EXCLUDED,
    AGENTS_FILE,
    ALPHA_ROLES,
    MAX_WARNINGS,
    utc_now,
)


class Agent:
    """Représente un agent Alpha avec suivi disciplinaire complet."""

    def __init__(self, name: str, role: str):
        if role not in ALPHA_ROLES:
            raise ValueError(f"Rôle invalide '{role}'. Rôles autorisés : {ALPHA_ROLES}")

        self.id: str = str(uuid.uuid4())[:8]
        self.name: str = name
        self.role: str = role
        self.status: str = AGENT_STATUS_CANDIDATE
        self.warnings: int = 0
        self.warning_reasons: list[str] = []
        self.interview_passed: bool = False
        self.interview_score: float = 0.0
        self.mode: str = "human"  # "human" ou "llm"
        self.decisions_log: list[dict] = []
        self.created_at: str = utc_now().isoformat()
        self.excluded_at: str | None = None
        self.verbal_discipline_score: float = 100.0  # KPI discipline verbale

    def activate(self) -> bool:
        """Passe le statut de candidat à actif. Requiert entretien réussi."""
        if self.status != AGENT_STATUS_CANDIDATE:
            return False
        if not self.interview_passed:
            return False
        self.status = AGENT_STATUS_ACTIVE
        return True

    def add_warning(self, reason: str) -> str:
        """Ajoute un avertissement. 3 = exclusion automatique."""
        if self.status == AGENT_STATUS_EXCLUDED:
            return "AGENT_DEJA_EXCLU"

        self.warnings += 1
        self.warning_reasons.append(f"[{utc_now().isoformat()}] {reason}")

        if self.warnings >= MAX_WARNINGS:
            self.status = AGENT_STATUS_EXCLUDED
            self.excluded_at = utc_now().isoformat()
            return "EXCLU"

        return f"AVERTISSEMENT_{self.warnings}/{MAX_WARNINGS}"

    def log_decision(self, decision: dict) -> None:
        """Enregistre une décision dans l'historique auditable."""
        decision["timestamp"] = utc_now().isoformat()
        self.decisions_log.append(decision)

    def is_active(self) -> bool:
        return self.status == AGENT_STATUS_ACTIVE

    def is_excluded(self) -> bool:
        return self.status == AGENT_STATUS_EXCLUDED

    def is_candidate(self) -> bool:
        return self.status == AGENT_STATUS_CANDIDATE

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "status": self.status,
            "warnings": self.warnings,
            "warning_reasons": self.warning_reasons,
            "interview_passed": self.interview_passed,
            "interview_score": self.interview_score,
            "mode": self.mode,
            "decisions_log": self.decisions_log,
            "created_at": self.created_at,
            "excluded_at": self.excluded_at,
            "verbal_discipline_score": self.verbal_discipline_score,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Agent":
        agent = cls.__new__(cls)
        for key, value in data.items():
            setattr(agent, key, value)
        return agent

    def __repr__(self) -> str:
        return (
            f"Agent(id={self.id}, name={self.name}, role={self.role}, "
            f"status={self.status}, warnings={self.warnings}/{MAX_WARNINGS})"
        )


class AgentRegistry:
    """
    Registre centralisé des agents Alpha avec persistance JSON.
    Lazy loading : charge un index léger au démarrage, instancie les Agent à la demande.
    Cache LRU : max AGENT_CACHE_MAX_SIZE agents en mémoire.
    """

    def __init__(self):
        self._index: dict[str, dict] = {}  # id → {status, role, name}
        self._cache: OrderedDict[str, Agent] = OrderedDict()
        self._audit_callback = None  # Posé par ManagerAlpha
        self._load_index()

    def add(self, agent: Agent) -> str:
        """Ajoute un agent au registre."""
        self._index[agent.id] = {
            "status": agent.status,
            "role": agent.role,
            "name": agent.name,
        }
        self._cache_put(agent.id, agent)
        self._save()
        return agent.id

    def get(self, agent_id: str) -> Agent | None:
        """Retourne un agent par ID. Cache LRU avec chargement paresseux."""
        if agent_id not in self._index:
            return None

        # Cache hit
        if agent_id in self._cache:
            self._cache.move_to_end(agent_id)
            return self._cache[agent_id]

        # Cache miss — chargement depuis le disque
        agent = self._load_single(agent_id)
        if agent is not None:
            self._cache_put(agent_id, agent)
        return agent

    def remove(self, agent_id: str) -> bool:
        if agent_id in self._index:
            del self._index[agent_id]
            self._cache.pop(agent_id, None)
            self._save()
            return True
        return False

    def list_all(self) -> list[Agent]:
        """Charge et retourne tous les agents."""
        return [self.get(aid) for aid in list(self._index.keys())]

    def list_by_status(self, status: str) -> list[Agent]:
        """Filtre sur l'index d'abord, puis charge uniquement les matchants."""
        matching_ids = [
            aid for aid, info in self._index.items()
            if info["status"] == status
        ]
        return [self.get(aid) for aid in matching_ids]

    def list_active(self) -> list[Agent]:
        return self.list_by_status(AGENT_STATUS_ACTIVE)

    def list_candidates(self) -> list[Agent]:
        return self.list_by_status(AGENT_STATUS_CANDIDATE)

    def list_excluded(self) -> list[Agent]:
        return self.list_by_status(AGENT_STATUS_EXCLUDED)

    def list_by_role(self, role: str) -> list[Agent]:
        matching_ids = [
            aid for aid, info in self._index.items()
            if info["role"] == role
        ]
        return [self.get(aid) for aid in matching_ids]

    def _cache_put(self, agent_id: str, agent: Agent) -> None:
        """Insère un agent dans le cache LRU avec éviction si nécessaire."""
        if agent_id in self._cache:
            self._cache.move_to_end(agent_id)
        self._cache[agent_id] = agent
        while len(self._cache) > AGENT_CACHE_MAX_SIZE:
            self._cache.popitem(last=False)

    def _load_single(self, agent_id: str) -> Agent | None:
        """Charge un seul agent depuis le fichier JSON."""
        if not os.path.exists(AGENTS_FILE):
            return None
        with open(AGENTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        agent_data = data.get(agent_id)
        if agent_data is None:
            return None
        return Agent.from_dict(agent_data)

    def _save(self) -> None:
        """Sauvegarde : lit le JSON existant, overlay les agents cachés, écrit."""
        os.makedirs(os.path.dirname(AGENTS_FILE) or ".", exist_ok=True)

        # Charger les données existantes du disque
        existing = {}
        if os.path.exists(AGENTS_FILE):
            with open(AGENTS_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)

        # Overlay les agents du cache (potentiellement mutés)
        for aid, agent in self._cache.items():
            existing[aid] = agent.to_dict()

        # Supprimer les agents qui ne sont plus dans l'index
        data = {aid: d for aid, d in existing.items() if aid in self._index}

        with open(AGENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Rafraîchir l'index depuis les données sauvegardées
        self._refresh_index(data)

    def _load_index(self) -> None:
        """Charge l'index léger depuis le fichier JSON (pas d'objets Agent)."""
        if os.path.exists(AGENTS_FILE):
            with open(AGENTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for aid, agent_data in data.items():
                self._index[aid] = {
                    "status": agent_data.get("status", ""),
                    "role": agent_data.get("role", ""),
                    "name": agent_data.get("name", ""),
                }

    def _refresh_index(self, data: dict) -> None:
        """Met à jour l'index depuis les données sauvegardées."""
        self._index.clear()
        for aid, agent_data in data.items():
            self._index[aid] = {
                "status": agent_data.get("status", ""),
                "role": agent_data.get("role", ""),
                "name": agent_data.get("name", ""),
            }
