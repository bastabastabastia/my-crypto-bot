"""Stratégies de trading. Chaque stratégie hérite de Strategy."""

from .base import Signal, Strategy
from .rsi_baseline import RsiBaseline

__all__ = ["Signal", "Strategy", "RsiBaseline", "REGISTRY"]

REGISTRY: dict[str, type[Strategy]] = {
    "rsi_baseline": RsiBaseline,
}
