"""Stratégies de trading. Chaque stratégie hérite de Strategy."""

from .base import Signal, Strategy, StrategyContext
from .hybride_prudente import HybridePrudente
from .rsi_baseline import RsiBaseline

__all__ = [
    "Signal", "Strategy", "StrategyContext",
    "RsiBaseline", "HybridePrudente", "REGISTRY",
]

REGISTRY: dict[str, type[Strategy]] = {
    "rsi_baseline": RsiBaseline,
    "hybride_prudente": HybridePrudente,
}
