"""Métriques de performance pour stratégies de trading.

Conventions :
- equity : pd.Series indexée par timestamp (ms ou datetime), valeur du portefeuille
- returns : variations period-over-period
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _periods_per_year(interval: str) -> float:
    """Combien de bougies dans une année selon l'intervalle."""
    table = {
        "1m": 365 * 24 * 60,
        "5m": 365 * 24 * 12,
        "15m": 365 * 24 * 4,
        "30m": 365 * 24 * 2,
        "1h": 365 * 24,
        "4h": 365 * 6,
        "1d": 365,
    }
    return table.get(interval, 365 * 24 * 4)


def total_return(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    return float(equity.iloc[-1] / equity.iloc[0] - 1.0)


def cagr(equity: pd.Series, interval: str) -> float:
    if len(equity) < 2:
        return 0.0
    n_periods = len(equity) - 1
    years = n_periods / _periods_per_year(interval)
    if years <= 0:
        return 0.0
    return float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1.0)


def max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    running_max = equity.cummax()
    drawdown = equity / running_max - 1.0
    return float(drawdown.min())


def sharpe(equity: pd.Series, interval: str, risk_free: float = 0.0) -> float:
    rets = equity.pct_change().dropna()
    if rets.std() == 0 or rets.empty:
        return 0.0
    periods = _periods_per_year(interval)
    excess = rets - risk_free / periods
    return float(excess.mean() / rets.std() * math.sqrt(periods))


def sortino(equity: pd.Series, interval: str, risk_free: float = 0.0) -> float:
    rets = equity.pct_change().dropna()
    if rets.empty:
        return 0.0
    periods = _periods_per_year(interval)
    excess = rets - risk_free / periods
    downside = rets[rets < 0]
    if downside.empty or downside.std() == 0:
        return 0.0
    return float(excess.mean() / downside.std() * math.sqrt(periods))


def win_rate(trade_pnls: list[float]) -> float:
    if not trade_pnls:
        return 0.0
    wins = sum(1 for p in trade_pnls if p > 0)
    return wins / len(trade_pnls)


def profit_factor(trade_pnls: list[float]) -> float:
    gains = sum(p for p in trade_pnls if p > 0)
    losses = -sum(p for p in trade_pnls if p < 0)
    if losses == 0:
        return float("inf") if gains > 0 else 0.0
    return gains / losses


def summary(equity: pd.Series, trade_pnls: list[float], interval: str) -> dict:
    return {
        "total_return": total_return(equity),
        "cagr": cagr(equity, interval),
        "sharpe": sharpe(equity, interval),
        "sortino": sortino(equity, interval),
        "max_drawdown": max_drawdown(equity),
        "win_rate": win_rate(trade_pnls),
        "profit_factor": profit_factor(trade_pnls),
        "nb_trades": len(trade_pnls),
        "equity_initial": float(equity.iloc[0]) if len(equity) else 0.0,
        "equity_final": float(equity.iloc[-1]) if len(equity) else 0.0,
    }
