# MANAGER IA ALPHA — REFERENCE TECHNIQUE CONDENSEE

> Contexte : Systeme de gestion d'equipe de trading algorithmique.
> Langage : Python 3.10+ | Aucune dependance externe en mode STANDBY.
> Tests : 170 unitaires + 59 stress-test = TOUS PASS.
> Version : 1.1 | Alpha Interface : v1.0.0

---

## LOI FONDATRICE

"Le role de l'equipe Alpha est d'etre fiable et previsible, en prenant des decisions justifiees par des faits mesurables, et jamais par des intuitions."

Alpha est une **machine a dire NON**. Moins de 5% des marches produisent un signal approuve.

---

## LES 10 REGLES D'OR (NON NEGOCIABLES)

| # | Regle | Consequence |
|---|---|---|
| 1 | Alpha ne trade jamais | Alpha analyse, structure, autorise. L'execution = autres equipes. |
| 2 | Aucun chiffre ne domine les autres | Si une metrique > 60% des mentions -> REJET. |
| 3 | Marche tradable != signal Alpha | Tradable = autorisation d'analyse. Signal = autorisation de trade. |
| 4 | L'edge brut ne suffit jamais | Seul l'edge net (apres couts, spread, marge) compte. Min 0.5%. |
| 5 | Le temps est un risque | Resolution > 72h -> REJET. Edge > 5% + temps > 48h -> SUSPECT. |
| 6 | Machine a dire NON | Si taux approbation > 5% -> blocage automatique. |
| 7 | Aucun langage flou | 33 mots interdits (FR+EN+LLM). Detection automatique. |
| 8 | Tout signal doit etre ecrit | Champ manquant ou vide -> rejet immediat. |
| 9 | Rater > mauvais trade | Autoriser un mauvais trade est une faute grave. |
| 10 | Discipline > intelligence | Agent brillant mais indiscipline -> rejet. |

---

## ARCHITECTURE — 14 MODULES + 1 PACKAGE

```
manager-alpha/
  config.py              # Constantes, seuils, regles (reference absolue)
  agent.py               # Classe Agent + AgentRegistry (persistance JSON)
  audit.py               # AuditSystem + @audit_required (autorite superieure)
  signal_alpha.py        # SignalAlpha : validation stricte 8 etapes
  interview.py           # InterviewEvaluator + InterviewSession (7 questions)
  kpi.py                 # KPITracker : blocage auto si >5% approbation
  llm_evaluator.py       # LLMEvaluator + AnthropicAgent + SimulatedLLMAgent
  manager.py             # ManagerAlpha : orchestrateur central (import tous)
  simulated_profiles.py  # 4 personas x 5 roles = 20 profils
  failure_corpus.py      # 30 scenarios de test (signaux + entretiens)
  stress_test.py         # 59 verifications automatisees
  test_alpha.py          # 170 tests unitaires
  main.py                # CLI interactive (13 options)
  alpha_interface/       # Couche d'interoperabilite AlphaDecision
    __init__.py           # Exports : AlphaDecisionBuilder, validate_against_schema
    alpha_decision.py     # Builder + validation structurelle
    decision_schema.json  # JSON Schema v2020-12
    rules_contract.md     # Contrat immutable versionne
    examples/             # 3 fichiers JSON (approved, rejected, surveillance)
```

**Dependances** : `manager.py` importe `agent`, `audit`, `interview`, `kpi`, `llm_evaluator`, `signal_alpha`, `alpha_interface`. Tous les modules importent `config.py`.

---

## SEUILS ET CONSTANTES (config.py)

| Constante | Valeur | Usage |
|---|---|---|
| `MAX_WARNINGS` | 3 | 3 avertissements = exclusion automatique irreversible |
| `MAX_APPROVAL_PCT` | 5.0% | Seuil de blocage automatique (min 5 signaux) |
| `INTERVIEW_PASS_SCORE_HUMAN` | 80% | Score minimum entretien humain |
| `INTERVIEW_PASS_SCORE_LLM` | 90% | Score minimum entretien LLM |
| `MIN_EDGE_NET` | 0.5% | Edge net minimum accepte |
| `MAX_TIME_TO_RESOLUTION_HOURS` | 72h | Temps max avant resolution |
| `LATE_EDGE_SUSPICION_HOURS` | 48h | Edge >5% + temps >48h = SUSPECT |
| `METRIC_DOMINANCE_THRESHOLD` | 0.60 | >60% mentions = dominance -> REJET |
| `LLM_API_MODE` | "STANDBY" | Aucun appel API reel en STANDBY |
| `ALPHA_INTERFACE_VERSION` | "1.0.0" | Version du format AlphaDecision |
| `ALPHA_ROLES` | 5 | DataEngineer, AlphaResearch, StrategySelector, Portfolio, Validation |
| `SIGNAL_TYPES` | 3 | ARBITRAGE, PROBA, MOMENTUM |
| `SIGNAL_REQUIRED_FIELDS` | 10 | signal_id, market, type, edge_net, volume, spread, time_to_resolution, risks, status, comment |
| `EQUIVALENT_METRICS` | 5 | edge_net, volume, spread, time_to_resolution, risks |

