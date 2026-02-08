# CONTRAT DE REGLES ALPHA — READ ONLY

> **Version** : 1.0.0
> **Statut** : IMMUTABLE
> **Date de creation** : 2026-02-08

---

## PRINCIPES FONDAMENTAUX

- Alpha ne trade jamais.
- Alpha n'impose jamais une taille, seulement des contraintes.
- Alpha peut retirer une decision a tout moment.
- Toute execution hors contraintes est une faute grave.
- Les autres equipes n'ont aucun droit de modification.

---

## LES 10 REGLES D'OR

| Regle | Titre | Description |
|-------|-------|-------------|
| R1 | Alpha ne trade jamais | Alpha analyse, structure, autorise. L'execution appartient a d'autres equipes. |
| R2 | Aucun chiffre ne domine les autres | Prix, spread, volume, temps, edge, risque sont equivalents. Si un seul est critique -> REJET. |
| R3 | Un marche tradable n'est PAS un signal | Marche tradable = autorisation d'analyse. Signal Alpha = autorisation de trade. |
| R4 | L'edge brut ne suffit jamais | Seul l'edge net (apres couts, spread, marge securite) est considere. |
| R5 | Le temps est un risque | Plus la resolution est proche, plus le signal est fragile. Un edge eleve tardif est suspect. |
| R6 | Alpha est une machine a dire NON | Moins de 5% des marches peuvent produire un signal approuve. |
| R7 | Aucun langage flou n'est autorise | Mots interdits : "je pense", "feeling", "probablement", etc. |
| R8 | Tout signal doit etre ecrit | Un signal non formalisable par ecrit est automatiquement rejete. |
| R9 | Rater une opportunite est acceptable | Autoriser un mauvais trade est une faute grave. |
| R10 | La discipline prime sur l'intelligence | Un agent brillant mais indiscipline est rejete. |

---

## CORRESPONDANCE REGLES <-> VALIDATION

| Regle | Verification | Module | Methode |
|-------|-------------|--------|---------|
| R1 | action != execute_trade | audit.py | check_rule_compliance() |
| R2 | Aucune metrique > 60% des mentions | signal_alpha.py | _check_single_metric_dominance() |
| R3 | type != market_tradable_as_signal | audit.py | check_rule_compliance() |
| R4 | edge_net >= 0.5% | signal_alpha.py | _check_edge_net() |
| R5 | time_to_resolution <= 72h, edge+temps suspect | signal_alpha.py | _check_time_to_resolution() |
| R6 | signals_approved_pct <= 5% | kpi.py | _check_approval_threshold() |
| R7 | Aucun mot interdit dans commentaire/risques | signal_alpha.py | _check_language() |
| R8 | Tous les 10 champs obligatoires presents | signal_alpha.py | _check_required_fields() |
| R9 | Pas de forced_trade | audit.py | check_rule_compliance() |
| R10 | Discipline > Intelligence (entretien + warnings) | interview.py | evaluate_response() |

---

## STATUTS AUTORISES

Alpha ne renvoie QUE ces statuts :

| Statut | Signification |
|--------|--------------|
| REJECTED | Signal invalide. Aucune action autorisee. |
| SURVEILLANCE | Signal valide mais sous observation. Action conditionnelle. |
| APPROVED | Signal valide. Execution autorisee dans les contraintes. |

Aucune nuance intermediaire. Aucune interpretation cote consommateur.

---

## FORMAT DE SORTIE : AlphaDecision

Voir `decision_schema.json` pour le schema complet.

Champs obligatoires :
- `decision_id` : Identifiant unique (AD-{signal_id}-{timestamp})
- `market` : Marche concerne
- `status` : REJECTED | SURVEILLANCE | APPROVED
- `confidence_level` : LOW | MEDIUM | HIGH
- `edge_net` : Edge net en %
- `constraints` : {max_size, urgency, expiry}
- `rules_passed` : Regles passees [1-10]
- `rules_failed` : Regles echouees [1-10]
- `audit_ref` : Reference au journal d'audit

Aucune cle optionnelle non documentee.
Aucune logique metier hors Alpha.

---

## IMMUTABILITE

Ce document est versionne. Toute modification requiert :
1. Un nouveau numero de version
2. Une entree dans le journal d'audit
3. L'approbation du Manager IA Alpha

Aucune equipe externe ne peut modifier ce contrat.
