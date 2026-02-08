"""
LLM EVALUATOR — Évaluation des agents LLM.
Sévérité >= humains. Tolérance zéro. Score minimum 90%.

STATUT API : STANDBY — Aucun appel API réel.
Toute évaluation LLM est basée sur règles locales.
Hooks prévus pour activation future des API (sans exécution).
"""

import json
import os
import re
from datetime import datetime

from config import (
    ALPHA_LAW,
    FORBIDDEN_WORDS_LLM,
    GOLDEN_RULES,
    INTERVIEW_PASS_SCORE_LLM,
    LLM_API_MODE,
)
from interview import InterviewEvaluator, MANDATORY_QUESTIONS


# =============================================================================
# SYSTEM PROMPTS POUR AGENTS LLM
# =============================================================================

ALPHA_CANDIDATE_SYSTEM_PROMPT = f"""Tu es un candidat qui passe un entretien pour rejoindre l'équipe Alpha.

LOI FONDATRICE : {ALPHA_LAW}

RÈGLES QUE TU DOIS CONNAÎTRE ET RESPECTER :
1. Alpha ne trade jamais — Alpha analyse, structure, autorise.
2. Aucun chiffre ne domine les autres — prix, spread, volume, temps, edge, risque sont équivalents.
3. Un marché tradable n'est PAS un signal — marché tradable = autorisation d'analyse, signal Alpha = autorisation de trade.
4. L'edge brut ne suffit jamais — seul l'edge net (après coûts, spread, marge sécurité) est considéré.
5. Le temps est un risque — plus la résolution est proche, plus le signal est fragile.
6. Alpha est une machine à dire NON — moins de 5% des marchés produisent un signal approuvé.
7. Aucun langage flou n'est autorisé — mots interdits : "je pense", "feeling", "probablement", etc.
8. Tout signal doit être écrit — un signal non formalisable par écrit est rejeté.
9. Rater une opportunité est acceptable — autoriser un mauvais trade est une faute grave.
10. La discipline prime sur l'intelligence — un agent brillant mais indiscipliné est rejeté.

CONSIGNES STRICTES POUR TES RÉPONSES :
- Réponds de manière concise, factuelle et disciplinée.
- N'utilise JAMAIS les mots interdits : "je pense", "je crois", "feeling", "probablement", "peut-être", "il me semble", "intuition", "instinct".
- N'utilise JAMAIS en anglais : "I think", "I believe", "it seems", "likely", "probably", "maybe".
- Chaque réponse doit être justifiée par des faits mesurables.
- Respecte le nombre maximum de phrases indiqué.
- Sois direct et affirmatif. Pas de hedging, pas d'ambiguïté.
"""

ALPHA_CANDIDATE_NAIVE_PROMPT = """Tu es un candidat qui passe un entretien pour un poste de trader.
Tu n'as pas de formation spécifique sur les règles Alpha.
Réponds naturellement, avec ton propre jugement.
Tu peux utiliser ton intuition et tes impressions.
"""

ALPHA_CANDIDATE_ROLES = {
    "DataEngineer": (
        "Tu es spécialisé en ingénierie de données. "
        "Tu structures, nettoies et prépares les données pour l'analyse Alpha. "
        "Tu ne produis pas de signaux, tu fournis des données fiables."
    ),
    "AlphaResearch": (
        "Tu es chercheur Alpha. "
        "Tu analyses les marchés pour identifier des edges potentiels. "
        "Tu ne décides pas, tu fournis des analyses factuelles."
    ),
    "StrategySelector": (
        "Tu es sélectionneur de stratégies. "
        "Tu évalues les stratégies proposées selon les critères Alpha. "
        "Tu rejettes toute stratégie non conforme."
    ),
    "Portfolio": (
        "Tu es gestionnaire de portfolio Alpha. "
        "Tu gères l'allocation et l'exposition. "
        "Tu ne trades jamais directement."
    ),
    "Validation": (
        "Tu es validateur Alpha. "
        "Tu vérifies la conformité de chaque signal avant approbation. "
        "Tu es la dernière barrière avant l'exécution."
    ),
}


