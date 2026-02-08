"""
CONFIGURATION ALPHA — Règles non négociables, constantes et seuils.
Ce fichier est la référence absolue. Aucune interprétation libre n'est autorisée.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Retourne l'heure courante en UTC. Utilisé partout à la place de datetime.now()."""
    return datetime.now(timezone.utc)

# =============================================================================
# LOI FONDATRICE
# =============================================================================
ALPHA_LAW = (
    "Le rôle de l'équipe Alpha est d'être fiable et prévisible, "
    "en prenant des décisions justifiées par des faits mesurables, "
    "et jamais par des intuitions."
)

# =============================================================================
# LES 10 RÈGLES D'OR (NON NÉGOCIABLES)
# =============================================================================
GOLDEN_RULES = {
    1: {
        "title": "Alpha ne trade jamais",
        "description": "Alpha analyse, structure, autorise. L'exécution appartient à d'autres équipes.",
    },
    2: {
        "title": "Aucun chiffre ne domine les autres",
        "description": (
            "Prix, spread, volume, temps, edge, risque sont équivalents. "
            "Si un seul est critique → REJET."
        ),
    },
    3: {
        "title": "Un marché tradable n'est PAS un signal",
        "description": (
            "Marché tradable = autorisation d'analyse. "
            "Signal Alpha = autorisation de trade."
        ),
    },
    4: {
        "title": "L'edge brut ne suffit jamais",
        "description": "Seul l'edge net (après coûts, spread, marge sécurité) est considéré.",
    },
    5: {
        "title": "Le temps est un risque",
        "description": (
            "Plus la résolution est proche, plus le signal est fragile. "
            "Un edge élevé tardif est suspect."
        ),
    },
    6: {
        "title": "Alpha est une machine à dire NON",
        "description": "Moins de 5% des marchés peuvent produire un signal approuvé.",
    },
    7: {
        "title": "Aucun langage flou n'est autorisé",
        "description": "Mots interdits : 'je pense', 'feeling', 'probablement'.",
    },
    8: {
        "title": "Tout signal doit être écrit",
        "description": "Un signal non formalisable par écrit est automatiquement rejeté.",
    },
    9: {
        "title": "Rater une opportunité est acceptable",
        "description": "Autoriser un mauvais trade est une faute grave.",
    },
    10: {
        "title": "La discipline prime sur l'intelligence",
        "description": "Un agent brillant mais indiscipliné est rejeté.",
    },
}

# =============================================================================
# MOTS INTERDITS
# =============================================================================
FORBIDDEN_WORDS_FR = [
    "je pense",
    "feeling",
    "probablement",
    "je crois",
    "peut-être",
    "il me semble",
    "j'ai l'impression",
    "intuition",
    "instinct",
    "ça devrait",
    "normalement",
    "à mon avis",
]

FORBIDDEN_WORDS_EN = [
    "i think",
    "i believe",
    "feeling",
    "probably",
    "maybe",
    "it seems",
    "likely",
    "gut feeling",
    "intuition",
    "instinct",
    "should be",
    "in my opinion",
]

FORBIDDEN_WORDS_LLM_EXTRA = [
    "it appears",
    "arguably",
    "presumably",
    "one could say",
    "it's possible",
    "might be",
    "could potentially",
    "tends to",
    "generally speaking",
]

FORBIDDEN_WORDS_ALL = FORBIDDEN_WORDS_FR + FORBIDDEN_WORDS_EN
FORBIDDEN_WORDS_LLM = FORBIDDEN_WORDS_ALL + FORBIDDEN_WORDS_LLM_EXTRA

# =============================================================================
# RÔLES ALPHA
# =============================================================================
ALPHA_ROLES = [
    "DataEngineer",
    "AlphaResearch",
    "StrategySelector",
    "Portfolio",
    "Validation",
]

# =============================================================================
# STATUTS DES AGENTS
# =============================================================================
AGENT_STATUS_CANDIDATE = "candidate"
AGENT_STATUS_ACTIVE = "active"
AGENT_STATUS_EXCLUDED = "excluded"
AGENT_STATUSES = [AGENT_STATUS_CANDIDATE, AGENT_STATUS_ACTIVE, AGENT_STATUS_EXCLUDED]