### Mots interdits

- **FR (12)** : je pense, feeling, probablement, je crois, peut-etre, il me semble, j'ai l'impression, intuition, instinct, ca devrait, normalement, a mon avis
- **EN (12)** : i think, i believe, feeling, probably, maybe, it seems, likely, gut feeling, intuition, instinct, should be, in my opinion
- **LLM extra (9)** : it appears, arguably, presumably, one could say, it's possible, might be, could potentially, tends to, generally speaking
- **FORBIDDEN_WORDS_ALL** = FR + EN (24) | **FORBIDDEN_WORDS_LLM** = ALL + extra (33)

---

## CLASSES ET METHODES — REFERENCE COMPLETE

### Agent (agent.py)

```python
class Agent:
    __init__(name: str, role: str)  # id=UUID[:8], status="candidate", warnings=0
    activate() -> bool              # candidate->active si interview_passed=True
    add_warning(reason: str) -> str # "AVERTISSEMENT_N/3" ou "EXCLU" si >=3
    log_decision(decision: dict)    # Horodate + append a decisions_log
    is_active/is_excluded/is_candidate() -> bool
    to_dict() -> dict               # Serialisation complete
    from_dict(data) -> Agent        # Classmethod deserialisaation

class AgentRegistry:
    __init__()                      # Charge data/agents.json
    add(agent) -> str               # Retourne agent.id, sauvegarde JSON
    get(agent_id) -> Agent|None
    remove(agent_id) -> bool
    list_all/list_active/list_candidates/list_excluded() -> list[Agent]
    list_by_status(status)/list_by_role(role) -> list[Agent]
```

**Statuts** : `"candidate"` -> `"active"` -> `"excluded"` (irreversible)

### AuditSystem (audit.py)

```python
class AuditViolation(Exception): pass  # Bloque les actions non autorisees

class AuditSystem:
    log(action, actor, details, result)              # Append-only dans logs/audit.log
    authorize(action, actor, context) -> bool         # AVANT toute action. AuditViolation si bypass interdit.
    authorize_signal_approval(kpi_data) -> bool       # AuditViolation si approbation >5%
    check_language(text, is_llm=False) -> dict        # {"clean": bool, "violations": list}
    check_rule_compliance(decision) -> dict           # {"compliant": bool, "violations": list}
    audit_decision(agent_id, decision) -> dict        # Score 0-100 (regles -30, justif -10/-20, langage -15)
    issue_warning(agent, reason) -> dict              # Delegue a agent.add_warning()
    review_agent_history(agent) -> dict               # Si echec >30% -> recommandation EXCLUSION
    detect_deviation(action, context) -> dict|None    # force_trade, minimize_risk, bypass_threshold
    read_log(last_n=50) -> list[str]                  # Lecture seule
    # PAS DE delete_log/edit_log/clear_log/modify_log

def audit_required(action_name: str)  # Decorateur: authorize() + detect_deviation() AVANT execution
```

**Methodes decorees dans manager.py** : start_interview, evaluate_llm_agent, evaluate_llm_agent_live, evaluate_llm_agent_simulated, submit_signal, audit_agent, review_all_agents, warn_agent

### SignalAlpha (signal_alpha.py)

```python
class SignalAlpha:
    __init__(data: dict)
    validate() -> dict  # {"valid": bool, "errors": list, "status": str, "comment": str}
```

**Pipeline de validation** (8 etapes sequentielles) :
1. `_check_required_fields()` — R8 : 10 champs obligatoires non vides
2. `_check_signal_type()` — ARBITRAGE/PROBA/MOMENTUM
3. `_check_signal_status()` — APPROVED/SURVEILLANCE/REJECTED
4. `_check_edge_net()` — R4 : numerique et >= 0.5%
5. `_check_time_to_resolution()` — R5 : <= 72h, edge>5% + temps>48h = SUSPECT
6. `_check_language()` — R7 : scan 24 mots interdits dans comment+risks
7. `_check_single_metric_dominance()` — R2 : ratio mentions >60% = REJET, 1 seule metrique mentionnee sur 3+ fournies = REJET
8. `_check_risks_field()` — risks >= 10 caracteres

