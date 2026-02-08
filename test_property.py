"""
PROPERTY-BASED TESTS — Manager IA Alpha
Tests génératifs avec hypothesis : vérifie les invariants structurels
sans dépendre de valeurs spécifiques.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hypothesis import given, settings, assume
from hypothesis import strategies as st

from config import (
    EQUIVALENT_METRICS,
    FORBIDDEN_WORDS_ALL,
    MAX_APPROVAL_PCT,
    MIN_EDGE_NET,
    MIN_SIGNALS_FOR_BLOCKING,
    SIGNAL_REQUIRED_FIELDS,
    SIGNAL_TYPES,
    SIGNAL_STATUSES,
)
from signal_alpha import SignalAlpha
from kpi import KPITracker
from alpha_interface.alpha_decision import AlphaDecisionBuilder, validate_against_schema
from audit import AuditSystem


# =========================================================================
# STRATÉGIES RÉUTILISABLES
# =========================================================================
def valid_signal_data():
    """Génère un signal valide conforme au protocole Alpha."""
    return st.fixed_dictionaries({
        "signal_id": st.text(min_size=1, max_size=20, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"),
        "market": st.text(min_size=1, max_size=20, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"),
        "type": st.sampled_from(SIGNAL_TYPES),
        "edge_net": st.floats(min_value=MIN_EDGE_NET, max_value=50.0).map(lambda x: str(round(x, 2))),
        "volume": st.integers(min_value=1000, max_value=10000000).map(str),
        "spread": st.floats(min_value=0.01, max_value=1.0).map(lambda x: str(round(x, 3))),
        "time_to_resolution": st.floats(min_value=1.0, max_value=48.0).map(lambda x: str(round(x, 1))),
        "risks": st.text(min_size=20, max_size=200, alphabet="abcdefghijklmnopqrstuvwxyz .,"),
        "status": st.sampled_from(SIGNAL_STATUSES),
        "comment": st.just(
            "Edge net confirme. Volume suffisant. Spread faible. Temps court. Risque controle."
        ),
    })


# =========================================================================
# TEST 1 : Signal valide -> toujours validé
# =========================================================================
@given(data=valid_signal_data())
@settings(max_examples=50)
def test_valid_signal_always_passes(data):
    """Tout signal conforme au protocole doit passer la validation."""
    signal = SignalAlpha(data)
    result = signal.validate()
    assert result["valid"], f"Signal valide rejeté : {result['errors']}"


# =========================================================================
# TEST 2 : Signal sans champs -> toujours rejeté
# =========================================================================
@given(data=st.dictionaries(
    keys=st.text(min_size=1, max_size=10),
    values=st.text(min_size=0, max_size=10),
    max_size=3,
))
@settings(max_examples=50)
def test_incomplete_signal_always_rejected(data):
    """Un signal avec des champs aléatoires (pas les 10 requis) est toujours rejeté."""
    # S'assurer qu'il manque au moins un champ obligatoire
    assume(not all(field in data for field in SIGNAL_REQUIRED_FIELDS))
    signal = SignalAlpha(data)
    result = signal.validate()
    assert not result["valid"], "Signal incomplet accepté à tort"


# =========================================================================
# TEST 3 : Signal edge <0.5% -> toujours rejeté
# =========================================================================
@given(edge=st.floats(min_value=0.0, max_value=MIN_EDGE_NET - 0.01))
@settings(max_examples=50)
def test_low_edge_always_rejected(edge):
    """Un edge_net inférieur au minimum est toujours rejeté."""
    assume(edge >= 0)
    data = {
        "signal_id": "PROP-001",
        "market": "TEST",
        "type": "ARBITRAGE",
        "edge_net": str(round(edge, 4)),
        "volume": "10000",
        "spread": "0.05",
        "time_to_resolution": "12",
        "risks": "Risque identifie et controle strictement pour ce test.",
        "status": "SURVEILLANCE",
        "comment": "Edge net faible. Volume present. Spread reduit. Temps court. Risque gere.",
    }
    signal = SignalAlpha(data)
    result = signal.validate()
    assert not result["valid"], f"Edge {edge}% accepté à tort"


# =========================================================================
# TEST 4 : Signal mot interdit -> toujours rejeté
# =========================================================================
@given(word=st.sampled_from(FORBIDDEN_WORDS_ALL))
@settings(max_examples=30)
def test_forbidden_word_always_rejected(word):
    """Tout mot interdit dans le commentaire doit provoquer un rejet."""
    data = {
        "signal_id": "PROP-002",
        "market": "TEST",
        "type": "PROBA",
        "edge_net": "3.0",
        "volume": "50000",
        "spread": "0.1",
        "time_to_resolution": "10",
        "risks": "Risque standard identifie clairement pour ce test.",
        "status": "APPROVED",
        "comment": f"Analyse complete. {word} que cela fonctionne.",
    }
    signal = SignalAlpha(data)
    result = signal.validate()
    assert not result["valid"], f"Mot interdit '{word}' non détecté"


# =========================================================================
# TEST 5 : AlphaDecision -> toujours conforme au schéma
# =========================================================================
@given(data=valid_signal_data())
@settings(max_examples=50)
def test_alpha_decision_always_conforms(data):
    """Toute AlphaDecision construite doit passer la validation de schéma."""
    signal = SignalAlpha(data)
    validation = signal.validate()
    clarity = 80.0

    decision = AlphaDecisionBuilder(
        signal_data=data,
        validation=validation,
        clarity_score=clarity,
        kpi_blocked=False,
    ).build()

    schema_check = validate_against_schema(decision)
    assert schema_check["valid"], f"Schema invalide : {schema_check['errors']}"
    assert decision["decision_id"].startswith("AD-"), "decision_id ne commence pas par AD-"
    assert decision["schema_version"] == "1.0.0", "Version schema incorrecte"


# =========================================================================
# TEST 6 : KPI <5% approval (>=20 signaux) -> jamais bloqué
# =========================================================================
@given(
    n_approved=st.integers(min_value=0, max_value=1),
    n_rejected=st.integers(min_value=19, max_value=100),
)
@settings(max_examples=50)
def test_kpi_below_threshold_never_blocked(n_approved, n_rejected):
    """Si le taux d'approbation est <=5% avec >=20 signaux, pas de blocage."""
    total = n_approved + n_rejected
    assume(total >= MIN_SIGNALS_FOR_BLOCKING)
    pct = (n_approved / total) * 100
    assume(pct <= MAX_APPROVAL_PCT)

    kpi = KPITracker()
    for _ in range(n_approved):
        kpi.record_signal("APPROVED")
    for _ in range(n_rejected):
        kpi.record_signal("REJECTED")

    assert not kpi.is_approval_blocked(), (
        f"KPI bloqué à tort : {n_approved}/{total} = {pct:.1f}%"
    )


