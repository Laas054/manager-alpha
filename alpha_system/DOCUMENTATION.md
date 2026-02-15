# TRADING BOT ALPHA — Documentation Officielle

## Version: 1.0
## Auteur: Annick
## Date: 2026-02-15

---

## 1. PRÉSENTATION

Trading Bot Alpha est un système de trading autonome pour les marchés de prédiction **Polymarket**.

Le bot analyse les marchés via une IA multi-modèles (Ollama Cloud), valide chaque décision à travers un pipeline de sécurité complet, puis exécute les trades en mode DRY (simulation) ou LIVE (réel).

**Objectif** : fiabilité maximale, protection du capital, stabilité long terme.

---

## 2. ARCHITECTURE

```
alpha_system/
├── main.py                          # Point d'entrée
├── orchestrator.py                  # Pipeline central
├── config.py                        # Configuration
│
├── ai/                              # Intelligence artificielle
│   ├── secure_ai_client.py          # Client IA sécurisé (retry, validation, fallback)
│   ├── confidence_manager.py        # Filtre confiance minimum
│   ├── profit_optimizer.py          # Calcul taille position
│   ├── ensemble_engine.py           # Ensemble 3 modèles
│   ├── agent_brain.py               # Wrapper agent IA
│   └── ollama_client.py             # Client Ollama bas niveau
│
├── market/                          # Lecture marchés
│   ├── polymarket_reader.py         # API Polymarket (Gamma)
│   └── adaptive_scanner.py          # Rate limit & backoff
│
├── execution/                       # Exécution trades
│   ├── execution_engine.py          # Moteur DRY/LIVE
│   ├── cost_calculator.py           # Frais + slippage
│   ├── polymarket_executor_dry.py   # Simulation réaliste
│   └── polymarket_executor_live.py  # CLOB Polymarket (py-clob-client)
│
├── risk/                            # Gestion risque
│   └── risk_engine_v2.py            # 8 validations avant trade
│
├── protection/                      # Sécurité
│   ├── kill_switch.py               # Arrêt si drawdown > 15%
│   ├── error_handler.py             # Capture exceptions (zero crash)
│   ├── live_safety_controller.py    # Arrêt après 5 pertes consécutives
│   └── institutional_guard.py       # Limite journalière (5% loss, 50 trades)
│
├── memory/                          # Persistance
│   └── database.py                  # SQLite (trades, state, audit, backup)
│
├── utils/                           # Utilitaires
│   └── logger.py                    # Logging structuré (fichier + console)
│
├── tests/                           # Tests
│   └── test_suite.py                # 10 tests unitaires
│
└── data/                            # Données
    ├── alpha_system.db              # Base SQLite
    ├── logs/                        # Fichiers log
    └── backups/                     # Backups automatiques DB
```

---

## 3. PIPELINE D'EXÉCUTION

Chaque cycle suit ce flux exact :

```
1. Health check (erreurs critiques)
2. Kill switch (drawdown > 15% → STOP)
3. Scan marchés Polymarket (API Gamma)
4. Tri par volume (top 3)
5. Évaluation IA (3 modèles en ensemble)
6. Validation confiance (>= 0.75)
7. Calcul coûts (frais + slippage + rentabilité)
8. Validation risque (8 checks)
9. Exécution trade (DRY ou LIVE)
10. Enregistrement SQLite
11. Logging complet
12. Sauvegarde état
```

---

## 4. MODÈLES IA

| Modèle | Provider | Utilisé par |
|--------|----------|-------------|
| `deepseek-v3.2` | Ollama Cloud | Agent 1 |
| `qwen3-next:80b` | Ollama Cloud | Agent 2 |
| `glm-5` | Ollama Cloud | Agent 3 |

**Endpoint** : `https://ollama.com/api/chat`
**Auth** : Bearer token (`OLLAMA_API_KEY`)
**Format réponse** : `data["message"]["content"]` (format Ollama, pas OpenAI)

**Sécurité IA** :
- Validation stricte JSON (trade, side, confidence)
- Retry automatique (2 tentatives)
- Fallback local si IA indisponible
- Benchmark latence et taux de succès

---

## 5. GESTION DU RISQUE (RiskEngineV2)

8 validations avant chaque trade :

| # | Check | Seuil |
|---|-------|-------|
| 1 | Capital positif | > 0 |
| 2 | Taille max | <= MAX_TRADE_SIZE |
| 3 | Risque par trade | <= 2% du capital |
| 4 | Drawdown global | <= 15% |
| 5 | Série de pertes | < 5 consécutives |
| 6 | Trades journaliers | < 50 |
| 7 | Perte journalière | < 5% du capital initial |
| 8 | Confiance minimum | >= 0.65 |

---

## 6. PROTECTIONS

| Protection | Déclencheur | Action |
|------------|-------------|--------|
| **Kill Switch** | Drawdown > 15% | Arrêt total trading |
| **Loss Streak** | 5 pertes consécutives | Pause trading |
| **Daily Guard** | Perte > 5% jour / 50 trades | Pause jusqu'à demain |
| **Error Handler** | Exception | Capture + continue |
| **Cost Check** | Trade non rentable après frais | Rejet |

---

## 7. BASE DE DONNÉES (SQLite)

Fichier : `data/alpha_system.db`

### Table `trades`
| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Auto-increment |
| timestamp | TEXT | ISO 8601 UTC |
| market | TEXT | Question du marché |
| side | TEXT | YES / NO |
| price | REAL | Prix d'entrée |
| size | REAL | Taille position |
| pnl | REAL | Profit/Perte |
| confidence | REAL | Confiance IA (0-1) |
| model | TEXT | Modèle IA utilisé |
| source | TEXT | "ai" ou "fallback" |
| status | TEXT | SIMULATED / LIVE |