**Mots-cles de metriques** (pour detection dominance R2) :
- edge: edge, rendement, profit, gain, yield, return
- volume: volume, liquidite, liquidity, depth
- spread: spread, ecart, bid-ask
- time: temps, time, resolution, expiry, deadline, delai
- risks: risque, risk, danger, exposition, exposure, drawdown

### InterviewEvaluator (interview.py)

```python
class InterviewEvaluator:
    __init__(is_llm: bool = False)  # LLM: 33 mots, seuil 90%, penalite 10%
    evaluate_response(question, response) -> dict  # Score 0-100
    get_overall_result() -> dict                   # Score moyen, toutes questions
```

**Scoring (100 pts max)** :
- Mots-cles requis : `(found/required) * 45` pts
- Phrases : 25 pts si `<= max_sentences`, 0 sinon
- Concepts : `(concepts_found/expected) * 30` pts (matching par racine min 4 chars)
- Penalite LLM : `score * 0.90` puis -5/hedging pattern detecte
- **Eliminatoire** : 1 mot interdit global OU 1 mot interdit de la question -> score=0

**7 questions d'entretien** :

| ID | Regle | Piege | Keywords requis | Keywords interdits | Max phrases |
|---|---|---|---|---|---|
| Q1 | R3 | Non | analyse, autorisation, signal, trade | meme chose, identique, pareil | 4 |
| Q2 | R4 | Non | cout, spread, net, risque | accepter, bon trade, profitable | 4 |
| Q3 | R5 | Non | temps, resolution, tardif | — | 4 |
| Q4 | R9 | Non | mauvais trade, autoriser | rater, opportunite manquee | 3 |
| Q5 | R10 | OUI | non, rejet, discipline | oui, garder, talent, exception | 3 |
| Q6 | R2 | OUI | non, analyse, risque, temps | oui, approuver, immediatement | 4 |
| Q7 | R7 | OUI | rejet, interdit, mesurable, fait | exploiter, suivre, valider | 3 |

```python
class InterviewSession:
    __init__(candidate_name, role, is_llm=False)
    get_current_question() -> dict|None
    submit_answer(answer) -> dict  # LLM: 1 echec = fin immediate
    get_final_result() -> dict
    is_active() -> bool
    questions_remaining() -> int
```

### KPITracker (kpi.py)

```python
class KPITracker:
    record_market_analysis(rejected: bool, reason="")
    record_signal(status, clarity_score=0.0, rejection_reasons=None)
    record_verbal_violation(agent_id)
    # Proprietes: markets_rejected_pct, signals_approved_pct, signals_rejected_pct, avg_signal_clarity, top_rejection_reasons, total_verbal_violations
    _check_approval_threshold()     # Si >5% ET >=5 signaux -> approval_blocked=True
    is_approval_blocked() -> bool
    manual_unblock(reviewer, reason) -> dict  # Requiert justification
    report() -> dict / format_report() -> str / get_kpi_data() -> dict
```

### LLMEvaluator (llm_evaluator.py)

```python
class AnthropicAgent:  # BLOQUE en STANDBY
    __init__(api_key, role, model="claude-sonnet-4-5-20250929", persona="disciplined")
    ask(question, max_sentences=4) -> str  # API Claude avec historique
    reset()

class SimulatedLLMAgent:  # Fonctionne toujours (pas d'API)
    __init__(role, persona="disciplined")
    ask(question, max_sentences=4) -> str  # Reponses pre-calibrees
    _identify_question(question) -> str    # Pattern matching Q1-Q7
    get_profile_summary() -> dict

class LLMEvaluator:
    __init__(api_provider=None, api_key=None)
    evaluate_local(question, response) -> dict    # Regles + extra_llm_checks
    _extra_llm_checks(response) -> dict           # Hedging, verbosite >150 mots, evasif, non-reponse
    run_live_interview(api_key, role, ...) -> dict # BLOQUE en STANDBY
    run_simulated_interview(role, persona, ...) -> dict  # Toujours disponible
    evaluate_via_api(question, llm_callable) -> dict
    run_full_evaluation(responses: dict) -> dict   # Tolerance zero: 1 echec = rejet
```

