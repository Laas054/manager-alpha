"""
AGENT ALPHA — Gestion des agents et registre.
Séparation stricte Candidate / Agent actif / Exclu.
"""

import json
import os
import uuid
from datetime import datetime

from config import (
    AGENT_STATUS_ACTIVE,
    AGENT_STATUS_CANDIDATE,
    AGENT_STATUS_EXCLUDED,
    AGENTS_FILE,
    ALPHA_ROLES,
    MAX_WARNINGS,
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
        self.created_at: str = datetime.now().isoformat()
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
        self.warning_reasons.append(f"[{datetime.now().isoformat()}] {reason}")

        if self.warnings >= MAX_WARNINGS:
            self.status = AGENT_STATUS_EXCLUDED
            self.excluded_at = datetime.now().isoformat()
            return "EXCLU"

        return f"AVERTISSEMENT_{self.warnings}/{MAX_WARNINGS}"

    def log_decision(self, decision: dict) -> None:
        """Enregistre une décision dans l'historique auditable."""
        decision["timestamp"] = datetime.now().isoformat()
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
    """Registre centralisé des agents Alpha avec persistance JSON."""

    def __init__(self):
        self.agents: dict[str, Agent] = {}
        self._load()

    def add(self, agent: Agent) -> str:
        """Ajoute un agent au registre."""
        self.agents[agent.id] = agent
        self._save()
        return agent.id

    def get(self, agent_id: str) -> Agent | None:
        return self.agents.get(agent_id)

    def remove(self, agent_id: str) -> bool:
        if agent_id in self.agents:
            del self.agents[agent_id]
            self._save()
            return True
        return False

    def list_all(self) -> list[Agent]:
        return list(self.agents.values())

    def list_by_status(self, status: str) -> list[Agent]:
        return [a for a in self.agents.values() if a.status == status]

    def list_active(self) -> list[Agent]:
        return self.list_by_status(AGENT_STATUS_ACTIVE)

    def list_candidates(self) -> list[Agent]:
        return self.list_by_status(AGENT_STATUS_CANDIDATE)

    def list_excluded(self) -> list[Agent]:
        return self.list_by_status(AGENT_STATUS_EXCLUDED)

    def list_by_role(self, role: str) -> list[Agent]:
        return [a for a in self.agents.values() if a.role == role]

    def _save(self) -> None:
        os.makedirs(os.path.dirname(AGENTS_FILE) or ".", exist_ok=True)
        data = {aid: agent.to_dict() for aid, agent in self.agents.items()}
        with open(AGENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load(self) -> None:
        if os.path.exists(AGENTS_FILE):
            with open(AGENTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for aid, agent_data in data.items():
                self.agents[aid] = Agent.from_dict(agent_data)
