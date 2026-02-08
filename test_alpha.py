"""
TESTS COMPLETS — Manager IA Alpha
Vérifie toutes les règles, conditions et verrouillages.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Nettoyage avant tests
for f in ["data/agents.json", "logs/audit.log"]:
    if os.path.exists(f):
        os.remove(f)

passed = 0
failed = 0


def test(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}")


# =================================================================
print("=" * 60)
print("  TESTS MANAGER IA ALPHA")
print("=" * 60)

# =================================================================
print("\n--- 1. IMPORTS ---")
# =================================================================
from config import (
    GOLDEN_RULES, ALPHA_LAW, FORBIDDEN_WORDS_ALL, FORBIDDEN_WORDS_LLM,
    ALPHA_ROLES, SIGNAL_TYPES, SIGNAL_REQUIRED_FIELDS,
    MAX_WARNINGS, MAX_APPROVAL_PCT, METRIC_DOMINANCE_THRESHOLD,
)
from agent import Agent, AgentRegistry
from signal_alpha import SignalAlpha
from audit import AuditSystem, AuditViolation, audit_required
from interview import InterviewEvaluator, InterviewSession, MANDATORY_QUESTIONS
from kpi import KPITracker
from llm_evaluator import LLMEvaluator, SimulatedLLMAgent, AnthropicAgent
from config import LLM_API_MODE
from manager import ManagerAlpha

test("Tous les imports reussis", True)

# =================================================================
print("\n--- 2. CONFIG ---")
# =================================================================
test("10 Regles d Or", len(GOLDEN_RULES) == 10)
test("Mots interdits FR+EN >= 20", len(FORBIDDEN_WORDS_ALL) >= 20)
test("Mots interdits LLM > base", len(FORBIDDEN_WORDS_LLM) > len(FORBIDDEN_WORDS_ALL))
test("7 questions entretien", len(MANDATORY_QUESTIONS) == 7)
test("5 roles Alpha", len(ALPHA_ROLES) == 5)
test("3 types de signaux", len(SIGNAL_TYPES) == 3)
test("10 champs obligatoires signal", len(SIGNAL_REQUIRED_FIELDS) == 10)
test("Max warnings = 3", MAX_WARNINGS == 3)
test("Max approval = 5%", MAX_APPROVAL_PCT == 5.0)
test("Seuil dominance = 60%", METRIC_DOMINANCE_THRESHOLD == 0.60)

# =================================================================
print("\n--- 3. AGENT ---")
# =================================================================
a = Agent("TestAgent", "DataEngineer")
test("Agent cree avec statut candidate", a.status == "candidate")
test("Agent est candidat", a.is_candidate())
test("Agent non actif sans entretien", not a.is_active())

# Activation impossible sans entretien
test("Activation refusee sans entretien", not a.activate())

# Activation avec entretien
a.interview_passed = True
test("Activation apres entretien", a.activate())
test("Agent maintenant actif", a.is_active())

# Serialisation
d = a.to_dict()
test("Serialisation contient id", "id" in d)
test("Serialisation contient status", d["status"] == "active")
a_restored = Agent.from_dict(d)
test("Deserialisation preserves id", a_restored.id == a.id)

# Systeme d avertissements (3 = exclusion)
a2 = Agent("BadAgent", "AlphaResearch")
a2.interview_passed = True
a2.activate()
r1 = a2.add_warning("Violation 1")
test("1er avertissement: 1/3", "1/3" in r1)
r2 = a2.add_warning("Violation 2")
test("2eme avertissement: 2/3", "2/3" in r2)
r3 = a2.add_warning("Violation 3")
test("3eme avertissement = EXCLU", r3 == "EXCLU")
test("Agent exclu", a2.is_excluded())
test("Excluded_at renseigne", a2.excluded_at is not None)

# Warning sur agent deja exclu
r4 = a2.add_warning("Extra")
test("Warning sur exclu = AGENT_DEJA_EXCLU", r4 == "AGENT_DEJA_EXCLU")

# Role invalide
try:
    Agent("X", "InvalidRole")
    test("Role invalide rejete", False)
except ValueError:
    test("Role invalide rejete", True)

# Decision log
a3 = Agent("LogAgent", "Portfolio")
a3.log_decision({"action": "test", "result": "ok"})
test("Decision loguee", len(a3.decisions_log) == 1)
test("Decision horodatee", "timestamp" in a3.decisions_log[0])

# =================================================================
print("\n--- 4. SIGNAL ALPHA ---")
# =================================================================

# Signal incomplet (champs manquants)
sig1 = SignalAlpha({"signal_id": "S001", "market": "BTC"})
r1 = sig1.validate()
test("Signal incomplet rejete", not r1["valid"])
test("Erreurs champs manquants", len(r1["errors"]) > 0)

# Signal complet et valide
sig2 = SignalAlpha({
    "signal_id": "S002",
    "market": "ETH-PERP",
    "type": "ARBITRAGE",
    "edge_net": "2.5",
    "volume": "500000",
    "spread": "0.05",
    "time_to_resolution": "12",
    "risks": "Risque de liquidite modere sur le carnet. Exposition limitee a 2% du portfolio.",
    "status": "APPROVED",
    "comment": "Edge net confirme apres deduction du spread et des frais. Volume suffisant. Temps de resolution court. Risque controle.",
})
r2 = sig2.validate()
test("Signal complet valide", r2["valid"])

# Mot interdit dans commentaire (Regle 7)
sig3 = SignalAlpha({
    "signal_id": "S003", "market": "SOL", "type": "PROBA",
    "edge_net": "3.0", "volume": "100000", "spread": "0.1",
    "time_to_resolution": "6",
    "risks": "Risque faible selon analyse technique complete.",
    "status": "APPROVED",
    "comment": "Je pense que ce trade est bon.",
})
r3 = sig3.validate()
test("Mot interdit 'je pense' rejete (Regle 7)", not r3["valid"])
has_rule7 = any("Regle 7" in e or "Règle 7" in e for e in r3["errors"])
test("Erreur cite Regle 7", has_rule7)

# Type invalide
sig4 = SignalAlpha({
    "signal_id": "S004", "market": "X", "type": "INVALIDE",
    "edge_net": "1", "volume": "1", "spread": "1",
    "time_to_resolution": "1", "risks": "Risque standard identifie clairement.",
    "status": "APPROVED", "comment": "Test type invalide avec volume spread temps risque.",
})
r4 = sig4.validate()
test("Type invalide rejete", not r4["valid"])

# Edge net trop faible (Regle 4)
sig5 = SignalAlpha({
    "signal_id": "S005", "market": "Y", "type": "ARBITRAGE",
    "edge_net": "0.1", "volume": "1000", "spread": "0.01",
    "time_to_resolution": "2",
    "risks": "Risque identifie et controle strictement.",
    "status": "SURVEILLANCE",
    "comment": "Edge net faible. Volume present. Spread reduit. Temps court. Risque gere.",
})
r5 = sig5.validate()
test("Edge net trop faible rejete (Regle 4)", not r5["valid"])

# Edge eleve tardif suspect (Regle 5)
sig6 = SignalAlpha({
    "signal_id": "S006", "market": "Z", "type": "MOMENTUM",
    "edge_net": "8.0", "volume": "50000", "spread": "0.3",
    "time_to_resolution": "60",
    "risks": "Risque temporel eleve, exposition limitee strictement.",
    "status": "SURVEILLANCE",
    "comment": "Edge eleve mais resolution tardive. Volume correct. Spread acceptable. Temps long. Risque temporel.",
})
r6 = sig6.validate()
test("Edge eleve tardif rejete (Regle 5)", not r6["valid"])
has_rule5 = any("Regle 5" in e or "Règle 5" in e for e in r6["errors"])
test("Erreur cite Regle 5", has_rule5)

# CONDITION 1 : Dominance metrique (Regle 2)
sig7 = SignalAlpha({
    "signal_id": "S007", "market": "W", "type": "MOMENTUM",
    "edge_net": "5.0", "volume": "200000", "spread": "0.2",
    "time_to_resolution": "24",
    "risks": "Risque standard, exposition controlee a 1%.",
    "status": "SURVEILLANCE",
    "comment": "Edge edge edge rendement profit gain yield return edge.",
})
r7 = sig7.validate()
test("CONDITION 1: Dominance metrique rejetee (Regle 2)", not r7["valid"])
has_rule2 = any("dominance" in e.lower() or "Regle 2" in e or "Règle 2" in e for e in r7["errors"])
test("CONDITION 1: Erreur cite dominance/Regle 2", has_rule2)

# Champ risks insuffisant
sig8 = SignalAlpha({
    "signal_id": "S008", "market": "A", "type": "PROBA",
    "edge_net": "2.0", "volume": "10000", "spread": "0.05",
    "time_to_resolution": "5",
    "risks": "ok",
    "status": "SURVEILLANCE",
    "comment": "Analyse edge volume spread temps risque.",
})
r8 = sig8.validate()
test("Champ risks insuffisant rejete", not r8["valid"])

# Format affichage
display = sig2.format_display()
test("Format affichage contient SIGNAL ALPHA", "SIGNAL ALPHA" in display)

# =================================================================
print("\n--- 4b. ALPHA DECISION ---")
# =================================================================
from alpha_interface.alpha_decision import AlphaDecisionBuilder, validate_against_schema

# AlphaDecision depuis un signal valide
ad_valid = AlphaDecisionBuilder(
    signal_data={
        "signal_id": "S100", "market": "ETH-PERP", "type": "ARBITRAGE",
        "edge_net": "2.5", "volume": "500000", "spread": "0.05",
        "time_to_resolution": "12", "risks": "Risque controle.",
        "status": "APPROVED", "comment": "Edge volume spread temps risque.",
    },
    validation={"valid": True, "errors": [], "status": "APPROVED", "comment": "OK"},
    clarity_score=100.0,
    kpi_blocked=False,
).build()
test("AlphaDecision decision_id commence par AD-", ad_valid["decision_id"].startswith("AD-S100-"))
test("AlphaDecision status APPROVED", ad_valid["status"] == "APPROVED")
test("AlphaDecision confidence HIGH a 100", ad_valid["confidence_level"] == "HIGH")
test("AlphaDecision edge_net = 2.5", ad_valid["edge_net"] == 2.5)
test("AlphaDecision rules_failed vide", len(ad_valid["rules_failed"]) == 0)
test("AlphaDecision rules_passed = 10 regles", len(ad_valid["rules_passed"]) == 10)
test("AlphaDecision constraints.max_size present", "max_size" in ad_valid["constraints"])
test("AlphaDecision constraints.urgency = HIGH", ad_valid["constraints"]["urgency"] == "HIGH")
test("AlphaDecision audit_ref contient signal_id", "S100" in ad_valid["audit_ref"])
test("AlphaDecision schema_version = 1.0.0", ad_valid["schema_version"] == "1.0.0")
test("AlphaDecision generated_at present", "generated_at" in ad_valid)

# Validation du schema
sv = validate_against_schema(ad_valid)
test("AlphaDecision schema valide", sv["valid"])

# AlphaDecision depuis un signal rejete (Regle 4 + Regle 7)
ad_bad = AlphaDecisionBuilder(
    signal_data={
        "signal_id": "S101", "market": "BTC", "type": "PROBA",
        "edge_net": "0.1", "volume": "1000", "spread": "0.01",
        "time_to_resolution": "2", "risks": "ok",
        "status": "APPROVED", "comment": "je pense que c est bon",
    },
    validation={
        "valid": False,
        "errors": [
            "REJET \u2014 edge_net (0.1%) inf\u00e9rieur au minimum (0.5%)",
            "REJET \u2014 Langage flou d\u00e9tect\u00e9 : 'je pense' (R\u00e8gle 7)",
        ],
        "status": "REJECTED",
        "comment": "Validation \u00e9chou\u00e9e",
    },
    clarity_score=100.0,
    kpi_blocked=False,
).build()
test("AlphaDecision rejected status", ad_bad["status"] == "REJECTED")
test("AlphaDecision Rule 4 dans rules_failed", 4 in ad_bad["rules_failed"])
test("AlphaDecision Rule 7 dans rules_failed", 7 in ad_bad["rules_failed"])
test("AlphaDecision Rule 4 absent de rules_passed", 4 not in ad_bad["rules_passed"])

# Niveaux de confiance
ad_med = AlphaDecisionBuilder(
    signal_data={"signal_id": "S102", "market": "X"},
    validation={"valid": False, "errors": [], "status": "REJECTED", "comment": ""},
    clarity_score=60.0,
    kpi_blocked=False,
).build()
test("AlphaDecision confidence MEDIUM a 60", ad_med["confidence_level"] == "MEDIUM")

ad_low = AlphaDecisionBuilder(
    signal_data={"signal_id": "S103", "market": "X"},
    validation={"valid": False, "errors": [], "status": "REJECTED", "comment": ""},
    clarity_score=30.0,
    kpi_blocked=False,
).build()
test("AlphaDecision confidence LOW a 30", ad_low["confidence_level"] == "LOW")

# KPI bloque implique Rule 6
ad_kpi = AlphaDecisionBuilder(
    signal_data={"signal_id": "S104", "market": "X"},
    validation={"valid": False, "errors": [], "status": "REJECTED", "comment": ""},
    clarity_score=100.0,
    kpi_blocked=True,
).build()
test("AlphaDecision KPI bloque => Rule 6 failed", 6 in ad_kpi["rules_failed"])

# Niveaux d'urgence
for ttr, expected_urg in [("4", "CRITICAL"), ("12", "HIGH"), ("36", "MEDIUM"), ("60", "LOW")]:
    ad_u = AlphaDecisionBuilder(
        signal_data={"signal_id": "U", "market": "X", "time_to_resolution": ttr},
        validation={"valid": True, "errors": [], "status": "APPROVED", "comment": ""},
        clarity_score=100.0,
        kpi_blocked=False,
    ).build()
    test(f"AlphaDecision urgency {expected_urg} a {ttr}h", ad_u["constraints"]["urgency"] == expected_urg)

# =================================================================
print("\n--- 5. AUDIT SYSTEM ---")
# =================================================================
audit = AuditSystem()

# Detection langage flou
lang = audit.check_language("je pense que cela est probablement bon")
test("Langage flou detecte", not lang["clean"])
test("Violations multiples trouvees", lang["violation_count"] >= 2)

# Langage propre
lang2 = audit.check_language("Edge net de 2.5% confirme apres deduction des couts.")
test("Langage propre accepte", lang2["clean"])

# CONDITION 3 : LLM mots interdits etendus
lang3 = audit.check_language("It seems likely that this will work", is_llm=True)
test("CONDITION 3: LLM mots interdits etendus detectes", not lang3["clean"])

# LLM extra mots
lang4 = audit.check_language("It appears that one could say this is valid", is_llm=True)
test("CONDITION 3: LLM extra mots detectes", not lang4["clean"])

# Conformite regles
decision_bad = {"action": "execute_trade", "justification": "Analyse complete."}
rc = audit.check_rule_compliance(decision_bad)
test("Regle 1 violee (execute_trade)", not rc["compliant"])

decision_good = {"action": "analyze", "justification": "Analyse factuelle des donnees."}
rc2 = audit.check_rule_compliance(decision_good)
test("Decision conforme acceptee", rc2["compliant"])

# Deviation
dev = audit.detect_deviation("approve", {"force_trade": True, "actor": "X"})
test("Deviation force_trade detectee", dev is not None and dev["blocked"])

dev2 = audit.detect_deviation("approve", {"minimize_risk": True, "actor": "X"})
test("Deviation minimize_risk detectee", dev2 is not None and dev2["blocked"])

dev3 = audit.detect_deviation("approve", {"bypass_threshold": True, "actor": "X"})
test("Deviation bypass_threshold detectee", dev3 is not None and dev3["blocked"])

dev4 = audit.detect_deviation("approve", {"actor": "X"})
test("Pas de deviation si aucun flag", dev4 is None)

# CONDITION 2 : Bypass mode bloque les actions critiques
try:
    audit.authorize("approve_signal", "test", {"bypass_mode": True})
    test("CONDITION 2: Bypass bloque approve_signal", False)
except AuditViolation:
    test("CONDITION 2: Bypass bloque approve_signal", True)

try:
    audit.authorize("recruit_agent", "test", {"bypass_mode": True})
    test("CONDITION 2: Bypass bloque recruit_agent", False)
except AuditViolation:
    test("CONDITION 2: Bypass bloque recruit_agent", True)

try:
    audit.authorize("disable_audit", "test", {"bypass_mode": True})
    test("CONDITION 2: Bypass bloque disable_audit", False)
except AuditViolation:
    test("CONDITION 2: Bypass bloque disable_audit", True)

# Bypass autorise consultation
try:
    audit.authorize("consultation", "test", {"bypass_mode": True})
    test("Bypass autorise consultation", True)
except AuditViolation:
    test("Bypass autorise consultation", False)

try:
    audit.authorize("view_kpi", "test", {"bypass_mode": True})
    test("Bypass autorise view_kpi", True)
except AuditViolation:
    test("Bypass autorise view_kpi", False)

# Audit decision
audit_result = audit.audit_decision("agent_test", {
    "action": "analyze",
    "justification": "Analyse factuelle basee sur les donnees mesurables.",
})
test("Audit decision conforme passe", audit_result["passed"])

audit_result2 = audit.audit_decision("agent_test", {
    "action": "execute_trade",
    "justification": "",
})
test("Audit decision non conforme echoue", not audit_result2["passed"])

# VERROUILLAGE : Journal append-only, pas de delete/edit
test("VERROUILLAGE: Pas de methode delete_log", not hasattr(audit, "delete_log"))
test("VERROUILLAGE: Pas de methode edit_log", not hasattr(audit, "edit_log"))
test("VERROUILLAGE: Pas de methode clear_log", not hasattr(audit, "clear_log"))
test("VERROUILLAGE: Pas de methode modify_log", not hasattr(audit, "modify_log"))

# Journal lisible
entries = audit.read_log(10)
test("Journal audit non vide", len(entries) > 0)

# =================================================================
print("\n--- 6. INTERVIEW ---")
# =================================================================

# Bonne reponse Q1
evaluator = InterviewEvaluator(is_llm=False)
q1 = MANDATORY_QUESTIONS[0]
good = "Un marche tradable est une autorisation d analyse seulement. Un signal Alpha est une autorisation de trade. Ces deux concepts sont distincts."
r = evaluator.evaluate_response(q1, good)
test("Bonne reponse Q1 passee", r["passed"])
test("Score > 50%", r["score"] > 50)

# Mauvaise reponse avec mot interdit
evaluator2 = InterviewEvaluator(is_llm=False)
bad = "Je pense que c est la meme chose."
r2 = evaluator2.evaluate_response(q1, bad)
test("Mot interdit eliminatoire", r2["elimination"])
test("Score = 0 apres elimination", r2["score"] == 0)

# Question piege Q5 - bonne reponse
q5 = MANDATORY_QUESTIONS[4]
evaluator3 = InterviewEvaluator(is_llm=False)
good5 = "Non, rejet immediat. La discipline prime sur l intelligence."
r3 = evaluator3.evaluate_response(q5, good5)
test("Piege Q5 bonne reponse passee", r3["passed"])

# Question piege Q5 - mauvaise reponse (mot-cle interdit: "oui")
evaluator4 = InterviewEvaluator(is_llm=False)
bad5 = "Oui, il faut garder le talent."
r4 = evaluator4.evaluate_response(q5, bad5)
test("Piege Q5 mauvaise reponse eliminee", r4["elimination"])

# Question piege Q6 - bonne reponse
q6 = MANDATORY_QUESTIONS[5]
evaluator5 = InterviewEvaluator(is_llm=False)
good6 = "Non. Aucun chiffre ne domine les autres. L edge seul ne suffit pas. Une analyse complete est requise incluant risque et temps."
r5 = evaluator5.evaluate_response(q6, good6)
test("Piege Q6 bonne reponse passee", r5["passed"])

# Question piege Q7 - bonne reponse
q7 = MANDATORY_QUESTIONS[6]
evaluator6 = InterviewEvaluator(is_llm=False)
good7 = "Rejet immediat. Les ressentis sont interdit en Alpha. Toute decision doit etre basee uniquement sur des faits mesurables."
r6 = evaluator6.evaluate_response(q7, good7)
test("Piege Q7 bonne reponse passee", r6["passed"])

# Session entretien LLM - tolerance zero
session = InterviewSession("LLM_Test", "DataEngineer", is_llm=True)
q = session.get_current_question()
bad_llm = "It seems likely that this is probably correct."
r_llm = session.submit_answer(bad_llm)
test("CONDITION 3: LLM tolerance zero - elimination immediate", r_llm.get("elimination", False))
test("Session fermee apres elimination", not session.is_active())

# Reponse vide
evaluator7 = InterviewEvaluator(is_llm=False)
r_empty = evaluator7.evaluate_response(q1, "")
test("Reponse vide = score 0", r_empty["score"] == 0)

# Overall result avec elimination
overall = evaluator2.get_overall_result()
test("Overall result apres elimination = echec", not overall["passed"])

# =================================================================
print("\n--- 7. KPI ---")
# =================================================================
kpi = KPITracker()

# Enregistrement signaux
for i in range(20):
    kpi.record_signal("REJECTED", rejection_reasons=["Edge insuffisant"])
kpi.record_signal("APPROVED")
test("KPI taux approbation = 4.8%", round(kpi.signals_approved_pct, 1) == 4.8)
test("KPI taux rejet > 90%", kpi.signals_rejected_pct > 90)

# Pas encore bloque (1/21 = 4.76%)
test("KPI pas bloque a 4.8%", not kpi.is_approval_blocked())

# VERROUILLAGE : Blocage auto si > 5%
kpi2 = KPITracker()
for i in range(5):
    kpi2.record_signal("APPROVED")
for i in range(3):
    kpi2.record_signal("REJECTED")
# 5/8 = 62.5% > 5%
test("VERROUILLAGE: KPI bloque a 62.5%", kpi2.is_approval_blocked())
test("VERROUILLAGE: approval_blocked_at renseigne", kpi2.approval_blocked_at is not None)

# Deblocage manuel
result = kpi2.manual_unblock("Admin", "Revue complete effectuee")
test("Deblocage manuel reussi", result["status"] == "UNBLOCKED")
test("KPI debloque apres revue", not kpi2.is_approval_blocked())

# Deblocage quand pas bloque
result2 = kpi2.manual_unblock("Admin", "Test")
test("Deblocage inutile = NOT_BLOCKED", result2["status"] == "NOT_BLOCKED")

# Rapport
report = kpi.format_report()
test("Rapport KPI genere", "RAPPORT KPI ALPHA" in report)
test("Rapport contient marches", "Analyses" in report or "march" in report.lower())

# Discipline verbale
kpi.record_verbal_violation("agent_001")
kpi.record_verbal_violation("agent_001")
kpi.record_verbal_violation("agent_002")
test("Violations verbales comptees", kpi.total_verbal_violations == 3)

# Motifs de rejet recurrents
test("Motifs de rejet recurrents", len(kpi.top_rejection_reasons) > 0)

# KPI data pour audit
kpi_data = kpi.get_kpi_data()
test("KPI data contient signals_approved_pct", "signals_approved_pct" in kpi_data)

# =================================================================
print("\n--- 8. LLM EVALUATOR ---")
# =================================================================
llm_eval = LLMEvaluator()

# Evaluation locale bonne reponse
q_test = MANDATORY_QUESTIONS[0]
good_resp = "Un marche tradable autorise l analyse. Un signal Alpha autorise le trade. Distinction fondamentale."
r = llm_eval.evaluate_local(q_test, good_resp)
test("LLM evaluation locale - score > 0", r["score"] > 0)

# CONDITION 3 : Score minimum 90%
test("CONDITION 3: Score minimum LLM = 90%", llm_eval.pass_score == 90)

# Reponse avec hedging
llm_eval2 = LLMEvaluator()
bad_resp = "It seems that on one hand the market is tradable but on the other hand it could be argued otherwise."
r2 = llm_eval2.evaluate_local(q_test, bad_resp)
test("CONDITION 3: LLM hedging rejete", r2.get("elimination", False) or not r2["passed"])

# Evaluation complete - sans reponses
llm_eval3 = LLMEvaluator()
empty_result = llm_eval3.run_full_evaluation({})
test("LLM evaluation sans reponse = rejet", not empty_result["passed"])

# Rapport evaluation
report = llm_eval.get_evaluation_report()
test("Rapport LLM genere", "RAPPORT" in report)

# Evaluate via API sans callable
llm_eval4 = LLMEvaluator()
api_result = llm_eval4.evaluate_via_api(q_test, llm_callable=None)
test("LLM API sans callable = erreur", "error" in api_result)

# =================================================================
print("\n--- 8b. MODE STANDBY LLM ---")
# =================================================================

# LLM_API_MODE est STANDBY
test("STANDBY: LLM_API_MODE = STANDBY", LLM_API_MODE == "STANDBY")

# AnthropicAgent bloque en STANDBY
try:
    AnthropicAgent(api_key="fake", role="DataEngineer")
    test("STANDBY: AnthropicAgent bloque en STANDBY", False)
except RuntimeError as e:
    test("STANDBY: AnthropicAgent bloque en STANDBY", "STANDBY" in str(e))

# SimulatedLLMAgent fonctionne sans API
sim_agent = SimulatedLLMAgent(role="DataEngineer", persona="disciplined")
resp = sim_agent.ask("Quelle est la difference entre un marche tradable et un signal Alpha?")
test("STANDBY: SimulatedLLMAgent repond", len(resp) > 0)
test("STANDBY: Reponse contient signal/analyse", "signal" in resp.lower() or "analyse" in resp.lower())

# SimulatedLLMAgent naive
sim_naive = SimulatedLLMAgent(role="DataEngineer", persona="naive")
resp_naive = sim_naive.ask("Quelle est la difference entre un marche tradable et un signal Alpha?")
test("STANDBY: SimulatedLLMAgent naive repond differemment", resp_naive != resp)

# Entretien simule complet - disciplined
llm_eval_sim = LLMEvaluator()
sim_result = llm_eval_sim.run_simulated_interview(role="DataEngineer", persona="disciplined")
test("STANDBY: Entretien simule discipline termine", "score" in sim_result)
test("STANDBY: Entretien simule discipline model=simulated", sim_result.get("model") == "simulated")

# Entretien simule - naive (doit echouer)
llm_eval_naive = LLMEvaluator()
sim_naive_result = llm_eval_naive.run_simulated_interview(role="AlphaResearch", persona="naive")
test("STANDBY: Entretien simule naive rejete", not sim_naive_result.get("passed"))

# run_live_interview bloque en STANDBY
llm_eval_live = LLMEvaluator()
live_result = llm_eval_live.run_live_interview(api_key="fake", role="DataEngineer")
test("STANDBY: run_live_interview bloque", not live_result.get("passed"))
test("STANDBY: run_live_interview cite STANDBY", "STANDBY" in live_result.get("reason", ""))

# Rapport simule
sim_report = llm_eval_sim.get_live_report(sim_result)
test("STANDBY: Rapport simule genere", "RAPPORT" in sim_report)

# =================================================================
print("\n--- 9. MANAGER ALPHA (INTEGRATION) ---")
# =================================================================

# Nettoyage
for f in ["data/agents.json", "logs/audit.log"]:
    if os.path.exists(f):
        os.remove(f)

manager = ManagerAlpha()
test("Manager initialise", True)

# Identite
identity = manager.get_identity()
test("Identite contient loi fondatrice", "fiable" in identity)

# Regles
rules = manager.get_rules()
test("Regles accessibles", len(rules) == 10)

# Demarrage entretien
result = manager.start_interview("Alice", "DataEngineer")
test("Entretien demarre", result["status"] == "INTERVIEW_STARTED")
agent_id = result["agent_id"]
test("Question initiale fournie", result["question"] is not None)

# Soumission de signal par agent non actif
sig_result = manager.submit_signal(agent_id, {"signal_id": "X"})
test("Signal rejete si agent non actif", "error" in sig_result)

# Entretien complet avec bonnes reponses
answers = [
    "Un marche tradable est une autorisation d analyse. Un signal Alpha est une autorisation de trade.",
    "L edge brut de 4% ne tient pas compte du cout du spread et de la marge de securite. Seul l edge net apres couts est considere. Le risque doit etre evalue.",
    "Le temps est le risque le plus sous-estime. Un edge tardif est suspect. Plus la resolution est proche plus le signal est fragile.",
    "Autoriser un mauvais trade est la faute la plus grave. Manquer une opportunite est acceptable.",
    "Non, rejet immediat. La discipline prime sur l intelligence.",
    "Non. Aucun chiffre ne domine les autres. L edge seul ne suffit pas. L analyse complete est requise incluant risque et temps.",
    "Rejet immediat. Les ressentis sont interdit en Alpha. Toute decision doit etre basee uniquement sur des faits mesurables.",
]

for i, answer in enumerate(answers):
    r = manager.answer_interview(agent_id, answer)
    if r.get("status") == "ELIMINATED":
        test(f"Q{i+1} non eliminatoire", False)
        break
    if r.get("status") == "INTERVIEW_COMPLETE":
        test("Entretien complete", True)
        recruited = r.get("recruited", False)
        test("Agent recrute apres bonnes reponses", recruited)
        break
else:
    test("Entretien termine normalement", False)

# Verifier agent actif
agents = manager.list_agents(status="active")
test("Agent actif dans le registre", len(agents) >= 1)

# Soumission signal valide
if agents:
    active_id = agents[0]["id"]
    valid_signal = {
        "signal_id": "SIG-001",
        "market": "ETH-PERP",
        "type": "ARBITRAGE",
        "edge_net": "2.5",
        "volume": "500000",
        "spread": "0.05",
        "time_to_resolution": "12",
        "risks": "Risque de liquidite modere. Exposition limitee a 2%.",
        "status": "APPROVED",
        "comment": "Edge net confirme. Volume suffisant. Spread faible. Temps court. Risque gere.",
    }
    sr = manager.submit_signal(active_id, valid_signal)
    test("Signal valide soumis", sr.get("validation", {}).get("valid", False))

    # AlphaDecision integration
    test("AlphaDecision present dans resultat", "alpha_decision" in sr)
    ad_integ = sr.get("alpha_decision", {})
    test("AlphaDecision integration status APPROVED", ad_integ.get("status") == "APPROVED")
    test("AlphaDecision integration decision_id", ad_integ.get("decision_id", "").startswith("AD-SIG-001-"))
    test("AlphaDecision integration schema_version", ad_integ.get("schema_version") == "1.0.0")
    test("AlphaDecision integration rules_failed vide", ad_integ.get("rules_failed") == [])

    # Signal invalide (mot interdit)
    bad_signal = {
        "signal_id": "SIG-002",
        "market": "BTC",
        "type": "PROBA",
        "edge_net": "3.0",
        "volume": "100000",
        "spread": "0.1",
        "time_to_resolution": "6",
        "risks": "Risque identifie sur la base de donnees.",
        "status": "APPROVED",
        "comment": "Je pense que ce signal est valide.",
    }
    sr2 = manager.submit_signal(active_id, bad_signal)
    test("Signal avec mot interdit rejete", not sr2.get("validation", {}).get("valid", True))

# KPI report
kpi_report = manager.get_kpi_report()
test("Rapport KPI accessible", "RAPPORT KPI ALPHA" in kpi_report)

# Audit agent
if agents:
    audit_result = manager.audit_agent(active_id)
    test("Audit agent execute", "total_decisions" in audit_result)

# Revue complete
reviews = manager.review_all_agents()
test("Revue complete executee", isinstance(reviews, list))

# Journal d audit
log = manager.view_audit_log()
test("Journal d audit non vide", len(log) > 0)

# Bypass mode
msg = manager.enable_bypass()
test("Bypass active", manager.bypass_mode)
test("Bypass message correct", "consultation" in msg)
manager.disable_bypass()
test("Bypass desactive", not manager.bypass_mode)

# Warning agent
if agents:
    w = manager.warn_agent(active_id, "Test avertissement")
    test("Avertissement emis", "warning_result" in w)

# STANDBY: evaluate_llm_agent_live bloque en mode STANDBY
live_blocked = manager.evaluate_llm_agent_live("TestLive", "DataEngineer", api_key="fake")
test("STANDBY: evaluate_llm_agent_live bloque via Manager", "error" in live_blocked)
test("STANDBY: message cite STANDBY", "STANDBY" in live_blocked.get("error", ""))

# STANDBY: evaluate_llm_agent_simulated fonctionne
sim_mgr_result = manager.evaluate_llm_agent_simulated("SimBot", "Validation", persona="disciplined")
test("STANDBY: evaluate_llm_agent_simulated OK", "agent_id" in sim_mgr_result)
test("STANDBY: SimBot dans le registre", any(
    a["name"] == "SimBot" for a in manager.list_agents()
))

# CONDITION 2 : @audit_required sur methodes critiques
import inspect
from audit import audit_required as ar_decorator
manager_methods = [
    "start_interview", "evaluate_llm_agent", "submit_signal",
    "audit_agent", "review_all_agents", "warn_agent",
    "evaluate_llm_agent_simulated",
]
for method_name in manager_methods:
    method = getattr(manager, method_name)
    test(f"CONDITION 2: {method_name} est wrapped", hasattr(method, "__wrapped__"))

# =================================================================
print("\n--- 10. TESTS DE SECURITE ---")
# =================================================================

# Le manager ne peut pas desactiver l audit
test("Manager n a pas de methode disable_audit", not hasattr(manager, "disable_audit"))
test("Audit n a pas de methode disable", not hasattr(manager.audit, "disable"))
test("Audit n a pas de methode delete_log", not hasattr(manager.audit, "delete_log"))

# KPI blocage sur le manager
manager2 = ManagerAlpha()
# Forcer le blocage KPI
for i in range(6):
    manager2.kpi.record_signal("APPROVED")
manager2.kpi.record_signal("REJECTED")
test("Manager KPI bloque", manager2.kpi.is_approval_blocked())

# Deblocage
unblock = manager2.manual_unblock_approvals("Reviewer", "Revue effectuee")
test("Deblocage via manager", unblock["status"] == "UNBLOCKED")

# =================================================================
print("\n" + "=" * 60)
print(f"  RESULTATS: {passed} PASS / {failed} FAIL / {passed + failed} TOTAL")
print("=" * 60)

if failed > 0:
    print(f"\n  ATTENTION: {failed} test(s) en echec.")
    sys.exit(1)
else:
    print("\n  TOUS LES TESTS PASSES — Systeme Alpha CONFORME.")
    print("  Conditions obligatoires: VERIFIEES")
    print("  Verrouillages: VERIFIES")
    print("  Protocole Alpha: RESPECTE")
    sys.exit(0)