**Extra LLM checks** (_extra_llm_checks) :
- Hedging conditionnel : `while...it's true...however`
- Expressions evasives : `on balance`, `more or less`, `to some extent`
- Hedging academique : `it could be argued`, `one might say`
- Minimisation : `not entirely`, `somewhat`, `rather`
- Verbosite : > 150 mots
- Structure evasive : `however` + `but` sans `therefore`/`thus`
- Non-reponse : `that's a great question`, `let me think`

### ManagerAlpha (manager.py) — Orchestrateur central

```python
class ManagerAlpha:
    __init__()  # Initialise AuditSystem, AgentRegistry, KPITracker, LLMEvaluator

    # RECRUTEMENT
    @audit_required("recruit_agent")
    start_interview(name, role, is_llm=False, context=None) -> dict
    answer_interview(agent_id, answer) -> dict  # Pas de decorateur (session en cours)

    @audit_required("recruit_agent")
    evaluate_llm_agent(name, role, responses, context=None) -> dict
    evaluate_llm_agent_live(name, role, api_key, model, persona, callback, context) -> dict  # STANDBY
    evaluate_llm_agent_simulated(name, role, persona, callback, context) -> dict

    # SIGNAL
    @audit_required("submit_signal")
    submit_signal(agent_id, signal_data, context=None) -> dict
    # Retourne: {validation, signal_display, clarity_score, kpi_blocked, alpha_decision}
    _calculate_clarity(signal_data) -> float  # 10 pts par champ present, max 100

    # AUDIT
    @audit_required("audit_agent")
    audit_agent(agent_id, context=None) -> dict  # echec>30% -> warning auto
    @audit_required("review_all_agents")
    review_all_agents(context=None) -> list[dict]

    # UTILITAIRES
    get_identity() -> str / get_rules() -> dict
    get_kpi_report() -> str / get_kpi_data() -> dict
    list_agents(status=None) -> list[dict]
    enable_bypass() -> str / disable_bypass() -> str  # Bypass != desactiver audit
    @audit_required("issue_warning")
    warn_agent(agent_id, reason, context=None) -> dict
    view_audit_log(last_n=50) -> list[str]
    manual_unblock_approvals(reviewer, reason) -> dict
```

### Simulated Profiles (simulated_profiles.py)

**4 personas x 5 roles = 20 profils** :

| Persona | Taux passage | Risque | Tics verbaux |
|---|---|---|---|
| disciplined | 95% | LOW | Aucun |
| mediocre | 20% | MEDIUM | "en general", "dans la plupart des cas", "normalement" |
| overconfident | 10% | HIGH | "evidemment", "clairement", "il est certain que" |
| naive | 0% | CRITICAL | "je pense", "feeling", "probablement", "intuition" |

Fonction `get_responses(role, persona) -> dict[str, str]` retourne les reponses Q1-Q7.

### Failure Corpus (failure_corpus.py)

| Categorie | Scenarios | Description |
|---|---|---|
| FAILED_SIGNALS | 15 | R2 dominance(x2), R4 edge(x2), R5 temps(x2), R7 langage(x4), R8 champs(x3), type invalide, risks court |
| FAILED_INTERVIEWS | 6 | Naif complet, mot interdit Q2, pieges Q5/Q6/Q7, hedging LLM |
| BORDERLINE_SIGNALS | 7 | Edge=0.5%(valid), 0.4%(invalid), time=48h(valid), 49h+edge6%(invalid), equilibre(valid), 72h(valid), 73h(invalid) |
| BORDERLINE_INTERVIEWS | 2 | Reponses tres courtes, concepts partiels |
| **TOTAL** | **30** | |

---

## ALPHA INTERFACE — FORMAT DE SORTIE UNIQUE

### Schema AlphaDecision (decision_schema.json)

```json
{
  "decision_id": "AD-{signal_id}-{YYYYMMDDHHmmss}",  // string, prefix "AD-"
  "market": "ETH-PERP",                               // string
  "status": "APPROVED|SURVEILLANCE|REJECTED",          // enum strict
  "confidence_level": "LOW|MEDIUM|HIGH",               // enum strict
  "edge_net": 2.5,                                     // number
  "constraints": {
    "max_size": 500000,                                // number (= volume signal)
    "urgency": "LOW|MEDIUM|HIGH|CRITICAL",             // enum strict
    "expiry": "2026-02-09T00:00:00"                    // ISO 8601
  },
  "rules_passed": [1,2,3,4,5,6,7,8,9,10],             // array[int]
  "rules_failed": [],                                  // array[int]
  "audit_ref": "[{timestamp}]-{signal_id}",            // string
  "schema_version": "1.0.0",                           // string
  "generated_at": "2026-02-08T12:00:00"                // ISO 8601
}
```

