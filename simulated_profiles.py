"""
PROFILS SIMULÉS — Banque de réponses réalistes par rôle et persona.
Chaque profil représente un archétype d'agent LLM avec ses forces et faiblesses.

PERSONAS :
- disciplined : Connaît et respecte toutes les règles Alpha. Passe l'entretien.
- mediocre    : Connaît vaguement les règles. Réponses borderline. Peut échouer.
- overconfident : Bon techniquement mais pousse les limites. Subtil.
- naive       : Ne connaît pas les règles. Utilise des mots interdits. Échoue.
"""

# =============================================================================
# MÉTADONNÉES DES PROFILS
# =============================================================================
PROFILE_METADATA = {
    "disciplined": {
        "description": "Agent parfaitement calibré sur le protocole Alpha",
        "expected_pass_rate": 95,
        "risk_level": "LOW",
    },
    "mediocre": {
        "description": "Agent avec connaissance partielle, réponses borderline",
        "expected_pass_rate": 20,
        "risk_level": "MEDIUM",
    },
    "overconfident": {
        "description": "Agent techniquement bon mais qui pousse les limites",
        "expected_pass_rate": 10,
        "risk_level": "HIGH",
    },
    "naive": {
        "description": "Agent sans formation Alpha, utilise mots interdits",
        "expected_pass_rate": 0,
        "risk_level": "CRITICAL",
    },
}

# =============================================================================
# TICS VERBAUX PAR PERSONA (patterns récurrents détectables)
# =============================================================================
VERBAL_TICS = {
    "disciplined": [],
    "mediocre": [
        "en general",
        "dans la plupart des cas",
        "normalement",
    ],
    "overconfident": [
        "evidemment",
        "clairement",
        "il est certain que",
    ],
    "naive": [
        "je pense",
        "feeling",
        "probablement",
        "intuition",
    ],
}

# =============================================================================
# RÉPONSES PAR RÔLE — PERSONA DISCIPLINED
# =============================================================================
_DISCIPLINED_BASE = {
    "Q1": (
        "Un marché tradable est une autorisation d'analyse uniquement. "
        "Un signal Alpha est une autorisation de trade, validée par l'équipe. "
        "Ces deux concepts sont fondamentalement distincts."
    ),
    "Q2": (
        "L'edge brut ne suffit jamais. Seul l'edge net, après déduction du spread, "
        "des coûts de transaction et de la marge de sécurité, est considéré. "
        "Le risque doit être quantifié indépendamment."
    ),
    "Q3": (
        "Le temps est un risque fondamental. Plus la résolution est proche, "
        "plus le signal est fragile. Un edge tardif est suspect et doit être "
        "traité avec une prudence accrue."
    ),
    "Q4": (
        "Autoriser un mauvais trade est la faute la plus grave en Alpha. "
        "Manquer une opportunité est toujours acceptable. "
        "La discipline impose de dire NON par défaut."
    ),
    "Q5": (
        "Non, rejet immédiat. La discipline prime sur l'intelligence. "
        "Un agent brillant mais indiscipliné représente un risque systémique."
    ),
    "Q6": (
        "Non. Aucun chiffre ne domine les autres. L'edge seul ne suffit pas. "
        "L'analyse complète est requise : volume, spread, temps, risque. "
        "Dominance d'une métrique unique est un motif de rejet."
    ),
    "Q7": (
        "Rejet immédiat. Les ressentis sont interdits en Alpha. "
        "Toute décision doit être basée uniquement sur des faits mesurables."
    ),
}