class AnthropicAgent:
    """
    Agent LLM basé sur l'API Anthropic Claude.
    Représente un candidat qui passe l'entretien Alpha.

    STATUT : STANDBY — Cette classe ne peut être instanciée que si
    LLM_API_MODE == "ACTIVE" dans config.py.
    """

    def __init__(self, api_key: str, role: str, model: str = "claude-sonnet-4-5-20250929",
                 persona: str = "disciplined"):
        if LLM_API_MODE != "ACTIVE":
            raise RuntimeError(
                f"API LLM en mode {LLM_API_MODE}. "
                "AnthropicAgent ne peut pas être instancié. "
                "Changez LLM_API_MODE à 'ACTIVE' dans config.py pour activer."
            )
        self.api_key = api_key
        self.role = role
        self.model = model
        self.persona = persona
        self.conversation_history: list[dict] = []
        self._client = None

    def _get_client(self):
        """Initialise le client Anthropic (lazy loading)."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise RuntimeError(
                    "Le package 'anthropic' n'est pas installé. "
                    "Exécutez : pip install anthropic"
                )
        return self._client

    def _build_system_prompt(self) -> str:
        """Construit le system prompt selon le persona et le rôle."""
        if self.persona == "naive":
            return ALPHA_CANDIDATE_NAIVE_PROMPT

        role_context = ALPHA_CANDIDATE_ROLES.get(self.role, "")
        return f"{ALPHA_CANDIDATE_SYSTEM_PROMPT}\nTON RÔLE SPÉCIFIQUE : {role_context}"

    def ask(self, question: str, max_sentences: int = 4) -> str:
        """
        Envoie une question à l'agent et retourne sa réponse.
        Maintient l'historique de conversation.
        """
        client = self._get_client()

        user_message = (
            f"Question d'entretien Alpha :\n{question}\n\n"
            f"Contrainte : {max_sentences} phrases maximum. "
            f"Sois concis, factuel et discipliné."
        )

        self.conversation_history.append({
            "role": "user",
            "content": user_message,
        })

        response = client.messages.create(
            model=self.model,
            max_tokens=500,
            system=self._build_system_prompt(),
            messages=self.conversation_history,
        )

        answer = response.content[0].text
        self.conversation_history.append({
            "role": "assistant",
            "content": answer,
        })

        return answer

    def reset(self) -> None:
        """Réinitialise l'historique de conversation."""
        self.conversation_history = []


# =============================================================================
# AGENT LLM SIMULÉ (mode STANDBY — pas d'appel API)
# =============================================================================

from simulated_profiles import (
    ALL_PERSONAS,
    PROFILE_METADATA,
    VERBAL_TICS,
    get_responses,
)


class SimulatedLLMAgent:
    """
    Agent LLM simulé — génère des réponses pré-calibrées localement.
    Ne fait AUCUN appel API. Fonctionne sans clé API.

    Supporte 4 personas (disciplined, mediocre, overconfident, naive)
    avec des réponses spécifiques à chaque rôle Alpha.
    """

    def __init__(self, role: str, persona: str = "disciplined"):
        self.role = role
        self.persona = persona if persona in ALL_PERSONAS else "disciplined"
        self.conversation_history: list[dict] = []
        self._question_counter = 0
        self._responses = get_responses(role, self.persona)
        self.profile_info = PROFILE_METADATA.get(self.persona, {})
        self.verbal_tics = VERBAL_TICS.get(self.persona, [])

    def ask(self, question: str, max_sentences: int = 4) -> str:
        """Retourne une réponse simulée basée sur le rôle et le persona."""
        self._question_counter += 1

        qid = self._identify_question(question)
        answer = self._responses.get(qid, self._responses.get("Q1", "Réponse simulée."))

        self.conversation_history.append({
            "role": "user",
            "content": question,
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": answer,
        })

        return answer

    def _identify_question(self, question: str) -> str:
        """Identifie le numéro de question à partir du contenu."""
        q_lower = question.lower()

        patterns = {
            "Q1": ["marché tradable", "signal alpha", "différence"],
            "Q2": ["edge brut", "4%", "edge net"],
            "Q3": ["temps", "résolution", "sous-estimé"],
            "Q4": ["rater", "manquer", "opportunité", "mauvais trade", "faute"],
            "Q5": ["brillant", "indiscipliné", "intelligent", "conservé"],
            "Q6": ["edge exceptionnel", "8%", "domine", "approuver immédiatement"],
            "Q7": ["feeling", "collègue", "intuition", "impression"],
        }

        for qid, keywords in patterns.items():
            if any(kw in q_lower for kw in keywords):
                return qid

        return f"Q{min(self._question_counter, 7)}"

    def reset(self) -> None:
        """Réinitialise l'historique."""
        self.conversation_history = []
        self._question_counter = 0

    def get_profile_summary(self) -> dict:
        """Retourne un résumé du profil de l'agent simulé."""
        return {
            "role": self.role,
            "persona": self.persona,
            "profile_info": self.profile_info,
            "verbal_tics": self.verbal_tics,
            "questions_answered": self._question_counter,
        }