`additionalProperties: false` sur racine et constraints.

### AlphaDecisionBuilder (alpha_decision.py)

```python
builder = AlphaDecisionBuilder(
    signal_data=signal_data,      # dict brut du signal (10 champs)
    validation=validation,        # retour de SignalAlpha.validate()
    clarity_score=clarity_score,  # float 0-100
    kpi_blocked=bool,             # KPITracker.is_approval_blocked()
)
decision = builder.build()  # -> dict conforme au schema
```

**Derivations** :

| Champ | Logique |
|---|---|
| status | `valid=False` -> REJECTED, sinon = validation.status |
| confidence_level | clarity >= 80 -> HIGH, >= 50 -> MEDIUM, < 50 -> LOW |
| urgency | ttr <= 6h -> CRITICAL, <= 24h -> HIGH, <= 48h -> MEDIUM, > 48h -> LOW |
| expiry | `now + time_to_resolution` heures |
| max_size | = signal_data.volume |
| rules_failed | Regex sur validation.errors + kpi_blocked -> R6 |
| rules_passed | `{1..10} - rules_failed` |

**Patterns regex de detection des regles echouees** :

| Regle | Patterns |
|---|---|
| R2 | `[Rr].gle 2`, `[Dd]ominance`, `aucun chiffre ne domine` |
| R4 | `edge_net.*inf.rieur`, `edge_net.*minimum`, `edge_net doit .tre num.rique` |
| R5 | `[Rr].gle 5`, `time_to_resolution.*d.passe`, `SUSPECT` |
| R7 | `[Rr].gle 7`, `[Ll]angage flou` |
| R8 | `[Cc]hamp obligatoire manquant`, `[Cc]hamp.*vide` |
| R6 | `kpi_blocked=True` (pas de regex, flag direct) |

```python
def validate_against_schema(decision: dict) -> dict:
    # Retourne {"valid": bool, "errors": list[str]}
    # Verifie : 9 champs requis, enums valides, edge_net numerique,
    # 3 contraintes presentes, urgence valide, listes, prefix "AD-"
```

### Integration dans submit_signal()

Apres validation + audit log, avant return :
```python
alpha_decision = AlphaDecisionBuilder(signal_data, validation, clarity_score, kpi_blocked).build()
# Log audit "alpha_decision_generated"
# Ajoute "alpha_decision": alpha_decision au dict retourne
```

---

## FLUX METIER

### submit_signal() — Flux complet

```
1. @audit_required("submit_signal") -> authorize() + detect_deviation()
2. Agent existe et is_active() ?
3. SignalAlpha(signal_data).validate() -> 8 etapes
4. AuditSystem.check_language(comment) -> violations verbales
5. Si APPROVED + valid : authorize_signal_approval(kpi_data) -> blocage si >5%
6. Calcul clarity_score (10pts par champ present)
7. KPITracker.record_signal() + record_market_analysis()
8. Agent.log_decision() + AuditSystem.log()
9. AlphaDecisionBuilder.build() -> AlphaDecision
10. AuditSystem.log("alpha_decision_generated")
11. Return {validation, signal_display, clarity_score, kpi_blocked, alpha_decision}
```

### Recrutement humain

```
1. start_interview(name, role) -> Agent(candidate) + InterviewSession
2. Pour chaque Q1-Q7 : answer_interview(agent_id, answer)
   - Mot interdit global -> ELIMINATION score=0
   - Mot interdit question -> ELIMINATION score=0
   - Scoring : keywords(45) + phrases(25) + concepts(30)
   - Score < 80% -> echec (mais continue pour humains)
3. Fin : score_moyen >= 80% ET toutes passees -> agent.activate()
```

### Recrutement LLM

```
1. evaluate_llm_agent_simulated(name, role, persona)
2. SimulatedLLMAgent.ask() pour chaque Q1-Q7
3. evaluate_local() : regles + _extra_llm_checks()
4. Score * 0.90 (penalite LLM) + hedging -5pts/pattern
5. TOLERANCE ZERO : 1 echec = REJET IMMEDIAT (pas de question suivante)
6. Score moyen >= 90% -> agent.activate()
```

### Blocage KPI