# =========================================================================
# TEST 7 : Chaîne hash audit -> croît monotoniquement et se vérifie
# =========================================================================
@given(n_entries=st.integers(min_value=1, max_value=20))
@settings(max_examples=10)
def test_audit_hash_chain_integrity(n_entries):
    """La chaîne de hash doit rester intègre quel que soit le nombre d'entrées."""
    # Nettoyage
    for f in ["logs/audit.log", "logs/audit.meta"]:
        if os.path.exists(f):
            os.remove(f)

    audit = AuditSystem()
    for i in range(n_entries):
        audit.log(f"ACTION_{i}", f"ACTOR_{i}", f"details_{i}", "OK")

    result = audit.verify_integrity()
    assert result["valid"], f"Chaîne corrompue après {n_entries} entrées"
    # INIT + n_entries = total
    assert result["entries"] == n_entries + 1, (
        f"Attendu {n_entries + 1} entrées, trouvé {result['entries']}"
    )


# =========================================================================
# EXÉCUTION
# =========================================================================
if __name__ == "__main__":
    tests = [
        ("Signal valide -> toujours validé", test_valid_signal_always_passes),
        ("Signal incomplet -> toujours rejeté", test_incomplete_signal_always_rejected),
        ("Edge < 0.5% -> toujours rejeté", test_low_edge_always_rejected),
        ("Mot interdit -> toujours rejeté", test_forbidden_word_always_rejected),
        ("AlphaDecision -> toujours conforme", test_alpha_decision_always_conforms),
        ("KPI <=5% -> jamais bloqué", test_kpi_below_threshold_never_blocked),
        ("Hash chain -> intégrité vérifiée", test_audit_hash_chain_integrity),
    ]

    print("=" * 60)
    print("  PROPERTY-BASED TESTS — Manager IA Alpha")
    print("=" * 60)
    print()

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            test_fn()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}")
            print(f"         {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"  RESULTATS: {passed} PASS / {failed} FAIL / {passed + failed} TOTAL")
    print("=" * 60)

    if failed == 0:
        print("\n  TOUS LES PROPERTY TESTS PASSES.")
    else:
        print(f"\n  ATTENTION: {failed} test(s) en échec.")

    sys.exit(0 if failed == 0 else 1)
