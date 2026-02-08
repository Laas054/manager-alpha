"""
MANAGER IA ALPHA — Interface CLI interactive.
Point d'entrée principal du système Alpha.
"""

import json
import os
import sys

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audit import AuditViolation
from config import (
    ALPHA_LAW,
    ALPHA_ROLES,
    GOLDEN_RULES,
    SIGNAL_REQUIRED_FIELDS,
    SIGNAL_STATUSES,
    SIGNAL_TYPES,
)
from manager import ManagerAlpha


# =============================================================================
# COULEURS TERMINAL (sans dépendance externe)
# =============================================================================
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"

    @staticmethod
    def disable():
        Colors.HEADER = ""
        Colors.BLUE = ""
        Colors.GREEN = ""
        Colors.YELLOW = ""
        Colors.RED = ""
        Colors.BOLD = ""
        Colors.UNDERLINE = ""
        Colors.END = ""


# Désactiver les couleurs si pas de support terminal
if not sys.stdout.isatty():
    Colors.disable()


def print_header(text: str) -> None:
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}  {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.END}\n")


def print_success(text: str) -> None:
    print(f"{Colors.GREEN}[OK] {text}{Colors.END}")


def print_error(text: str) -> None:
    print(f"{Colors.RED}[ERREUR] {text}{Colors.END}")


def print_warning(text: str) -> None:
    print(f"{Colors.YELLOW}[ALERTE] {text}{Colors.END}")


def print_info(text: str) -> None:
    print(f"{Colors.BLUE}[INFO] {text}{Colors.END}")