```
Chaque signal -> KPITracker.record_signal()
  -> _check_approval_threshold()
  -> Si signals_approved_pct > 5% ET total >= 5 : approval_blocked = True
  -> Tout signal APPROVED suivant est REJETE
  -> Deblocage : manual_unblock(reviewer, reason)
```

### Avertissements

```
Agent.add_warning(reason)
  -> warnings < 3 : "AVERTISSEMENT_N/3"
  -> warnings >= 3 : status="excluded", "EXCLU" (irreversible)
  -> Agent deja exclu : "AGENT_DEJA_EXCLU"
```

---

## SECURITE ET VERROUILLAGES

1. **Audit append-only** : `AuditSystem` n'a PAS de delete_log/edit_log/clear_log/modify_log
2. **@audit_required** : 8 methodes decorees, audit AVANT execution, non contournable
3. **Mode bypass** : consultation uniquement, ne desactive JAMAIS l'audit
   - Autorise : consultation, export, replay, simulation, list_agents, view_kpi, view_audit_log
   - Interdit : approve_signal, recruit_agent, modify_agent, exclude_agent, disable_audit
4. **Blocage KPI** : automatique si >5% (min 5 signaux), deblocage manuel obligatoire
5. **3 warnings = exclusion** : irreversible, horodate, agent ne peut plus soumettre
6. **Tolerance zero LLM** : 90% min, 33 mots interdits, -10% penalite, 1 echec = rejet, detection hedging/verbosite/evasion/non-reponse

---

## TESTS

### test_alpha.py — 170 tests (12 sections)

| Section | N | Cible |
|---|---|---|
| 1. IMPORTS | 1 | Tous les imports |
| 2. CONFIG | 10 | Regles, mots, roles, types, champs, seuils |
| 3. AGENT | 18 | Creation, activation, warnings (3=exclusion), serialisation |
| 4. SIGNAL | 13 | Champs, mots interdits, types, edge, temps, dominance, risques |
| 4b. ALPHA DECISION | 23 | Builder, status, confidence, rules, urgency, schema validation |
| 5. AUDIT | 23 | Langage, regles, bypass, decisions, append-only, verrouillages |
| 6. INTERVIEW | 12 | Reponses, elimination, pieges Q5/Q6/Q7, tolerance LLM |
| 7. KPI | 13 | Taux, blocage, deblocage, rapport, violations |
| 8. LLM EVALUATOR | 6 | Local, seuil 90%, hedging, API |
| 8b. STANDBY | 11 | Mode STANDBY, AnthropicAgent bloque, SimulatedLLMAgent OK |
| 9. MANAGER | 35 | Integration complete + alpha_decision dans submit_signal |
| 10. SECURITE | 5 | Absence methodes dangereuses, KPI blocage |

### stress_test.py — 59 verifications (8 sections)

| Section | N | Description |
|---|---|---|
| 1. Entretiens simules | 20 | 5 roles x 4 personas (disciplined passe, autres echouent) |
| 2. Signaux invalides | 15 | Tous rejetes |
| 3. Signaux borderline | 7 | Chacun a son resultat attendu |
| 4. Entretiens echoues | 6 | Tous rejetes |
| 5. Entretiens borderline | 2 | Observation |
| 6. Stress KPI | 5 | Recrutement, 3 approved + 2 rejected, blocage, signal bloque, deblocage |
| 7. Stress warnings | 1 | 3 warnings -> exclusion |
| 8. Integration | 3 | disciplined recrute, naive rejete, overconfident rejete |

---

## FICHIERS DE DONNEES

- `data/agents.json` — Registre persistant (chaque agent : id, name, role, status, warnings, interview_passed, score, mode, decisions_log, created_at, excluded_at, verbal_discipline_score)
- `data/questions.json` — Banque de 7 questions (miroir MANDATORY_QUESTIONS)
- `logs/audit.log` — Journal append-only : `[{timestamp}] ACTION={action} | ACTOR={actor} | DETAILS={details} | RESULT={result}`

---

## CLI (main.py)

```
python main.py                     # Mode normal
python main.py --bypass-permission # Mode consultation
```

13 options : (1) Recruter humain, (2) Evaluer LLM, (3) Soumettre signal, (4) Auditer agent, (5) KPIs, (6) Lister agents, (7) Revue complete, (8) Journal audit, (9) Regles d'Or, (10) Avertir agent, (11) Toggle bypass, (12) Debloquer approbations, (13) Stress-test, (0) Quitter.

Mode STANDBY pour option 2 : (1) Simule (2) Manuel. Mode ACTIVE ajoute : Live via API Anthropic.
