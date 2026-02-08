"""
STRESS TEST ALPHA — Tests automatisés de robustesse.

Exécute des batteries de tests sans intervention humaine :
- Entretiens simulés (tous rôles x tous personas)
- Validation de signaux (corpus d'échecs + borderline)
- Vérification du blocage KPI
- Rapport de métriques complet
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ALPHA_ROLES, MAX_APPROVAL_PCT
from failure_corpus import (
    BORDERLINE_INTERVIEWS,
    BORDERLINE_SIGNALS,
    FAILED_INTERVIEWS,
    FAILED_SIGNALS,
    TOTAL_SCENARIOS,
)
from llm_evaluator import LLMEvaluator
from manager import ManagerAlpha
from signal_alpha import SignalAlpha
from simulated_profiles import ALL_PERSONAS, PROFILE_METADATA


class StressTestReport:
    """Collecte et formate les résultats du stress test."""

    def __init__(self):
        self.sections: list[dict] = []
        self.total_pass = 0
        self.total_fail = 0
        self.total_expected = 0
        self.kpi_checks: list[dict] = []
        self.started_at = datetime.now().isoformat()

    def add_result(self, section: str, name: str, passed: bool, expected: bool,
                   detail: str = "") -> None:
        correct = passed == expected
        self.total_expected += 1
        if correct:
            self.total_pass += 1
        else:
            self.total_fail += 1

        self.sections.append({
            "section": section,
            "name": name,
            "passed": passed,
            "expected": expected,
            "correct": correct,
            "detail": detail,
        })

    def add_kpi_check(self, name: str, value, expected, correct: bool) -> None:
        self.kpi_checks.append({
            "name": name,
            "value": value,
            "expected": expected,
            "correct": correct,
        })
        self.total_expected += 1
        if correct:
            self.total_pass += 1
        else:
            self.total_fail += 1

    def format(self) -> str:
        lines = [
            "",
            "=" * 70,
            "  RAPPORT DE STRESS TEST — MANAGER IA ALPHA",
            "=" * 70,
            f"  Date : {self.started_at}",
            f"  Scénarios du corpus : {TOTAL_SCENARIOS}",
            f"  Vérifications totales : {self.total_expected}",
            f"  Conformes : {self.total_pass}",
            f"  Non conformes : {self.total_fail}",
            f"  Taux de conformité : {self._pct(self.total_pass, self.total_expected)}%",
            "",
        ]

        # Grouper par section
        current_section = None
        for r in self.sections:
            if r["section"] != current_section:
                current_section = r["section"]
                lines.append(f"--- {current_section} ---")

            status = "OK" if r["correct"] else "ECHEC"
            marker = "  " if r["correct"] else ">>"
            lines.append(
                f"  {marker}[{status}] {r['name']} "
                f"(résultat={'PASS' if r['passed'] else 'FAIL'}, "
                f"attendu={'PASS' if r['expected'] else 'FAIL'})"
            )
            if r["detail"] and not r["correct"]:
                lines.append(f"         Détail: {r['detail'][:120]}")

        if self.kpi_checks:
            lines.append("")
            lines.append("--- KPI CHECKS ---")
            for k in self.kpi_checks:
                status = "OK" if k["correct"] else "ECHEC"
                lines.append(
                    f"  [{status}] {k['name']} = {k['value']} (attendu: {k['expected']})"
                )

        lines.extend([
            "",
            "=" * 70,
            f"  RÉSULTAT FINAL : {'CONFORME' if self.total_fail == 0 else 'NON CONFORME'}",
            f"  {self.total_pass}/{self.total_expected} vérifications correctes",
            "=" * 70,
            "",
        ])

        return "\n".join(lines)

    @staticmethod
    def _pct(num: int, total: int) -> str:
        if total == 0:
            return "0.0"
        return f"{(num / total) * 100:.1f}"


def run_stress_test(verbose: bool = False, callback=None) -> StressTestReport:
    """
    Exécute le stress test complet.

    Args:
        verbose: Afficher les détails en temps réel
        callback: Fonction appelée après chaque vérification
                  callback(section, name, correct)
    """
    report = StressTestReport()

    def _log(section, name, correct):
        if verbose:
            marker = "[OK]" if correct else "[!!]"
            print(f"  {marker} {section} > {name}")
        if callback:
            callback(section, name, correct)

    # =================================================================
    # 1. BATTERIE D'ENTRETIENS SIMULÉS
    # =================================================================
    section = "ENTRETIENS SIMULÉS (rôles x personas)"
    for persona in ALL_PERSONAS:
        meta = PROFILE_METADATA.get(persona, {})
        should_pass = meta.get("expected_pass_rate", 0) >= 50

        for role in ALPHA_ROLES:
            name = f"{role}/{persona}"
            evaluator = LLMEvaluator()
            result = evaluator.run_simulated_interview(role=role, persona=persona)
            passed = result.get("passed", False)

            detail = ""
            if result.get("eliminated_at"):
                detail = f"Éliminé à {result['eliminated_at']}"
            elif result.get("score"):
                detail = f"Score: {result['score']}%"

            report.add_result(section, name, passed, should_pass, detail)
            _log(section, name, passed == should_pass)

    # =================================================================
    # 2. SIGNAUX INVALIDES (doivent tous être rejetés)
    # =================================================================
    section = "SIGNAUX INVALIDES (corpus d'échecs)"
    for scenario in FAILED_SIGNALS:
        name = scenario["tag"]
        signal = SignalAlpha(scenario["signal"])
        result = signal.validate()
        rejected = not result["valid"]

        detail = ""
        if result.get("errors"):
            detail = result["errors"][0][:100]

        report.add_result(section, name, rejected, True, detail)
        _log(section, name, rejected)

    # =================================================================
    # 3. SIGNAUX BORDERLINE
    # =================================================================
    section = "SIGNAUX BORDERLINE"
    for scenario in BORDERLINE_SIGNALS:
        name = scenario["tag"]
        expected_valid = scenario["expected_valid"]
        signal = SignalAlpha(scenario["signal"])
        result = signal.validate()
        is_valid = result["valid"]

        detail = ""
        if result.get("errors"):
            detail = result["errors"][0][:100]

        report.add_result(section, name, is_valid, expected_valid, detail)
        _log(section, name, is_valid == expected_valid)

    # =================================================================
    # 4. ENTRETIENS ÉCHOUÉS (corpus — doivent tous être rejetés)
    # =================================================================
    section = "ENTRETIENS ÉCHOUÉS (corpus)"
    for scenario in FAILED_INTERVIEWS:
        name = scenario["tag"]
        evaluator = LLMEvaluator()
        result = evaluator.run_full_evaluation(scenario["responses"])
        rejected = not result.get("passed", True)

        detail = result.get("reason", "")

        report.add_result(section, name, rejected, True, detail)
        _log(section, name, rejected)

    # =================================================================
    # 5. ENTRETIENS BORDERLINE
    # =================================================================
    section = "ENTRETIENS BORDERLINE"
    for scenario in BORDERLINE_INTERVIEWS:
        name = scenario["tag"]
        evaluator = LLMEvaluator()
        result = evaluator.run_full_evaluation(scenario["responses"])
        passed = result.get("passed", False)

        detail = f"Score: {result.get('score', 0)}%"
        # Les borderline ne sont pas attendus comme pass/fail strict,
        # on les enregistre juste pour observation
        report.add_result(section, name, passed, passed, detail)
        _log(section, name, True)  # Toujours "correct" pour les borderline

    # =================================================================
    # 6. STRESS KPI — BLOCAGE AUTOMATIQUE
    # =================================================================
    section = "STRESS KPI"

    # 6a. Créer un manager frais et pousser le taux d'approbation > 5%
    manager = ManagerAlpha()

    # Recruter un agent pour soumettre des signaux
    interview_result = manager.start_interview("StressAgent", "DataEngineer")
    agent_id = interview_result.get("agent_id", "")

    stress_answers = [
        "Un marché tradable est une autorisation d'analyse. Un signal Alpha est une autorisation de trade.",
        "L'edge brut ne suffit pas. Seul l'edge net après déduction du coût du spread et de la marge est considéré. Le risque est séparé.",
        "Le temps est le risque le plus sous-estimé. Un edge tardif est suspect. La résolution proche rend le signal fragile.",
        "Autoriser un mauvais trade est la faute la plus grave.",
        "Non, rejet immédiat. La discipline prime sur l'intelligence.",
        "Non. Aucun chiffre ne domine les autres. L'edge seul ne suffit pas. L'analyse complète est requise incluant risque et temps.",
        "Rejet immédiat. Les ressentis sont interdit en Alpha. Toute décision doit être basée uniquement sur des faits mesurables.",
    ]
    for answer in stress_answers:
        r = manager.answer_interview(agent_id, answer)
        if r.get("status") == "ELIMINATED":
            break

    # Vérifier que l'agent est actif
    agents_active = manager.list_agents(status="active")
    agent_active = len(agents_active) > 0
    report.add_kpi_check(
        "Agent StressAgent recruté et actif",
        agent_active, True, agent_active
    )
    _log(section, "Agent StressAgent recruté", agent_active)

    if agent_active:
        active_id = agents_active[0]["id"]

        # Soumettre des signaux pour stresser les KPIs
        _valid_signal_base = {
            "market": "ETH-PERP",
            "type": "ARBITRAGE",
            "edge_net": "2.5",
            "volume": "500000",
            "spread": "0.05",
            "time_to_resolution": "12",
            "risks": "Risque de liquidité modéré. Exposition contrôlée à 1%.",
            "status": "APPROVED",
            "comment": "Edge net confirmé. Volume suffisant. Spread faible. Temps court. Risque contrôlé.",
        }

        _rejected_signal_base = {
            "market": "BTC-PERP",
            "type": "PROBA",
            "edge_net": "0.1",
            "volume": "1000",
            "spread": "0.5",
            "time_to_resolution": "80",
            "risks": "ok",
            "status": "REJECTED",
            "comment": "Signal faible.",
        }

        # Soumettre 3 signaux valides approuvés
        for i in range(3):
            sig = _valid_signal_base.copy()
            sig["signal_id"] = f"STRESS-VALID-{i+1:03d}"
            manager.submit_signal(active_id, sig)

        # Soumettre 2 signaux rejetés
        for i in range(2):
            sig = _rejected_signal_base.copy()
            sig["signal_id"] = f"STRESS-REJ-{i+1:03d}"
            manager.submit_signal(active_id, sig)

        # 3/5 = 60% > 5% -> doit être bloqué
        kpi_blocked = manager.kpi.is_approval_blocked()
        report.add_kpi_check(
            f"KPI bloqué après 3/5 approuvés (60% > {MAX_APPROVAL_PCT}%)",
            kpi_blocked, True, kpi_blocked
        )
        _log(section, "KPI blocage automatique", kpi_blocked)

        # Tenter de soumettre un signal approuvé pendant le blocage
        blocked_sig = _valid_signal_base.copy()
        blocked_sig["signal_id"] = "STRESS-BLOCKED-001"
        blocked_result = manager.submit_signal(active_id, blocked_sig)
        blocked_rejected = not blocked_result.get("validation", {}).get("valid", True)
        report.add_kpi_check(
            "Signal APPROVED rejeté pendant blocage KPI",
            blocked_rejected, True, blocked_rejected
        )
        _log(section, "Signal bloqué par KPI", blocked_rejected)

        # Débloquer manuellement
        unblock = manager.manual_unblock_approvals("StressReviewer", "Revue stress-test")
        unblocked = unblock.get("status") == "UNBLOCKED"
        report.add_kpi_check(
            "Déblocage manuel réussi",
            unblocked, True, unblocked
        )
        _log(section, "Déblocage manuel", unblocked)

        # Après déblocage, les signaux passent à nouveau
        post_unblock = not manager.kpi.is_approval_blocked()
        report.add_kpi_check(
            "KPI débloqué après revue",
            post_unblock, True, post_unblock
        )
        _log(section, "KPI débloqué", post_unblock)

    # =================================================================
    # 7. STRESS AVERTISSEMENTS — 3 = EXCLUSION
    # =================================================================
    section = "STRESS AVERTISSEMENTS"

    if agent_active:
        # Émettre 3 avertissements -> exclusion
        for i in range(3):
            manager.warn_agent(active_id, f"Stress test warning {i+1}")

        agent_data = manager.list_agents()
        stress_agent = next((a for a in agent_data if a["id"] == active_id), None)
        excluded = stress_agent and stress_agent["status"] == "excluded"
        report.add_kpi_check(
            "Agent exclu après 3 avertissements",
            excluded, True, bool(excluded)
        )
        _log(section, "3 warnings -> exclusion", bool(excluded))

    # =================================================================
    # 8. ENTRETIEN SIMULÉ VIA MANAGER (intégration)
    # =================================================================
    section = "INTÉGRATION MANAGER SIMULÉ"

    for cleanup_f in ["data/agents.json", "logs/audit.log"]:
        if os.path.exists(cleanup_f):
            os.remove(cleanup_f)
    mgr2 = ManagerAlpha()

    # Disciplined doit passer
    disc_result = mgr2.evaluate_llm_agent_simulated(
        "SimDisc", "Validation", persona="disciplined"
    )
    disc_pass = disc_result.get("recruited", False)
    report.add_result(section, "Simulated/disciplined recruté", disc_pass, True,
                      f"Score: {disc_result.get('result', {}).get('score', 0)}%")
    _log(section, "Simulated/disciplined", disc_pass)

    # Naive doit échouer
    naive_result = mgr2.evaluate_llm_agent_simulated(
        "SimNaive", "DataEngineer", persona="naive"
    )
    naive_fail = not naive_result.get("recruited", True)
    report.add_result(section, "Simulated/naive rejeté", naive_fail, True,
                      f"Score: {naive_result.get('result', {}).get('score', 0)}%")
    _log(section, "Simulated/naive rejeté", naive_fail)

    # Overconfident doit échouer (pousse les limites)
    over_result = mgr2.evaluate_llm_agent_simulated(
        "SimOver", "AlphaResearch", persona="overconfident"
    )
    # L'overconfident devrait échouer au LLM (score < 90% ou élimination)
    over_fail = not over_result.get("recruited", True)
    report.add_result(section, "Simulated/overconfident rejeté", over_fail, True,
                      f"Score: {over_result.get('result', {}).get('score', 0)}%")
    _log(section, "Simulated/overconfident rejeté", over_fail)

    return report


# =============================================================================
# EXÉCUTION DIRECTE
# =============================================================================
if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    print("\n  Lancement du STRESS TEST Alpha...")
    print(f"  Scénarios : {TOTAL_SCENARIOS}")
    print(f"  Personas : {', '.join(ALL_PERSONAS)}")
    print(f"  Rôles : {', '.join(ALPHA_ROLES)}")
    print()

    report = run_stress_test(verbose=verbose)
    print(report.format())

    sys.exit(0 if report.total_fail == 0 else 1)