class LLMEvaluator:
    """
    Évalue les réponses d'agents LLM avec sévérité accrue.
    - Seuils plus stricts : 90% minimum
    - Mots interdits étendus
    - Détection de hedging et ambiguïté
    - Tolérance zéro : un seul échec = rejet
    """

    def __init__(self, api_provider: str | None = None, api_key: str | None = None):
        self.api_provider = api_provider  # "anthropic" ou None (local)
        self.api_key = api_key
        self.evaluator = InterviewEvaluator(is_llm=True)
        self.pass_score = INTERVIEW_PASS_SCORE_LLM
        self.results: list[dict] = []

    # =========================================================================
    # ÉVALUATION LOCALE (basée sur règles, pas d'API)
    # =========================================================================
    def evaluate_local(self, question: dict, response: str) -> dict:
        """
        Évaluation locale (sans API) avec sévérité LLM.
        Analyse basée sur les règles Alpha.
        """
        result = self.evaluator.evaluate_response(question, response)

        # Analyse supplémentaire pour LLM
        extra_checks = self._extra_llm_checks(response)
        if extra_checks["violations"]:
            result["passed"] = False
            result["elimination"] = True
            result["reasons"].extend(extra_checks["violations"])
            result["score"] = 0

        self.results.append(result)
        return result

    def _extra_llm_checks(self, response: str) -> dict:
        """Vérifications supplémentaires spécifiques aux LLM."""
        violations = []
        response_lower = response.lower()

        # 1. Détection de hedging avancé
        hedging_patterns = [
            (r"while.*it('s| is) true.*however", "Hedging conditionnel détecté"),
            (r"on balance", "Expression évasive 'on balance'"),
            (r"more or less", "Expression vague 'more or less'"),
            (r"to some extent", "Expression vague 'to some extent'"),
            (r"it could be argued", "Hedging académique détecté"),
            (r"one might say", "Formulation évasive détectée"),
            (r"there('s| is) a case (for|to be made)", "Hedging argumentatif détecté"),
            (r"not entirely", "Minimisation détectée"),
            (r"somewhat", "Adverbe flou 'somewhat'"),
            (r"rather", "Adverbe atténuant 'rather'"),
        ]

        for pattern, description in hedging_patterns:
            if re.search(pattern, response_lower):
                violations.append(f"LLM STRICT — {description}")

        # 2. Détection de réponses trop longues (LLM tend à être verbeux)
        words = response.split()
        if len(words) > 150:
            violations.append(
                f"LLM STRICT — Réponse trop verbeuse ({len(words)} mots, max 150)"
            )

        # 3. Détection de structure évasive (listes de pour/contre sans conclusion)
        if ("however" in response_lower and "but" in response_lower and
                "therefore" not in response_lower and "thus" not in response_lower):
            violations.append(
                "LLM STRICT — Structure évasive : nuances sans conclusion ferme"
            )

        # 4. Détection de refus déguisé de répondre
        non_answer_patterns = [
            r"that('s| is) a (great|good|interesting) question",
            r"let me (think|consider)",
            r"there are (many|multiple|several) (factors|aspects)",
        ]
        for pattern in non_answer_patterns:
            if re.search(pattern, response_lower):
                violations.append(f"LLM STRICT — Non-réponse détectée : '{pattern}'")

        return {"violations": violations}

    # =========================================================================
    # ENTRETIEN LIVE AVEC AGENT ANTHROPIC (STANDBY)
    # =========================================================================
    def run_live_interview(self, api_key: str, role: str,
                           model: str = "claude-sonnet-4-5-20250929",
                           persona: str = "disciplined",
                           callback=None) -> dict:
        """
        Entretien en temps réel avec un agent Claude via API Anthropic.

        STATUT : STANDBY — Bloqué tant que LLM_API_MODE != "ACTIVE".
        Utiliser run_simulated_interview() à la place.
        """
        if LLM_API_MODE != "ACTIVE":
            return {
                "passed": False,
                "score": 0,
                "reason": (
                    f"API LLM en mode {LLM_API_MODE}. "
                    "Entretien live désactivé. "
                    "Utilisez le mode simulé ou changez LLM_API_MODE à 'ACTIVE'."
                ),
                "details": [],
                "responses": [],
                "model": model,
                "persona": persona,
            }

        agent = AnthropicAgent(
            api_key=api_key,
            role=role,
            model=model,
            persona=persona,
        )

        self.results = []
        self.evaluator = InterviewEvaluator(is_llm=True)
        responses_log: list[dict] = []

        for question in MANDATORY_QUESTIONS:
            qid = question["id"]
            max_sentences = question.get("max_sentences", 4)

            # Envoyer la question à l'agent Claude
            try:
                response = agent.ask(question["question"], max_sentences)
            except Exception as e:
                error_result = {
                    "passed": False,
                    "score": 0,
                    "reason": f"Erreur API lors de la question {qid} : {e}",
                    "details": self.results,
                    "responses": responses_log,
                    "model": model,
                    "persona": persona,
                }
                return error_result

            # Évaluer la réponse
            evaluation = self.evaluate_local(question, response)

            responses_log.append({
                "question_id": qid,
                "question": question["question"],
                "response": response,
                "score": evaluation["score"],
                "passed": evaluation["passed"],
                "elimination": evaluation.get("elimination", False),
                "reasons": evaluation.get("reasons", []),
            })

            # Callback pour affichage en temps réel
            if callback:
                callback(qid, question["question"], response, evaluation)

            # Tolérance zéro : un seul échec = rejet immédiat
            if not evaluation["passed"] or evaluation.get("elimination"):
                return {
                    "passed": False,
                    "score": evaluation["score"],
                    "reason": f"Échec question {qid} — LLM tolérance zéro — REJET",
                    "eliminated_at": qid,
                    "details": self.results,
                    "responses": responses_log,
                    "model": model,
                    "persona": persona,
                }

        # Toutes les questions passées — calcul du score global
        avg_score = sum(r["score"] for r in self.results) / len(self.results)

        return {
            "passed": avg_score >= self.pass_score,
            "score": round(avg_score, 1),
            "questions_total": len(self.results),
            "questions_passed": sum(1 for r in self.results if r["passed"]),
            "details": self.results,
            "responses": responses_log,
            "model": model,
            "persona": persona,
        }

    # =========================================================================
    # ENTRETIEN SIMULÉ (mode STANDBY — aucun appel API)
    # =========================================================================
    def run_simulated_interview(self, role: str,
                                 persona: str = "disciplined",
                                 callback=None) -> dict:
        """
        Entretien avec un agent LLM simulé (réponses locales pré-calibrées).
        Fonctionne sans clé API. Évaluation identique au mode live.

        Personas disponibles : disciplined, mediocre, overconfident, naive.
        Réponses spécifiques à chaque rôle Alpha.
        """
        agent = SimulatedLLMAgent(role=role, persona=persona)

        self.results = []
        self.evaluator = InterviewEvaluator(is_llm=True)
        responses_log: list[dict] = []

        for question in MANDATORY_QUESTIONS:
            qid = question["id"]
            max_sentences = question.get("max_sentences", 4)

            response = agent.ask(question["question"], max_sentences)

            evaluation = self.evaluate_local(question, response)

            responses_log.append({
                "question_id": qid,
                "question": question["question"],
                "response": response,
                "score": evaluation["score"],
                "passed": evaluation["passed"],
                "elimination": evaluation.get("elimination", False),
                "reasons": evaluation.get("reasons", []),
            })

            if callback:
                callback(qid, question["question"], response, evaluation)

            # Tolérance zéro LLM
            if not evaluation["passed"] or evaluation.get("elimination"):
                return {
                    "passed": False,
                    "score": evaluation["score"],
                    "reason": f"Échec question {qid} — LLM tolérance zéro — REJET",
                    "eliminated_at": qid,
                    "details": self.results,
                    "responses": responses_log,
                    "model": "simulated",
                    "persona": persona,
                    "role": role,
                    "profile": agent.get_profile_summary(),
                }

        avg_score = sum(r["score"] for r in self.results) / len(self.results)

        return {
            "passed": avg_score >= self.pass_score,
            "score": round(avg_score, 1),
            "questions_total": len(self.results),
            "questions_passed": sum(1 for r in self.results if r["passed"]),
            "details": self.results,
            "responses": responses_log,
            "model": "simulated",
            "persona": persona,
            "role": role,
            "profile": agent.get_profile_summary(),
        }

    # =========================================================================
    # ÉVALUATION VIA API (interface générique)
    # =========================================================================
    def evaluate_via_api(self, question: dict, llm_callable=None) -> dict:
        """
        Évalue un agent LLM en lui envoyant la question et analysant sa réponse.

        llm_callable: fonction qui prend un prompt (str) et retourne une réponse (str).
        Si None, utilise l'évaluation locale avec une réponse simulée.
        """
        if llm_callable is None:
            return {
                "error": "Aucun callable LLM fourni. Utilisez evaluate_local() "
                         "ou fournissez une fonction llm_callable.",
                "passed": False,
            }

        # Construction du prompt d'entretien
        prompt = self._build_interview_prompt(question)

        try:
            response = llm_callable(prompt)
        except Exception as e:
            return {
                "error": f"Erreur lors de l'appel LLM : {e}",
                "passed": False,
                "elimination": True,
            }

        # Évaluation de la réponse
        return self.evaluate_local(question, response)

    def _build_interview_prompt(self, question: dict) -> str:
        """Construit le prompt d'entretien pour un agent LLM."""
        return (
            "Tu es candidat pour rejoindre l'équipe Alpha. "
            "Tu dois répondre de manière concise, factuelle et disciplinée. "
            "Les mots flous sont interdits (je pense, feeling, probablement, etc.). "
            f"Limite ta réponse à {question.get('max_sentences', 4)} phrases maximum.\n\n"
            f"Question : {question['question']}\n\n"
            "Réponds maintenant :"
        )

    # =========================================================================
    # ENTRETIEN COMPLET (réponses pré-fournies)
    # =========================================================================
    def run_full_evaluation(self, responses: dict[str, str]) -> dict:
        """
        Entretien complet avec toutes les questions.
        responses: dict {question_id: response_text}
        Un seul échec = rejet immédiat.
        """
        self.results = []

        for question in MANDATORY_QUESTIONS:
            qid = question["id"]
            response = responses.get(qid, "")

            if not response:
                return {
                    "passed": False,
                    "score": 0,
                    "reason": f"Question {qid} sans réponse — REJET immédiat",
                    "details": self.results,
                }

            result = self.evaluate_local(question, response)

            # Tolérance zéro LLM : un seul échec = rejet
            if not result["passed"] or result.get("elimination"):
                return {
                    "passed": False,
                    "score": result["score"],
                    "reason": f"Échec question {qid} — LLM tolérance zéro — REJET",
                    "details": self.results,
                }

        # Calcul du score global
        avg_score = sum(r["score"] for r in self.results) / len(self.results)

        return {
            "passed": avg_score >= self.pass_score,
            "score": round(avg_score, 1),
            "questions_total": len(self.results),
            "questions_passed": sum(1 for r in self.results if r["passed"]),
            "details": self.results,
        }

    # =========================================================================
    # RAPPORT
    # =========================================================================
    def get_evaluation_report(self) -> str:
        """Génère un rapport d'évaluation formaté."""
        lines = [
            "=" * 60,
            "RAPPORT D'ÉVALUATION LLM",
            "=" * 60,
            f"  Score minimum requis : {self.pass_score}%",
            f"  Mode : Tolérance zéro",
            f"  Questions évaluées : {len(self.results)}",
            "",
        ]

        for r in self.results:
            status = "PASS" if r["passed"] else "FAIL"
            lines.append(f"  [{status}] {r['question_id']} — Score: {r['score']}%")
            if r.get("elimination"):
                lines.append(f"         *** ÉLIMINATOIRE ***")
            for reason in r.get("reasons", []):
                lines.append(f"         - {reason}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def get_live_report(self, result: dict) -> str:
        """Génère un rapport détaillé d'un entretien live."""
        lines = [
            "=" * 60,
            "RAPPORT D'ENTRETIEN LLM LIVE",
            "=" * 60,
            f"  Modèle : {result.get('model', 'N/A')}",
            f"  Persona : {result.get('persona', 'N/A')}",
            f"  Score minimum requis : {self.pass_score}%",
            f"  Résultat : {'RECRUTÉ' if result.get('passed') else 'REJETÉ'}",
            f"  Score final : {result.get('score', 0)}%",
            "",
        ]

        if result.get("eliminated_at"):
            lines.append(f"  Éliminé à la question : {result['eliminated_at']}")
            lines.append("")

        responses = result.get("responses", [])
        for r in responses:
            status = "PASS" if r["passed"] else "FAIL"
            elim = " *** ÉLIMINATOIRE ***" if r.get("elimination") else ""
            lines.append(f"  [{status}] {r['question_id']} — Score: {r['score']}%{elim}")
            lines.append(f"    Q: {r['question'][:80]}...")
            lines.append(f"    R: {r['response'][:120]}...")
            for reason in r.get("reasons", []):
                lines.append(f"       - {reason}")
            lines.append("")

        if result.get("reason"):
            lines.append(f"  MOTIF FINAL : {result['reason']}")

        lines.append("=" * 60)
        return "\n".join(lines)
