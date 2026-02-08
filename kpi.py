"""
KPI ALPHA — Indicateurs de qualité.
Un bon Alpha = peu de signaux, très propres.
Si signals_approved_pct > 5% → blocage automatique.
"""

from collections import Counter
from datetime import datetime

from config import MAX_APPROVAL_PCT


class KPITracker:
    """Suivi des indicateurs de qualité Alpha."""

    def __init__(self):
        self.total_markets_analyzed: int = 0
        self.total_markets_rejected: int = 0
        self.total_signals_submitted: int = 0
        self.total_signals_approved: int = 0
        self.total_signals_surveillance: int = 0
        self.total_signals_rejected: int = 0
        self.rejection_reasons: list[str] = []
        self.approval_blocked: bool = False
        self.approval_blocked_at: str | None = None
        self.verbal_violations: dict[str, int] = {}  # agent_id → count
        self.signal_clarity_scores: list[float] = []

    # =========================================================================
    # ENREGISTREMENT
    # =========================================================================
    def record_market_analysis(self, rejected: bool, reason: str = "") -> None:
        self.total_markets_analyzed += 1
        if rejected:
            self.total_markets_rejected += 1
            if reason:
                self.rejection_reasons.append(reason)

    def record_signal(self, status: str, clarity_score: float = 0.0,
                      rejection_reasons: list[str] | None = None) -> None:
        self.total_signals_submitted += 1

        if status == "APPROVED":
            self.total_signals_approved += 1
        elif status == "SURVEILLANCE":
            self.total_signals_surveillance += 1
        elif status == "REJECTED":
            self.total_signals_rejected += 1
            if rejection_reasons:
                self.rejection_reasons.extend(rejection_reasons)

        if clarity_score > 0:
            self.signal_clarity_scores.append(clarity_score)

        # Vérification blocage automatique
        self._check_approval_threshold()

    def record_verbal_violation(self, agent_id: str) -> None:
        self.verbal_violations[agent_id] = self.verbal_violations.get(agent_id, 0) + 1

    # =========================================================================
    # CALCULS
    # =========================================================================
    @property
    def markets_rejected_pct(self) -> float:
        if self.total_markets_analyzed == 0:
            return 0.0
        return (self.total_markets_rejected / self.total_markets_analyzed) * 100

    @property
    def signals_approved_pct(self) -> float:
        if self.total_signals_submitted == 0:
            return 0.0
        return (self.total_signals_approved / self.total_signals_submitted) * 100

    @property
    def signals_rejected_pct(self) -> float:
        if self.total_signals_submitted == 0:
            return 0.0
        return (self.total_signals_rejected / self.total_signals_submitted) * 100

    @property
    def avg_signal_clarity(self) -> float:
        if not self.signal_clarity_scores:
            return 0.0
        return sum(self.signal_clarity_scores) / len(self.signal_clarity_scores)

    @property
    def top_rejection_reasons(self) -> list[tuple[str, int]]:
        counter = Counter(self.rejection_reasons)
        return counter.most_common(10)

    @property
    def total_verbal_violations(self) -> int:
        return sum(self.verbal_violations.values())

    # =========================================================================
    # BLOCAGE AUTOMATIQUE
    # =========================================================================
    def _check_approval_threshold(self) -> None:
        """Si > 5% signaux approuvés → blocage automatique."""
        if self.signals_approved_pct > MAX_APPROVAL_PCT and self.total_signals_submitted >= 5:
            self.approval_blocked = True
            self.approval_blocked_at = datetime.now().isoformat()

    def is_approval_blocked(self) -> bool:
        return self.approval_blocked

    def manual_unblock(self, reviewer: str, reason: str) -> dict:
        """Déblocage manuel après revue. Requiert justification."""
        if not self.approval_blocked:
            return {"status": "NOT_BLOCKED", "message": "Aucun blocage en cours"}

        self.approval_blocked = False
        self.approval_blocked_at = None
        return {
            "status": "UNBLOCKED",
            "reviewer": reviewer,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        }

    # =========================================================================
    # RAPPORT
    # =========================================================================
    def report(self) -> dict:
        return {
            "total_markets_analyzed": self.total_markets_analyzed,
            "total_markets_rejected": self.total_markets_rejected,
            "markets_rejected_pct": round(self.markets_rejected_pct, 1),
            "total_signals_submitted": self.total_signals_submitted,
            "total_signals_approved": self.total_signals_approved,
            "total_signals_surveillance": self.total_signals_surveillance,
            "total_signals_rejected": self.total_signals_rejected,
            "signals_approved_pct": round(self.signals_approved_pct, 1),
            "signals_rejected_pct": round(self.signals_rejected_pct, 1),
            "avg_signal_clarity": round(self.avg_signal_clarity, 1),
            "top_rejection_reasons": self.top_rejection_reasons,
            "approval_blocked": self.approval_blocked,
            "approval_blocked_at": self.approval_blocked_at,
            "total_verbal_violations": self.total_verbal_violations,
            "verbal_violations_by_agent": dict(self.verbal_violations),
        }

    def format_report(self) -> str:
        r = self.report()
        lines = [
            "=" * 60,
            "RAPPORT KPI ALPHA",
            "=" * 60,
            "",
            "--- MARCHÉS ---",
            f"  Analysés .............. {r['total_markets_analyzed']}",
            f"  Rejetés ............... {r['total_markets_rejected']}",
            f"  Taux de rejet ......... {r['markets_rejected_pct']}%",
            "",
            "--- SIGNAUX ---",
            f"  Soumis ................ {r['total_signals_submitted']}",
            f"  Approuvés ............. {r['total_signals_approved']}",
            f"  Surveillance .......... {r['total_signals_surveillance']}",
            f"  Rejetés ............... {r['total_signals_rejected']}",
            f"  Taux approbation ...... {r['signals_approved_pct']}%",
            f"  Taux rejet ............ {r['signals_rejected_pct']}%",
            f"  Clarté moyenne ........ {r['avg_signal_clarity']}%",
            "",
            "--- DISCIPLINE ---",
            f"  Violations verbales ... {r['total_verbal_violations']}",
        ]

        if r["approval_blocked"]:
            lines.extend([
                "",
                "  *** ALERTE : APPROBATIONS BLOQUÉES ***",
                f"  Bloqué depuis : {r['approval_blocked_at']}",
                "  Raison : Taux approbation > 5%",
                "  Action requise : Revue manuelle obligatoire",
            ])

        if r["top_rejection_reasons"]:
            lines.extend(["", "--- MOTIFS DE REJET RÉCURRENTS ---"])
            for reason, count in r["top_rejection_reasons"]:
                lines.append(f"  [{count}x] {reason}")

        if r["verbal_violations_by_agent"]:
            lines.extend(["", "--- VIOLATIONS VERBALES PAR AGENT ---"])
            for agent_id, count in r["verbal_violations_by_agent"].items():
                lines.append(f"  Agent {agent_id} : {count} violations")

        lines.append("=" * 60)
        return "\n".join(lines)

    def get_kpi_data(self) -> dict:
        """Retourne les données KPI pour l'audit."""
        return {
            "signals_approved_pct": self.signals_approved_pct,
            "approval_blocked": self.approval_blocked,
        }
