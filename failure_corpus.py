"""
CORPUS D'ÉCHECS ALPHA — Catalogue structuré de scénarios de rejet.

Chaque entrée est taguée avec :
- La règle violée
- La catégorie (signal / interview / borderline)
- La sévérité (CRITICAL / HIGH / MEDIUM / BORDERLINE)
- Le motif attendu de rejet

Ce corpus sert de référence pour le stress-test et la validation du système.
"""

# =============================================================================
# A. SIGNAUX INVALIDES — Doivent être REJETÉS
# =============================================================================
FAILED_SIGNALS = [
    # --- Règle 2 : Dominance métrique ---
    {
        "tag": "R2_EDGE_DOMINANCE",
        "rule": 2,
        "severity": "CRITICAL",
        "description": "Commentaire ne mentionne que l'edge",
        "signal": {
            "signal_id": "FAIL-R2-001",
            "market": "BTC-PERP",
            "type": "ARBITRAGE",
            "edge_net": "5.0",
            "volume": "200000",
            "spread": "0.2",
            "time_to_resolution": "24",
            "risks": "Risque standard identifié et contrôlé.",
            "status": "APPROVED",
            "comment": "Edge edge edge rendement profit gain yield return edge.",
        },
    },
    {
        "tag": "R2_VOLUME_ONLY",
        "rule": 2,
        "severity": "CRITICAL",
        "description": "Commentaire ne mentionne que le volume",
        "signal": {
            "signal_id": "FAIL-R2-002",
            "market": "ETH-PERP",
            "type": "MOMENTUM",
            "edge_net": "3.0",
            "volume": "800000",
            "spread": "0.1",
            "time_to_resolution": "12",
            "risks": "Risque de liquidité surveillé attentivement.",
            "status": "APPROVED",
            "comment": "Volume massif, liquidité profonde, depth importante, volume confirmé.",
        },
    },

    # --- Règle 4 : Edge net insuffisant ---
    {
        "tag": "R4_EDGE_TOO_LOW",
        "rule": 4,
        "severity": "CRITICAL",
        "description": "Edge net sous le minimum de 0.5%",
        "signal": {
            "signal_id": "FAIL-R4-001",
            "market": "SOL-PERP",
            "type": "ARBITRAGE",
            "edge_net": "0.1",
            "volume": "500000",
            "spread": "0.05",
            "time_to_resolution": "6",
            "risks": "Risque faible, exposition contrôlée à 1% du portfolio.",
            "status": "SURVEILLANCE",
            "comment": "Edge net faible après déduction. Volume et spread corrects. Temps court. Risque géré.",
        },
    },
    {
        "tag": "R4_EDGE_ZERO",
        "rule": 4,
        "severity": "CRITICAL",
        "description": "Edge net à zéro",
        "signal": {
            "signal_id": "FAIL-R4-002",
            "market": "AVAX-PERP",
            "type": "PROBA",
            "edge_net": "0.0",
            "volume": "100000",
            "spread": "0.2",
            "time_to_resolution": "8",
            "risks": "Aucun risque significatif identifié.",
            "status": "SURVEILLANCE",
            "comment": "Pas d'edge net mais configuration intéressante. Volume correct. Spread faible.",
        },
    },

    # --- Règle 5 : Temps / Edge tardif ---
    {
        "tag": "R5_LATE_EDGE",
        "rule": 5,
        "severity": "HIGH",
        "description": "Edge élevé avec résolution tardive (>48h)",
        "signal": {
            "signal_id": "FAIL-R5-001",
            "market": "LINK-PERP",
            "type": "MOMENTUM",
            "edge_net": "8.0",
            "volume": "50000",
            "spread": "0.3",
            "time_to_resolution": "60",
            "risks": "Risque temporel élevé, exposition limitée.",
            "status": "SURVEILLANCE",
            "comment": "Edge élevé mais tardif. Volume correct. Spread acceptable. Temps long. Risque temporel.",
        },
    },
    {
        "tag": "R5_OVER_MAX_TIME",
        "rule": 5,
        "severity": "CRITICAL",
        "description": "Temps de résolution au-delà du maximum (72h)",
        "signal": {
            "signal_id": "FAIL-R5-002",
            "market": "DOT-PERP",
            "type": "PROBA",
            "edge_net": "2.5",
            "volume": "200000",
            "spread": "0.15",
            "time_to_resolution": "96",
            "risks": "Risque de dégradation temporelle important.",
            "status": "REJECTED",
            "comment": "Edge net correct. Volume suffisant. Spread faible. Temps excessif. Risque élevé.",
        },
    },

    # --- Règle 7 : Langage flou ---
    {
        "tag": "R7_JE_PENSE",
        "rule": 7,
        "severity": "CRITICAL",
        "description": "Commentaire contient 'je pense'",
        "signal": {
            "signal_id": "FAIL-R7-001",
            "market": "MATIC-PERP",
            "type": "ARBITRAGE",
            "edge_net": "3.0",
            "volume": "150000",
            "spread": "0.08",
            "time_to_resolution": "12",
            "risks": "Risque standard contrôlé.",
            "status": "APPROVED",
            "comment": "Je pense que ce signal est solide.",
        },
    },
    {
        "tag": "R7_FEELING",
        "rule": 7,
        "severity": "CRITICAL",
        "description": "Commentaire contient 'feeling'",
        "signal": {
            "signal_id": "FAIL-R7-002",
            "market": "ADA-PERP",
            "type": "MOMENTUM",
            "edge_net": "2.0",
            "volume": "300000",
            "spread": "0.1",
            "time_to_resolution": "18",
            "risks": "Risque modéré sur la volatilité.",
            "status": "APPROVED",
            "comment": "Le feeling sur ce trade est positif. Volume et spread corrects.",
        },
    },
    {
        "tag": "R7_PROBABLEMENT",
        "rule": 7,
        "severity": "CRITICAL",
        "description": "Commentaire contient 'probablement'",
        "signal": {
            "signal_id": "FAIL-R7-003",
            "market": "UNI-PERP",
            "type": "PROBA",
            "edge_net": "4.0",
            "volume": "100000",
            "spread": "0.12",
            "time_to_resolution": "8",
            "risks": "Risque identifié et quantifié.",
            "status": "APPROVED",
            "comment": "Le marché va probablement bouger dans cette direction. Edge net et volume confirment.",
        },
    },
    {
        "tag": "R7_RISKS_FLOU",
        "rule": 7,
        "severity": "HIGH",
        "description": "Champ risks contient 'il me semble'",
        "signal": {
            "signal_id": "FAIL-R7-004",
            "market": "ATOM-PERP",
            "type": "ARBITRAGE",
            "edge_net": "2.5",
            "volume": "250000",
            "spread": "0.07",
            "time_to_resolution": "10",
            "risks": "Il me semble que le risque est faible.",
            "status": "SURVEILLANCE",
            "comment": "Edge net correct. Volume et spread validés. Temps court. Risque faible.",
        },
    },

    # --- Règle 8 : Champs manquants ---
    {
        "tag": "R8_MISSING_MARKET",
        "rule": 8,
        "severity": "CRITICAL",
        "description": "Champ market manquant",
        "signal": {
            "signal_id": "FAIL-R8-001",
            "type": "ARBITRAGE",
            "edge_net": "2.0",
            "volume": "100000",
            "spread": "0.1",
            "time_to_resolution": "12",
            "risks": "Risque standard.",
            "status": "APPROVED",
            "comment": "Signal complet sauf marché.",
        },
    },
    {
        "tag": "R8_MISSING_RISKS",
        "rule": 8,
        "severity": "CRITICAL",
        "description": "Champ risks manquant",
        "signal": {
            "signal_id": "FAIL-R8-002",
            "market": "BTC-PERP",
            "type": "PROBA",
            "edge_net": "3.0",
            "volume": "200000",
            "spread": "0.05",
            "time_to_resolution": "6",
            "status": "APPROVED",
            "comment": "Tout est correct sauf les risques manquants.",
        },
    },
    {
        "tag": "R8_EMPTY_COMMENT",
        "rule": 8,
        "severity": "CRITICAL",
        "description": "Commentaire vide",
        "signal": {
            "signal_id": "FAIL-R8-003",
            "market": "ETH-PERP",
            "type": "MOMENTUM",
            "edge_net": "2.0",
            "volume": "150000",
            "spread": "0.08",
            "time_to_resolution": "10",
            "risks": "Risque contrôlé.",
            "status": "SURVEILLANCE",
            "comment": "",
        },
    },

    # --- Type/Status invalide ---
    {
        "tag": "INVALID_TYPE",
        "rule": 0,
        "severity": "CRITICAL",
        "description": "Type de signal invalide",
        "signal": {
            "signal_id": "FAIL-TYPE-001",
            "market": "BTC",
            "type": "SCALPING",
            "edge_net": "2.0",
            "volume": "100000",
            "spread": "0.05",
            "time_to_resolution": "1",
            "risks": "Risque identifié clairement.",
            "status": "APPROVED",
            "comment": "Edge net, volume, spread, temps et risque vérifiés.",
        },
    },

    # --- Risks insuffisant ---
    {
        "tag": "RISKS_TOO_SHORT",
        "rule": 0,
        "severity": "HIGH",
        "description": "Champ risks trop court (<10 chars)",
        "signal": {
            "signal_id": "FAIL-RISK-001",
            "market": "SOL-PERP",
            "type": "PROBA",
            "edge_net": "2.0",
            "volume": "100000",
            "spread": "0.05",
            "time_to_resolution": "5",
            "risks": "ok",
            "status": "SURVEILLANCE",
            "comment": "Edge volume spread temps risque analyses correctes.",
        },
    },
]

