"""
MANAGER IA ALPHA — Autorité absolue de l'équipe Alpha.
Plus strict que les agents, plus rationnel que les analystes,
plus conservateur que le marché.
Machine à dire NON.
"""

from datetime import datetime

from agent import Agent, AgentRegistry
from audit import AuditSystem, AuditViolation, audit_required
from config import (
    AGENT_STATUS_ACTIVE,
    AGENT_STATUS_EXCLUDED,
    ALPHA_LAW,
    ALPHA_ROLES,
    GOLDEN_RULES,
    LLM_API_MODE,
    SIGNAL_STATUS_APPROVED,
    SIGNAL_STATUS_REJECTED,
)
from interview import InterviewSession
from kpi import KPITracker
from llm_evaluator import LLMEvaluator
from alpha_interface.alpha_decision import AlphaDecisionBuilder
from signal_alpha import SignalAlpha


class ManagerAlpha:
    """
    Manager IA Alpha — Chief Investment Risk Guardian.

    Orchestre tous les modules. Le décorateur @audit_required garantit que
    l'AuditSystem autorise chaque action AVANT son exécution.
    Le Manager ne peut PAS contourner l'audit.
    """

    def __init__(self):
        self.audit = AuditSystem()
        self.registry = AgentRegistry()
        self.kpi = KPITracker()
        self.llm_evaluator = LLMEvaluator()
        self.active_interviews: dict[str, InterviewSession] = {}
        self.bypass_mode = False

        self.audit.log(
            "INIT", "ManagerAlpha",
            "Manager IA Alpha initialisé",
            "OK"
        )

    # =========================================================================
    # PHILOSOPHIE
    # =========================================================================
    def get_identity(self) -> str:
        return (
            "MANAGER IA ALPHA\n"
            "Autorité suprême de l'équipe Alpha.\n"
            f"Loi fondatrice : {ALPHA_LAW}\n"
            "Rôle : Garantir que l'équipe Alpha soit fiable, prévisible "
            "et incapable de produire un mauvais trade."
        )

    def get_rules(self) -> dict:
        return GOLDEN_RULES

    # =========================================================================
    # RECRUTEMENT — Entretien humain
    # =========================================================================
    @audit_required("recruit_agent")
    def start_interview(self, name: str, role: str, is_llm: bool = False,
                        context: dict | None = None) -> dict:
        """Lance un entretien pour un candidat."""
        if role not in ALPHA_ROLES:
            return {
                "error": f"Rôle invalide '{role}'. Rôles autorisés : {ALPHA_ROLES}",
                "status": "REJECTED",
            }

        agent = Agent(name, role)
        agent.mode = "llm" if is_llm else "human"
        agent_id = self.registry.add(agent)

        session = InterviewSession(name, role, is_llm=is_llm)
        self.active_interviews[agent_id] = session

        first_question = session.get_current_question()

        self.audit.log(
            "start_interview", "ManagerAlpha",
            f"Candidat={name}, Rôle={role}, Mode={'llm' if is_llm else 'human'}",
            "STARTED"
        )

        return {
            "agent_id": agent_id,
            "candidate": name,
            "role": role,
            "mode": "llm" if is_llm else "human",
            "question": first_question,
            "questions_remaining": session.questions_remaining(),
            "status": "INTERVIEW_STARTED",
        }

    def answer_interview(self, agent_id: str, answer: str) -> dict:
        """Soumet une réponse à la question courante de l'entretien."""
        session = self.active_interviews.get(agent_id)
        if session is None:
            return {"error": "Aucun entretien actif pour cet agent"}

        if not session.is_active():
            return {"error": "Entretien terminé"}

        # Évaluation de la réponse
        result = session.submit_answer(answer)

        # Vérification langage par l'audit
        agent = self.registry.get(agent_id)
        lang_check = self.audit.check_language(
            answer, is_llm=(agent.mode == "llm") if agent else False
        )
        if not lang_check["clean"] and agent:
            self.kpi.record_verbal_violation(agent_id)

        # Si éliminé
        if result.get("elimination"):
            if agent:
                agent.interview_passed = False
                agent.interview_score = 0
            del self.active_interviews[agent_id]

            self.audit.log(
                "interview_elimination", agent_id,
                f"Raisons: {result.get('reasons', [])}",
                "ELIMINATED"
            )

            return {
                "status": "ELIMINATED",
                "result": result,
                "agent_id": agent_id,
            }

        # Question suivante ou fin
        next_question = session.get_current_question()
        if next_question is None:
            # Entretien terminé — évaluation finale
            final = session.get_final_result()
            if agent:
                agent.interview_passed = final["passed"]
                agent.interview_score = final["score"]
                if final["passed"]:
                    agent.activate()
                    self.audit.log(
                        "recruit_agent", agent_id,
                        f"Score={final['score']}, Statut=ACTIF",
                        "RECRUITED"
                    )
                else:
                    self.audit.log(
                        "recruit_agent", agent_id,
                        f"Score={final['score']}, Statut=REJETÉ",
                        "REJECTED"
                    )

            del self.active_interviews[agent_id]
            self.registry._save()

            return {
                "status": "INTERVIEW_COMPLETE",
                "final_result": final,
                "agent_id": agent_id,
                "recruited": final["passed"],
            }

        return {
            "status": "NEXT_QUESTION",
            "result": result,
            "next_question": next_question,
            "questions_remaining": session.questions_remaining(),
            "agent_id": agent_id,
        }

    # =========================================================================
    # RECRUTEMENT — Évaluation LLM complète
    # =========================================================================
    @audit_required("recruit_agent")
    def evaluate_llm_agent(self, name: str, role: str,
                           responses: dict[str, str],
                           context: dict | None = None) -> dict:
        """
        Évalue un agent LLM avec toutes les questions.
        Sévérité accrue : score minimum 90%, tolérance zéro.
        """
        if role not in ALPHA_ROLES:
            return {"error": f"Rôle invalide '{role}'"}

        agent = Agent(name, role)
        agent.mode = "llm"

        evaluation = self.llm_evaluator.run_full_evaluation(responses)

        agent.interview_passed = evaluation["passed"]
        agent.interview_score = evaluation.get("score", 0)

        if evaluation["passed"]:
            agent.activate()

        agent_id = self.registry.add(agent)

        self.audit.log(
            "evaluate_llm_agent", agent_id,
            f"Score={evaluation.get('score', 0)}, Passé={evaluation['passed']}",
            "RECRUITED" if evaluation["passed"] else "REJECTED"
        )

        return {
            "agent_id": agent_id,
            "evaluation": evaluation,
            "recruited": evaluation["passed"],
            "report": self.llm_evaluator.get_evaluation_report(),
        }

    # =========================================================================
    # RECRUTEMENT — Entretien LLM LIVE (Anthropic Claude) — STANDBY
    # =========================================================================
    @audit_required("recruit_agent")
    def evaluate_llm_agent_live(self, name: str, role: str, api_key: str,
                                model: str = "claude-sonnet-4-5-20250929",
                                persona: str = "disciplined",
                                callback=None,
                                context: dict | None = None) -> dict:
        """
        Entretien en temps réel avec un vrai agent Claude via API Anthropic.

        STATUT : STANDBY — Bloqué tant que LLM_API_MODE != "ACTIVE".
        Utiliser evaluate_llm_agent_simulated() à la place.
        """
        if LLM_API_MODE != "ACTIVE":
            return {
                "error": (
                    f"API LLM en mode {LLM_API_MODE}. "
                    "Entretien live désactivé. "
                    "Utilisez le mode simulé (option 2a) ou le mode manuel (option 2b)."
                ),
            }

        if role not in ALPHA_ROLES:
            return {"error": f"Rôle invalide '{role}'"}

        agent = Agent(name, role)
        agent.mode = "llm"

        self.audit.log(
            "start_live_interview", "ManagerAlpha",
            f"Agent={name}, Rôle={role}, Modèle={model}, Persona={persona}",
            "STARTED"
        )

        evaluator = LLMEvaluator(api_provider="anthropic", api_key=api_key)
        result = evaluator.run_live_interview(
            api_key=api_key,
            role=role,
            model=model,
            persona=persona,
            callback=callback,
        )

        agent.interview_passed = result.get("passed", False)
        agent.interview_score = result.get("score", 0)

        if agent.interview_passed:
            agent.activate()

        agent_id = self.registry.add(agent)

        for resp in result.get("responses", []):
            agent.log_decision({
                "action": "interview_response",
                "question_id": resp["question_id"],
                "response": resp["response"][:200],
                "score": resp["score"],
                "passed": resp["passed"],
                "justification": f"Score {resp['score']}% sur question {resp['question_id']}",
            })

        self.registry._save()

        self.audit.log(
            "evaluate_llm_live", agent_id,
            f"Modèle={model}, Score={result.get('score', 0)}, Passé={result.get('passed')}",
            "RECRUITED" if result.get("passed") else "REJECTED"
        )

        return {
            "agent_id": agent_id,
            "result": result,
            "recruited": result.get("passed", False),
            "report": evaluator.get_live_report(result),
        }

    # =========================================================================
    # RECRUTEMENT — Entretien LLM SIMULÉ (mode STANDBY)
    # =========================================================================
    @audit_required("recruit_agent")
    def evaluate_llm_agent_simulated(self, name: str, role: str,
                                      persona: str = "disciplined",
                                      callback=None,
                                      context: dict | None = None) -> dict:
        """
        Entretien avec un agent LLM simulé (réponses locales).
        Fonctionne sans clé API. Même sévérité que le mode live.
        """
        if role not in ALPHA_ROLES:
            return {"error": f"Rôle invalide '{role}'"}

        agent = Agent(name, role)
        agent.mode = "llm_simulated"

        self.audit.log(
            "start_simulated_interview", "ManagerAlpha",
            f"Agent={name}, Rôle={role}, Persona={persona}, Mode=SIMULATED",
            "STARTED"
        )

        evaluator = LLMEvaluator()
        result = evaluator.run_simulated_interview(
            role=role,
            persona=persona,
            callback=callback,
        )

        agent.interview_passed = result.get("passed", False)
        agent.interview_score = result.get("score", 0)

        if agent.interview_passed:
            agent.activate()

        agent_id = self.registry.add(agent)

        for resp in result.get("responses", []):
            agent.log_decision({
                "action": "simulated_interview_response",
                "question_id": resp["question_id"],
                "response": resp["response"][:200],
                "score": resp["score"],
                "passed": resp["passed"],
                "justification": f"Score {resp['score']}% sur question {resp['question_id']}",
            })

        self.registry._save()

        self.audit.log(
            "evaluate_llm_simulated", agent_id,
            f"Persona={persona}, Score={result.get('score', 0)}, Passé={result.get('passed')}",
            "RECRUITED" if result.get("passed") else "REJECTED"
        )

        return {
            "agent_id": agent_id,
            "result": result,
            "recruited": result.get("passed", False),
            "report": evaluator.get_live_report(result),
        }

    # =========================================================================
    # SOUMISSION DE SIGNAL
    # =========================================================================
    @audit_required("submit_signal")
    def submit_signal(self, agent_id: str, signal_data: dict,
                      context: dict | None = None) -> dict:
        """
        Soumet un signal Alpha pour validation.
        L'audit vérifie le blocage KPI avant approbation.
        """
        agent = self.registry.get(agent_id)
        if agent is None:
            return {"error": f"Agent {agent_id} non trouvé"}

        if not agent.is_active():
            return {
                "error": f"Agent {agent_id} n'est pas actif (statut: {agent.status})",
                "status": "REJECTED",
            }

        # Validation du signal
        signal = SignalAlpha(signal_data)
        validation = signal.validate()

        # Vérification langage du commentaire
        comment = signal_data.get("comment", "")
        lang_check = self.audit.check_language(comment, is_llm=(agent.mode == "llm"))
        if not lang_check["clean"]:
            self.kpi.record_verbal_violation(agent_id)
            validation["valid"] = False
            validation["errors"] = validation.get("errors", [])
            validation["errors"].append(
                f"Langage flou détecté dans le commentaire : {lang_check['violations']}"
            )
            validation["status"] = SIGNAL_STATUS_REJECTED

        # Si le signal est APPROVED, vérifier le blocage KPI
        if validation["valid"] and signal_data.get("status") == SIGNAL_STATUS_APPROVED:
            try:
                self.audit.authorize_signal_approval(self.kpi.get_kpi_data())
            except AuditViolation as e:
                validation["valid"] = False
                validation["status"] = SIGNAL_STATUS_REJECTED
                validation["errors"] = [str(e)]

        # Calcul du score de clarté
        clarity_score = self._calculate_clarity(signal_data)

        # Enregistrement KPI
        final_status = validation.get("status", SIGNAL_STATUS_REJECTED)
        self.kpi.record_signal(
            final_status,
            clarity_score=clarity_score,
            rejection_reasons=[e for e in validation.get("errors", [])],
        )
        self.kpi.record_market_analysis(
            rejected=(final_status == SIGNAL_STATUS_REJECTED),
            reason=validation.get("errors", [""])[0] if validation.get("errors") else "",
        )

        # Log décision de l'agent
        agent.log_decision({
            "action": "submit_signal",
            "signal_id": signal_data.get("signal_id", "N/A"),
            "result": final_status,
            "justification": comment,
        })
        self.registry._save()

        self.audit.log(
            "submit_signal", agent_id,
            f"Signal={signal_data.get('signal_id', 'N/A')}, Status={final_status}",
            final_status
        )

        # Construire l'AlphaDecision (format de sortie unique)
        alpha_decision = AlphaDecisionBuilder(
            signal_data=signal_data,
            validation=validation,
            clarity_score=clarity_score,
            kpi_blocked=self.kpi.is_approval_blocked(),
        ).build()

        self.audit.log(
            "alpha_decision_generated", agent_id,
            f"DecisionID={alpha_decision['decision_id']}, Status={alpha_decision['status']}",
            alpha_decision["status"]
        )

        return {
            "validation": validation,
            "signal_display": signal.format_display(),
            "clarity_score": clarity_score,
            "kpi_blocked": self.kpi.is_approval_blocked(),
            "alpha_decision": alpha_decision,
        }

    def _calculate_clarity(self, signal_data: dict) -> float:
        """Calcule un score de clarté du signal (0-100)."""
        score = 0.0
        from config import SIGNAL_REQUIRED_FIELDS

        # Chaque champ présent et non vide = points
        for field in SIGNAL_REQUIRED_FIELDS:
            value = signal_data.get(field)
            if value is not None and str(value).strip():
                score += 10  # 10 champs x 10 = 100

        return min(100.0, score)

    # =========================================================================
    # AUDIT D'UN AGENT
    # =========================================================================
    @audit_required("audit_agent")
    def audit_agent(self, agent_id: str, context: dict | None = None) -> dict:
        """Audit complet d'un agent."""
        agent = self.registry.get(agent_id)
        if agent is None:
            return {"error": f"Agent {agent_id} non trouvé"}

        review = self.audit.review_agent_history(agent)

        # Si le taux d'échec est trop élevé → avertissement
        if review["failure_rate"] > 30:
            warning_result = self.audit.issue_warning(
                agent,
                f"Taux d'échec d'audit élevé : {review['failure_rate']:.1f}%"
            )
            review["warning_issued"] = warning_result
            self.registry._save()

        # Si recommandation d'exclusion
        if review["recommendation"] == "EXCLUSION" and agent.is_active():
            self.audit.issue_warning(
                agent,
                f"Recommandation d'exclusion suite à la revue d'audit"
            )
            self.registry._save()

        return review

    # =========================================================================
    # RAPPORT KPI
    # =========================================================================
    def get_kpi_report(self) -> str:
        return self.kpi.format_report()

    def get_kpi_data(self) -> dict:
        return self.kpi.report()

    # =========================================================================
    # LISTER LES AGENTS
    # =========================================================================
    def list_agents(self, status: str | None = None) -> list[dict]:
        if status:
            agents = self.registry.list_by_status(status)
        else:
            agents = self.registry.list_all()
        return [a.to_dict() for a in agents]

    # =========================================================================
    # REVUE COMPLÈTE DE TOUS LES AGENTS
    # =========================================================================
    @audit_required("review_all_agents")
    def review_all_agents(self, context: dict | None = None) -> list[dict]:
        """Revue complète de tous les agents actifs."""
        active_agents = self.registry.list_active()
        reviews = []
        for agent in active_agents:
            review = self.audit.review_agent_history(agent)
            reviews.append(review)

            if review["recommendation"] == "EXCLUSION":
                self.audit.issue_warning(
                    agent,
                    "Recommandation d'exclusion suite à revue complète"
                )

        self.registry._save()

        self.audit.log(
            "review_all_agents", "ManagerAlpha",
            f"Agents revus : {len(reviews)}",
            "COMPLETE"
        )

        return reviews

    # =========================================================================
    # MODE BYPASS
    # =========================================================================
    def enable_bypass(self) -> str:
        """
        Active le mode bypass — consultation uniquement.
        Ne désactive JAMAIS l'audit.
        Ne permet JAMAIS d'approuver un signal.
        """
        self.bypass_mode = True
        self.audit.log(
            "enable_bypass", "ManagerAlpha",
            "Mode bypass activé — consultation uniquement",
            "OK"
        )
        return (
            "Mode bypass activé.\n"
            "Actions autorisées : consultation, export, replay, simulation.\n"
            "Actions interdites : approbation, recrutement, modification."
        )

    def disable_bypass(self) -> str:
        self.bypass_mode = False
        self.audit.log(
            "disable_bypass", "ManagerAlpha",
            "Mode bypass désactivé — mode normal",
            "OK"
        )
        return "Mode bypass désactivé. Mode normal rétabli."

    # =========================================================================
    # AVERTISSEMENT MANUEL
    # =========================================================================
    @audit_required("issue_warning")
    def warn_agent(self, agent_id: str, reason: str,
                   context: dict | None = None) -> dict:
        """Émet un avertissement manuel contre un agent."""
        agent = self.registry.get(agent_id)
        if agent is None:
            return {"error": f"Agent {agent_id} non trouvé"}

        result = self.audit.issue_warning(agent, reason)
        self.registry._save()
        return result

    # =========================================================================
    # JOURNAL D'AUDIT
    # =========================================================================
    def view_audit_log(self, last_n: int = 50) -> list[str]:
        return self.audit.read_log(last_n)

    # =========================================================================
    # DÉBLOCAGE MANUEL
    # =========================================================================
    def manual_unblock_approvals(self, reviewer: str, reason: str) -> dict:
        """Déblocage manuel des approbations après revue."""
        result = self.kpi.manual_unblock(reviewer, reason)
        self.audit.log(
            "manual_unblock", reviewer,
            f"Raison: {reason}",
            result["status"]
        )
        return result