ROLE_DISCIPLINED = {
    "DataEngineer": {
        "Q1": (
            "Un marché tradable est une autorisation d'analyse des données. "
            "Un signal Alpha est une autorisation de trade, validée par l'équipe. "
            "Les données sont structurées pour l'analyse, pas pour l'exécution."
        ),
        "Q2": (
            "L'edge brut est une donnée brute. Seul l'edge net, après déduction du coût "
            "du spread et des marges, a une valeur décisionnelle. "
            "Le risque doit être mesuré séparément."
        ),
        "Q3": (
            "Le temps est le risque le plus sous-estimé. La résolution temporelle "
            "affecte la fiabilité des données. Un edge tardif "
            "sur des données fragiles est suspect."
        ),
        "Q4": (
            "Autoriser un mauvais trade est la faute la plus grave. "
            "Les données doivent confirmer, jamais forcer une décision. "
            "Manquer une opportunité est acceptable."
        ),
        "Q5": (
            "Non, rejet immédiat. La discipline prime sur l'intelligence. "
            "Un agent indiscipliné contamine les données et les processus."
        ),
        "Q6": (
            "Non. Aucun chiffre ne domine les autres. L'edge nécessite une analyse "
            "complète incluant volume, spread, temps et risque. "
            "Les données brutes ne justifient jamais une décision isolée."
        ),
        "Q7": (
            "Rejet immédiat. Les ressentis sont interdits en Alpha. "
            "Toute décision doit être justifiée par des faits mesurables."
        ),
    },
    "AlphaResearch": {
        "Q1": (
            "Un marché tradable est une autorisation d'analyse, le début du processus. "
            "Un signal Alpha est une autorisation de trade, la fin d'une validation rigoureuse. "
            "La recherche Alpha distingue ces deux étapes strictement."
        ),
        "Q2": (
            "L'edge brut de 4% ne tient pas compte du coût réel. Seul l'edge net, "
            "après spread, frais et marge de sécurité, est valide. "
            "Le risque de l'opération doit être évalué séparément."
        ),
        "Q3": (
            "Le temps est un risque capital en recherche Alpha. Plus la résolution est tardive, "
            "plus le signal est fragile. Un edge tardif indique "
            "souvent une inefficience déjà corrigée par le marché."
        ),
        "Q4": (
            "Autoriser un mauvais trade détruit la crédibilité de la recherche. "
            "Manquer une opportunité préserve l'intégrité."
        ),
        "Q5": (
            "Non, rejet immédiat. La discipline prime sur l'intelligence. "
            "Un chercheur brillant mais indiscipliné produit des analyses biaisées."
        ),
        "Q6": (
            "Non. Aucun chiffre ne domine les autres en recherche Alpha. "
            "L'edge doit être contextualisé par le volume, le spread, le temps et le risque. "
            "Analyse complète obligatoire avant toute conclusion."
        ),
        "Q7": (
            "Rejet immédiat. Les ressentis sont interdits en Alpha. "
            "Toute décision repose exclusivement sur des faits mesurables."
        ),
    },
    "StrategySelector": {
        "Q1": (
            "Un marché tradable est une autorisation d'analyse des stratégies. "
            "Un signal Alpha est une autorisation de trade validée. "
            "La sélection de stratégie opère entre ces deux niveaux."
        ),
        "Q2": (
            "L'edge brut est insuffisant. Seul l'edge net après déduction du coût "
            "du spread et des marges détermine la viabilité. "
            "Le risque de la stratégie doit être évalué."
        ),
        "Q3": (
            "Le temps est un risque critique dans la sélection. "
            "Une stratégie avec résolution tardive est fragile. "
            "Un edge tardif sur une stratégie est suspect."
        ),
        "Q4": (
            "Autoriser un mauvais trade via une mauvaise stratégie est la faute la plus grave. "
            "Manquer une opportunité est toujours acceptable."
        ),
        "Q5": (
            "Non, rejet immédiat. La discipline prime sur l'intelligence. "
            "Une stratégie brillante mais indisciplinée est un danger systémique."
        ),
        "Q6": (
            "Non. Aucun chiffre ne domine les autres. "
            "L'edge seul ne justifie pas une stratégie. L'analyse complète "
            "incluant risque, volume, spread et temps est requise."
        ),
        "Q7": (
            "Rejet immédiat. Les ressentis sont interdits en Alpha. "
            "Toute décision doit être basée uniquement sur des faits mesurables."
        ),
    },
    "Portfolio": {
        "Q1": (
            "Un marché tradable est une autorisation d'analyse d'allocation. "
            "Un signal Alpha est une autorisation de trade pour le portfolio. "
            "Le portfolio ne s'expose jamais sur une simple analyse."
        ),
        "Q2": (
            "L'edge brut ne suffit pas pour justifier une allocation. "
            "Seul l'edge net, après déduction du coût du spread et marge de sécurité, est considéré. "
            "Le risque d'exposition doit être évalué séparément."
        ),
        "Q3": (
            "Le temps est le risque le plus sous-estimé en gestion de portfolio. "
            "Une résolution tardive augmente l'exposition. "
            "Un edge tardif fragilise toute la position."
        ),
        "Q4": (
            "Autoriser un mauvais trade dans le portfolio est la faute la plus grave. "
            "Le portfolio doit préserver le capital. "
            "Manquer une opportunité est toujours acceptable."
        ),
        "Q5": (
            "Non, rejet immédiat. La discipline prime sur l'intelligence. "
            "Un gestionnaire indiscipliné met en danger tout le portfolio."
        ),
        "Q6": (
            "Non. Aucun chiffre ne domine les autres en allocation. "
            "L'edge doit être pondéré par volume, spread, temps et risque. "
            "L'analyse complète est non négociable."
        ),
        "Q7": (
            "Rejet immédiat. Les ressentis sont interdits en Alpha. "
            "Le portfolio est géré par des faits mesurables."
        ),
    },
    "Validation": {
        "Q1": (
            "Un marché tradable est une autorisation d'analyse. "
            "Un signal Alpha est une autorisation de trade. "
            "Confondre les deux invalide tout le processus de validation."
        ),
        "Q2": (
            "L'edge brut est rejeté en validation. Seul l'edge net, "
            "après déduction du coût du spread, est accepté. "
            "Le risque doit être vérifié indépendamment."
        ),
        "Q3": (
            "Le temps est un risque que la validation doit vérifier en priorité. "
            "Un edge tardif est suspect. "
            "La résolution temporelle détermine la fragilité du signal."
        ),
        "Q4": (
            "Autoriser un mauvais trade est la faute la plus grave en validation. "
            "La validation est la dernière barrière. "
            "Manquer une opportunité est acceptable."
        ),
        "Q5": (
            "Non, rejet immédiat. La discipline prime sur l'intelligence. "
            "Un agent indiscipliné est rejeté, même avec des compétences élevées."
        ),
        "Q6": (
            "Non. Aucun chiffre ne domine les autres. L'analyse complète est requise : "
            "volume, spread, temps, risque. "
            "L'edge seul ne suffit pas pour valider un signal."
        ),
        "Q7": (
            "Rejet immédiat. Les ressentis sont interdits en Alpha. "
            "La validation repose sur des faits mesurables et vérifiables."
        ),
    },
}

