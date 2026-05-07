"""Stratégie baseline : RSI < 30 → BUY, RSI > 70 → SELL.

Référence simple. Utilise le RSI Wilder (standard académique).
"""

from __future__ import annotations

import pandas as pd

from ..indicators import rsi
from .base import Signal, Strategy, StrategyContext


class RsiBaseline(Strategy):
    name = "rsi_baseline"

    def __init__(self, window: int = 14, oversold: float = 30, overbought: float = 70):
        super().__init__(window=window, oversold=oversold, overbought=overbought)
        self.window = window
        self.oversold = oversold
        self.overbought = overbought

    def warmup(self) -> int:
        return self.window + 5

    def decide(self, ctx: StrategyContext) -> Signal:
        rsi_serie = rsi(ctx.df["close"], self.window)
        current = rsi_serie.iloc[-1]
        if pd.isna(current):
            return Signal("HOLD", raison="RSI non calculable")

        if not ctx.position_ouverte and current < self.oversold:
            return Signal(
                "BUY",
                raison=f"RSI {current:.1f} < {self.oversold} (survendu)",
                contexte={"rsi": float(current)},
            )
        if ctx.position_ouverte and current > self.overbought:
            return Signal(
                "SELL",
                raison=f"RSI {current:.1f} > {self.overbought} (suracheté)",
                contexte={"rsi": float(current)},
            )
        return Signal(
            "HOLD",
            raison=f"RSI {current:.1f} dans la zone neutre",
            contexte={"rsi": float(current)},
        )