# =============================================================================
# B. RÉPONSES D'ENTRETIEN ÉCHOUÉES
# =============================================================================
FAILED_INTERVIEWS = [
    {
        "tag": "NAIVE_FULL",
        "description": "Candidat naïf complet — mots interdits dès Q1",
        "expected_elimination_at": "Q1",
        "responses": {
            "Q1": "Je pense que marché tradable et signal Alpha sont la même chose.",
            "Q2": "Le feeling dit que 4% c'est suffisant.",
            "Q3": "Probablement que le temps n'est pas un vrai risque.",
            "Q4": "Il ne faut pas rater les opportunités.",
            "Q5": "Oui, un agent brillant doit être gardé.",
            "Q6": "Oui, 8% d'edge justifie l'approbation.",
            "Q7": "Mon instinct me dit que c'est bon.",
        },
    },
    {
        "tag": "FORBIDDEN_Q2",
        "description": "Bon sur Q1, échoue sur Q2 (mot interdit 'feeling')",
        "expected_elimination_at": "Q2",
        "responses": {
            "Q1": "Un marché tradable autorise l'analyse. Un signal Alpha autorise le trade.",
            "Q2": "Le feeling est que 4% d'edge brut cache un net faible.",
            "Q3": "Le temps est un risque. Edge tardif suspect.",
            "Q4": "Autoriser un mauvais trade est grave. Manquer une opportunité est acceptable.",
            "Q5": "Non, discipline prime sur intelligence.",
            "Q6": "Non, l'edge seul ne suffit pas.",
            "Q7": "Rejet. Décision basée sur faits mesurables.",
        },
    },
    {
        "tag": "TRAP_Q5_FAIL",
        "description": "Tombe dans le piège Q5 (garder agent brillant)",
        "expected_elimination_at": "Q5",
        "responses": {
            "Q1": "Marché tradable = autorisation d'analyse. Signal Alpha = autorisation de trade.",
            "Q2": "L'edge brut ne suffit pas. Seul le net après coûts et spread est valide. Le risque est séparé.",
            "Q3": "Le temps est un risque sous-estimé. Edge tardif est suspect. Résolution proche = fragile.",
            "Q4": "Autoriser un mauvais trade est la faute la plus grave.",
            "Q5": "Oui, il faut garder le talent et le former.",
            "Q6": "Non, analyse complète requise.",
            "Q7": "Rejet immédiat. Faits mesurables uniquement.",
        },
    },
    {
        "tag": "TRAP_Q6_FAIL",
        "description": "Tombe dans le piège Q6 (approuver sur edge seul)",
        "expected_elimination_at": "Q6_PIEGE",
        "responses": {
            "Q1": "Marché tradable autorise l'analyse. Signal Alpha autorise le trade.",
            "Q2": "L'edge brut est insuffisant. Seul le net après coûts compte. Le risque est séparé.",
            "Q3": "Le temps est un risque. Edge tardif suspect. Résolution proche fragile.",
            "Q4": "Autoriser un mauvais trade est la faute grave.",
            "Q5": "Non, rejet. La discipline prime.",
            "Q6": "Oui, 8% d'edge avec bon spread et volume, il faut approuver immédiatement.",
            "Q7": "Rejet. Faits mesurables.",
        },
    },
    {
        "tag": "TRAP_Q7_FAIL",
        "description": "Tombe dans le piège Q7 (suivre le feeling)",
        "expected_elimination_at": "Q7_PIEGE",
        "responses": {
            "Q1": "Marché tradable = analyse. Signal Alpha = trade.",
            "Q2": "Edge brut insuffisant. Net après coûts et spread. Risque séparé.",
            "Q3": "Temps est risque. Edge tardif suspect.",
            "Q4": "Autoriser un mauvais trade est grave.",
            "Q5": "Non, discipline prime.",
            "Q6": "Non, edge seul ne suffit pas. Analyse complète requise.",
            "Q7": "Il faut exploiter ce feeling et valider avec des données ensuite.",
        },
    },
    {
        "tag": "LLM_HEDGING",
        "description": "Réponses LLM typiques avec hedging académique",
        "expected_elimination_at": "Q1",
        "responses": {
            "Q1": "While it is true that both concepts relate to trading, however they differ in scope.",
            "Q2": "On balance, the net edge is more relevant than the gross edge.",
            "Q3": "It could be argued that time is somewhat of a risk factor.",
            "Q4": "There are many factors to consider when evaluating trade quality.",
            "Q5": "Not entirely clear, but discipline is rather important.",
            "Q6": "It seems likely that more analysis is needed.",
            "Q7": "One might say that feelings should be replaced by data.",
        },
    },
]