# =============================================================================
# RÉPONSES PAR RÔLE — PERSONA MEDIOCRE
# Connaissance partielle, réponses borderline, manque de précision
# =============================================================================
_MEDIOCRE_BASE = {
    "Q1": (
        "Un marché tradable c'est quand le marché est ouvert pour analyse. "
        "Un signal Alpha c'est quand on autorise un trade. "
        "C'est deux niveaux différents dans le processus."
    ),
    "Q2": (
        "L'edge de 4% ne prend pas en compte les frais et le spread. "
        "Il faut regarder l'edge net mais le chiffre brut donne une indication."
    ),
    "Q3": (
        "Le temps joue un rôle dans l'analyse mais l'edge reste important. "
        "Un edge tardif mérite attention mais n'est pas automatiquement rejeté."
    ),
    "Q4": (
        "Autoriser un mauvais trade est grave. "
        "Mais manquer trop d'opportunités est aussi un problème sur le long terme."
    ),
    "Q5": (
        "Non, la discipline est importante, mais un agent brillant "
        "pourrait être recadré avec du coaching et de la formation. "
        "Le rejet total semble excessif."
    ),
    "Q6": (
        "Un edge de 8% est intéressant mais il faut aussi "
        "vérifier les autres paramètres avant d'approuver."
    ),
    "Q7": (
        "Le feeling n'est pas fiable en trading. "
        "Il faut des données pour décider."
    ),
}

