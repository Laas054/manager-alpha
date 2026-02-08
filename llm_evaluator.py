"""
LLM EVALUATOR — Évaluation des agents LLM.
Sévérité >= humains. Tolérance zéro. Score minimum 90%.
"""

import json
import os
import re
from datetime import datetime

from config import (
    FORBIDDEN_WORDS_LLM,
    INTERVIEW_PASS_SCORE_LLM,
)
from interview import InterviewEvaluator, MANDATORY_QUESTIONS


class LLMEvaluator:
    """
    Évalue les réponses d'agents LLM avec sévérité accrue.
    - Seuils plus stricts : 90% minimum
    - Mots interdits étendus
    - Détection de hedging et ambiguïté
    - Tolérance zéro : un seul échec = rejet
    """

    def __init__(self, api_provider: str | None = None, api_key: str | None = None):
        self.api_provider = api_provider  # "openai", "anthropic", ou None (local)
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
    # ÉVALUATION VIA API (si disponible)
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
    # ENTRETIEN COMPLET
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
