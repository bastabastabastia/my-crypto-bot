"""Contrat de stratégie."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal

import pandas as pd


@dataclass
class Signal:
    action: Literal["BUY", "SELL", "HOLD"]
    raison: str = ""
    # Montant USD demandé pour un BUY. None = utiliser plafond_position du moteur.
    montant_usd: float | None = None
    contexte: dict = field(default_factory=dict)


@dataclass
class StrategyContext:
    """Contexte passé à la stratégie pour décider.

    Plus riche que juste un bool : nécessaire pour les stratégies qui
    regardent le cash global, le nb de positions, ou la durée de détention.
    """
    df: pd.DataFrame                 # OHLCV jusqu'à la bougie courante (incluse)
    ts_courant_ms: int               # timestamp ms de la bougie courante
    marche: str                      # ex "BTC"
    position_quantite: float = 0.0   # 0 = pas de position
    position_prix_achat: float = 0.0
    position_ts_achat_ms: int = 0
    cash_global: float = 0.0         # cash partagé entre marchés
    nb_positions_ouvertes: int = 0   # toutes positions ouvertes (autres marchés inclus)

    @property
    def position_ouverte(self) -> bool:
        return self.position_quantite > 0


class Strategy(ABC):
    name: str = "base"

    def __init__(self, **params):
        self.params = params

    @abstractmethod
    def decide(self, ctx: StrategyContext) -> Signal:
        ...

    def warmup(self) -> int:
        """Nb min de bougies avant de pouvoir décider."""
        return 50