# =============================================================================
# TYPES DE SIGNAUX
# =============================================================================
SIGNAL_TYPES = ["ARBITRAGE", "PROBA", "MOMENTUM"]

# =============================================================================
# STATUTS DE SIGNAUX
# =============================================================================
SIGNAL_STATUS_APPROVED = "APPROVED"
SIGNAL_STATUS_SURVEILLANCE = "SURVEILLANCE"
SIGNAL_STATUS_REJECTED = "REJECTED"
SIGNAL_STATUSES = [SIGNAL_STATUS_APPROVED, SIGNAL_STATUS_SURVEILLANCE, SIGNAL_STATUS_REJECTED]

# =============================================================================
# CHAMPS OBLIGATOIRES D'UN SIGNAL
# =============================================================================
SIGNAL_REQUIRED_FIELDS = [
    "signal_id",
    "market",
    "type",
    "edge_net",
    "volume",
    "spread",
    "time_to_resolution",
    "risks",
    "status",
    "comment",
]

# =============================================================================
# MÉTRIQUES ÉQUIVALENTES (Règle 2)
# =============================================================================
EQUIVALENT_METRICS = ["edge_net", "volume", "spread", "time_to_resolution", "risks"]
METRIC_DOMINANCE_THRESHOLD = 0.60  # > 60% = dominance détectée → REJET

# =============================================================================
# SEUILS
# =============================================================================
MAX_WARNINGS = 3  # 3 avertissements = exclusion
AGENT_CACHE_MAX_SIZE = 50  # Taille max du cache LRU AgentRegistry
MAX_APPROVAL_PCT = 5.0  # Si > 5% signaux approuvés → blocage automatique
MIN_SIGNALS_FOR_BLOCKING = 20  # Nombre minimum de signaux avant activation du blocage
INTERVIEW_PASS_SCORE_HUMAN = 80  # Score minimum humain (%)
INTERVIEW_PASS_SCORE_LLM = 90  # Score minimum LLM (%) — plus strict

# =============================================================================
# SEUILS SIGNAL
# =============================================================================
MIN_EDGE_NET = 0.5  # Edge net minimum en %
MAX_TIME_TO_RESOLUTION_HOURS = 72  # Temps max avant résolution
LATE_EDGE_SUSPICION_HOURS = 48  # Edge élevé tardif = suspect au-delà de ce seuil

# =============================================================================
# CHEMINS
# =============================================================================
DATA_DIR = "data"
LOGS_DIR = "logs"
AGENTS_FILE = "data/agents.json"
AUDIT_LOG_FILE = "logs/audit.log"
AUDIT_META_FILE = "logs/audit.meta"
KPI_LOG_FILE = "logs/kpi.log"
QUESTIONS_FILE = "data/questions.json"

# =============================================================================
# ACTIONS AUDITABLES
# =============================================================================
AUDITABLE_ACTIONS = [
    "recruit_agent",
    "submit_signal",
    "approve_signal",
    "reject_signal",
    "issue_warning",
    "exclude_agent",
    "modify_agent",
]

# =============================================================================
# BYPASS PERMISSION — Autorisations limitées
# =============================================================================
BYPASS_ALLOWED_ACTIONS = [
    "consultation",
    "export",
    "replay",
    "simulation",
    "list_agents",
    "view_kpi",
    "view_audit_log",
]

BYPASS_FORBIDDEN_ACTIONS = [
    "approve_signal",
    "recruit_agent",
    "modify_agent",
    "exclude_agent",
    "disable_audit",
]

# =============================================================================
# MODE API LLM — STANDBY
# =============================================================================
# "STANDBY" = Aucun appel API réel. Évaluation locale uniquement.
# "ACTIVE"  = Appels API autorisés (nécessite clé API valide).
# Ce flag est le SEUL point de contrôle pour activer/désactiver les API LLM.
LLM_API_MODE = "STANDBY"

# =============================================================================
# FILE D'ATTENTE PERSISTÉE (SQLite)
# =============================================================================
QUEUE_DB_PATH = "data/alpha_queue.db"
QUEUE_MAX_RETRIES = 3
QUEUE_ENABLED = True

# =============================================================================
# ALPHA INTERFACE — Couche d'interoperabilite
# =============================================================================
ALPHA_INTERFACE_VERSION = "1.0.0"
ALPHA_INTERFACE_SCHEMA = "alpha_interface/decision_schema.json"
