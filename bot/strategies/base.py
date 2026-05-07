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
    # taille demandée en fraction du capital alloué au marché [0, 1]
    taille: float = 1.0
    contexte: dict = field(default_factory=dict)


class Strategy(ABC):
    """Stratégie sans état partagé entre marchés.

    Le moteur appelle decide() pour chaque bougie en passant l'historique
    OHLCV jusqu'à la bougie courante (incluse). La stratégie retourne un
    Signal (BUY / SELL / HOLD).
    """

    name: str = "base"

    def __init__(self, **params):
        self.params = params

    @abstractmethod
    def decide(self, df: pd.DataFrame, position_ouverte: bool) -> Signal:
        """Retourne un signal pour la bougie courante (df.iloc[-1])."""
        ...

    def warmup(self) -> int:
        """Nombre minimum de bougies nécessaires avant de pouvoir décider."""
        return 50
