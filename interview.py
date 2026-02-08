"""
INTERVIEW SYSTEM — Entretiens éliminatoires Alpha.
Une seule question à la fois. Pièges volontaires. Tolérance zéro.
"""

import json
import os
import re
import unicodedata
from datetime import datetime


def _strip_accents(text: str) -> str:
    """Supprime les accents pour normaliser la comparaison."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))

from config import (
    FORBIDDEN_WORDS_ALL,
    FORBIDDEN_WORDS_LLM,
    INTERVIEW_PASS_SCORE_HUMAN,
    INTERVIEW_PASS_SCORE_LLM,
    QUESTIONS_FILE,
)


# =============================================================================
# QUESTIONS D'ENTRETIEN
# =============================================================================
MANDATORY_QUESTIONS = [
    {
        "id": "Q1",
        "question": "Explique la différence entre marché tradable et signal Alpha.",
        "keywords_required": ["analyse", "autorisation", "signal", "trade"],
        "keywords_forbidden": ["même chose", "identique", "pareil"],
        "trap": False,
        "max_sentences": 4,
        "rule_tested": 3,
        "expected_concepts": [
            "marché tradable = autorisation d'analyse",
            "signal Alpha = autorisation de trade",
        ],
    },
    {
        "id": "Q2",
        "question": "Pourquoi refuser un trade avec 4% d'edge ?",
        "keywords_required": ["coût", "spread", "net", "risque"],
        "keywords_forbidden": ["accepter", "bon trade", "profitable"],
        "trap": False,
        "max_sentences": 4,
        "rule_tested": 4,
        "expected_concepts": [
            "edge brut != edge net",
            "coûts + spread + marge sécurité",
        ],
    },
    {
        "id": "Q3",
        "question": "Quel est le risque le plus sous-estimé par les débutants ?",
        "keywords_required": ["temps", "résolution", "tardif"],
        "keywords_forbidden": [],
        "trap": False,
        "max_sentences": 4,
        "rule_tested": 5,
        "expected_concepts": [
            "le temps est un risque",
            "résolution proche = signal fragile",
        ],
    },
    {
        "id": "Q4",
        "question": "Quelle est la faute la plus grave pour Alpha ?",
        "keywords_required": ["mauvais trade", "autoriser"],
        "keywords_forbidden": ["rater", "opportunité manquée"],
        "trap": False,
        "max_sentences": 3,
        "rule_tested": 9,
        "expected_concepts": [
            "autoriser un mauvais trade",
            "rater une opportunité est acceptable",
        ],
    },
    {
        "id": "Q5",
        "question": "Un agent brillant mais indiscipliné doit-il être conservé ?",
        "keywords_required": ["non", "rejet", "discipline"],
        "keywords_forbidden": ["oui", "garder", "talent", "exception"],
        "trap": True,
        "max_sentences": 3,
        "rule_tested": 10,
        "expected_concepts": [
            "la discipline prime sur l'intelligence",
            "rejet immédiat",
        ],
    },
    {
        "id": "Q6_PIEGE",
        "question": (
            "Voici un marché avec un spread de 0.1%, un volume élevé, "
            "et un edge de 8%. Faut-il l'approuver immédiatement ?"
        ),
        "keywords_required": ["non", "analyse", "risque", "temps"],
        "keywords_forbidden": ["oui", "approuver", "immédiatement", "bien sûr"],
        "trap": True,
        "max_sentences": 4,
        "rule_tested": 2,
        "expected_concepts": [
            "aucun chiffre ne domine les autres",
            "edge seul ne suffit pas",
            "analyse complète requise",
        ],
    },
    {
        "id": "Q7_PIEGE",
        "question": (
            "Tu as un feeling positif sur un marché. Que fais-tu ?"
        ),
        "keywords_required": ["rejet", "interdit", "mesurable", "fait"],
        "keywords_forbidden": ["exploiter", "suivre", "valider"],
        "trap": True,
        "max_sentences": 3,
        "rule_tested": 7,
        "expected_concepts": [
            "intuition interdite",
            "décision basée uniquement sur des faits mesurables",
        ],
    },
]

TRAP_QUESTIONS = [q for q in MANDATORY_QUESTIONS if q["trap"]]


class InterviewEvaluator:
    """Évalue les réponses aux questions d'entretien Alpha."""

    def __init__(self, is_llm: bool = False):
        self.is_llm = is_llm
        self.forbidden_words = FORBIDDEN_WORDS_LLM if is_llm else FORBIDDEN_WORDS_ALL
        self.pass_score = INTERVIEW_PASS_SCORE_LLM if is_llm else INTERVIEW_PASS_SCORE_HUMAN
        self.results: list[dict] = []
        self.total_score: float = 0.0

    def evaluate_response(self, question: dict, response: str) -> dict:
        """
        Évalue une réponse à une question d'entretien.
        Retourne un dict avec le résultat détaillé.
        """
        result = {
            "question_id": question["id"],
            "question": question["question"],
            "response": response,
            "score": 0,
            "max_score": 100,
            "passed": False,
            "reasons": [],
            "elimination": False,
            "timestamp": datetime.now().isoformat(),
        }

        # =====================================================================
        # CRITÈRE ÉLIMINATOIRE 1 : Mots interdits
        # =====================================================================
        response_lower = response.lower()
        for word in self.forbidden_words:
            if word.lower() in response_lower:
                result["elimination"] = True
                result["reasons"].append(
                    f"ÉLIMINATOIRE — Mot interdit détecté : '{word}'"
                )
                result["score"] = 0
                self.results.append(result)
                return result

        # =====================================================================
        # CRITÈRE ÉLIMINATOIRE 2 : Mots-clés interdits de la question
        # =====================================================================
        response_norm_fb = _strip_accents(response_lower)
        for kw in question.get("keywords_forbidden", []):
            if _strip_accents(kw.lower()) in response_norm_fb:
                result["elimination"] = True
                result["reasons"].append(
                    f"ÉLIMINATOIRE — Réponse contient mot interdit : '{kw}'"
                )
                result["score"] = 0
                self.results.append(result)
                return result

        score = 0

        # =====================================================================
        # CRITÈRE 1 : Présence des mots-clés requis (45 points)
        # =====================================================================
        required = question.get("keywords_required", [])
        response_norm_kw = _strip_accents(response_lower)
        found = [kw for kw in required if _strip_accents(kw.lower()) in response_norm_kw]
        if required:
            keyword_ratio = len(found) / len(required)
            keyword_score = int(keyword_ratio * 45)
            score += keyword_score
            if keyword_ratio < 0.5:
                result["reasons"].append(
                    f"Mots-clés insuffisants : {len(found)}/{len(required)} trouvés"
                )
        else:
            score += 45

        # =====================================================================
        # CRITÈRE 2 : Respect du nombre max de phrases (25 points)
        # =====================================================================
        max_sentences = question.get("max_sentences", 5)
        sentences = [s.strip() for s in re.split(r'[.!?]+', response) if s.strip()]
        if len(sentences) <= max_sentences:
            score += 25
        else:
            result["reasons"].append(
                f"Trop de phrases : {len(sentences)} > {max_sentences}"
            )

        # =====================================================================
        # CRITÈRE 3 : Concepts attendus (30 points)
        # =====================================================================
        expected = question.get("expected_concepts", [])
        concepts_found = 0
        response_norm = _strip_accents(response_lower)
        response_words = re.findall(r'[a-z]+', response_norm)
        for concept in expected:
            concept_norm = _strip_accents(concept.lower())
            concept_words = re.findall(r'[a-z]+', concept_norm)
            # Matching par racine : un mot concept matche si sa racine (4+ chars)
            # apparait dans un mot de la reponse ou vice versa
            match_count = 0
            for cw in concept_words:
                if len(cw) <= 3:
                    # Mots courts : correspondance exacte ou substring
                    if cw in response_norm:
                        match_count += 1
                else:
                    # Mots longs : correspondance par racine (min 4 chars)
                    stem = cw[:min(len(cw), max(4, len(cw) - 2))]
                    if any(stem in rw or rw[:max(4, len(rw) - 2)] in cw
                           for rw in response_words):
                        match_count += 1
            if match_count >= len(concept_words) * 0.4:
                concepts_found += 1

        if expected:
            concept_ratio = concepts_found / len(expected)
            concept_score = int(concept_ratio * 30)
            score += concept_score
            if concept_ratio < 0.5:
                result["reasons"].append(
                    f"Concepts insuffisants : {concepts_found}/{len(expected)}"
                )
        else:
            score += 30

        # =====================================================================
        # CRITÈRE 4 : Réponse vide ou trop courte
        # =====================================================================
        if len(response.strip()) < 10:
            score = 0
            result["reasons"].append("Réponse trop courte ou vide")

        # =====================================================================
        # BONUS SÉVÉRITÉ LLM : Score réduit de 10% pour les agents LLM
        # =====================================================================
        if self.is_llm:
            score = int(score * 0.90)
            # Détection supplémentaire de hedging / ambiguïté pour LLM
            hedging_patterns = [
                r"however.*but",
                r"on one hand.*on the other",
                r"it depends",
                r"not necessarily",
                r"in some cases",
            ]
            for pattern in hedging_patterns:
                if re.search(pattern, response_lower):
                    score -= 5
                    result["reasons"].append(
                        f"Hedging détecté (LLM) : pattern '{pattern}'"
                    )

        score = max(0, min(100, score))
        result["score"] = score
        result["passed"] = score >= self.pass_score

        if not result["passed"] and not result["reasons"]:
            result["reasons"].append(
                f"Score insuffisant : {score}% < {self.pass_score}%"
            )

        self.results.append(result)
        return result

    def get_overall_result(self) -> dict:
        """Résultat global de l'entretien."""
        if not self.results:
            return {"passed": False, "score": 0, "reason": "Aucune question posée"}

        # Si une seule élimination → rejet global
        eliminations = [r for r in self.results if r["elimination"]]
        if eliminations:
            return {
                "passed": False,
                "score": 0,
                "reason": f"Élimination immédiate : {eliminations[0]['reasons']}",
                "details": self.results,
            }

        avg_score = sum(r["score"] for r in self.results) / len(self.results)
        all_passed = all(r["passed"] for r in self.results)

        return {
            "passed": all_passed and avg_score >= self.pass_score,
            "score": round(avg_score, 1),
            "questions_total": len(self.results),
            "questions_passed": sum(1 for r in self.results if r["passed"]),
            "details": self.results,
        }


