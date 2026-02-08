"""
ALPHA INTERFACE -- Couche d'interoperabilite AlphaDecision.
Format de sortie UNIQUE d'Alpha vers les autres equipes.
Aucune logique metier hors Alpha. Contrat IMMUTABLE.
"""

from alpha_interface.alpha_decision import AlphaDecisionBuilder, validate_against_schema

__all__ = ["AlphaDecisionBuilder", "validate_against_schema"]
