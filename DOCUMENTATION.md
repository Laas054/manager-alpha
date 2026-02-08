# DOCUMENTATION COMPLETE — MANAGER IA ALPHA

> **Version** : 1.2
> **Python** : 3.10+
> **Statut API LLM** : STANDBY
> **Alpha Interface** : v1.0.0 (AlphaDecision)
> **Tests** : 170 unitaires + 59 stress-test + 7 property-based = TOUS PASS
> **Dependance optionnelle** : `hypothesis>=6.0.0` (property-based testing)
> **Reference IA** : `REFERENCE_IA.md` (version condensee pour transmission IA)
> **Repository** : github.com/Laas054/manager-alpha

---

## TABLE DES MATIERES

1. [Presentation du projet](#1-presentation-du-projet)
2. [Architecture](#2-architecture)
3. [Les 10 Regles d'Or](#3-les-10-regles-dor)
4. [Module config.py](#4-module-configpy)
5. [Module agent.py](#5-module-agentpy)
6. [Module audit.py](#6-module-auditpy)
7. [Module signal_alpha.py](#7-module-signal_alphapy)
8. [Module interview.py](#8-module-interviewpy)
9. [Module kpi.py](#9-module-kpipy)
10. [Module llm_evaluator.py](#10-module-llm_evaluatorpy)
11. [Module manager.py](#11-module-managerpy)
12. [Module simulated_profiles.py](#12-module-simulated_profilespy)
13. [Module failure_corpus.py](#13-module-failure_corpuspy)
14. [Module stress_test.py](#14-module-stress_testpy)
15. [Module test_alpha.py](#15-module-test_alphapy)
16. [Module main.py](#16-module-mainpy)
17. [Flux metier](#17-flux-metier)
18. [Systeme de securite et verrouillages](#18-systeme-de-securite-et-verrouillages)
19. [Conditions obligatoires](#19-conditions-obligatoires)
20. [Guide d'utilisation CLI](#20-guide-dutilisation-cli)
21. [Tests et validation](#21-tests-et-validation)
22. [Tableau des seuils et constantes](#22-tableau-des-seuils-et-constantes)
23. [Mots interdits](#23-mots-interdits)
24. [Alpha Interface — Couche d'interoperabilite](#24-alpha-interface--couche-dinteroperabilite)
25. [Module alpha_queue.py](#25-module-alpha_queuepy)
26. [Les 7 optimisations](#26-les-7-optimisations)
27. [Reference IA condensee (REFERENCE_IA.md)](#27-reference-ia-condensee-reference_iamd)

---

## 1. PRESENTATION DU PROJET

### Objectif

Le **Manager IA Alpha** est un systeme de gestion d'equipe de trading algorithmique. Il implemente le **Protocole Officiel Equipe Alpha** : un cadre de regles non negociables qui garantit que l'equipe Alpha reste fiable, previsible et incapable de produire un mauvais trade.

### Philosophie

**"Machine a dire NON"** — Le Manager Alpha est concu pour rejeter. Moins de 5% des marches produisent un signal approuve. Chaque decision est justifiee par des faits mesurables, jamais par des intuitions.

### Loi fondatrice

> *"Le role de l'equipe Alpha est d'etre fiable et previsible, en prenant des decisions justifiees par des faits mesurables, et jamais par des intuitions."*

### Fonctionnalites principales

| Fonctionnalite | Description |
|---|---|
| Entretiens eliminatoires | 7 questions obligatoires + pieges, evaluation automatique |
| Recrutement LLM | Evaluation d'agents IA avec severite accrue (90% minimum) |
| Validation de signaux | Format strict a 10 champs, detection de langage flou, **fail-fast** (arret des la premiere erreur) |
| Audit continu | Journal append-only avec **chaine de hash SHA-256**, autorite superieure au Manager |
| Systeme d'avertissements | 3 avertissements = exclusion automatique |
| Suivi KPI | Blocage automatique si taux approbation > 5% (minimum **20 signaux**) |
| AgentRegistry optimise | **Lazy loading** + **cache LRU** (max 50 agents en memoire) |
| Queue SQLite | **File d'attente persistee** pour livraison fiable des AlphaDecision |
| Horodatage UTC strict | **Toutes les timestamps en UTC** via `utc_now()` centralisee |
| Stress-test | Batterie de 59 verifications automatisees |
| Property-based testing | **7 tests generatifs** (hypothesis) verifiant les invariants structurels |
| Alpha Interface | Format de sortie AlphaDecision (schema JSON, contrat immutable, validation) |
| Reference IA | Documentation condensee pour transmission a d'autres IA |

---

## 2. ARCHITECTURE

### Arborescence du projet

```
C:\Users\Annick\manager-alpha\
|
|-- config.py                 # Configuration centrale (regles, seuils, constantes, utc_now())
|-- agent.py                  # Classe Agent + AgentRegistry (lazy loading + cache LRU)
|-- audit.py                  # Systeme d'audit + chaine SHA-256 + decorateur @audit_required
|-- signal_alpha.py           # Validation stricte des signaux Alpha (fail-fast)
|-- interview.py              # Systeme d'entretien (questions, pieges, scoring)
|-- kpi.py                    # Indicateurs de qualite + blocage automatique (N>=20)
|-- llm_evaluator.py          # Evaluation d'agents LLM (live + simule)
|-- manager.py                # Classe ManagerAlpha (orchestrateur central + queue)
|-- alpha_queue.py            # File d'attente SQLite persistee pour AlphaDecision
|-- simulated_profiles.py     # Profils simules (4 personas x 5 roles)
|-- failure_corpus.py         # Corpus de tests (signaux + entretiens echoues)
|-- stress_test.py            # Tests de robustesse automatises
|-- test_alpha.py             # 170 tests unitaires
|-- test_property.py          # 7 tests property-based (hypothesis)
|-- main.py                   # Interface CLI interactive (13 options)
|
|-- alpha_interface/
|   |-- __init__.py           # Package exports (AlphaDecisionBuilder, validate_against_schema)
|   |-- alpha_decision.py     # Classe AlphaDecisionBuilder + validation structurelle
|   |-- decision_schema.json  # JSON Schema AlphaDecision v1.0.0
|   |-- rules_contract.md     # Contrat de regles IMMUTABLE et versionne
|   |-- examples/
|       |-- approved.json     # Exemple AlphaDecision APPROVED
|       |-- rejected.json     # Exemple AlphaDecision REJECTED
|       |-- surveillance.json # Exemple AlphaDecision SURVEILLANCE
|
|-- data/
|   |-- agents.json           # Registre persistant des agents
|   |-- questions.json        # Banque de questions d'entretien
|   |-- alpha_queue.db        # Base SQLite file d'attente AlphaDecision
|
|-- logs/
|   |-- audit.log             # Journal d'audit append-only (chaine SHA-256)
|   |-- audit.meta            # Dernier hash de la chaine d'audit
|
|-- DOCUMENTATION.md          # Documentation complete (ce fichier)
|-- REFERENCE_IA.md           # Reference condensee pour transmission IA
|-- requirements.txt          # Dependances (hypothesis>=6.0.0)
|-- .gitignore                # Fichiers exclus du versionnement
```

### Organisation en 4 couches

**Couche Core (6 modules)** — Logique metier fondamentale :
- `config.py` — Regles, seuils, constantes, `utc_now()` centralise
- `agent.py` — Entite Agent et registre (lazy loading + cache LRU max 50)
- `audit.py` — Systeme d'audit (autorite superieure, chaine SHA-256)
- `signal_alpha.py` — Moteur de validation des signaux (fail-fast)
- `alpha_queue.py` — File d'attente SQLite persistee pour AlphaDecision
- `manager.py` — Orchestrateur central (+ queue + audit callback)

**Couche Interoperabilite (1 package)** — Sortie unique d'Alpha :
- `alpha_interface/` — Format AlphaDecision, schema JSON, contrat de regles, validation structurelle

**Couche Support (5 modules)** — Fonctionnalites complementaires :
- `interview.py` — Systeme d'entretien et scoring
- `kpi.py` — Indicateurs de qualite (fenetre N>=20)
- `llm_evaluator.py` — Evaluation d'agents LLM
- `simulated_profiles.py` — Banque de reponses simulees
- `failure_corpus.py` — Donnees de test

**Couche Execution (4 modules)** — Points d'entree :
- `main.py` — Interface CLI interactive
- `stress_test.py` — Tests de robustesse
- `test_alpha.py` — Tests unitaires
- `test_property.py` — Tests property-based (hypothesis)

### Graphe de dependances

```
main.py
  |-- manager.py
  |     |-- agent.py -----------> config.py
  |     |-- audit.py -----------> config.py
  |     |-- interview.py -------> config.py
  |     |-- kpi.py -------------> config.py
  |     |-- llm_evaluator.py ---> config.py, interview.py, simulated_profiles.py
  |     |-- signal_alpha.py ----> config.py
  |     |-- alpha_queue.py -----> config.py (SQLite)
  |     |-- alpha_interface/ ---> (AlphaDecisionBuilder)
  |-- audit.py (AuditViolation)
  |-- config.py

stress_test.py
  |-- config.py
  |-- failure_corpus.py (donnees pures)
  |-- llm_evaluator.py
  |-- manager.py
  |-- signal_alpha.py
  |-- simulated_profiles.py (donnees pures)

test_alpha.py
  |-- tous les modules
  |-- alpha_interface/ (AlphaDecisionBuilder, validate_against_schema)

test_property.py
  |-- config.py
  |-- signal_alpha.py
  |-- kpi.py
  |-- audit.py
  |-- alpha_interface/ (AlphaDecisionBuilder, validate_against_schema)
```

### Fichiers de donnees

**`data/agents.json`** — Registre persistant des agents. Structure par agent :
```json
{
  "id": "abc12345",
  "name": "AgentName",
  "role": "DataEngineer",
  "status": "active",
  "warnings": 0,
  "warning_reasons": [],
  "interview_passed": true,
  "interview_score": 90.0,
  "mode": "llm_simulated",
  "decisions_log": [],
  "created_at": "2026-02-08T...",
  "excluded_at": null,
  "verbal_discipline_score": 100.0
}
```

**`data/questions.json`** — Banque de 7 questions d'entretien au format JSON (miroir des constantes `MANDATORY_QUESTIONS` dans `interview.py`).

**`data/alpha_queue.db`** — Base de donnees SQLite pour la file d'attente persistee des AlphaDecision. Table `alpha_decisions` avec colonnes : `id`, `decision_id`, `payload` (JSON immutable), `status` (PENDING/DELIVERED/FAILED), `created_at`, `delivered_at`, `retry_count`, `max_retries`.

**`logs/audit.log`** — Journal d'audit en mode append-only avec chaine de hash SHA-256. Format par entree :
```
[2026-02-08T12:00:00+00:00] HASH=a1b2c3... | ACTION=submit_signal | ACTOR=agent_id | DETAILS=... | RESULT=APPROVED
```

**`logs/audit.meta`** — Fichier contenant le dernier hash de la chaine d'audit. Utilise pour reprendre le chainage SHA-256 apres redemarrage.

---

## 3. LES 10 REGLES D'OR

Ces regles sont **non negociables**. Elles sont definies dans `config.py` sous `GOLDEN_RULES`.

| # | Titre | Description |
|---|---|---|
| 1 | Alpha ne trade jamais | Alpha analyse, structure, autorise. L'execution appartient a d'autres equipes. |
| 2 | Aucun chiffre ne domine les autres | Prix, spread, volume, temps, edge, risque sont equivalents. Si un seul est critique -> REJET. |
| 3 | Un marche tradable n'est PAS un signal | Marche tradable = autorisation d'analyse. Signal Alpha = autorisation de trade. |
| 4 | L'edge brut ne suffit jamais | Seul l'edge net (apres couts, spread, marge securite) est considere. |
| 5 | Le temps est un risque | Plus la resolution est proche, plus le signal est fragile. Un edge eleve tardif est suspect. |
| 6 | Alpha est une machine a dire NON | Moins de 5% des marches peuvent produire un signal approuve. |
| 7 | Aucun langage flou n'est autorise | Mots interdits : "je pense", "feeling", "probablement", etc. |
| 8 | Tout signal doit etre ecrit | Un signal non formalisable par ecrit est automatiquement rejete. |
| 9 | Rater une opportunite est acceptable | Autoriser un mauvais trade est une faute grave. |
| 10 | La discipline prime sur l'intelligence | Un agent brillant mais indiscipline est rejete. |

---

## 4. MODULE `config.py`

**Role** : Reference absolue du systeme. Toutes les regles, seuils, constantes et chemins sont centralises ici. Aucune interpretation libre n'est autorisee.

### Fonction utilitaire

```python
def utc_now() -> datetime:
    """Retourne l'heure courante en UTC."""
    return datetime.now(timezone.utc)
```

Toutes les timestamps du systeme utilisent `utc_now()` au lieu de `datetime.now()`. Cela garantit la coherence horaire sur tous les modules (16 occurrences remplacees dans 8 fichiers).

### Constantes principales

| Constante | Type | Valeur | Description |
|---|---|---|---|
| `ALPHA_LAW` | `str` | *"Le role de l'equipe Alpha..."* | Loi fondatrice |
| `GOLDEN_RULES` | `dict[int, dict]` | 10 entrees | Les 10 Regles d'Or |
| `ALPHA_ROLES` | `list[str]` | 5 roles | DataEngineer, AlphaResearch, StrategySelector, Portfolio, Validation |
| `SIGNAL_TYPES` | `list[str]` | 3 types | ARBITRAGE, PROBA, MOMENTUM |
| `SIGNAL_REQUIRED_FIELDS` | `list[str]` | 10 champs | Champs obligatoires d'un signal |
| `EQUIVALENT_METRICS` | `list[str]` | 5 metriques | edge_net, volume, spread, time_to_resolution, risks |
| `LLM_API_MODE` | `str` | "STANDBY" | Mode de l'API LLM (STANDBY ou ACTIVE) |
| `ALPHA_INTERFACE_VERSION` | `str` | "1.0.0" | Version du format AlphaDecision |
| `ALPHA_INTERFACE_SCHEMA` | `str` | "alpha_interface/decision_schema.json" | Chemin du schema JSON |

### Seuils

| Constante | Valeur | Description |
|---|---|---|
| `MAX_WARNINGS` | 3 | 3 avertissements = exclusion automatique |
| `MAX_APPROVAL_PCT` | 5.0% | Si > 5% signaux approuves -> blocage |
| `MIN_SIGNALS_FOR_BLOCKING` | 20 | Nombre minimum de signaux avant activation du blocage KPI |
| `INTERVIEW_PASS_SCORE_HUMAN` | 80% | Score minimum pour les humains |
| `INTERVIEW_PASS_SCORE_LLM` | 90% | Score minimum pour les LLM |
| `MIN_EDGE_NET` | 0.5% | Edge net minimum accepte |
| `MAX_TIME_TO_RESOLUTION_HOURS` | 72h | Temps maximum avant resolution |
| `LATE_EDGE_SUSPICION_HOURS` | 48h | Edge eleve + temps > 48h = suspect |
| `METRIC_DOMINANCE_THRESHOLD` | 60% | Si une metrique > 60% des mentions -> REJET |
| `AGENT_CACHE_MAX_SIZE` | 50 | Taille max du cache LRU AgentRegistry |
| `QUEUE_MAX_RETRIES` | 3 | Nombre max de tentatives de livraison queue |
| `QUEUE_ENABLED` | True | Active la file d'attente SQLite |

### Statuts

| Type | Constantes | Valeurs |
|---|---|---|
| Agent | `AGENT_STATUS_CANDIDATE`, `_ACTIVE`, `_EXCLUDED` | "candidate", "active", "excluded" |
| Signal | `SIGNAL_STATUS_APPROVED`, `_SURVEILLANCE`, `_REJECTED` | "APPROVED", "SURVEILLANCE", "REJECTED" |

### Mots interdits

| Liste | Contenu | Total |
|---|---|---|
| `FORBIDDEN_WORDS_FR` | je pense, feeling, probablement, je crois, peut-etre, il me semble, j'ai l'impression, intuition, instinct, ca devrait, normalement, a mon avis | 12 |
| `FORBIDDEN_WORDS_EN` | i think, i believe, feeling, probably, maybe, it seems, likely, gut feeling, intuition, instinct, should be, in my opinion | 12 |
| `FORBIDDEN_WORDS_LLM_EXTRA` | it appears, arguably, presumably, one could say, it's possible, might be, could potentially, tends to, generally speaking | 9 |
| `FORBIDDEN_WORDS_ALL` | FR + EN | 24 |
| `FORBIDDEN_WORDS_LLM` | ALL + LLM_EXTRA | 33 |

### Permissions bypass

| Liste | Actions |
|---|---|
| `BYPASS_ALLOWED_ACTIONS` | consultation, export, replay, simulation, list_agents, view_kpi, view_audit_log |
| `BYPASS_FORBIDDEN_ACTIONS` | approve_signal, recruit_agent, modify_agent, exclude_agent, disable_audit |

### Chemins

| Constante | Chemin |
|---|---|
| `DATA_DIR` | "data" |
| `LOGS_DIR` | "logs" |
| `AGENTS_FILE` | "data/agents.json" |
| `AUDIT_LOG_FILE` | "logs/audit.log" |
| `AUDIT_META_FILE` | "logs/audit.meta" |
| `KPI_LOG_FILE` | "logs/kpi.log" |
| `QUESTIONS_FILE` | "data/questions.json" |
| `QUEUE_DB_PATH` | "data/alpha_queue.db" |

---

## 5. MODULE `agent.py`

**Role** : Gestion des agents Alpha avec separation stricte des statuts (candidat / actif / exclu) et suivi disciplinaire complet.

### Classe `Agent`

Represente un agent Alpha avec son historique auditable.

**Constructeur** :
```python
Agent(name: str, role: str)
```
- Genere un `id` unique (UUID tronque a 8 caracteres)
- Statut initial : `"candidate"`
- Leve `ValueError` si le role n'est pas dans `ALPHA_ROLES`

**Attributs** :

| Attribut | Type | Description |
|---|---|---|
| `id` | `str` | Identifiant unique (UUID[:8]) |
| `name` | `str` | Nom de l'agent |
| `role` | `str` | Role Alpha (DataEngineer, etc.) |
| `status` | `str` | candidate / active / excluded |
| `warnings` | `int` | Compteur d'avertissements (0-3) |
| `warning_reasons` | `list[str]` | Motifs des avertissements horodates |
| `interview_passed` | `bool` | Entretien reussi |
| `interview_score` | `float` | Score de l'entretien (0-100) |
| `mode` | `str` | "human", "llm", ou "llm_simulated" |
| `decisions_log` | `list[dict]` | Historique auditable des decisions |
| `created_at` | `str` | Date de creation (ISO) |
| `excluded_at` | `str\|None` | Date d'exclusion (ISO) |
| `verbal_discipline_score` | `float` | Score de discipline verbale (0-100) |

**Methodes** :

| Methode | Signature | Description |
|---|---|---|
| `activate()` | `-> bool` | Passe de candidat a actif. Requiert `interview_passed=True`. Retourne `False` si echec. |
| `add_warning(reason)` | `(str) -> str` | Ajoute un avertissement. Retourne `"EXCLU"` si 3 atteints, `"AGENT_DEJA_EXCLU"` si deja exclu, sinon `"AVERTISSEMENT_N/3"`. |
| `log_decision(decision)` | `(dict) -> None` | Enregistre une decision horodatee dans `decisions_log`. |
| `is_active()` | `-> bool` | Statut == "active" |
| `is_excluded()` | `-> bool` | Statut == "excluded" |
| `is_candidate()` | `-> bool` | Statut == "candidate" |
| `to_dict()` | `-> dict` | Serialisation complete pour JSON |
| `from_dict(data)` | `classmethod -> Agent` | Deserialisaation depuis un dict |

### Classe `AgentRegistry`

Registre centralise avec **lazy loading** et **cache LRU** (max 50 agents en memoire).

**Constructeur** :
```python
AgentRegistry()
```
- Charge un **index leger** depuis `data/agents.json` (id -> {status, role, name}).
- Les objets `Agent` complets ne sont charges qu'a la demande (**lazy loading**).
- Un cache LRU (`OrderedDict`, max `AGENT_CACHE_MAX_SIZE=50`) evite les relectures frequentes.

**Architecture interne** :
- `_index` : `dict[str, dict]` — Index leger (toujours en memoire)
- `_cache` : `OrderedDict` — Cache LRU des agents charges (max 50)
- `_audit_callback` : `callable|None` — Callback d'audit pose par `manager.py`

**Methodes** :

| Methode | Signature | Description |
|---|---|---|
| `add(agent)` | `(Agent) -> str` | Ajoute un agent, met a jour index + cache, sauvegarde |
| `get(agent_id)` | `(str) -> Agent\|None` | Cache hit -> retour (move_to_end). Cache miss -> `_load_single()` + `_cache_put()`. |
| `remove(agent_id)` | `(str) -> bool` | Supprime de l'index + cache + sauvegarde |
| `list_all()` | `-> list[Agent]` | Charge tous les agents via `get()` |
| `list_by_status(status)` | `(str) -> list[Agent]` | Filtre sur l'index d'abord, puis charge uniquement les agents matchants |
| `list_active()` | `-> list[Agent]` | Agents actifs |
| `list_candidates()` | `-> list[Agent]` | Candidats |
| `list_excluded()` | `-> list[Agent]` | Agents exclus |
| `list_by_role(role)` | `(str) -> list[Agent]` | Filtrage par role |
| `_load_index()` | `-> None` | Charge le JSON et construit l'index leger |
| `_load_single(agent_id)` | `(str) -> Agent\|None` | Lit le JSON, deserialise UN seul agent |
| `_cache_put(agent_id, agent)` | `(str, Agent) -> None` | Insertion dans le cache + eviction LRU si > 50 |
| `_refresh_index()` | `-> None` | Rafraichit l'index depuis le JSON |
| `_save()` | `-> None` | Lit le JSON existant, overlay les agents caches, supprime les non-indexes, ecrit |

---

## 6. MODULE `audit.py`

**Role** : Systeme d'audit avec **autorite superieure au Manager**. Journal append-only avec **chaine de hash SHA-256**, horodatage UTC obligatoire, non modifiable. Le Manager ne peut pas contourner l'audit.

### Classe `AuditViolation`

Exception personnalisee levee quand l'audit bloque une action ou quand la chaine de hash est corrompue.

```python
class AuditViolation(Exception): pass
```

### Classe `AuditSystem`

**Constructeur** :
```python
AuditSystem()
```
- Cree le repertoire `logs/` si absent
- Initialise le journal d'audit avec une entree INIT hashee
- Charge le dernier hash depuis `logs/audit.meta` (genesis = `"0" * 64`)

**Chaine de hash SHA-256** :

Chaque entree du journal est chainee cryptographiquement. Le hash de chaque entree est calcule via `SHA-256(previous_hash + raw_entry)`. Cette chaine garantit l'integrite du journal : toute modification, insertion ou suppression d'une entree est detectable.

- **Genesis hash** : `"0" * 64` (64 zeros)
- **Format d'entree** : `[{timestamp}] HASH={sha256} | ACTION=... | ACTOR=... | DETAILS=... | RESULT=...`
- **Persistance** : Le dernier hash est sauvegarde dans `logs/audit.meta` apres chaque ecriture

**Methodes** :

| Methode | Signature | Description |
|---|---|---|
| `log(action, actor, details, result)` | `(str, str, str, str) -> None` | Ecrit une entree horodatee et hashee dans le journal. **Append-only** : ouverture en mode `"a"`. Chaque entree est chainee par SHA-256. |
| `authorize(action, actor, context)` | `(str, str, dict\|None) -> bool` | Autorise ou bloque une action AVANT execution. Leve `AuditViolation` si bypass interdit. |
| `authorize_signal_approval(kpi_data)` | `(dict) -> bool` | Verifie si les approbations sont autorisees. Bloque si taux > 5%. |
| `check_language(text, is_llm)` | `(str, bool) -> dict` | Detecte le langage flou (Regle 7). Retourne `{"clean": bool, "violations": list}`. |
| `check_rule_compliance(decision)` | `(dict) -> dict` | Verifie conformite aux 10 Regles d'Or. Retourne `{"compliant": bool, "violations": list}`. |
| `audit_decision(agent_id, decision)` | `(str, dict) -> dict` | Audit complet d'une decision. Score base sur : regles (-30/violation), justification (-10 a -20), langage (-15/violation). |
| `issue_warning(agent, reason)` | `(Agent, str) -> dict` | Emet un avertissement formel. Delegue a `agent.add_warning()`. |
| `review_agent_history(agent)` | `(Agent) -> dict` | Revue complete de l'historique. Si echec > 30% -> recommandation EXCLUSION. |
| `detect_deviation(action, context)` | `(str, dict) -> dict\|None` | Detecte les tentatives de deviation (forcer trade, minimiser risque, contourner seuil). |
| `read_log(last_n)` | `(int) -> list[str]` | Lit les N dernieres entrees du journal. Lecture seule. |
| `verify_integrity()` | `-> dict` | Parcourt tout le journal, recalcule chaque hash, verifie la chaine. Retourne `{"valid": bool, "entries": int}`. Leve `AuditViolation` si la chaine est corrompue. |
| `_load_last_hash()` | `-> str` | Charge le dernier hash depuis `audit.meta` (genesis si absent). |
| `_save_last_hash()` | `-> None` | Sauvegarde le dernier hash dans `audit.meta`. |
| `_compute_hash(prev_hash, raw_entry)` | `(str, str) -> str` | Calcule SHA-256(prev_hash + raw_entry). |

**Verrouillage** : La classe `AuditSystem` ne possede **aucune methode** `delete_log`, `edit_log`, `clear_log` ou `modify_log`. Le journal est immuable. La chaine de hash SHA-256 rend toute alteration detectable.

### Decorateur `@audit_required`

```python
def audit_required(action_name: str)
```

Decorateur qui impose l'autorisation de l'audit AVANT toute action critique du Manager. Appele sur chaque methode decoree :

1. Verifie que `self.audit` (AuditSystem) est initialise
2. Appelle `audit.authorize(action_name, "ManagerAlpha", context)`
3. Appelle `audit.detect_deviation(action_name, context)`
4. Si une violation est detectee -> leve `AuditViolation`
5. Sinon, execute la methode originale

**Methodes decorees dans `manager.py`** :
- `start_interview` -> `"recruit_agent"`
- `evaluate_llm_agent` -> `"recruit_agent"`
- `evaluate_llm_agent_live` -> `"recruit_agent"`
- `evaluate_llm_agent_simulated` -> `"recruit_agent"`
- `submit_signal` -> `"submit_signal"`
- `audit_agent` -> `"audit_agent"`
- `review_all_agents` -> `"review_all_agents"`
- `warn_agent` -> `"issue_warning"`

---

## 7. MODULE `signal_alpha.py`

**Role** : Format officiel et validation stricte des signaux Alpha. Champ manquant = rejet automatique. Aucune exception. **Fail-fast** : la validation s'arrete des la premiere erreur detectee (court-circuit entre les 8 etapes).

### Classe `SignalAlpha`

**Constructeur** :
```python
SignalAlpha(data: dict)
```

**Champs obligatoires du signal** (10 champs) :

| Champ | Description |
|---|---|
| `signal_id` | Identifiant unique du signal |
| `market` | Marche concerne (ex: ETH-PERP, BTC-PERP) |
| `type` | ARBITRAGE, PROBA, ou MOMENTUM |
| `edge_net` | Edge net en % (apres couts) |
| `volume` | Volume du marche |
| `spread` | Spread en % |
| `time_to_resolution` | Temps avant resolution en heures |
| `risks` | Description factuelle des risques |
| `status` | APPROVED, SURVEILLANCE, ou REJECTED |
| `comment` | Commentaire factuel (mots flous interdits) |

**Methode principale** :

```python
validate() -> dict
```

Retourne `{"valid": bool, "errors": list, "status": str, "comment": str}`.

**Pipeline de validation fail-fast** (dans cet ordre, **arret des la premiere erreur**) :

1. **`_check_required_fields()`** — Regle 8 : Tout signal doit etre ecrit. Champ manquant ou vide -> rejet immediat.
   *Si erreur(s) -> REJET immediat, etapes 2-8 non executees.*

2. **`_check_signal_type()`** — Type doit etre dans `["ARBITRAGE", "PROBA", "MOMENTUM"]`.
   *Si erreur(s) -> REJET immediat, etapes 3-8 non executees.*

3. **`_check_signal_status()`** — Statut doit etre dans `["APPROVED", "SURVEILLANCE", "REJECTED"]`.
   *Si erreur(s) -> REJET immediat, etapes 4-8 non executees.*

4. **`_check_edge_net()`** — Regle 4 : Edge net doit etre numerique et >= 0.5%.
   *Si erreur(s) -> REJET immediat, etapes 5-8 non executees.*

5. **`_check_time_to_resolution()`** — Regle 5 : Temps <= 72h. Si edge > 5% ET temps > 48h -> signal SUSPECT.
   *Si erreur(s) -> REJET immediat, etapes 6-8 non executees.*

6. **`_check_language()`** — Regle 7 : Detection de mots flous dans le commentaire et les risques.
   *Si erreur(s) -> REJET immediat, etapes 7-8 non executees.*

7. **`_check_single_metric_dominance()`** — Regle 2 (CONDITION 1) : Si une metrique represente > 60% des mentions dans le commentaire -> REJET. Si le commentaire ne mentionne qu'une seule metrique alors que 3+ sont fournies -> REJET.
   *Si erreur(s) -> REJET immediat, etape 8 non executee.*

8. **`_check_risks_field()`** — Champ risques doit faire au moins 10 caracteres.

**Note** : Le fail-fast est entre les methodes. Les erreurs internes a une meme methode sont toutes collectees avant le court-circuit.

**Autres methodes** :

| Methode | Signature | Description |
|---|---|---|
| `to_dict()` | `-> dict` | Signal + metadonnees de validation |
| `format_display()` | `-> str` | Affichage formate officiel |

---

## 8. MODULE `interview.py`

**Role** : Systeme d'entretien eliminatoire Alpha. Une seule question a la fois. Pieges volontaires. Tolerance zero.

### Constantes

**`MANDATORY_QUESTIONS`** — 7 questions obligatoires :

| ID | Question | Pieges | Regle testee | Max phrases |
|---|---|---|---|---|
| Q1 | Difference entre marche tradable et signal Alpha | Non | 3 | 4 |
| Q2 | Pourquoi refuser un trade avec 4% d'edge | Non | 4 | 4 |
| Q3 | Risque le plus sous-estime par les debutants | Non | 5 | 4 |
| Q4 | Faute la plus grave pour Alpha | Non | 9 | 3 |
| Q5 | Agent brillant mais indiscipline | **OUI** | 10 | 3 |
| Q6_PIEGE | Marche avec edge 8%, approuver immediatement ? | **OUI** | 2 | 4 |
| Q7_PIEGE | Feeling positif sur un marche, que faire ? | **OUI** | 7 | 3 |

Chaque question definit :
- `keywords_required` : Mots-cles qui doivent apparaitre dans la reponse
- `keywords_forbidden` : Mots-cles eliminatoires
- `expected_concepts` : Concepts attendus (matching par racine)

### Fonction utilitaire

```python
_strip_accents(text: str) -> str
```
Supprime les accents pour normaliser la comparaison (ex: "resume" matche "resume").

### Classe `InterviewEvaluator`

**Constructeur** :
```python
InterviewEvaluator(is_llm: bool = False)
```
- Si `is_llm=True` : mots interdits etendus (33), seuil 90%, penalite de 10%

**Methode principale** :

```python
evaluate_response(question: dict, response: str) -> dict
```

**Systeme de scoring** (100 points max) :

| Critere | Points | Description |
|---|---|---|
| Mots-cles requis | 45 pts | `(found / required) * 45` — Matching par substring apres normalisation |
| Nombre de phrases | 25 pts | 25 si <= max_sentences, 0 sinon |
| Concepts attendus | 30 pts | `(concepts_found / expected) * 30` — Matching par racine (min 4 chars) |

**Criteres eliminatoires** (avant le scoring) :
1. Mot interdit global detecte -> elimination, score = 0
2. Mot-cle interdit de la question detecte -> elimination, score = 0

**Penalite LLM** :
- Score brut multiplie par 0.90 (reduction de 10%)
- Detection de hedging patterns : -5 points par pattern detecte

**Seuils de passage** :
- Humain : >= 80%
- LLM : >= 90%

**Methode de resultat global** :

```python
get_overall_result() -> dict
```
- Si une seule elimination -> rejet global
- Calcul du score moyen
- Passe si : toutes les questions passees ET score moyen >= seuil

### Classe `InterviewSession`

Gere une session d'entretien complete.

**Constructeur** :
```python
InterviewSession(candidate_name: str, role: str, is_llm: bool = False)
```

**Methodes** :

| Methode | Signature | Description |
|---|---|---|
| `get_current_question()` | `-> dict\|None` | Retourne la question courante ou None si termine |
| `submit_answer(answer)` | `(str) -> dict` | Soumet une reponse. Pour LLM : un seul echec = fin immediate. |
| `get_final_result()` | `-> dict` | Resultat final avec nom, role, mode, dates |
| `is_active()` | `-> bool` | Session encore en cours |
| `questions_remaining()` | `-> int` | Nombre de questions restantes |

### Fonction

```python
load_custom_questions() -> list[dict]
```
Charge des questions personnalisees depuis `data/questions.json`.

---

## 9. MODULE `kpi.py`

**Role** : Suivi des indicateurs de qualite Alpha. Un bon Alpha = peu de signaux, tres propres. Blocage automatique si taux d'approbation depasse 5%.

### Classe `KPITracker`

**Constructeur** :
```python
KPITracker()
```

**Attributs** :

| Attribut | Type | Description |
|---|---|---|
| `total_markets_analyzed` | `int` | Nombre de marches analyses |
| `total_markets_rejected` | `int` | Nombre de marches rejetes |
| `total_signals_submitted` | `int` | Signaux soumis |
| `total_signals_approved` | `int` | Signaux approuves |
| `total_signals_surveillance` | `int` | Signaux en surveillance |
| `total_signals_rejected` | `int` | Signaux rejetes |
| `rejection_reasons` | `list[str]` | Motifs de rejet |
| `approval_blocked` | `bool` | Approbations bloquees |
| `approval_blocked_at` | `str\|None` | Date du blocage |
| `verbal_violations` | `dict[str, int]` | Violations par agent |
| `signal_clarity_scores` | `list[float]` | Scores de clarte |

**Methodes d'enregistrement** :

| Methode | Signature | Description |
|---|---|---|
| `record_market_analysis(rejected, reason)` | `(bool, str) -> None` | Enregistre une analyse de marche |
| `record_signal(status, clarity_score, rejection_reasons)` | `(str, float, list) -> None` | Enregistre un signal et verifie le seuil |
| `record_verbal_violation(agent_id)` | `(str) -> None` | Enregistre une violation verbale |

**Proprietes calculees** :

| Propriete | Type | Description |
|---|---|---|
| `markets_rejected_pct` | `float` | % de marches rejetes |
| `signals_approved_pct` | `float` | % de signaux approuves |
| `signals_rejected_pct` | `float` | % de signaux rejetes |
| `avg_signal_clarity` | `float` | Clarte moyenne des signaux |
| `top_rejection_reasons` | `list[tuple]` | Top 10 motifs de rejet |
| `total_verbal_violations` | `int` | Total des violations verbales |

**Methodes de controle** :

| Methode | Signature | Description |
|---|---|---|
| `_check_approval_threshold()` | `-> None` | Verifie si > 5% approuves (minimum **20 signaux** = `MIN_SIGNALS_FOR_BLOCKING`) -> bloque |
| `is_approval_blocked()` | `-> bool` | Etat du blocage |
| `manual_unblock(reviewer, reason)` | `(str, str) -> dict` | Deblocage manuel avec justification |

**Methodes de rapport** :

| Methode | Signature | Description |
|---|---|---|
| `report()` | `-> dict` | Donnees brutes du rapport |
| `format_report()` | `-> str` | Rapport formate avec sections |
| `get_kpi_data()` | `-> dict` | Donnees pour l'audit |

---

## 10. MODULE `llm_evaluator.py`

**Role** : Evaluation des agents LLM avec severite accrue. Tolerance zero. Score minimum 90%. Supporte le mode STANDBY (simule) et le mode ACTIVE (API Anthropic).

### Constantes

| Constante | Description |
|---|---|
| `ALPHA_CANDIDATE_SYSTEM_PROMPT` | Prompt systeme pour agents disciplines (contient les 10 regles) |
| `ALPHA_CANDIDATE_NAIVE_PROMPT` | Prompt systeme pour agents naifs (pas de formation Alpha) |
| `ALPHA_CANDIDATE_ROLES` | Descriptions de role pour chaque poste Alpha |

### Classe `AnthropicAgent`

Agent LLM base sur l'API Anthropic Claude. **Bloque en mode STANDBY**.

**Constructeur** :
```python
AnthropicAgent(api_key: str, role: str, model: str = "claude-sonnet-4-5-20250929", persona: str = "disciplined")
```
- Leve `RuntimeError` si `LLM_API_MODE != "ACTIVE"`

**Methodes** :

| Methode | Signature | Description |
|---|---|---|
| `_get_client()` | `-> Anthropic` | Initialise le client (lazy loading) |
| `_build_system_prompt()` | `-> str` | Construit le prompt selon persona et role |
| `ask(question, max_sentences)` | `(str, int) -> str` | Envoie une question, maintient l'historique |
| `reset()` | `-> None` | Reinitialise l'historique |

### Classe `SimulatedLLMAgent`

Agent LLM simule — reponses pre-calibrees locales. **Aucun appel API**.

**Constructeur** :
```python
SimulatedLLMAgent(role: str, persona: str = "disciplined")
```
- Charge les reponses via `get_responses(role, persona)` depuis `simulated_profiles.py`

**Methodes** :

| Methode | Signature | Description |
|---|---|---|
| `ask(question, max_sentences)` | `(str, int) -> str` | Retourne une reponse simulee basee sur le role et persona |
| `_identify_question(question)` | `(str) -> str` | Identifie Q1-Q7 par mots-cles dans la question |
| `reset()` | `-> None` | Reinitialise l'historique |
| `get_profile_summary()` | `-> dict` | Resume du profil (role, persona, stats) |

### Classe `LLMEvaluator`

Moteur d'evaluation principal.

**Constructeur** :
```python
LLMEvaluator(api_provider: str | None = None, api_key: str | None = None)
```

**Methodes** :

| Methode | Signature | Description |
|---|---|---|
| `evaluate_local(question, response)` | `(dict, str) -> dict` | Evaluation locale (regles) + checks LLM supplementaires |
| `_extra_llm_checks(response)` | `(str) -> dict` | Detection avancee : hedging, verbosite (>150 mots), structure evasive, non-reponse |
| `run_live_interview(api_key, role, model, persona, callback)` | `(...) -> dict` | Entretien temps reel via API Anthropic. **Bloque en STANDBY**. |
| `run_simulated_interview(role, persona, callback)` | `(...) -> dict` | Entretien avec agent simule. Meme severite que live. |
| `evaluate_via_api(question, llm_callable)` | `(dict, callable) -> dict` | Interface generique (callable -> reponse -> evaluation) |
| `run_full_evaluation(responses)` | `(dict[str, str]) -> dict` | Entretien complet avec reponses pre-fournies. Tolerance zero. |
| `get_evaluation_report()` | `-> str` | Rapport d'evaluation formate |
| `get_live_report(result)` | `(dict) -> str` | Rapport detaille d'un entretien live/simule |

**Checks LLM supplementaires** (`_extra_llm_checks`) :
- Hedging conditionnel (`while...it's true...however`)
- Expressions evasives (`on balance`, `more or less`, `to some extent`)
- Hedging academique (`it could be argued`, `one might say`)
- Minimisation (`not entirely`, `somewhat`, `rather`)
- Verbosite excessive (> 150 mots)
- Structure evasive (however + but sans conclusion)
- Non-reponse (`that's a great question`, `let me think`)

---

## 11. MODULE `manager.py`

**Role** : Autorite absolue de l'equipe Alpha. Orchestre tous les modules. Plus strict que les agents, plus rationnel que les analystes, plus conservateur que le marche. **Machine a dire NON**.

### Classe `ManagerAlpha`

**Constructeur** :
```python
ManagerAlpha()
```
Initialise :
- `AuditSystem` — systeme d'audit
- `AgentRegistry` — registre des agents (+ callback d'audit pour tracer les acces)
- `KPITracker` — suivi des KPIs
- `LLMEvaluator` — evaluateur LLM
- `AlphaDecisionQueue` — file d'attente SQLite (si `QUEUE_ENABLED=True`)
- `active_interviews` — sessions d'entretien en cours
- `bypass_mode` — mode consultation (desactive par defaut)

**Methodes de recrutement** :

| Methode | Decorateur | Description |
|---|---|---|
| `start_interview(name, role, is_llm, context)` | `@audit_required("recruit_agent")` | Lance un entretien humain. Cree l'agent comme candidat. |
| `answer_interview(agent_id, answer)` | Aucun | Soumet une reponse. Gere elimination, passage, fin. |
| `evaluate_llm_agent(name, role, responses, context)` | `@audit_required("recruit_agent")` | Evaluation LLM avec reponses pre-fournies. |
| `evaluate_llm_agent_live(name, role, api_key, model, persona, callback, context)` | `@audit_required("recruit_agent")` | Entretien live via API Anthropic. **Bloque en STANDBY**. |
| `evaluate_llm_agent_simulated(name, role, persona, callback, context)` | `@audit_required("recruit_agent")` | Entretien avec agent simule. |

**Methodes de signal** :

| Methode | Decorateur | Description |
|---|---|---|
| `submit_signal(agent_id, signal_data, context)` | `@audit_required("submit_signal")` | Valide un signal Alpha. Verifie : agent actif, validation signal, langage, blocage KPI. Enregistre les KPIs. **Genere automatiquement un AlphaDecision** via `AlphaDecisionBuilder`. **Enqueue la decision** dans la file SQLite (non bloquant, try/except). |

**Methodes d'audit** :

| Methode | Decorateur | Description |
|---|---|---|
| `audit_agent(agent_id, context)` | `@audit_required("audit_agent")` | Audit complet d'un agent. Avertissement si echec > 30%. |
| `review_all_agents(context)` | `@audit_required("review_all_agents")` | Revue de tous les agents actifs. |

**Methodes utilitaires** :

| Methode | Description |
|---|---|
| `get_identity()` | Retourne l'identite du Manager (loi fondatrice, role) |
| `get_rules()` | Retourne les 10 Regles d'Or |
| `get_kpi_report()` | Rapport KPI formate |
| `get_kpi_data()` | Donnees KPI brutes |
| `list_agents(status)` | Liste des agents (filtre optionnel par statut) |
| `enable_bypass()` | Active le mode consultation. Ne desactive JAMAIS l'audit. |
| `disable_bypass()` | Retour au mode normal |
| `warn_agent(agent_id, reason)` | Avertissement manuel (`@audit_required("issue_warning")`) |
| `view_audit_log(last_n)` | Consultation du journal d'audit |
| `manual_unblock_approvals(reviewer, reason)` | Deblocage manuel des approbations |

---

## 12. MODULE `simulated_profiles.py`

**Role** : Banque de reponses realistes pour 4 personas x 5 roles Alpha. Chaque profil represente un archetype d'agent LLM avec ses forces et faiblesses.

### Personas

| Persona | Description | Taux de passage attendu | Niveau de risque |
|---|---|---|---|
| `disciplined` | Connait et respecte toutes les regles Alpha | 95% | LOW |
| `mediocre` | Connaissance partielle, reponses borderline | 20% | MEDIUM |
| `overconfident` | Bon techniquement mais pousse les limites | 10% | HIGH |
| `naive` | Ne connait pas les regles, utilise des mots interdits | 0% | CRITICAL |

### Tics verbaux par persona

| Persona | Tics |
|---|---|
| `disciplined` | Aucun |
| `mediocre` | "en general", "dans la plupart des cas", "normalement" |
| `overconfident` | "evidemment", "clairement", "il est certain que" |
| `naive` | "je pense", "feeling", "probablement", "intuition" |

### Structure des reponses

Chaque persona a :
- Un dictionnaire de base (`_DISCIPLINED_BASE`, etc.) avec les reponses Q1-Q7 generiques
- Un dictionnaire par role (`ROLE_DISCIPLINED`, etc.) avec des reponses specifiques

Pour le persona `disciplined`, les 5 roles ont des reponses Q1-Q7 entierement personnalisees. Exemples :
- **DataEngineer Q1** : "Un marche tradable est une autorisation d'analyse des donnees..."
- **AlphaResearch Q1** : "Un marche tradable est une autorisation d'analyse, le debut du processus..."
- **Validation Q1** : "Un marche tradable est une autorisation d'analyse. Confondre les deux invalide..."

### Constantes exportees

| Constante | Type | Description |
|---|---|---|
| `PROFILE_METADATA` | `dict` | Metadonnees par persona (taux, risque) |
| `VERBAL_TICS` | `dict` | Tics verbaux par persona |
| `ALL_PROFILES` | `dict` | Dictionnaire complet des 4 personas |
| `ALL_PERSONAS` | `list[str]` | Liste des noms de personas |

### Fonction

```python
get_responses(role: str, persona: str) -> dict[str, str]
```
Retourne les reponses Q1-Q7 pour un role et persona donnes. Complete avec les reponses de base si certaines manquent.

---

## 13. MODULE `failure_corpus.py`

**Role** : Corpus de tests structure pour le stress-test. Contient des scenarios qui doivent echouer et des cas limites.

### Signaux invalides (`FAILED_SIGNALS`) — 15 scenarios

| Tag | Regle violee | Description |
|---|---|---|
| `R2_EDGE_DOMINANCE` | Regle 2 | Commentaire ne mentionne que l'edge |
| `R2_VOLUME_ONLY` | Regle 2 | Commentaire ne mentionne que le volume |
| `R4_EDGE_TOO_LOW` | Regle 4 | Edge net = 0.1% (< 0.5%) |
| `R4_EDGE_ZERO` | Regle 4 | Edge net = 0% |
| `R5_LATE_EDGE` | Regle 5 | Edge 6% avec resolution a 60h (suspect) |
| `R5_OVER_MAX_TIME` | Regle 5 | Resolution a 80h (> 72h max) |
| `R7_JE_PENSE` | Regle 7 | "je pense" dans le commentaire |
| `R7_FEELING` | Regle 7 | "feeling" dans les risques |
| `R7_PROBABLEMENT` | Regle 7 | "probablement" dans le commentaire |
| `R7_RISKS_FLOU` | Regle 7 | "il me semble" dans les risques |
| `R8_MISSING_MARKET` | Regle 8 | Champ market vide |
| `R8_MISSING_RISKS` | Regle 8 | Champ risks absent |
| `R8_EMPTY_COMMENT` | Regle 8 | Commentaire vide |
| `INVALID_TYPE` | Type | Type "TREND" (invalide) |
| `RISKS_TOO_SHORT` | Risques | Champ risks = "ok" (< 10 chars) |

### Entretiens echoues (`FAILED_INTERVIEWS`) — 6 scenarios

| Tag | Description |
|---|---|
| `NAIVE_FULL` | Candidat naif sur toutes les questions |
| `FORBIDDEN_Q2` | Mot interdit "feeling" a la Q2 |
| `TRAP_Q5_FAIL` | Piege Q5 : "oui, garder le talent" |
| `TRAP_Q6_FAIL` | Piege Q6 : "oui, approuver" |
| `TRAP_Q7_FAIL` | Piege Q7 : "suivre l'intuition" |
| `LLM_HEDGING` | Reponses avec hedging LLM ("it depends", "however...but") |

### Signaux borderline (`BORDERLINE_SIGNALS`) — 7 scenarios

| Tag | Attendu | Description |
|---|---|---|
| `BORDER_EDGE_MINIMUM` | VALID | Edge net = 0.5% (pile au minimum) |
| `BORDER_EDGE_JUST_BELOW` | INVALID | Edge net = 0.4% (juste sous le seuil) |
| `BORDER_TIME_AT_48H` | VALID | Resolution = 48h (sous le seuil suspect) |
| `BORDER_TIME_JUST_OVER_48H` | INVALID | Resolution = 49h + edge 6% (suspect) |
| `BORDER_COMMENT_BALANCED` | VALID | Commentaire equilibre (toutes metriques mentionnees) |
| `BORDER_TIME_AT_72H` | VALID | Resolution = 72h (pile au maximum) |
| `BORDER_TIME_OVER_72H` | INVALID | Resolution = 73h (depasse le max) |

### Entretiens borderline (`BORDERLINE_INTERVIEWS`) — 2 scenarios

| Tag | Description |
|---|---|
| `BORDER_TERSE` | Reponses tres courtes mais correctes |
| `BORDER_PARTIAL_CONCEPTS` | Concepts partiellement couverts |

### Constantes

```python
TOTAL_SCENARIOS = 30  # 15 + 6 + 7 + 2
ALL_FAILURE_SCENARIOS = {
    "failed_signals": FAILED_SIGNALS,
    "failed_interviews": FAILED_INTERVIEWS,
    "borderline_signals": BORDERLINE_SIGNALS,
    "borderline_interviews": BORDERLINE_INTERVIEWS,
}
```

---

## 14. MODULE `stress_test.py`

**Role** : Tests automatises de robustesse. Execute des batteries de tests sans intervention humaine.

### Classe `StressTestReport`

**Constructeur** :
```python
StressTestReport()
```

**Methodes** :

| Methode | Signature | Description |
|---|---|---|
| `add_result(section, name, passed, expected, detail)` | `(...) -> None` | Ajoute un resultat de test |
| `add_kpi_check(name, value, expected, correct)` | `(...) -> None` | Ajoute une verification KPI |
| `format()` | `-> str` | Rapport complet formate |

### Fonction `run_stress_test`

```python
run_stress_test(verbose: bool = False, callback=None) -> StressTestReport
```

Execute 8 sections de test (59 verifications au total) :

| Section | Tests | Description |
|---|---|---|
| 1. Entretiens simules | 20 | 5 roles x 4 personas. Disciplined doit passer, les autres doivent echouer. |
| 2. Signaux invalides | 15 | Corpus FAILED_SIGNALS. Tous doivent etre rejetes. |
| 3. Signaux borderline | 7 | Corpus BORDERLINE_SIGNALS. Chacun a son resultat attendu. |
| 4. Entretiens echoues | 6 | Corpus FAILED_INTERVIEWS. Tous doivent etre rejetes. |
| 5. Entretiens borderline | 2 | Corpus BORDERLINE_INTERVIEWS. Observation (toujours correct). |
| 6. Stress KPI | 5 | Recrutement agent, injection directe 12 APPROVED + 8 REJECTED (20 signaux, 60% approbation), blocage KPI, signal bloque, deblocage manuel. |
| 7. Stress avertissements | 1 | 3 warnings -> exclusion automatique. |
| 8. Integration Manager | 3 | Simulated/disciplined recrute, simulated/naive rejete, simulated/overconfident rejete. |

**Execution standalone** :
```bash
python stress_test.py --verbose
```

---

## 15. MODULE `test_alpha.py`

**Role** : 170 tests unitaires couvrant tous les modules du systeme.

### Sections de test

| Section | Tests | Description |
|---|---|---|
| 1. IMPORTS | 1 | Verification que tous les imports fonctionnent |
| 2. CONFIG | 10 | 10 regles, mots interdits, questions, roles, types, champs, seuils |
| 3. AGENT | 18 | Creation, activation, avertissements (3=exclusion), serialisation, decisions |
| 4. SIGNAL ALPHA | 13 | Champs manquants, mots interdits, types, edge, temps, dominance, risques |
| 4b. ALPHA DECISION | 23 | Builder (decision_id, status, confidence, rules, urgency), validation schema |
| 5. AUDIT SYSTEM | 23 | Langage, regles, bypass, decisions, journal append-only, verrouillages |
| 6. INTERVIEW | 12 | Bonnes reponses, elimination, pieges Q5/Q6/Q7, tolerance zero LLM |
| 7. KPI | 13 | Taux, blocage, deblocage, rapport, violations verbales |
| 8. LLM EVALUATOR | 6 | Evaluation locale, seuil 90%, hedging, API sans callable |
| 8b. MODE STANDBY | 11 | STANDBY actif, AnthropicAgent bloque, SimulatedLLMAgent OK, entretiens |
| 9. MANAGER ALPHA | 35 | Integration complete : identite, entretien, signal, audit, revue, bypass, avertissements, STANDBY, decorateurs, alpha_decision |
| 10. TESTS DE SECURITE | 5 | Absence de methodes dangereuses (disable_audit, delete_log), KPI blocage |
| **TOTAL** | **170** | |

**Execution** :
```bash
python test_alpha.py
```

---

## 16. MODULE `main.py`

**Role** : Interface CLI interactive. Point d'entree principal du systeme Alpha.

### Lancement

```bash
python main.py                    # Mode normal
python main.py --bypass-permission  # Mode consultation uniquement
```

### Menu principal (13 options)

| Option | Action | Mode bypass |
|---|---|---|
| 1 | Recruter un agent (entretien humain) | Interdit |
| 2 | Evaluer un agent LLM | Interdit |
| 3 | Soumettre un signal Alpha | Interdit |
| 4 | Auditer un agent | Autorise |
| 5 | Voir les KPIs | Autorise |
| 6 | Lister les agents | Autorise |
| 7 | Revue complete de tous les agents | Interdit |
| 8 | Voir le journal d'audit | Autorise |
| 9 | Afficher les Regles d'Or | Autorise |
| 10 | Avertir un agent | Interdit |
| 11 | Basculer mode bypass | Autorise |
| 12 | Debloquer les approbations | Interdit |
| 13 | Stress-test automatise | Autorise |
| 0 | Quitter | Autorise |

### Sous-menu Evaluation LLM (option 2)

**En mode STANDBY** :
1. Entretien SIMULE (reponses locales pre-calibrees)
2. Entretien MANUEL (saisie des reponses a la main)

**En mode ACTIVE** :
1. Entretien LIVE (API Anthropic Claude)
2. Entretien SIMULE
3. Entretien MANUEL

### Modeles disponibles (mode LIVE)

| Choix | Modele | Description |
|---|---|---|
| 1 | claude-haiku-4-5-20251001 | Haiku 4.5 (rapide, economique) |
| 2 | claude-sonnet-4-5-20250929 | Sonnet 4.5 (equilibre) |
| 3 | claude-opus-4-6 | Opus 4.6 (plus capable) |

### Personas disponibles

| Choix | Persona | Description |
|---|---|---|
| 1 | disciplined | Connait les regles Alpha |
| 2 | mediocre | Connaissance partielle — borderline |
| 3 | overconfident | Bon techniquement, pousse les limites |
| 4 | naive | Ne connait pas les regles — test de rejet |

### Fonctions d'affichage

| Fonction | Description |
|---|---|
| `print_header(text)` | En-tete formate avec couleurs |
| `print_success(text)` | Message vert [OK] |
| `print_error(text)` | Message rouge [ERREUR] |
| `print_warning(text)` | Message jaune [ALERTE] |
| `print_info(text)` | Message bleu [INFO] |
| `safe_input(prompt)` | Input protege (EOFError, KeyboardInterrupt) |

---

## 17. FLUX METIER

### Flux Recrutement Humain

```
Utilisateur selectionne "1. Recruter un agent"
  |
  v
Saisie nom + role
  |
  v
@audit_required verifie l'autorisation
  |
  v
Agent cree (statut: candidate)
  |
  v
Session d'entretien demarree
  |
  v
Pour chaque question Q1-Q7 :
  |
  |-- Affichage de la question
  |-- Saisie de la reponse
  |-- Verification mots interdits -> ELIMINATION si detecte
  |-- Verification mots-cles requis (45 pts)
  |-- Verification nombre de phrases (25 pts)
  |-- Verification concepts attendus (30 pts)
  |-- Score >= 80% -> PASS (question suivante)
  |-- Score < 80% -> continue mais accumule
  |
  v
Toutes questions passees ?
  |-- OUI + score moyen >= 80% -> Agent ACTIVE (statut: active)
  |-- NON -> Agent reste candidat (statut: candidate)
```

### Flux Recrutement LLM

```
Choix du mode (simule / live / manuel)
  |
  v
@audit_required verifie l'autorisation
  |
  v
Agent cree (statut: candidate, mode: llm/llm_simulated)
  |
  v
Pour chaque question Q1-Q7 :
  |
  |-- Question envoyee a l'agent LLM
  |-- Reponse recue (simulee ou API)
  |-- Evaluation locale + checks LLM supplementaires
  |-- Penalite LLM : score * 0.90
  |-- Score >= 90% -> PASS (question suivante)
  |-- Score < 90% -> TOLERANCE ZERO -> REJET IMMEDIAT
  |
  v
Toutes questions passees + score moyen >= 90% ?
  |-- OUI -> Agent RECRUTE (statut: active)
  |-- NON -> Agent REJETE
```

### Flux Signal Alpha

```
Utilisateur selectionne "3. Soumettre un signal"
  |
  v
Choix de l'agent actif + saisie des 10 champs
  |
  v
@audit_required verifie l'autorisation
  |
  v
Verification agent actif
  |
  v
SignalAlpha.validate() (FAIL-FAST : arret des la premiere erreur) :
  |-- Champs obligatoires presents ? -> si erreur : REJET immediat
  |-- Type valide (ARBITRAGE/PROBA/MOMENTUM) ? -> si erreur : REJET immediat
  |-- Statut valide (APPROVED/SURVEILLANCE/REJECTED) ? -> si erreur : REJET immediat
  |-- Edge net >= 0.5% ? -> si erreur : REJET immediat
  |-- Temps <= 72h ? Edge eleve + temps > 48h = suspect ? -> si erreur : REJET immediat
  |-- Langage flou dans commentaire/risques ? -> si erreur : REJET immediat
  |-- Dominance d'une metrique (> 60%) ? -> si erreur : REJET immediat
  |-- Risques suffisamment detailles (>= 10 chars) ?
  |
  v
Si signal APPROVED :
  |-- Verification blocage KPI (taux > 5%)
  |-- Si bloque -> REJET automatique
  |
  v
Enregistrement KPI (signal + marche)
  |
  v
Log decision de l'agent + journal d'audit
  |
  v
AlphaDecisionBuilder.build() :
  |-- Genere decision_id (AD-{signal_id}-{timestamp})
  |-- Determine status (APPROVED/SURVEILLANCE/REJECTED)
  |-- Calcule confidence_level (clarity_score: <50=LOW, 50+=MEDIUM, 80+=HIGH)
  |-- Construit constraints (max_size, urgency, expiry)
  |-- Extrait rules_failed par regex sur les erreurs
  |-- Calcule rules_passed = {1..10} - rules_failed
  |-- Valide contre le schema
  |
  v
Log audit : alpha_decision_generated
  |
  v
Queue SQLite : enqueue(alpha_decision) (non bloquant, try/except)
  |
  v
Resultat : APPROVED / SURVEILLANCE / REJECTED + alpha_decision
```

### Flux Audit

```
Utilisateur selectionne "4. Auditer un agent"
  |
  v
@audit_required verifie l'autorisation
  |
  v
AuditSystem.review_agent_history(agent) :
  |
  |-- Pour chaque decision dans decisions_log :
  |     |-- Verification conformite aux 10 regles
  |     |-- Verification qualite justification
  |     |-- Verification discipline du langage
  |     |-- Score (100 - deductions)
  |     |-- passed si score >= 60
  |
  v
Calcul taux d'echec global
  |-- Si echec > 30% -> Recommandation EXCLUSION
  |-- Avertissement emis automatiquement
  |
  v
Si 3 avertissements -> EXCLUSION AUTOMATIQUE
```

### Flux KPI et Blocage

```
Chaque signal soumis -> KPITracker.record_signal()
  |
  v
_check_approval_threshold() :
  |-- signals_approved_pct > 5% ET total >= 20 (MIN_SIGNALS_FOR_BLOCKING) ?
  |     |-- OUI -> approval_blocked = True
  |     |-- NON -> continue
  |
  v
Si blocage actif :
  |-- Tout signal APPROVED est automatiquement rejete
  |-- Deblocage uniquement via manual_unblock(reviewer, reason)
  |-- Log dans le journal d'audit
```

---

## 18. SYSTEME DE SECURITE ET VERROUILLAGES

### 1. Journal d'audit append-only avec chaine SHA-256

Le fichier `logs/audit.log` est ouvert en mode `"a"` (append) a chaque ecriture. Chaque entree est chainee cryptographiquement par **SHA-256** : `hash_n = SHA-256(hash_{n-1} + raw_entry)`. La methode `verify_integrity()` parcourt tout le journal et verifie la chaine complete. Toute alteration est detectee et leve `AuditViolation`.

La classe `AuditSystem` ne possede **aucune methode** de suppression, modification ou vidage :
- Pas de `delete_log()`
- Pas de `edit_log()`
- Pas de `clear_log()`
- Pas de `modify_log()`

### 2. Decorateur `@audit_required`

Chaque methode critique du Manager est protegee par le decorateur `@audit_required`. L'audit est appele **AVANT** l'execution de la methode. Le Manager **ne peut pas** contourner cette verification.

### 3. Mode bypass

Le mode `--bypass-permission` limite les actions a la consultation :
- **Autorise** : consultation, export, replay, simulation, list_agents, view_kpi, view_audit_log
- **Interdit** : approve_signal, recruit_agent, modify_agent, exclude_agent, disable_audit
- Le mode bypass ne desactive **JAMAIS** l'audit

### 4. Blocage KPI automatique

Si le taux d'approbation depasse 5% (avec minimum **20 signaux** soumis = `MIN_SIGNALS_FOR_BLOCKING`) :
- `approval_blocked = True` automatiquement
- Tout nouveau signal APPROVED est rejete
- Deblocage uniquement par `manual_unblock(reviewer, reason)` avec justification

### 5. Systeme d'avertissements

- Chaque agent peut recevoir des avertissements (manuels ou automatiques)
- **3 avertissements = exclusion automatique**
- L'exclusion est irreversible (`status = "excluded"`)
- Un agent deja exclu ne peut pas recevoir de nouveaux avertissements

### 6. Tolerance zero LLM

Pour les agents LLM :
- Score minimum : 90% (vs 80% pour les humains)
- Mots interdits etendus (33 vs 24)
- Un seul echec a une question = rejet immediat de tout l'entretien
- Detection de hedging et ambiguite
- Penalite automatique de 10% sur le score brut

---

## 19. CONDITIONS OBLIGATOIRES

### CONDITION 1 — Regle 2 formalisee (`signal_alpha.py`)

La methode `_check_single_metric_dominance()` implemente :
- Comptage des mentions de chaque metrique dans le commentaire
- Si une metrique > 60% des mentions totales -> REJET
- Si le commentaire ne mentionne qu'une seule metrique alors que 3+ metriques sont fournies dans les donnees -> REJET
- Mots-cles par metrique : edge (edge, rendement, profit, gain), volume (volume, liquidite), spread (spread, ecart), temps (temps, resolution, expiry), risques (risque, danger, exposition)

### CONDITION 2 — Audit superieur au Manager (`audit.py`)

- Le decorateur `@audit_required` est applique sur **8 methodes** du Manager
- `AuditSystem.authorize()` est appele AVANT toute action
- `AuditSystem.detect_deviation()` verifie les tentatives de manipulation
- Si le Manager n'a pas d'attribut `audit` -> `AuditViolation` levee
- En mode bypass, les actions interdites levent `AuditViolation`

### CONDITION 3 — Severite LLM >= humains (`interview.py`, `llm_evaluator.py`)

| Critere | Humain | LLM |
|---|---|---|
| Score minimum | 80% | 90% |
| Mots interdits | 24 (FR + EN) | 33 (+ LLM extras) |
| Penalite sur score | Aucune | -10% (score * 0.90) |
| Tolerance aux echecs | Partielle | Zero (1 echec = rejet) |
| Detection hedging | Non | Oui (10 patterns) |
| Detection verbosite | Non | Oui (> 150 mots) |
| Detection non-reponse | Non | Oui (3 patterns) |

---

## 20. GUIDE D'UTILISATION CLI

### Lancement

```bash
# Mode normal
python main.py

# Mode consultation uniquement (bypass)
python main.py --bypass-permission
```

### Exemple : Recruter un agent humain (option 1)

```
Choix : 1

RECRUTEMENT — ENTRETIEN HUMAIN
Nom du candidat : Jean Dupont
Roles disponibles : DataEngineer, AlphaResearch, StrategySelector, Portfolio, Validation
Role : DataEngineer

[OK] Entretien demarre pour Jean Dupont (ID: abc12345)
[INFO] Questions restantes : 7

[Q1] Explique la difference entre marche tradable et signal Alpha.
  (Maximum 4 phrases)

Reponse : Un marche tradable est une autorisation d'analyse.
Un signal Alpha est une autorisation de trade validee par l'equipe.
Ces concepts sont fondamentalement distincts.

[OK] Question passee — Score: 90%
```

### Exemple : Evaluer un agent LLM simule (option 2)

```
Choix : 2

EVALUATION AGENT LLM
[ALERTE] API LLM en STANDBY — Mode simule et manuel uniquement.

Mode :
  1. Entretien SIMULE (reponses locales pre-calibrees)
  2. Entretien MANUEL (saisie des reponses)

Choix [1/2] : 1

Nom de l'agent LLM simule : TestBot
Roles disponibles : DataEngineer, ...
Role : DataEngineer

Persona du candidat simule :
  1. Discipline (connait les regles Alpha)
  2. Mediocre (connaissance partielle — borderline)
  3. Surconfiant (bon techniquement, pousse les limites)
  4. Naif (ne connait pas les regles — test de rejet)

Persona [1/2/3/4] : 1

(Entretien automatique — 7 questions evaluees)

[OK] Agent LLM simule TestBot RECRUTE (ID: def67890)
```

### Exemple : Soumettre un signal (option 3)

```
Choix : 3

SOUMISSION — SIGNAL ALPHA
Agents actifs :
  [abc12345] Jean Dupont — DataEngineer

ID de l'agent : abc12345

SIGNAL_ID : SIG-001
MARKET : ETH-PERP
TYPE : ARBITRAGE
EDGE_NET (%) : 2.5
VOLUME : 500000
SPREAD (%) : 0.05
TIME_TO_RESOLUTION (heures) : 12
RISKS (description factuelle) : Risque de liquidite modere. Exposition controlee a 1%.
STATUS : APPROVED
COMMENTAIRE FACTUEL : Edge net confirme. Volume suffisant. Spread faible. Temps court. Risque controle.

[OK] Signal VALIDE — Status: APPROVED
```

### Exemple : Stress-test (option 13)

```
Choix : 13

STRESS-TEST AUTOMATISE — BATTERIE COMPLETE
Lancer le stress-test ? [O/N] : O
Mode verbose ? [O/N] : O

(59 verifications executees automatiquement)

RESULTAT FINAL : CONFORME
59/59 verifications correctes
```

---

## 21. TESTS ET VALIDATION

### Tests unitaires (`test_alpha.py`)

**Execution** :
```bash
python test_alpha.py
```

**Resultat attendu** :
```
RESULTATS: 170 PASS / 0 FAIL / 170 TOTAL
TOUS LES TESTS PASSES — Systeme Alpha CONFORME.
```

**Couverture** : 12 sections couvrant imports, config, agent, signal, alpha_decision, audit, interview, KPI, LLM evaluator, STANDBY, manager et securite.

### Stress-test (`stress_test.py`)

**Execution** :
```bash
python stress_test.py --verbose
```

**Resultat attendu** :
```
RESULTAT FINAL : CONFORME
59/59 verifications correctes
```

**Couverture** : 8 sections testant 20 combinaisons roles x personas, 15 signaux invalides, 7 signaux borderline, 6 entretiens echoues, 2 entretiens borderline, stress KPI (20 signaux minimum), stress avertissements, et integration Manager.

### Property-based testing (`test_property.py`)

**Dependance** : `hypothesis>=6.0.0` (`pip install hypothesis`)

**Execution** :
```bash
python test_property.py
```

**Resultat attendu** :
```
RESULTATS: 7 PASS / 0 FAIL / 7 TOTAL
TOUS LES PROPERTY TESTS PASSES.
```

**7 tests generatifs** verifiant les invariants structurels du systeme :

| Test | Invariant verifie | Max examples |
|---|---|---|
| Signal valide -> toujours valide | Tout signal conforme au protocole passe la validation | 50 |
| Signal incomplet -> toujours rejete | Un signal avec champs aleatoires (pas les 10 requis) est rejete | 50 |
| Edge < 0.5% -> toujours rejete | Un edge_net inferieur au minimum est rejete | 50 |
| Mot interdit -> toujours rejete | Tout mot interdit dans le commentaire provoque un rejet | 30 |
| AlphaDecision -> toujours conforme | Toute AlphaDecision construite passe la validation de schema | 50 |
| KPI <= 5% -> jamais bloque | Si taux approbation <= 5% avec >= 20 signaux, pas de blocage | 50 |
| Hash chain -> integrite verifiee | La chaine de hash reste integre quel que soit le nombre d'entrees | 10 |

**Strategies hypothesis utilisees** : `st.fixed_dictionaries`, `st.sampled_from`, `st.floats`, `st.integers`, `st.text` pour generer des signaux valides et invalides aleatoirement.

---

## 22. TABLEAU DES SEUILS ET CONSTANTES

| Parametre | Valeur | Fichier | Description |
|---|---|---|---|
| Score humain minimum | 80% | config.py | `INTERVIEW_PASS_SCORE_HUMAN` |
| Score LLM minimum | 90% | config.py | `INTERVIEW_PASS_SCORE_LLM` |
| Penalite LLM | -10% | interview.py | `score * 0.90` |
| Max avertissements | 3 | config.py | `MAX_WARNINGS` |
| Max approbation % | 5.0% | config.py | `MAX_APPROVAL_PCT` |
| Min signaux pour blocage | 20 | config.py | `MIN_SIGNALS_FOR_BLOCKING = 20` |
| Cache LRU max agents | 50 | config.py | `AGENT_CACHE_MAX_SIZE = 50` |
| Queue max tentatives | 3 | config.py | `QUEUE_MAX_RETRIES = 3` |
| Edge net minimum | 0.5% | config.py | `MIN_EDGE_NET` |
| Temps max resolution | 72h | config.py | `MAX_TIME_TO_RESOLUTION_HOURS` |
| Seuil edge tardif suspect | 48h | config.py | `LATE_EDGE_SUSPICION_HOURS` |
| Seuil dominance metrique | 60% | config.py | `METRIC_DOMINANCE_THRESHOLD` |
| Scoring mots-cles | 45 pts | interview.py | `keyword_ratio * 45` |
| Scoring phrases | 25 pts | interview.py | 25 si <= max_sentences |
| Scoring concepts | 30 pts | interview.py | `concept_ratio * 30` |
| Audit echec seuil | 60/100 | audit.py | `score >= 60` pour passer |
| Audit echec recommendation | 30% | audit.py | `> 30%` echecs -> EXCLUSION |
| LLM max mots | 150 | llm_evaluator.py | Verbosite excessive |
| Risques min longueur | 10 chars | signal_alpha.py | Champ risks insuffisant |

---

## 23. MOTS INTERDITS

### Francais (12 termes)

| Mot | Statut |
|---|---|
| je pense | Interdit (tous) |
| feeling | Interdit (tous) |
| probablement | Interdit (tous) |
| je crois | Interdit (tous) |
| peut-etre | Interdit (tous) |
| il me semble | Interdit (tous) |
| j'ai l'impression | Interdit (tous) |
| intuition | Interdit (tous) |
| instinct | Interdit (tous) |
| ca devrait | Interdit (tous) |
| normalement | Interdit (tous) |
| a mon avis | Interdit (tous) |

### Anglais (12 termes)

| Mot | Statut |
|---|---|
| i think | Interdit (tous) |
| i believe | Interdit (tous) |
| feeling | Interdit (tous) |
| probably | Interdit (tous) |
| maybe | Interdit (tous) |
| it seems | Interdit (tous) |
| likely | Interdit (tous) |
| gut feeling | Interdit (tous) |
| intuition | Interdit (tous) |
| instinct | Interdit (tous) |
| should be | Interdit (tous) |
| in my opinion | Interdit (tous) |

### Supplementaires LLM (9 termes)

| Mot | Statut |
|---|---|
| it appears | Interdit (LLM uniquement) |
| arguably | Interdit (LLM uniquement) |
| presumably | Interdit (LLM uniquement) |
| one could say | Interdit (LLM uniquement) |
| it's possible | Interdit (LLM uniquement) |
| might be | Interdit (LLM uniquement) |
| could potentially | Interdit (LLM uniquement) |
| tends to | Interdit (LLM uniquement) |
| generally speaking | Interdit (LLM uniquement) |

---

## 24. ALPHA INTERFACE — COUCHE D'INTEROPERABILITE

### Principe

**Alpha est un fournisseur de decisions, pas un moteur partage.** Aucune equipe externe (Beta, Gamma, Delta) n'accede au code interne Alpha. Toute interaction passe par une interface contractuelle IMMUTABLE : le format **AlphaDecision**.

Chaque decision validee par `submit_signal()` produit automatiquement un AlphaDecision au format standardise.

### Package `alpha_interface/`

#### `__init__.py`

Exporte les deux elements publics du package :
```python
from alpha_interface.alpha_decision import AlphaDecisionBuilder, validate_against_schema
__all__ = ["AlphaDecisionBuilder", "validate_against_schema"]
```

#### `decision_schema.json` — Schema JSON AlphaDecision v1.0.0

Schema JSON (draft 2020-12) definissant le format contractuel. `additionalProperties: false` sur la racine et les contraintes.

| Champ | Type | Description |
|---|---|---|
| `decision_id` | `string` | Format `"AD-{signal_id}-{timestamp}"` |
| `market` | `string` | Marche concerne |
| `status` | `enum` | `REJECTED`, `SURVEILLANCE`, `APPROVED` |
| `confidence_level` | `enum` | `LOW`, `MEDIUM`, `HIGH` |
| `edge_net` | `number` | Edge net en % |
| `constraints` | `object` | `{max_size, urgency, expiry}` |
| `constraints.max_size` | `number` | Taille maximale autorisee (= volume du signal) |
| `constraints.urgency` | `enum` | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `constraints.expiry` | `string` | Date d'expiration ISO 8601 |
| `rules_passed` | `array[int]` | Numeros des regles passees |
| `rules_failed` | `array[int]` | Numeros des regles echouees |
| `audit_ref` | `string` | Reference d'audit `"[{timestamp}]-{signal_id}"` |
| `schema_version` | `string` | Version du schema (`"1.0.0"`) |
| `generated_at` | `string` | Date de generation ISO 8601 |

#### `rules_contract.md` — Contrat de regles IMMUTABLE

Document versionne (v1.0.0) qui definit :

**5 principes fondamentaux** :
1. Alpha ne trade jamais — il autorise ou refuse
2. Alpha n'impose jamais de taille de position — `max_size` est un plafond, pas un ordre
3. Alpha peut retirer une decision a tout moment
4. L'execution hors contraintes est une faute grave
5. Aucune equipe externe ne peut modifier une AlphaDecision

**Mapping regles -> methodes de validation** :

| Regle | Methode de validation | Module |
|---|---|---|
| R1 | Structurelle (Alpha ne trade pas) | `config.py` |
| R2 | `_check_single_metric_dominance()` | `signal_alpha.py` |
| R3 | Semantique (tradable != signal) | `interview.py` |
| R4 | `_check_edge_net()` | `signal_alpha.py` |
| R5 | `_check_time_to_resolution()` | `signal_alpha.py` |
| R6 | `_check_approval_threshold()` | `kpi.py` |
| R7 | `_check_language()` | `signal_alpha.py` |
| R8 | `_check_required_fields()` | `signal_alpha.py` |
| R9 | Structurelle (rater > mauvais trade) | `config.py` |
| R10 | `interview.py` + `llm_evaluator.py` | Multi-modules |

#### `alpha_decision.py` — Classe AlphaDecisionBuilder

**Constantes** :

| Constante | Description |
|---|---|
| `ALL_RULE_NUMBERS` | `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]` |
| `RULE_ERROR_PATTERNS` | Dictionnaire de patterns regex pour detecter les regles violees |

**Patterns de detection des regles echouees** :

| Regle | Patterns regex |
|---|---|
| R2 | `[Rr].gle 2`, `[Dd]ominance`, `aucun chiffre ne domine` |
| R4 | `edge_net.*inf.rieur`, `edge_net.*minimum`, `edge_net doit .tre num.rique` |
| R5 | `[Rr].gle 5`, `time_to_resolution.*d.passe`, `SUSPECT` |
| R7 | `[Rr].gle 7`, `[Ll]angage flou` |
| R8 | `[Cc]hamp obligatoire manquant`, `[Cc]hamp.*vide` |

**Classe `AlphaDecisionBuilder`** :

```python
AlphaDecisionBuilder(
    signal_data: dict,      # Donnees brutes du signal
    validation: dict,       # Resultat de SignalAlpha.validate()
    clarity_score: float,   # Score de clarte (0-100)
    kpi_blocked: bool,      # KPI bloque (taux > 5%)
)
```

**Methodes** :

| Methode | Signature | Description |
|---|---|---|
| `build()` | `-> dict` | Produit le dict AlphaDecision conforme au schema |
| `_generate_decision_id()` | `-> str` | `"AD-{signal_id}-{timestamp}"` |
| `_determine_status()` | `-> str` | REJECTED si `valid=False`, sinon status de la validation |
| `_compute_confidence_level()` | `-> str` | `clarity >= 80 -> HIGH`, `>= 50 -> MEDIUM`, `< 50 -> LOW` |
| `_parse_edge_net()` | `-> float` | Parse edge_net en float (0.0 si invalide) |
| `_build_constraints()` | `-> dict` | Construit `{max_size, urgency, expiry}` |
| `_extract_rules_failed()` | `-> list[int]` | Extrait les regles echouees par regex + kpi_blocked -> R6 |
| `_compute_rules_passed()` | `-> list[int]` | Complement `{1..10} - rules_failed` |
| `_generate_audit_ref()` | `-> str` | `"[{timestamp}]-{signal_id}"` |
| `_parse_float(field, default)` | `-> float` | Parse un champ en float avec fallback |

**Derivation de l'urgence** :

| Condition | Urgence |
|---|---|
| `time_to_resolution <= 6h` | `CRITICAL` |
| `time_to_resolution <= 24h` | `HIGH` |
| `time_to_resolution <= 48h` | `MEDIUM` |
| `time_to_resolution > 48h` | `LOW` |

**Fonction `validate_against_schema`** :

```python
validate_against_schema(decision: dict) -> dict
```

Retourne `{"valid": bool, "errors": list[str]}`. Validation structurelle pure sans dependance externe (`jsonschema` non requis).

**Verifications effectuees** :
- 9 champs requis presents
- `status` dans `{REJECTED, SURVEILLANCE, APPROVED}`
- `confidence_level` dans `{LOW, MEDIUM, HIGH}`
- `edge_net` numerique (int ou float)
- 3 champs contraintes presents (`max_size`, `urgency`, `expiry`)
- `urgency` dans `{LOW, MEDIUM, HIGH, CRITICAL}`
- `rules_passed` et `rules_failed` sont des listes
- `decision_id` commence par `"AD-"`

### Exemples AlphaDecision

**APPROVED** (`examples/approved.json`) :
```json
{
  "decision_id": "AD-SIG-001-20260208120000",
  "market": "ETH-PERP",
  "status": "APPROVED",
  "confidence_level": "HIGH",
  "edge_net": 2.5,
  "constraints": {"max_size": 500000, "urgency": "HIGH", "expiry": "2026-02-09T00:00:00"},
  "rules_passed": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  "rules_failed": []
}
```

**REJECTED** (`examples/rejected.json`) :
```json
{
  "decision_id": "AD-SIG-002-20260208130000",
  "market": "BTC-PERP",
  "status": "REJECTED",
  "confidence_level": "HIGH",
  "edge_net": 0.1,
  "constraints": {"max_size": 1000000, "urgency": "CRITICAL", "expiry": "2026-02-08T17:00:00"},
  "rules_passed": [1, 2, 3, 5, 6, 7, 8, 9, 10],
  "rules_failed": [4]
}
```

**SURVEILLANCE** (`examples/surveillance.json`) :
```json
{
  "decision_id": "AD-SIG-003-20260208140000",
  "market": "SOL-PERP",
  "status": "SURVEILLANCE",
  "confidence_level": "MEDIUM",
  "edge_net": 1.2,
  "constraints": {"max_size": 200000, "urgency": "MEDIUM", "expiry": "2026-02-10T02:00:00"},
  "rules_passed": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  "rules_failed": []
}
```

### Integration dans `manager.py`

Dans `submit_signal()`, apres la validation du signal et le log d'audit, le builder est appele automatiquement :

```python
alpha_decision = AlphaDecisionBuilder(
    signal_data=signal_data,
    validation=validation,
    clarity_score=clarity_score,
    kpi_blocked=self.kpi.is_approval_blocked(),
).build()
```

La cle `"alpha_decision"` est ajoutee au dict retourne par `submit_signal()` (ajout additif, non cassant). Un log d'audit `"alpha_decision_generated"` est enregistre.

### Tests Alpha Decision (section 4b de `test_alpha.py`)

23 tests unitaires couvrant :
- Format du `decision_id` (`AD-{signal_id}-{timestamp}`)
- Mapping des statuts (valid=True -> status du signal, valid=False -> REJECTED)
- Niveaux de confiance (clarity 90 -> HIGH, 60 -> MEDIUM, 30 -> LOW)
- Extraction des regles echouees par regex (R4, R7)
- KPI bloque -> R6 dans rules_failed
- Derivation de l'urgence (CRITICAL/HIGH/MEDIUM/LOW a 4h/12h/36h/60h)
- Validation schema (champs requis, statut invalide, confidence invalide, edge non numerique, urgence invalide, decision_id invalide)

5 tests d'integration dans la section 9 :
- `alpha_decision` present dans le retour de `submit_signal()`
- Status APPROVED confirme
- `decision_id` commence par `AD-SIG-001-`
- `schema_version` = `"1.0.0"`
- `rules_failed` vide pour un signal valide

---

## 25. MODULE `alpha_queue.py`

**Role** : File d'attente persistee SQLite pour la livraison fiable des AlphaDecision aux equipes externes. Le payload JSON est **immutable** une fois enqueue.

### Classe `AlphaDecisionQueue`

**Constructeur** :
```python
AlphaDecisionQueue(db_path: str | None = None)
```
- Cree le repertoire `data/` si absent
- Initialise la base SQLite `data/alpha_queue.db`
- Cree la table `alpha_decisions` si elle n'existe pas

**Table `alpha_decisions`** :

| Colonne | Type | Description |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY` | Identifiant auto-incremente |
| `decision_id` | `TEXT UNIQUE NOT NULL` | ID de la decision Alpha |
| `payload` | `TEXT NOT NULL` | JSON serialise (immutable) |
| `status` | `TEXT NOT NULL` | `PENDING`, `DELIVERED`, ou `FAILED` |
| `created_at` | `TEXT NOT NULL` | Date d'insertion (ISO 8601 UTC) |
| `delivered_at` | `TEXT` | Date de livraison (ISO 8601 UTC) |
| `retry_count` | `INTEGER` | Nombre de tentatives echouees |
| `max_retries` | `INTEGER` | Maximum de tentatives (defaut: 3) |

**Methodes** :

| Methode | Signature | Description |
|---|---|---|
| `enqueue(decision)` | `(dict) -> str` | Insere une AlphaDecision (JSON immutable). Retourne le decision_id. |
| `fetch_pending(limit)` | `(int) -> list[dict]` | Recupere les decisions en attente (FIFO). |
| `mark_delivered(decision_id)` | `(str) -> bool` | Marque comme livree (NE modifie PAS le payload). |
| `mark_failed(decision_id)` | `(str) -> bool` | Marque comme echouee, incremente retry_count. |
| `retry_failed()` | `-> int` | Remet en PENDING les FAILED si retry_count < max_retries. |
| `count_pending()` | `-> int` | Nombre de decisions en attente. |
| `count_all()` | `-> dict` | Compteurs par statut. |

**Integration dans `manager.py`** : Apres la generation de l'AlphaDecision dans `submit_signal()`, la decision est enqueue de maniere non bloquante (try/except). La queue ne bloque **jamais** le flux principal.

---

## 26. LES 7 OPTIMISATIONS

Les optimisations suivantes ont ete implementees sans modifier l'ADN du systeme (regles d'or, seuils de decision, comportement de rejet). Elles renforcent la fiabilite, la performance et la tracabilite.

### Optimisation 1 : UTC Strict

**Fichiers modifies** : config.py, agent.py, audit.py, interview.py, kpi.py, signal_alpha.py, stress_test.py, alpha_decision.py

Toutes les timestamps du systeme utilisent desormais `utc_now()` (definie dans `config.py`) au lieu de `datetime.now()`. Cela garantit la coherence horaire entre tous les modules, quel que soit le fuseau du serveur. **16 occurrences remplacees dans 8 fichiers.**

### Optimisation 2 : Signal Validation Fail-Fast

**Fichier modifie** : signal_alpha.py

La methode `validate()` s'arrete desormais des la premiere erreur detectee. Apres chaque appel `_check_*()`, si `self.validation_errors` est non vide, la validation retourne immediatement un rejet. L'ordre des 8 etapes est preserve. Cela evite du travail inutile et rend les messages d'erreur plus precis.

### Optimisation 3 : KPI Fenetre N>=20

**Fichiers modifies** : config.py, kpi.py, test_alpha.py, stress_test.py

Le seuil minimum de signaux avant activation du blocage KPI passe de 5 a **20** (`MIN_SIGNALS_FOR_BLOCKING = 20`). Le seuil de 5% (`MAX_APPROVAL_PCT`) reste inchange. Cela evite les faux positifs sur un echantillon trop petit.

### Optimisation 4 : Audit Hash Chain SHA-256

**Fichiers modifies** : config.py, audit.py

Chaque entree du journal d'audit est desormais chainee par **SHA-256**. Le hash de chaque entree depend du hash precedent, formant une chaine cryptographique. La methode `verify_integrity()` permet de verifier l'integrite complete du journal. Toute alteration est detectee et leve `AuditViolation`.

### Optimisation 5 : AgentRegistry Lazy Loading + Cache LRU

**Fichiers modifies** : config.py, agent.py, manager.py

L'`AgentRegistry` ne charge plus tous les agents en memoire au demarrage. Un index leger est maintenu, et les objets `Agent` sont charges a la demande avec un **cache LRU** (max 50, `AGENT_CACHE_MAX_SIZE`). Un callback d'audit est pose par `manager.py` pour tracer les acces au registre.

### Optimisation 6 : Queue SQLite

**Fichiers crees** : alpha_queue.py
**Fichiers modifies** : config.py, manager.py

Une file d'attente persistee SQLite garantit la livraison des AlphaDecision aux equipes externes. Le payload JSON est immutable. La queue est transparente (try/except) et ne bloque jamais le flux principal.

### Optimisation 7 : Property-Based Testing

**Fichiers crees** : test_property.py
**Fichiers modifies** : requirements.txt

7 tests generatifs (hypothesis) verifient les invariants structurels du systeme : signaux valides/invalides, mots interdits, AlphaDecision conforme, KPI coherent, chaine de hash integre. Dependance : `hypothesis>=6.0.0`.

---

## 27. REFERENCE IA CONDENSEE (REFERENCE_IA.md)

### Objectif

Le fichier `REFERENCE_IA.md` est une version **condensee** de cette documentation, optimisee pour etre transmise a d'autres IA. Il contient la totalite des informations techniques necessaires pour comprendre, analyser et travailler avec le systeme Manager Alpha sans acceder au code source.

### Contenu

| Section | Description |
|---|---|
| Loi fondatrice + 10 Regles d'Or | Regles avec consequences directes |
| Architecture | 16 modules + 1 package avec dependances |
| Seuils et constantes | Toutes les valeurs de config.py (incluant les 7 optimisations) |
| Mots interdits | 33 termes (FR + EN + LLM) listes |
| Classes et methodes | Signatures, parametres, retours, comportements |
| 7 questions d'entretien | Keywords requis/interdits, pieges, max phrases |
| Pipeline de validation | 8 etapes fail-fast avec mots-cles de detection |
| Alpha Interface | Schema JSON, builder, derivations, regex |
| Queue SQLite | File d'attente persistee pour AlphaDecision |
| Flux metier | Signal, recrutement humain, recrutement LLM, blocage KPI |
| Securite | 7 verrouillages documentes (incluant hash chain SHA-256) |
| Tests | 170 unitaires + 59 stress + 7 property-based |
| CLI | 13 options, modes STANDBY/ACTIVE |

### Differences avec DOCUMENTATION.md

| Critere | DOCUMENTATION.md | REFERENCE_IA.md |
|---|---|---|
| Public cible | Humains + IA | IA uniquement |
| Format | Explicatif, exemples CLI, guides | Tableaux, signatures, listes structurees |
| Exemples d'utilisation CLI | Oui (option par option) | Non |
| Exemples JSON complets | Oui (3 fichiers) | Schemas annotes |
| Descriptions textuelles | Oui | Non (format telegraphique) |
| Couverture technique | 100% | 100% |

### Usage recommande

Pour transmettre le contexte complet du projet a une autre IA :
1. Fournir `REFERENCE_IA.md` comme contexte initial
2. L'IA disposera de toutes les regles, classes, methodes, seuils et flux
3. Aucun acces au code source n'est necessaire pour comprendre le systeme

---

*Documentation generee automatiquement a partir du code source du projet Manager IA Alpha.*
*170 tests unitaires + 59 stress-test + 7 property-based = TOUS PASS.*