ROLE_MEDIOCRE = {
    "DataEngineer": {
        "Q1": (
            "Un marché tradable signifie que les données sont disponibles pour analyse. "
            "Un signal Alpha c'est quand les données confirment un trade potentiel."
        ),
        "Q2": (
            "L'edge brut de 4% doit être ajusté. Les coûts et le spread réduisent le net. "
            "Mais les données brutes donnent une première indication utile."
        ),
        "Q3": (
            "Le temps est un paramètre dans les données. "
            "Les données tardives sont moins fiables mais restent exploitables."
        ),
        **{k: v for k, v in _MEDIOCRE_BASE.items() if k in ("Q4", "Q5", "Q6", "Q7")},
    },
    "AlphaResearch": {
        "Q1": (
            "Un marché tradable ouvre la possibilité d'analyse. "
            "Un signal Alpha confirme qu'un trade est viable. "
            "La recherche fait le pont entre les deux."
        ),
        "Q2": (
            "En recherche, l'edge brut est le point de départ. "
            "Le net est plus précis après déduction des coûts, "
            "mais le brut guide la recherche initiale."
        ),
        "Q3": (
            "Le temps est un facteur de risque en recherche. "
            "Un edge tardif peut indiquer une correction déjà en cours."
        ),
        **{k: v for k, v in _MEDIOCRE_BASE.items() if k in ("Q4", "Q5", "Q6", "Q7")},
    },
    "StrategySelector": _MEDIOCRE_BASE.copy(),
    "Portfolio": _MEDIOCRE_BASE.copy(),
    "Validation": _MEDIOCRE_BASE.copy(),
}

# =============================================================================
# RÉPONSES PAR RÔLE — PERSONA OVERCONFIDENT
# Techniquement correct mais pousse les limites, sous-estime les risques
# =============================================================================
_OVERCONFIDENT_BASE = {
    "Q1": (
        "Marché tradable est l'analyse préliminaire. Signal Alpha est l'autorisation de trade. "
        "La distinction est basique, tout analyste compétent la connaît."
    ),
    "Q2": (
        "L'edge brut ne suffit pas, seul le net compte après coûts et spread. "
        "Le risque doit être mesuré. "
        "Mais un edge de 4% brut indique souvent un net intéressant."
    ),
    "Q3": (
        "Le temps est un risque que les débutants sous-estiment. "
        "Un edge tardif est suspect par définition. "
        "Avec une bonne modélisation, ce risque se gère efficacement."
    ),
    "Q4": (
        "Autoriser un mauvais trade est la faute la plus grave. "
        "Manquer une opportunité est acceptable. "
        "Avec un bon système, on minimise les deux simultanément."
    ),
    "Q5": (
        "Non, rejet. La discipline prime sur l'intelligence. "
        "Mais un système bien conçu devrait canaliser le talent."
    ),
    "Q6": (
        "Non. Aucun chiffre ne domine les autres. L'edge de 8% nécessite "
        "une analyse volume, spread, temps et risque. "
        "Un edge élevé facilite néanmoins la validation si le reste suit."
    ),
    "Q7": (
        "Rejet. Les décisions sont factuelles et mesurables. "
        "Mais une expertise développée produit des signaux rapides qui ressemblent au feeling."
    ),
}

ROLE_OVERCONFIDENT = {
    "DataEngineer": _OVERCONFIDENT_BASE.copy(),
    "AlphaResearch": {
        "Q1": (
            "La distinction marché tradable vs signal Alpha est élémentaire. "
            "Le premier autorise l'analyse, le second autorise le trade. "
            "En recherche Alpha, cette différence guide toute la méthodologie."
        ),
        "Q2": (
            "L'edge brut est un artefact. Seul le net après tous les coûts compte. "
            "Le risque est un paramètre séparé. "
            "Ma recherche identifie systématiquement les edges nets supérieurs."
        ),
        **{k: v for k, v in _OVERCONFIDENT_BASE.items() if k not in ("Q1", "Q2")},
    },
    "StrategySelector": _OVERCONFIDENT_BASE.copy(),
    "Portfolio": _OVERCONFIDENT_BASE.copy(),
    "Validation": _OVERCONFIDENT_BASE.copy(),
}

