"""
AUDIT SYSTEM — Autorité supérieure au Manager.
Journal append-only, horodatage obligatoire, non modifiable.
"""

import functools
import os
from datetime import datetime

from config import (
    AUDIT_LOG_FILE,
    AUDITABLE_ACTIONS,
    BYPASS_ALLOWED_ACTIONS,
    BYPASS_FORBIDDEN_ACTIONS,
    FORBIDDEN_WORDS_ALL,
    FORBIDDEN_WORDS_LLM,
    GOLDEN_RULES,
    LOGS_DIR,
    MAX_WARNINGS,
)


class AuditViolation(Exception):
    """Exception levée quand l'audit bloque une action."""
    pass


class AuditSystem:
    """
    Système d'audit avec autorité supérieure au Manager.
    - Journal append-only
    - Horodatage obligatoire
    - Non modifiable par le Manager
    - Peut bloquer toute action
    """

    def __init__(self):
        os.makedirs(LOGS_DIR, exist_ok=True)
        self._log_file = AUDIT_LOG_FILE
        self._ensure_log_exists()

    def _ensure_log_exists(self) -> None:
        if not os.path.exists(self._log_file):
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().isoformat()}] AUDIT SYSTEM INITIALIZED\n")

    # =========================================================================
    # JOURNAL APPEND-ONLY
    # =========================================================================
    def log(self, action: str, actor: str, details: str, result: str) -> None:
        """
        Écrit une entrée dans le journal d'audit. Append-only.
        Aucune méthode delete/edit n'existe dans cette classe.
        """
        timestamp = datetime.now().isoformat()
        entry = (
            f"[{timestamp}] ACTION={action} | ACTOR={actor} | "
            f"DETAILS={details} | RESULT={result}\n"
        )
        with open(self._log_file, "a", encoding="utf-8") as f:
            f.write(entry)

    # =========================================================================
    # AUTORISATION — Appelé AVANT toute action du Manager
    # =========================================================================
    def authorize(self, action: str, actor: str, context: dict | None = None) -> bool:
        """
        Autorise ou bloque une action AVANT son exécution.
        Le Manager ne peut PAS contourner cette vérification.
        """
        context = context or {}
        bypass_mode = context.get("bypass_mode", False)

        # En mode bypass, seules les actions de consultation sont autorisées
        if bypass_mode:
            if action in BYPASS_FORBIDDEN_ACTIONS:
                self.log(
                    action, actor,
                    f"BLOQUÉ — bypass_mode interdit l'action '{action}'",
                    "DENIED"
                )
                raise AuditViolation(
                    f"Action '{action}' interdite en mode bypass. "
                    f"Actions autorisées : {BYPASS_ALLOWED_ACTIONS}"
                )
            if action not in BYPASS_ALLOWED_ACTIONS:
                self.log(
                    action, actor,
                    f"BLOQUÉ — action '{action}' non autorisée en bypass",
                    "DENIED"
                )
                raise AuditViolation(
                    f"Action '{action}' non reconnue en mode bypass."
                )

        # Vérification que l'action est connue
        if action in AUDITABLE_ACTIONS:
            self.log(action, actor, str(context), "AUTHORIZED")

        return True

    def authorize_signal_approval(self, kpi_data: dict) -> bool:
        """
        Vérifie si de nouvelles approbations sont autorisées.
        Si signals_approved_pct > 5% → BLOCAGE.
        """
        approval_pct = kpi_data.get("signals_approved_pct", 0.0)
        if approval_pct > 5.0:
            self.log(
                "approve_signal", "SYSTEM",
                f"BLOCAGE AUTOMATIQUE — Taux approbation {approval_pct:.1f}% > 5%",
                "BLOCKED"
            )
            raise AuditViolation(
                f"BLOCAGE AUTOMATIQUE — Taux d'approbation ({approval_pct:.1f}%) "
                f"dépasse le seuil de 5%. Revue manuelle obligatoire."
            )
        return True

    # =========================================================================
    # VÉRIFICATION DU LANGAGE
    # =========================================================================
    def check_language(self, text: str, is_llm: bool = False) -> dict:
        """
        Détecte le langage flou. Règle 7.
        Retourne dict avec 'clean' (bool), 'violations' (list).
        """
        text_lower = text.lower()
        forbidden = FORBIDDEN_WORDS_LLM if is_llm else FORBIDDEN_WORDS_ALL
        violations = []

        for word in forbidden:
            if word.lower() in text_lower:
                violations.append(word)

        result = {
            "clean": len(violations) == 0,
            "violations": violations,
            "text_length": len(text),
            "violation_count": len(violations),
        }

        if violations:
            self.log(
                "check_language", "AUDIT",
                f"Violations détectées : {violations}",
                "FAILED"
            )

        return result

    # =========================================================================
    # VÉRIFICATION DE CONFORMITÉ AUX RÈGLES
    # =========================================================================
    def check_rule_compliance(self, decision: dict) -> dict:
        """
        Vérifie qu'une décision respecte les 10 Règles d'Or.
        Retourne dict avec 'compliant' (bool), 'violations' (list).
        """
        violations = []

        # Règle 1 : Alpha ne trade jamais
        if decision.get("action") == "execute_trade":
            violations.append("Règle 1 violée : Alpha ne trade jamais")

        # Règle 3 : Marché tradable != signal
        if decision.get("type") == "market_tradable_as_signal":
            violations.append("Règle 3 violée : Un marché tradable n'est pas un signal")

        # Règle 4 : Edge brut au lieu d'edge net
        if decision.get("edge_type") == "brut":
            violations.append("Règle 4 violée : Seul l'edge net est considéré")

        # Règle 7 : Langage flou dans la justification
        justification = decision.get("justification", "")
        if justification:
            lang_check = self.check_language(justification)
            if not lang_check["clean"]:
                violations.append(
                    f"Règle 7 violée : Langage flou dans la justification — {lang_check['violations']}"
                )

        # Règle 8 : Décision non formalisée
        if not decision.get("written", True):
            violations.append("Règle 8 violée : Décision non formalisée par écrit")

        # Règle 9 : Forcer un trade
        if decision.get("forced_trade", False):
            violations.append("Règle 9 violée : Tentative de forcer un trade")

        result = {
            "compliant": len(violations) == 0,
            "violations": violations,
            "rules_checked": len(GOLDEN_RULES),
        }

        if violations:
            self.log(
                "check_rule_compliance", "AUDIT",
                f"Violations : {violations}",
                "NON_COMPLIANT"
            )

        return result

    # =========================================================================
    # AUDIT D'UNE DÉCISION
    # =========================================================================
    def audit_decision(self, agent_id: str, decision: dict) -> dict:
        """
        Audit complet d'une décision d'agent.
        Vérifie : règles, justification, langage.
        Retourne un score et les violations.
        """
        score = 100
        all_violations = []

        # 1. Conformité aux règles
        rule_check = self.check_rule_compliance(decision)
        if not rule_check["compliant"]:
            score -= 30 * len(rule_check["violations"])
            all_violations.extend(rule_check["violations"])

        # 2. Qualité de justification
        justification = decision.get("justification", "")
        if not justification:
            score -= 20
            all_violations.append("Absence de justification")
        elif len(justification) < 20:
            score -= 10
            all_violations.append("Justification trop courte")

        # 3. Discipline du langage
        if justification:
            is_llm = decision.get("agent_mode") == "llm"
            lang_check = self.check_language(justification, is_llm=is_llm)
            if not lang_check["clean"]:
                score -= 15 * lang_check["violation_count"]
                all_violations.append(
                    f"Langage flou ({lang_check['violation_count']} violations)"
                )

        score = max(0, score)
        result = {
            "agent_id": agent_id,
            "score": score,
            "violations": all_violations,
            "passed": score >= 60,
            "timestamp": datetime.now().isoformat(),
        }

        self.log(
            "audit_decision", agent_id,
            f"Score={score}, Violations={len(all_violations)}",
            "PASS" if result["passed"] else "FAIL"
        )

        return result

    # =========================================================================
    # AVERTISSEMENT
    # =========================================================================
    def issue_warning(self, agent, reason: str) -> dict:
        """Émet un avertissement formel. Délègue à l'agent."""
        result = agent.add_warning(reason)
        self.log(
            "issue_warning", agent.id,
            f"Raison: {reason} | Résultat: {result}",
            result
        )
        return {
            "agent_id": agent.id,
            "warning_result": result,
            "total_warnings": agent.warnings,
            "max_warnings": MAX_WARNINGS,
            "reason": reason,
        }

    # =========================================================================
    # REVUE COMPLÈTE
    # =========================================================================
    def review_agent_history(self, agent) -> dict:
        """Revue complète de l'historique d'un agent."""
        total_decisions = len(agent.decisions_log)
        failed_audits = 0
        all_violations = []

        for decision in agent.decisions_log:
            audit = self.audit_decision(agent.id, decision)
            if not audit["passed"]:
                failed_audits += 1
                all_violations.extend(audit["violations"])

        result = {
            "agent_id": agent.id,
            "agent_name": agent.name,
            "total_decisions": total_decisions,
            "failed_audits": failed_audits,
            "failure_rate": (failed_audits / total_decisions * 100) if total_decisions > 0 else 0,
            "all_violations": all_violations,
            "warnings": agent.warnings,
            "status": agent.status,
            "recommendation": "EXCLUSION" if failed_audits > total_decisions * 0.3 else "OK",
        }

        self.log(
            "review_agent_history", agent.id,
            f"Décisions={total_decisions}, Échecs={failed_audits}",
            result["recommendation"]
        )

        return result

    # =========================================================================
    # DÉTECTION DE DÉVIATION
    # =========================================================================
    def detect_deviation(self, action: str, context: dict) -> dict | None:
        """
        Détecte les tentatives de déviation :
        - Forcer un trade
        - Minimiser un risque
        - Contourner un seuil
        """
        deviations = []

        if context.get("force_trade"):
            deviations.append("Tentative de forcer un trade")

        if context.get("minimize_risk"):
            deviations.append("Tentative de minimiser un risque")

        if context.get("bypass_threshold"):
            deviations.append("Tentative de contourner un seuil")

        if context.get("override_rejection"):
            deviations.append("Tentative de renverser un rejet")

        if deviations:
            self.log(
                "detect_deviation", context.get("actor", "UNKNOWN"),
                f"Déviations : {deviations}",
                "BLOCKED"
            )
            return {
                "blocked": True,
                "deviations": deviations,
                "action_required": "Blocage immédiat + Revue complète des décisions passées",
            }

        return None

    # =========================================================================
    # LECTURE DU JOURNAL (consultation uniquement)
    # =========================================================================
    def read_log(self, last_n: int = 50) -> list[str]:
        """Lit les N dernières entrées du journal. Lecture seule."""
        if not os.path.exists(self._log_file):
            return []
        with open(self._log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return lines[-last_n:]


def audit_required(action_name: str):
    """
    Décorateur — Impose l'autorisation de l'audit AVANT toute action critique.
    Le Manager ne peut PAS contourner ce décorateur.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            audit = getattr(self, "audit", None)
            if audit is None:
                raise AuditViolation(
                    "AuditSystem non initialisé. Aucune action autorisée sans audit."
                )

            context = kwargs.get("context", {})
            actor = "ManagerAlpha"

            # L'audit autorise ou lève AuditViolation
            audit.authorize(action_name, actor, context)

            # Détection de déviation
            deviation = audit.detect_deviation(action_name, context)
            if deviation:
                raise AuditViolation(
                    f"DÉVIATION DÉTECTÉE : {deviation['deviations']}. "
                    f"Action requise : {deviation['action_required']}"
                )

            return func(self, *args, **kwargs)
        return wrapper
    return decorator