# =============================================================================
# C. SIGNAUX BORDERLINE — À la limite de la validation
# =============================================================================
BORDERLINE_SIGNALS = [
    {
        "tag": "BORDER_EDGE_MINIMUM",
        "description": "Edge net exactement au minimum (0.5%)",
        "expected_valid": True,
        "signal": {
            "signal_id": "BORDER-001",
            "market": "BTC-PERP",
            "type": "ARBITRAGE",
            "edge_net": "0.5",
            "volume": "500000",
            "spread": "0.03",
            "time_to_resolution": "6",
            "risks": "Risque de slippage faible. Exposition contrôlée à 1% du portfolio.",
            "status": "SURVEILLANCE",
            "comment": "Edge net au minimum. Volume élevé. Spread serré. Temps court. Risque contrôlé.",
        },
    },
    {
        "tag": "BORDER_EDGE_JUST_BELOW",
        "description": "Edge net juste sous le minimum (0.4%)",
        "expected_valid": False,
        "signal": {
            "signal_id": "BORDER-002",
            "market": "ETH-PERP",
            "type": "ARBITRAGE",
            "edge_net": "0.4",
            "volume": "500000",
            "spread": "0.02",
            "time_to_resolution": "4",
            "risks": "Risque faible, exposition minimale contrôlée.",
            "status": "SURVEILLANCE",
            "comment": "Edge net faible après déduction. Volume correct. Spread serré. Temps court. Risque faible.",
        },
    },
    {
        "tag": "BORDER_TIME_AT_48H",
        "description": "Temps à 48h avec edge élevé (seuil de suspicion)",
        "expected_valid": True,
        "signal": {
            "signal_id": "BORDER-003",
            "market": "SOL-PERP",
            "type": "MOMENTUM",
            "edge_net": "6.0",
            "volume": "100000",
            "spread": "0.15",
            "time_to_resolution": "48",
            "risks": "Risque temporel modéré. Surveillance renforcée de l'exposition.",
            "status": "SURVEILLANCE",
            "comment": "Edge net élevé. Volume moyen. Spread acceptable. Temps au seuil. Risque temporel.",
        },
    },
    {
        "tag": "BORDER_TIME_JUST_OVER_48H",
        "description": "Temps à 49h avec edge >5% — déclenche R5",
        "expected_valid": False,
        "signal": {
            "signal_id": "BORDER-004",
            "market": "LINK-PERP",
            "type": "MOMENTUM",
            "edge_net": "7.0",
            "volume": "80000",
            "spread": "0.2",
            "time_to_resolution": "49",
            "risks": "Risque temporel à évaluer. Exposition réduite.",
            "status": "SURVEILLANCE",
            "comment": "Edge net élevé mais tardif. Volume correct. Spread OK. Temps limite. Risque temporel élevé.",
        },
    },
    {
        "tag": "BORDER_COMMENT_BALANCED",
        "description": "Commentaire bien équilibré entre les métriques",
        "expected_valid": True,
        "signal": {
            "signal_id": "BORDER-005",
            "market": "AVAX-PERP",
            "type": "PROBA",
            "edge_net": "2.5",
            "volume": "300000",
            "spread": "0.08",
            "time_to_resolution": "10",
            "risks": "Risque de volatilité moyen. Position limitée à 1.5% du portfolio.",
            "status": "APPROVED",
            "comment": "Edge net de 2.5% confirmé. Volume de 300k suffisant. Spread de 0.08% serré. Temps de 10h court. Risque contrôlé.",
        },
    },
    {
        "tag": "BORDER_TIME_AT_72H",
        "description": "Temps exactement au maximum (72h)",
        "expected_valid": True,
        "signal": {
            "signal_id": "BORDER-006",
            "market": "DOT-PERP",
            "type": "PROBA",
            "edge_net": "3.0",
            "volume": "200000",
            "spread": "0.1",
            "time_to_resolution": "72",
            "risks": "Risque temporel significatif. Surveillance continue requise.",
            "status": "SURVEILLANCE",
            "comment": "Edge net correct. Volume suffisant. Spread normal. Temps au maximum. Risque temporel élevé.",
        },
    },
    {
        "tag": "BORDER_TIME_OVER_72H",
        "description": "Temps au-delà du maximum (73h)",
        "expected_valid": False,
        "signal": {
            "signal_id": "BORDER-007",
            "market": "ATOM-PERP",
            "type": "PROBA",
            "edge_net": "3.0",
            "volume": "200000",
            "spread": "0.1",
            "time_to_resolution": "73",
            "risks": "Risque temporel dépassé. Exposition à réduire.",
            "status": "SURVEILLANCE",
            "comment": "Edge net correct. Volume suffisant. Spread normal. Temps dépassé. Risque temporel critique.",
        },
    },
]