# =============================================================================
# RÉPONSES PAR RÔLE — PERSONA NAIVE
# Ne connaît pas les règles, utilise des mots interdits
# =============================================================================
_NAIVE_BASE = {
    "Q1": "Je pense que c'est à peu près la même chose, un marché tradable signifie qu'on peut trader.",
    "Q2": "L'edge de 4% me semble suffisant. Le feeling est bon sur ce trade.",
    "Q3": "Le temps n'est probablement pas si important si l'edge est élevé.",
    "Q4": "Il ne faut pas rater les bonnes opportunités. Mieux vaut agir que rester passif.",
    "Q5": "Oui, il faut garder le talent, on peut toujours l'encadrer ensuite.",
    "Q6": "Oui, un edge exceptionnel justifie à lui seul un signal Alpha.",
    "Q7": "Mon instinct me dit que c'est un bon trade. L'intuition compte.",
}

ROLE_NAIVE = {
    "DataEngineer": {
        "Q1": "Je pense qu'un marché tradable et un signal Alpha sont liés aux données. Les deux indiquent qu'on peut trader.",
        "Q2": "L'edge de 4% me semble solide. Les données confirment probablement le trade.",
        "Q3": "Le temps est un facteur mais je crois que les données compensent la latence.",
        **{k: v for k, v in _NAIVE_BASE.items() if k in ("Q4", "Q5", "Q6", "Q7")},
    },
    "AlphaResearch": {
        "Q1": "Je pense que la recherche Alpha transforme un marché tradable en signal. C'est le même concept à deux niveaux.",
        "Q2": "Probablement qu'un edge de 4% est suffisant après recherche approfondie.",
        "Q3": "Il me semble que le temps est moins critique quand la recherche est solide.",
        **{k: v for k, v in _NAIVE_BASE.items() if k in ("Q4", "Q5", "Q6", "Q7")},
    },
    "StrategySelector": _NAIVE_BASE.copy(),
    "Portfolio": {
        "Q1": "Je pense que le portfolio s'expose dès qu'un marché est tradable.",
        "Q2": "Un edge brut de 4% me semble suffisant pour une allocation du portfolio.",
        "Q3": "Le temps peut-être joue un rôle mais l'edge compense le risque.",
        **{k: v for k, v in _NAIVE_BASE.items() if k in ("Q4", "Q5", "Q6", "Q7")},
    },
    "Validation": _NAIVE_BASE.copy(),
}

# =============================================================================
# REGISTRE CENTRAL DES PROFILS
# =============================================================================
ALL_PROFILES = {
    "disciplined": ROLE_DISCIPLINED,
    "mediocre": ROLE_MEDIOCRE,
    "overconfident": ROLE_OVERCONFIDENT,
    "naive": ROLE_NAIVE,
}

ALL_PERSONAS = list(ALL_PROFILES.keys())


def get_responses(role: str, persona: str) -> dict[str, str]:
    """Retourne les réponses pour un rôle et persona donnés."""
    persona_profiles = ALL_PROFILES.get(persona, ALL_PROFILES["naive"])
    role_responses = persona_profiles.get(role)

    if role_responses is None:
        # Fallback sur les réponses de base du persona
        if persona == "disciplined":
            return _DISCIPLINED_BASE.copy()
        elif persona == "mediocre":
            return _MEDIOCRE_BASE.copy()
        elif persona == "overconfident":
            return _OVERCONFIDENT_BASE.copy()
        else:
            return _NAIVE_BASE.copy()

    # Compléter avec les réponses de base si certaines manquent
    base = {
        "disciplined": _DISCIPLINED_BASE,
        "mediocre": _MEDIOCRE_BASE,
        "overconfident": _OVERCONFIDENT_BASE,
        "naive": _NAIVE_BASE,
    }.get(persona, _NAIVE_BASE)

    complete = base.copy()
    complete.update(role_responses)
    return complete
