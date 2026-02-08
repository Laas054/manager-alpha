"""
SIGNAL ALPHA — Format officiel et validation stricte.
Champ manquant = rejet automatique. Aucune exception.
"""

from config import (
    EQUIVALENT_METRICS,
    FORBIDDEN_WORDS_ALL,
    LATE_EDGE_SUSPICION_HOURS,
    MAX_TIME_TO_RESOLUTION_HOURS,
    METRIC_DOMINANCE_THRESHOLD,
    MIN_EDGE_NET,
    SIGNAL_REQUIRED_FIELDS,
    SIGNAL_STATUS_REJECTED,
    SIGNAL_STATUSES,
    SIGNAL_TYPES,
    utc_now,
)


class SignalAlpha:
    """Signal Alpha avec validation stricte conforme au Protocole Officiel."""

    def __init__(self, data: dict):
        self.data = data
        self.validation_errors: list[str] = []
        self.validated: bool = False

    def validate(self) -> dict:
        """
        Validation complète du signal.
        Retourne un dict avec 'valid' (bool), 'errors' (list), 'status' (str).
        """
        self.validation_errors = []

        self._check_required_fields()
        if self.validation_errors:
            return self._reject("Champs obligatoires manquants")

        self._check_signal_type()
        if self.validation_errors:
            return self._reject("Validation échouée")

        self._check_signal_status()
        if self.validation_errors:
            return self._reject("Validation échouée")

        self._check_edge_net()
        if self.validation_errors:
            return self._reject("Validation échouée")

        self._check_time_to_resolution()
        if self.validation_errors:
            return self._reject("Validation échouée")

        self._check_language()
        if self.validation_errors:
            return self._reject("Validation échouée")

        self._check_single_metric_dominance()
        if self.validation_errors:
            return self._reject("Validation échouée")

        self._check_risks_field()
        if self.validation_errors:
            return self._reject("Validation échouée")

        self.validated = True
        return {
            "valid": True,
            "errors": [],
            "status": self.data.get("status", SIGNAL_STATUS_REJECTED),
            "comment": "Signal conforme au Protocole Alpha.",
        }

    def _check_required_fields(self) -> None:
        """Règle 8 : Tout signal doit être écrit. Champ manquant = rejet."""
        for field in SIGNAL_REQUIRED_FIELDS:
            value = self.data.get(field)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                self.validation_errors.append(
                    f"REJET — Champ obligatoire manquant ou vide : '{field}'"
                )

    def _check_signal_type(self) -> None:
        sig_type = self.data.get("type", "")
        if sig_type not in SIGNAL_TYPES:
            self.validation_errors.append(
                f"REJET — Type invalide '{sig_type}'. Autorisés : {SIGNAL_TYPES}"
            )

    def _check_signal_status(self) -> None:
        status = self.data.get("status", "")
        if status not in SIGNAL_STATUSES:
            self.validation_errors.append(
                f"REJET — Statut invalide '{status}'. Autorisés : {SIGNAL_STATUSES}"
            )

    def _check_edge_net(self) -> None:
        """Règle 4 : Seul l'edge net est considéré."""
        edge_net = self.data.get("edge_net")
        if edge_net is None:
            return  # Déjà attrapé par _check_required_fields

        try:
            edge_val = float(edge_net)
        except (ValueError, TypeError):
            self.validation_errors.append(
                f"REJET — edge_net doit être numérique, reçu : '{edge_net}'"
            )
            return

        if edge_val < MIN_EDGE_NET:
            self.validation_errors.append(
                f"REJET — edge_net ({edge_val}%) inférieur au minimum ({MIN_EDGE_NET}%)"
            )

    def _check_time_to_resolution(self) -> None:
        """Règle 5 : Le temps est un risque."""
        ttr = self.data.get("time_to_resolution")
        if ttr is None:
            return

        try:
            ttr_val = float(ttr)
        except (ValueError, TypeError):
            self.validation_errors.append(
                f"REJET — time_to_resolution doit être numérique (heures), reçu : '{ttr}'"
            )
            return

        if ttr_val > MAX_TIME_TO_RESOLUTION_HOURS:
            self.validation_errors.append(
                f"REJET — time_to_resolution ({ttr_val}h) dépasse le maximum ({MAX_TIME_TO_RESOLUTION_HOURS}h)"
            )

        # Edge élevé tardif = suspect
        edge_net = self.data.get("edge_net")
        if edge_net is not None:
            try:
                edge_val = float(edge_net)
                if ttr_val > LATE_EDGE_SUSPICION_HOURS and edge_val > 5.0:
                    self.validation_errors.append(
                        f"REJET — Edge élevé ({edge_val}%) avec résolution tardive ({ttr_val}h) = SUSPECT (Règle 5)"
                    )
            except (ValueError, TypeError):
                pass

    def _check_language(self) -> None:
        """Règle 7 : Aucun langage flou n'est autorisé."""
        comment = self.data.get("comment", "")
        risks = self.data.get("risks", "")
        text_to_check = f"{comment} {risks}".lower()

        for word in FORBIDDEN_WORDS_ALL:
            if word.lower() in text_to_check:
                self.validation_errors.append(
                    f"REJET — Langage flou détecté : '{word}' (Règle 7)"
                )

    def _check_single_metric_dominance(self) -> None:
        """
        Règle 2 — CONDITION OBLIGATOIRE : Aucun chiffre ne domine les autres.

        Vérifie que la justification/commentaire ne repose pas sur une seule métrique.
        Si un champ représente > 60% de la justification → REJET.
        """
        comment = self.data.get("comment", "").lower()
        if not comment:
            return

        metric_keywords = {
            "edge_net": ["edge", "rendement", "profit", "gain", "yield", "return"],
            "volume": ["volume", "liquidité", "liquidity", "depth"],
            "spread": ["spread", "écart", "bid-ask", "bid ask"],
            "time_to_resolution": ["temps", "time", "résolution", "expiry", "deadline", "délai"],
            "risks": ["risque", "risk", "danger", "exposition", "exposure", "drawdown"],
        }

        mention_counts: dict[str, int] = {}
        total_mentions = 0

        for metric, keywords in metric_keywords.items():
            count = 0
            for kw in keywords:
                count += comment.count(kw)
            mention_counts[metric] = count
            total_mentions += count

        if total_mentions == 0:
            return

        for metric, count in mention_counts.items():
            ratio = count / total_mentions
            if ratio > METRIC_DOMINANCE_THRESHOLD:
                self.validation_errors.append(
                    f"REJET — Dominance métrique détectée : '{metric}' représente "
                    f"{ratio:.0%} des mentions (seuil: {METRIC_DOMINANCE_THRESHOLD:.0%}). "
                    f"Règle 2 : aucun chiffre ne domine les autres."
                )

        # Vérification complémentaire : edge élevé sans mention des autres métriques
        metrics_with_values = []
        for m in EQUIVALENT_METRICS:
            val = self.data.get(m)
            if val is not None:
                try:
                    float_val = float(val) if m != "risks" else None
                    if float_val is not None:
                        metrics_with_values.append(m)
                except (ValueError, TypeError):
                    if isinstance(val, str) and val.strip():
                        metrics_with_values.append(m)

        mentioned_in_comment = [
            m for m, keywords in metric_keywords.items()
            if any(kw in comment for kw in keywords)
        ]

        if len(mentioned_in_comment) == 1 and len(metrics_with_values) >= 3:
            sole_metric = mentioned_in_comment[0]
            self.validation_errors.append(
                f"REJET — Le commentaire ne mentionne que '{sole_metric}' "
                f"alors que {len(metrics_with_values)} métriques sont fournies. "
                f"Règle 2 : analyse équivalente requise."
            )

    def _check_risks_field(self) -> None:
        """Vérifie que le champ risques est substantiel."""
        risks = self.data.get("risks", "")
        if isinstance(risks, str) and len(risks.strip()) < 10:
            self.validation_errors.append(
                "REJET — Le champ 'risks' est insuffisant. "
                "Les risques doivent être identifiés de manière factuelle et détaillée."
            )

    def _reject(self, reason: str) -> dict:
        return {
            "valid": False,
            "errors": self.validation_errors,
            "status": SIGNAL_STATUS_REJECTED,
            "comment": reason,
        }

    def to_dict(self) -> dict:
        return {
            **self.data,
            "validated": self.validated,
            "validation_errors": self.validation_errors,
            "validation_timestamp": utc_now().isoformat(),
        }

    def format_display(self) -> str:
        """Format d'affichage officiel du signal."""
        lines = [
            "=" * 60,
            "SIGNAL ALPHA",
            "=" * 60,
        ]
        for field in SIGNAL_REQUIRED_FIELDS:
            value = self.data.get(field, "N/A")
            lines.append(f"  {field.upper():.<30} {value}")
        lines.append("=" * 60)

        if self.validation_errors:
            lines.append("ERREURS DE VALIDATION :")
            for err in self.validation_errors:
                lines.append(f"  >> {err}")
            lines.append("=" * 60)

        return "\n".join(lines)