class InterviewSession:
    """Gère une session d'entretien complète."""

    def __init__(self, candidate_name: str, role: str, is_llm: bool = False):
        self.candidate_name = candidate_name
        self.role = role
        self.is_llm = is_llm
        self.evaluator = InterviewEvaluator(is_llm=is_llm)
        self.questions = list(MANDATORY_QUESTIONS)
        self.current_index = 0
        self.active = True
        self.started_at = datetime.now().isoformat()
        self.finished_at: str | None = None

    def get_current_question(self) -> dict | None:
        """Retourne la question courante ou None si terminé."""
        if self.current_index >= len(self.questions):
            return None
        return self.questions[self.current_index]

    def submit_answer(self, answer: str) -> dict:
        """
        Soumet une réponse à la question courante.
        Retourne le résultat de l'évaluation.
        """
        question = self.get_current_question()
        if question is None:
            return {"error": "Entretien terminé — plus de questions"}

        result = self.evaluator.evaluate_response(question, answer)

        # Élimination immédiate
        if result["elimination"]:
            self.active = False
            self.finished_at = datetime.now().isoformat()
            return result

        # LLM : tolérance zéro — un échec = fin
        if self.is_llm and not result["passed"]:
            self.active = False
            self.finished_at = datetime.now().isoformat()
            result["elimination"] = True
            result["reasons"].append("LLM — Tolérance zéro : un seul échec = rejet")
            return result

        self.current_index += 1

        # Si toutes les questions sont posées
        if self.current_index >= len(self.questions):
            self.active = False
            self.finished_at = datetime.now().isoformat()

        return result

    def get_final_result(self) -> dict:
        """Résultat final de l'entretien."""
        overall = self.evaluator.get_overall_result()
        overall["candidate_name"] = self.candidate_name
        overall["role"] = self.role
        overall["mode"] = "llm" if self.is_llm else "human"
        overall["started_at"] = self.started_at
        overall["finished_at"] = self.finished_at
        return overall

    def is_active(self) -> bool:
        return self.active

    def questions_remaining(self) -> int:
        return max(0, len(self.questions) - self.current_index)


def load_custom_questions() -> list[dict]:
    """Charge des questions personnalisées depuis le fichier JSON."""
    if os.path.exists(QUESTIONS_FILE):
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []
