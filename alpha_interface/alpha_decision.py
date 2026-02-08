"""
ALPHA DECISION BUILDER -- Produit un AlphaDecision conforme au schema.
Chaque decision validee dans submit_signal() est automatiquement convertie.
Ce format est la SEULE sortie autorisee d'Alpha vers l'exterieur.
"""

import re
import sys
import os
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import utc_now


# =========================================================================
# REGLES ET PATTERNS D'ERREUR
# =========================================================================
ALL_RULE_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

RULE_ERROR_PATTERNS = {
    2: [r"[Rr].gle 2", r"[Dd]ominance", r"aucun chiffre ne domine"],
    4: [r"edge_net.*inf.rieur", r"edge_net.*minimum", r"edge_net doit .tre num.rique"],
    5: [r"[Rr].gle 5", r"time_to_resolution.*d.passe", r"SUSPECT"],
    7: [r"[Rr].gle 7", r"[Ll]angage flou"],
    8: [r"[Cc]hamp obligatoire manquant", r"[Cc]hamp.*vide"],
}


class AlphaDecisionBuilder:
    """Construit un AlphaDecision conforme au schema a partir des resultats de validation."""

    SCHEMA_VERSION = "1.0.0"

    def __init__(
        self,
        signal_data: dict,
        validation: dict,
        clarity_score: float,
        kpi_blocked: bool,
    ):
        self.signal_data = signal_data
        self.validation = validation
        self.clarity_score = clarity_score
        self.kpi_blocked = kpi_blocked
        self._timestamp = utc_now()

    def build(self) -> dict:
        """Produit le dict AlphaDecision conforme au schema."""
        rules_failed = self._extract_rules_failed()
        rules_passed = self._compute_rules_passed(rules_failed)

        return {
            "decision_id": self._generate_decision_id(),
            "market": self.signal_data.get("market", "UNKNOWN"),
            "status": self._determine_status(),
            "confidence_level": self._compute_confidence_level(),
            "edge_net": self._parse_edge_net(),
            "constraints": self._build_constraints(),
            "rules_passed": rules_passed,
            "rules_failed": rules_failed,
            "audit_ref": self._generate_audit_ref(),
            "schema_version": self.SCHEMA_VERSION,
            "generated_at": self._timestamp.isoformat(),
        }

    def _generate_decision_id(self) -> str:
        signal_id = self.signal_data.get("signal_id", "UNKNOWN")
        ts = self._timestamp.strftime("%Y%m%d%H%M%S")
        return f"AD-{signal_id}-{ts}"

    def _determine_status(self) -> str:
        if not self.validation.get("valid", False):
            return "REJECTED"
        return self.validation.get("status", "REJECTED")

    def _compute_confidence_level(self) -> str:
        if self.clarity_score >= 80:
            return "HIGH"
        elif self.clarity_score >= 50:
            return "MEDIUM"
        return "LOW"

    def _parse_edge_net(self) -> float:
        try:
            return float(self.signal_data.get("edge_net", 0))
        except (ValueError, TypeError):
            return 0.0

    def _build_constraints(self) -> dict:
        max_size = self._parse_float("volume", 0.0)
        ttr = self._parse_float("time_to_resolution", 0.0)

        if ttr <= 6:
            urgency = "CRITICAL"
        elif ttr <= 24:
            urgency = "HIGH"
        elif ttr <= 48:
            urgency = "MEDIUM"
        else:
            urgency = "LOW"

        expiry = (self._timestamp + timedelta(hours=ttr)).isoformat()

        return {
            "max_size": max_size,
            "urgency": urgency,
            "expiry": expiry,
        }

    def _extract_rules_failed(self) -> list[int]:
        errors = self.validation.get("errors", [])
        failed = set()

        for error in errors:
            for rule_num, patterns in RULE_ERROR_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, error, re.IGNORECASE):
                        failed.add(rule_num)
                        break

        if self.kpi_blocked:
            failed.add(6)

        return sorted(failed)

    def _compute_rules_passed(self, rules_failed: list[int]) -> list[int]:
        return sorted(r for r in ALL_RULE_NUMBERS if r not in rules_failed)

    def _generate_audit_ref(self) -> str:
        signal_id = self.signal_data.get("signal_id", "UNKNOWN")
        return f"[{self._timestamp.isoformat()}]-{signal_id}"

    def _parse_float(self, field: str, default: float) -> float:
        try:
            return float(self.signal_data.get(field, default))
        except (ValueError, TypeError):
            return default


def validate_against_schema(decision: dict) -> dict:
    """
    Valide un AlphaDecision contre le schema.
    Retourne {"valid": bool, "errors": list[str]}.
    Validation structurelle sans dependance externe.
    """
    errors = []
    required_fields = [
        "decision_id", "market", "status", "confidence_level",
        "edge_net", "constraints", "rules_passed", "rules_failed", "audit_ref",
    ]

    for field in required_fields:
        if field not in decision:
            errors.append(f"Champ requis manquant: '{field}'")

    status = decision.get("status")
    if status not in ("REJECTED", "SURVEILLANCE", "APPROVED"):
        errors.append(f"Statut invalide: '{status}'")

    confidence = decision.get("confidence_level")
    if confidence not in ("LOW", "MEDIUM", "HIGH"):
        errors.append(f"Niveau de confiance invalide: '{confidence}'")

    if not isinstance(decision.get("edge_net"), (int, float)):
        errors.append("edge_net doit etre numerique")

    constraints = decision.get("constraints", {})
    for cf in ("max_size", "urgency", "expiry"):
        if cf not in constraints:
            errors.append(f"Contrainte manquante: '{cf}'")

    urgency = constraints.get("urgency")
    if urgency not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
        errors.append(f"Urgence invalide: '{urgency}'")

    if not isinstance(decision.get("rules_passed"), list):
        errors.append("rules_passed doit etre une liste")

    if not isinstance(decision.get("rules_failed"), list):
        errors.append("rules_failed doit etre une liste")

    did = decision.get("decision_id", "")
    if not isinstance(did, str) or not did.startswith("AD-"):
        errors.append("decision_id doit commencer par 'AD-'")

    return {"valid": len(errors) == 0, "errors": errors}