def safe_input(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\n")
        return ""


# =============================================================================
# MENU PRINCIPAL
# =============================================================================
def show_menu(bypass_mode: bool = False) -> None:
    print_header("MANAGER IA ALPHA — MENU PRINCIPAL")
    print(f"  {Colors.BOLD}Loi fondatrice :{Colors.END} {ALPHA_LAW[:80]}...")
    if bypass_mode:
        print(f"  {Colors.YELLOW}[MODE BYPASS — Consultation uniquement]{Colors.END}")
    print()
    print("  1. Recruter un agent (entretien humain)")
    print("  2. Évaluer un agent LLM")
    print("  3. Soumettre un signal Alpha")
    print("  4. Auditer un agent")
    print("  5. Voir les KPIs")
    print("  6. Lister les agents")
    print("  7. Revue complète de tous les agents")
    print("  8. Voir le journal d'audit")
    print("  9. Afficher les Règles d'Or")
    print("  10. Avertir un agent")
    print("  11. Basculer mode bypass")
    print("  12. Débloquer les approbations (revue manuelle)")
    print("  0. Quitter")
    print()


# =============================================================================
# 1. RECRUTEMENT HUMAIN
# =============================================================================
def recruit_human(manager: ManagerAlpha) -> None:
    print_header("RECRUTEMENT — ENTRETIEN HUMAIN")

    name = safe_input("Nom du candidat : ")
    if not name:
        print_error("Nom requis.")
        return

    print(f"\nRôles disponibles : {', '.join(ALPHA_ROLES)}")
    role = safe_input("Rôle : ")
    if role not in ALPHA_ROLES:
        print_error(f"Rôle invalide. Choix : {ALPHA_ROLES}")
        return

    try:
        result = manager.start_interview(name, role)
    except AuditViolation as e:
        print_error(f"Audit bloque le recrutement : {e}")
        return

    if "error" in result:
        print_error(result["error"])
        return

    agent_id = result["agent_id"]
    print_success(f"Entretien démarré pour {name} (ID: {agent_id})")
    print_info(f"Questions restantes : {result['questions_remaining']}")

    # Boucle d'entretien
    while True:
        question = result.get("question") or result.get("next_question")
        if question is None:
            break

        print(f"\n{Colors.BOLD}[{question['id']}] {question['question']}{Colors.END}")
        if question.get("max_sentences"):
            print(f"  (Maximum {question['max_sentences']} phrases)")

        answer = safe_input("\nRéponse : ")
        if not answer:
            print_error("Réponse vide — ÉLIMINÉ")
            break

        result = manager.answer_interview(agent_id, answer)

        if result.get("status") == "ELIMINATED":
            print_error("ÉLIMINÉ — Critère éliminatoire déclenché.")
            for reason in result.get("result", {}).get("reasons", []):
                print(f"  >> {reason}")
            return

        if result.get("status") == "INTERVIEW_COMPLETE":
            final = result.get("final_result", {})
            if result.get("recruited"):
                print_success(
                    f"RECRUTÉ — Score : {final.get('score', 0)}% — "
                    f"Agent {name} est maintenant ACTIF."
                )
            else:
                print_error(
                    f"REJETÉ — Score : {final.get('score', 0)}% — "
                    f"Seuil non atteint."
                )
            return

        if result.get("status") == "NEXT_QUESTION":
            r = result.get("result", {})
            if r.get("passed"):
                print_success(f"Question passée — Score: {r.get('score', 0)}%")
            else:
                print_warning(f"Score faible : {r.get('score', 0)}%")
                for reason in r.get("reasons", []):
                    print(f"  >> {reason}")


# =============================================================================
# 2. ÉVALUATION LLM (ANTHROPIC CLAUDE — LIVE)
# =============================================================================

AVAILABLE_MODELS = {
    "1": ("claude-haiku-4-5-20251001", "Haiku 4.5 (rapide, economique)"),
    "2": ("claude-sonnet-4-5-20250929", "Sonnet 4.5 (equilibre)"),
    "3": ("claude-opus-4-6", "Opus 4.6 (plus capable)"),
}

AVAILABLE_PERSONAS = {
    "1": ("disciplined", "Discipline (connait les regles Alpha)"),
    "2": ("naive", "Naif (ne connait pas les regles — test de rejet)"),
}


def _get_anthropic_api_key() -> str | None:
    """Récupère la clé API Anthropic (env ou saisie)."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        print_info(f"Cle API trouvee dans ANTHROPIC_API_KEY (***{key[-4:]})")
        return key

    key = safe_input("Cle API Anthropic : ")
    if not key:
        print_error("Cle API requise.")
        return None
    return key


def _live_interview_callback(qid, question, response, evaluation):
    """Callback pour affichage temps réel de l'entretien LLM."""
    print(f"\n{Colors.BOLD}[{qid}] QUESTION :{Colors.END}")
    print(f"  {question}")
    print(f"\n{Colors.BLUE}[CLAUDE] REPONSE :{Colors.END}")
    # Afficher la réponse complète ligne par ligne
    for line in response.split("\n"):
        print(f"  {line}")

    score = evaluation.get("score", 0)
    passed = evaluation.get("passed", False)
    elimination = evaluation.get("elimination", False)

    if elimination:
        print(f"\n{Colors.RED}[VERDICT] ELIMINATOIRE — Score: {score}%{Colors.END}")
    elif passed:
        print(f"\n{Colors.GREEN}[VERDICT] PASS — Score: {score}%{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}[VERDICT] FAIL — Score: {score}%{Colors.END}")

    for reason in evaluation.get("reasons", []):
        print(f"  >> {reason}")

    print(f"{'─' * 50}")


def evaluate_llm(manager: ManagerAlpha) -> None:
    print_header("ENTRETIEN LLM LIVE — ANTHROPIC CLAUDE")
    print_info("Severite accrue : score minimum 90%, tolerance zero.")
    print_info("Le Manager Alpha va interroger un agent Claude en temps reel.\n")

    # Mode de fonctionnement
    print("  Mode :")
    print("    1. Entretien LIVE (API Anthropic)")
    print("    2. Entretien MANUEL (saisie des reponses)")
    mode = safe_input("\n  Choix [1/2] : ")

    if mode == "2":
        _evaluate_llm_manual(manager)
        return

    # --- MODE LIVE ---
    api_key = _get_anthropic_api_key()
    if not api_key:
        return

    name = safe_input("\nNom de l'agent LLM : ")
    if not name:
        print_error("Nom requis.")
        return

    print(f"\nRoles disponibles : {', '.join(ALPHA_ROLES)}")
    role = safe_input("Role : ")
    if role not in ALPHA_ROLES:
        print_error("Role invalide.")
        return

    # Choix du modèle
    print("\n  Modeles disponibles :")
    for k, (mid, desc) in AVAILABLE_MODELS.items():
        print(f"    {k}. {desc}")
    model_choice = safe_input("\n  Modele [1/2/3] : ") or "1"
    model = AVAILABLE_MODELS.get(model_choice, AVAILABLE_MODELS["1"])[0]

    # Choix du persona
    print("\n  Persona du candidat :")
    for k, (pid, desc) in AVAILABLE_PERSONAS.items():
        print(f"    {k}. {desc}")
    persona_choice = safe_input("\n  Persona [1/2] : ") or "1"
    persona = AVAILABLE_PERSONAS.get(persona_choice, AVAILABLE_PERSONAS["1"])[0]

    print_header(
        f"ENTRETIEN EN COURS — {name} ({role})\n"
        f"  Modele: {model} | Persona: {persona}"
    )

    try:
        result = manager.evaluate_llm_agent_live(
            name=name,
            role=role,
            api_key=api_key,
            model=model,
            persona=persona,
            callback=_live_interview_callback,
        )
    except AuditViolation as e:
        print_error(f"Audit bloque l'evaluation : {e}")
        return
    except Exception as e:
        print_error(f"Erreur : {e}")
        return

    if "error" in result:
        print_error(result["error"])
        return

    # Rapport final
    print("\n" + result.get("report", ""))

    if result.get("recruited"):
        print_success(f"Agent LLM {name} RECRUTE (ID: {result['agent_id']})")
    else:
        print_error(f"Agent LLM {name} REJETE")


def _evaluate_llm_manual(manager: ManagerAlpha) -> None:
    """Mode manuel : saisie des réponses LLM à la main."""
    name = safe_input("\nNom de l'agent LLM : ")
    if not name:
        print_error("Nom requis.")
        return

    print(f"\nRoles disponibles : {', '.join(ALPHA_ROLES)}")
    role = safe_input("Role : ")
    if role not in ALPHA_ROLES:
        print_error("Role invalide.")
        return

    from interview import MANDATORY_QUESTIONS

    responses = {}
    print_info(f"\n{len(MANDATORY_QUESTIONS)} questions a repondre.\n")

    for q in MANDATORY_QUESTIONS:
        print(f"{Colors.BOLD}[{q['id']}] {q['question']}{Colors.END}")
        if q.get("max_sentences"):
            print(f"  (Maximum {q['max_sentences']} phrases)")

        answer = safe_input("\nReponse LLM : ")
        if not answer:
            print_error("Reponse vide — REJET immediat.")
            return

        responses[q["id"]] = answer
        print()

    try:
        result = manager.evaluate_llm_agent(name, role, responses)
    except AuditViolation as e:
        print_error(f"Audit bloque l'evaluation : {e}")
        return

    if "error" in result:
        print_error(result["error"])
        return

    print("\n" + result.get("report", ""))

    if result.get("recruited"):
        print_success(f"Agent LLM {name} RECRUTE (ID: {result['agent_id']})")
    else:
        print_error(f"Agent LLM {name} REJETE")


# =============================================================================
# 3. SOUMISSION DE SIGNAL
# =============================================================================
def submit_signal(manager: ManagerAlpha) -> None:
    print_header("SOUMISSION — SIGNAL ALPHA")

    # Lister les agents actifs
    active = manager.list_agents(status="active")
    if not active:
        print_error("Aucun agent actif. Recrutez d'abord un agent.")
        return

    print("Agents actifs :")
    for a in active:
        print(f"  [{a['id']}] {a['name']} — {a['role']}")

    agent_id = safe_input("\nID de l'agent : ")
    if not agent_id:
        return

    print(f"\nChamps obligatoires du signal Alpha :")
    signal_data = {}

    signal_data["signal_id"] = safe_input("  SIGNAL_ID : ")
    signal_data["market"] = safe_input("  MARKET : ")

    print(f"  Types : {', '.join(SIGNAL_TYPES)}")
    signal_data["type"] = safe_input("  TYPE : ").upper()

    signal_data["edge_net"] = safe_input("  EDGE_NET (%) : ")
    signal_data["volume"] = safe_input("  VOLUME : ")
    signal_data["spread"] = safe_input("  SPREAD (%) : ")
    signal_data["time_to_resolution"] = safe_input("  TIME_TO_RESOLUTION (heures) : ")
    signal_data["risks"] = safe_input("  RISKS (description factuelle) : ")

    print(f"  Statuts : {', '.join(SIGNAL_STATUSES)}")
    signal_data["status"] = safe_input("  STATUS : ").upper()

    signal_data["comment"] = safe_input("  COMMENTAIRE FACTUEL : ")

    try:
        result = manager.submit_signal(agent_id, signal_data)
    except AuditViolation as e:
        print_error(f"Audit bloque la soumission : {e}")
        return

    if "error" in result:
        print_error(result["error"])
        return

    print("\n" + result.get("signal_display", ""))

    validation = result.get("validation", {})
    if validation.get("valid"):
        print_success(f"Signal VALIDÉ — Status: {validation.get('status')}")
    else:
        print_error("Signal REJETÉ")
        for err in validation.get("errors", []):
            print(f"  >> {err}")

    if result.get("kpi_blocked"):
        print_warning("APPROBATIONS BLOQUÉES — Taux > 5%. Revue manuelle requise.")


# =============================================================================
# 4. AUDIT D'UN AGENT
# =============================================================================
def audit_agent(manager: ManagerAlpha) -> None:
    print_header("AUDIT — AGENT")

    agents = manager.list_agents()
    if not agents:
        print_error("Aucun agent dans le registre.")
        return

    print("Agents :")
    for a in agents:
        print(f"  [{a['id']}] {a['name']} — {a['role']} — {a['status']} — "
              f"Warnings: {a['warnings']}/3")

    agent_id = safe_input("\nID de l'agent à auditer : ")
    if not agent_id:
        return

    try:
        result = manager.audit_agent(agent_id)
    except AuditViolation as e:
        print_error(f"Erreur d'audit : {e}")
        return

    if "error" in result:
        print_error(result["error"])
        return

    print(f"\n{'=' * 50}")
    print(f"  Agent : {result.get('agent_name', 'N/A')} ({result.get('agent_id', 'N/A')})")
    print(f"  Statut : {result.get('status', 'N/A')}")
    print(f"  Décisions totales : {result.get('total_decisions', 0)}")
    print(f"  Audits échoués : {result.get('failed_audits', 0)}")
    print(f"  Taux d'échec : {result.get('failure_rate', 0):.1f}%")
    print(f"  Avertissements : {result.get('warnings', 0)}/3")
    print(f"  Recommandation : {result.get('recommendation', 'N/A')}")

    if result.get("all_violations"):
        print(f"\n  Violations :")
        for v in result["all_violations"]:
            print(f"    >> {v}")

    if result.get("warning_issued"):
        w = result["warning_issued"]
        print_warning(f"Avertissement émis : {w.get('warning_result')}")

    print(f"{'=' * 50}")


# =============================================================================
# 5. KPIS
# =============================================================================
def show_kpis(manager: ManagerAlpha) -> None:
    print(manager.get_kpi_report())


# =============================================================================
# 6. LISTER LES AGENTS
# =============================================================================
def list_agents(manager: ManagerAlpha) -> None:
    print_header("REGISTRE DES AGENTS")

    agents = manager.list_agents()
    if not agents:
        print_info("Aucun agent dans le registre.")
        return

    for a in agents:
        status_color = {
            "active": Colors.GREEN,
            "candidate": Colors.YELLOW,
            "excluded": Colors.RED,
        }.get(a["status"], "")

        print(
            f"  [{a['id']}] {a['name']:.<20} {a['role']:.<20} "
            f"{status_color}{a['status'].upper()}{Colors.END}  "
            f"Warnings: {a['warnings']}/3  "
            f"Score: {a.get('interview_score', 0)}%  "
            f"Mode: {a.get('mode', 'N/A')}"
        )


# =============================================================================
# 7. REVUE COMPLÈTE
# =============================================================================
def review_all(manager: ManagerAlpha) -> None:
    print_header("REVUE COMPLÈTE — TOUS LES AGENTS ACTIFS")

    try:
        reviews = manager.review_all_agents()
    except AuditViolation as e:
        print_error(f"Erreur : {e}")
        return

    if not reviews:
        print_info("Aucun agent actif à revoir.")
        return

    for r in reviews:
        status_icon = "OK" if r["recommendation"] == "OK" else "ALERTE"
        color = Colors.GREEN if r["recommendation"] == "OK" else Colors.RED

        print(
            f"  {color}[{status_icon}]{Colors.END} "
            f"{r.get('agent_name', 'N/A')} — "
            f"Décisions: {r.get('total_decisions', 0)} — "
            f"Échecs: {r.get('failed_audits', 0)} — "
            f"Recommandation: {r.get('recommendation', 'N/A')}"
        )


# =============================================================================
# 8. JOURNAL D'AUDIT
# =============================================================================
def show_audit_log(manager: ManagerAlpha) -> None:
    print_header("JOURNAL D'AUDIT (50 dernières entrées)")

    entries = manager.view_audit_log(50)
    if not entries:
        print_info("Journal d'audit vide.")
        return

    for entry in entries:
        print(f"  {entry.rstrip()}")


# =============================================================================
# 9. RÈGLES D'OR
# =============================================================================
def show_rules() -> None:
    print_header("LES 10 RÈGLES D'OR ALPHA")

    for num, rule in GOLDEN_RULES.items():
        print(f"  {Colors.BOLD}Règle {num}{Colors.END} — {rule['title']}")
        print(f"    {rule['description']}")
        print()


# =============================================================================
# 10. AVERTIR UN AGENT
# =============================================================================
def warn_agent(manager: ManagerAlpha) -> None:
    print_header("AVERTISSEMENT — AGENT")

    agents = manager.list_agents()
    if not agents:
        print_error("Aucun agent.")
        return

    for a in agents:
        if a["status"] != "excluded":
            print(f"  [{a['id']}] {a['name']} — Warnings: {a['warnings']}/3")

    agent_id = safe_input("\nID de l'agent : ")
    reason = safe_input("Raison de l'avertissement : ")

    if not agent_id or not reason:
        print_error("ID et raison requis.")
        return

    try:
        result = manager.warn_agent(agent_id, reason)
    except AuditViolation as e:
        print_error(f"Erreur : {e}")
        return

    if "error" in result:
        print_error(result["error"])
        return

    wr = result.get("warning_result", "")
    if wr == "EXCLU":
        print_error(f"Agent EXCLU — 3 avertissements atteints.")
    else:
        print_warning(f"{wr} — Raison : {reason}")


# =============================================================================
# 11. TOGGLE BYPASS
# =============================================================================
def toggle_bypass(manager: ManagerAlpha) -> None:
    if manager.bypass_mode:
        print(manager.disable_bypass())
    else:
        print(manager.enable_bypass())


# =============================================================================
# 12. DÉBLOCAGE MANUEL
# =============================================================================
def manual_unblock(manager: ManagerAlpha) -> None:
    print_header("DÉBLOCAGE MANUEL DES APPROBATIONS")

    if not manager.kpi.is_approval_blocked():
        print_info("Aucun blocage en cours.")
        return

    print_warning("Les approbations sont actuellement BLOQUÉES (taux > 5%).")
    reviewer = safe_input("Nom du reviewer : ")
    reason = safe_input("Justification du déblocage : ")

    if not reviewer or not reason:
        print_error("Reviewer et justification requis.")
        return

    result = manager.manual_unblock_approvals(reviewer, reason)
    if result["status"] == "UNBLOCKED":
        print_success("Approbations débloquées.")
    else:
        print_error(f"Échec : {result.get('message', '')}")


# =============================================================================
# BOUCLE PRINCIPALE
# =============================================================================
def main():
    # Vérifier le mode bypass en argument
    bypass_arg = "--bypass-permission" in sys.argv

    print_header("INITIALISATION DU MANAGER IA ALPHA")
    print(f"  {Colors.BOLD}{ALPHA_LAW}{Colors.END}")
    print()

    manager = ManagerAlpha()

    if bypass_arg:
        print(manager.enable_bypass())

    while True:
        show_menu(bypass_mode=manager.bypass_mode)
        choice = safe_input("Choix : ")

        if choice == "0":
            print_info("Manager IA Alpha — Arrêt. La discipline ne s'arrête jamais.")
            break
        elif choice == "1":
            if manager.bypass_mode:
                print_error("Recrutement interdit en mode bypass.")
            else:
                recruit_human(manager)
        elif choice == "2":
            if manager.bypass_mode:
                print_error("Évaluation LLM interdite en mode bypass.")
            else:
                evaluate_llm(manager)
        elif choice == "3":
            if manager.bypass_mode:
                print_error("Soumission de signal interdite en mode bypass.")
            else:
                submit_signal(manager)
        elif choice == "4":
            audit_agent(manager)
        elif choice == "5":
            show_kpis(manager)
        elif choice == "6":
            list_agents(manager)
        elif choice == "7":
            if manager.bypass_mode:
                print_error("Revue complète interdite en mode bypass.")
            else:
                review_all(manager)
        elif choice == "8":
            show_audit_log(manager)
        elif choice == "9":
            show_rules()
        elif choice == "10":
            if manager.bypass_mode:
                print_error("Avertissement interdit en mode bypass.")
            else:
                warn_agent(manager)
        elif choice == "11":
            toggle_bypass(manager)
        elif choice == "12":
            if manager.bypass_mode:
                print_error("Déblocage interdit en mode bypass.")
            else:
                manual_unblock(manager)
        else:
            print_error("Choix invalide.")


if __name__ == "__main__":
    main()
