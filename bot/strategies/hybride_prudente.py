"""Hybride Prudente v1.0 — reproduction fidèle de /root/strategie.py (prod).

Logique vente (position ouverte) :
  1. Stop-loss : prix vs prix_achat ≤ -3 %
  2. Take-profit : RSI ≥ 70
  3. Durée max : 4 h détenue → vente forcée
  4. Sinon : GARDER

Logique achat (pas de position) :
  1. Limite 3 positions ouvertes
  2. Cash ≥ 200 $
  3. RSI < 35 (survente — note : 35, pas 30)
  4. Prix > MM50 (filtre tendance)

Achat fixe à 200 $.
"""

from __future__ import annotations

import pandas as pd

from ..indicators import rsi_sma
from .base import Signal, Strategy, StrategyContext


class HybridePrudente(Strategy):
    name = "hybride_prudente"

    def __init__(
        self,
        rsi_periode: int = 14,
        rsi_survente: float = 35.0,
        rsi_surachat: float = 70.0,
        stop_loss_pct: float = -3.0,
        max_duree_heures: float = 4.0,
        montant_par_trade: float = 200.0,
        max_positions: int = 3,
        mm_periode: int = 50,
    ):
        super().__init__(
            rsi_periode=rsi_periode,
            rsi_survente=rsi_survente,
            rsi_surachat=rsi_surachat,
            stop_loss_pct=stop_loss_pct,
            max_duree_heures=max_duree_heures,
            montant_par_trade=montant_par_trade,
            max_positions=max_positions,
            mm_periode=mm_periode,
        )
        self.rsi_periode = rsi_periode
        self.rsi_survente = rsi_survente
        self.rsi_surachat = rsi_surachat
        self.stop_loss_pct = stop_loss_pct
        self.max_duree_heures = max_duree_heures
        self.montant_par_trade = montant_par_trade
        self.max_positions = max_positions
        self.mm_periode = mm_periode

    def warmup(self) -> int:
        return max(self.mm_periode, self.rsi_periode) + 5

    def decide(self, ctx: StrategyContext) -> Signal:
        prix = float(ctx.df.iloc[-1]["close"])
        rsi_val = rsi_sma(ctx.df["close"], self.rsi_periode).iloc[-1]
        if pd.isna(rsi_val):
            return Signal("HOLD", raison="RSI non calculable")

        if ctx.position_ouverte:
            return self._decide_vente(ctx, prix, float(rsi_val))
        return self._decide_achat(ctx, prix, float(rsi_val))

    def _decide_vente(
        self, ctx: StrategyContext, prix: float, rsi_val: float
    ) -> Signal:
        var_pct = ((prix - ctx.position_prix_achat) / ctx.position_prix_achat) * 100

        if var_pct <= self.stop_loss_pct:
            return Signal(
                "SELL",
                raison=f"STOP-LOSS : {var_pct:+.2f}%",
                contexte={"rsi": rsi_val, "var_pct": var_pct, "trigger": "stop_loss"},
            )

        if rsi_val >= self.rsi_surachat:
            return Signal(
                "SELL",
                raison=f"TAKE-PROFIT : RSI={rsi_val:.1f} | P&L: {var_pct:+.2f}%",
                contexte={"rsi": rsi_val, "var_pct": var_pct, "trigger": "take_profit"},
            )

        # Durée détenue (à partir du timestamp d'entrée tracké par le moteur)
        if ctx.position_ts_achat_ms > 0:
            heures = (ctx.ts_courant_ms - ctx.position_ts_achat_ms) / 3_600_000
            if heures >= self.max_duree_heures:
                return Signal(
                    "SELL",
                    raison=f"DUREE MAX : {heures:.1f}h | P&L: {var_pct:+.2f}%",
                    contexte={"rsi": rsi_val, "var_pct": var_pct, "trigger": "duree_max"},
                )

        return Signal(
            "HOLD",
            raison=f"P&L: {var_pct:+.2f}% | RSI: {rsi_val:.1f}",
            contexte={"rsi": rsi_val, "var_pct": var_pct},
        )

    def _decide_achat(
        self, ctx: StrategyContext, prix: float, rsi_val: float
    ) -> Signal:
        if ctx.nb_positions_ouvertes >= self.max_positions:
            return Signal(
                "HOLD",
                raison=f"Limite {self.max_positions} positions atteinte",
                contexte={"trigger": "max_positions"},
            )
        if ctx.cash_global < self.montant_par_trade:
            return Signal(
                "HOLD",
                raison=f"Cash insuffisant ({ctx.cash_global:.2f}$)",
                contexte={"trigger": "cash_insuffisant"},
            )
        if rsi_val >= self.rsi_survente:
            return Signal(
                "HOLD",
                raison=f"Pas de survente : RSI={rsi_val:.1f}",
                contexte={"rsi": rsi_val},
            )
        mm = ctx.df["close"].rolling(self.mm_periode).mean().iloc[-1]
        if pd.isna(mm) or prix < mm:
            mm_str = f"{mm:.2f}" if not pd.isna(mm) else "n/a"
            return Signal(
                "HOLD",
                raison=f"Prix sous MM{self.mm_periode} : {prix:.2f} < {mm_str}",
                contexte={"rsi": rsi_val, "mm50": float(mm) if not pd.isna(mm) else None},
            )

        return Signal(
            "BUY",
            raison=f"OK : RSI={rsi_val:.1f}, prix>MM{self.mm_periode}",
            montant_usd=self.montant_par_trade,
            contexte={"rsi": rsi_val, "mm50": float(mm)},
        )