### Table `system_state`
| Colonne | Type | Description |
|---------|------|-------------|
| capital | REAL | Capital actuel |
| starting_capital | REAL | Capital initial |
| total_pnl | REAL | PnL cumulé |
| total_trades | INTEGER | Nombre total de trades |
| wins | INTEGER | Trades gagnants |
| losses | INTEGER | Trades perdants |

### Table `audit_log`
| Colonne | Type | Description |
|---------|------|-------------|
| timestamp | TEXT | ISO 8601 UTC |
| action | TEXT | EXECUTED, RISK_BLOCKED, KILL_SWITCH, ERROR |
| detail | TEXT | Détails |

---

## 8. CONFIGURATION

Fichier : `config.py` + `.env`

```python
CONFIG = {
    "STARTING_CAPITAL": 1000,
    "CONFIDENCE_THRESHOLD": 0.75,
    "MAX_RISK_PER_TRADE": 0.02,       # 2%
    "MAX_DRAWDOWN_PCT": 0.15,          # 15%
    "MAX_TRADE_SIZE": env(MAX_TRADE_SIZE, 100),
    "SCAN_INTERVAL": 60,               # secondes
    "MODE": env(TRADING_MODE, "DRY"),
    "DB_PATH": "alpha_system/data/alpha_system.db",
}
```

### Variables d'environnement (.env)
| Variable | Description | Valeur actuelle |
|----------|-------------|-----------------|
| `TRADING_MODE` | DRY ou LIVE | DRY |
| `MAX_TRADE_SIZE` | Taille max par trade | 1 |
| `OLLAMA_API_KEY` | Clé API Ollama Cloud | Configurée |
| `POLYMARKET_PRIVATE_KEY` | Clé privée wallet | Non configurée |

---

## 9. API POLYMARKET

**Endpoint** : `https://gamma-api.polymarket.com/markets`
**Params** : `closed=false`, `active=true`, `limit=100`

**Points critiques** :
- `outcomePrices` est un **JSON string** (pas une liste Python)
- `clobTokenIds` est un **JSON string** (pas une liste Python)
- Nécessite `json.loads()` pour parser ces champs

---

## 10. MODES D'EXÉCUTION

### DRY RUN (par défaut)
- Aucune connexion wallet
- PnL simulé (winrate ajusté par confiance IA)
- Toutes les protections actives
- Logging et DB identiques au LIVE

### LIVE
- Requiert `POLYMARKET_PRIVATE_KEY` valide
- Requiert wallet avec USDC sur Polygon (chain_id=137)
- Utilise `py-clob-client` pour les ordres
- PnL réel calculé à la clôture
- `MAX_TRADE_SIZE=1` recommandé au début

---

## 11. CONDITIONS PASSAGE EN LIVE

| Critère | Seuil | Actuel |
|---------|-------|--------|
| Trades DRY minimum | 500 | En cours |
| Winrate IA | > 60% | En cours |
| Drawdown max observé | < 10% | OK |
| Crashs système | 0 | OK |
| Tests unitaires | 10/10 | OK |

---

## 12. COMMANDES

```bash
# Lancer le bot
python alpha_system/main.py

# Lancer les tests
python alpha_system/tests/test_suite.py

# Monitoring temps réel
python alpha_system/monitor.py
```

---

## 13. LOGGING

### Fichiers log
| Fichier | Contenu |
|---------|---------|
| `data/logs/alpha_system.log` | Tous les événements (DEBUG+) |
| `data/logs/errors.log` | Erreurs uniquement (ERROR+) |

### Format
```
2026-02-15 20:50:58 | INFO     | 100 markets fetched
2026-02-15 20:52:47 | INFO     | TRADE | Will X happen? | NO | size:1 | pnl:-0.1 | conf:0.999
2026-02-15 20:52:47 | WARNING  | RISK | Blocked: daily loss limit
```

---

## 14. BACKUP & RECOVERY

- **Backup auto** : toutes les 100 cycles (`data/backups/`)
- **State persistence** : sauvegarde SQLite après chaque trade
- **Crash recovery** : au redémarrage, l'état est restauré depuis la DB
- **Shutdown propre** : backup + save state sur Ctrl+C

---

## 15. DÉPENDANCES

```
requests          # HTTP client
python-dotenv     # Variables d'environnement
py-clob-client    # Polymarket LIVE (optionnel)
eth-account       # Wallet Ethereum (optionnel)
web3              # Blockchain (optionnel)
```

---

## 16. SÉCURITÉ

- Clés API dans `.env` (jamais en dur dans le code)
- `.env` ne doit PAS être commité (ajouter à `.gitignore`)
- Validation stricte de toutes les réponses IA
- Aucune exécution sans validation risque complète
- Kill switch hardware (drawdown)
- Zero crash garanti (ErrorHandler)

---

## 17. AUDIT CHECKLIST

Pour auditer le système, vérifier :

- [ ] `config.py` : seuils de risque corrects
- [ ] `risk_engine_v2.py` : 8 validations présentes
- [ ] `kill_switch.py` : drawdown max = 15%
- [ ] `secure_ai_client.py` : validation JSON stricte + fallback
- [ ] `database.py` : tables trades, state, audit existent
- [ ] `error_handler.py` : aucune exception non capturée
- [ ] `cost_calculator.py` : frais Polymarket corrects (2% taker)
- [ ] `.env` : TRADING_MODE=DRY avant tests
- [ ] `tests/test_suite.py` : 10/10 tests passent
- [ ] Logs : `data/logs/` contient les fichiers
- [ ] Backups : `data/backups/` contient les snapshots
- [ ] Pas de clé privée en clair dans le code source