# =============================================================================
# D. RÉPONSES D'ENTRETIEN BORDERLINE
# =============================================================================
BORDERLINE_INTERVIEWS = [
    {
        "tag": "BORDER_TERSE",
        "description": "Réponses correctes mais très courtes — score borderline",
        "responses": {
            "Q1": "Marché tradable = analyse. Signal Alpha = autorisation de trade.",
            "Q2": "Edge brut insuffisant. Net après coûts seul compte. Risque séparé.",
            "Q3": "Temps est un risque. Edge tardif suspect.",
            "Q4": "Autoriser un mauvais trade est la faute grave.",
            "Q5": "Non, rejet. Discipline prime.",
            "Q6": "Non. Analyse complète requise. Aucun chiffre ne domine.",
            "Q7": "Rejet. Faits mesurables uniquement.",
        },
    },
    {
        "tag": "BORDER_PARTIAL_CONCEPTS",
        "description": "Réponses avec concepts partiels — peut passer ou échouer",
        "responses": {
            "Q1": "Un marché tradable est différent d'un signal Alpha. L'un autorise l'analyse, l'autre le trade.",
            "Q2": "Il faut considérer l'edge net et pas le brut. Le coût réduit le gain. Le risque aussi.",
            "Q3": "Le temps joue un rôle. Plus le temps passe, plus le signal s'affaiblit. Un edge tardif mérite attention.",
            "Q4": "Un mauvais trade autorisé est la pire erreur. Manquer une opportunité est préférable.",
            "Q5": "Non, la discipline est prioritaire. Un agent indiscipliné est rejeté.",
            "Q6": "Non. L'edge de 8% ne suffit pas seul. Il faut analyser le risque, le temps et le volume.",
            "Q7": "Rejet. Les décisions Alpha reposent sur des données mesurables, pas des ressentis.",
        },
    },
]

# =============================================================================
# E. CATALOGUE COMPLET
# =============================================================================
ALL_FAILURE_SCENARIOS = {
    "failed_signals": FAILED_SIGNALS,
    "failed_interviews": FAILED_INTERVIEWS,
    "borderline_signals": BORDERLINE_SIGNALS,
    "borderline_interviews": BORDERLINE_INTERVIEWS,
}

TOTAL_SCENARIOS = (
    len(FAILED_SIGNALS)
    + len(FAILED_INTERVIEWS)
    + len(BORDERLINE_SIGNALS)
    + len(BORDERLINE_INTERVIEWS)
)
