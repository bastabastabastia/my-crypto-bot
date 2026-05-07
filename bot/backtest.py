"""Moteur de backtest.

Logique :
- pour chaque marché, simuler une exécution à la bougie suivante (close)
  pour éviter le look-ahead bias
- frais et slippage appliqués à chaque trade
- capital partagé OU alloué par marché ; ici alloué (CAPITAL_PAR_MARCHE)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

import pandas as pd

from .config import (
    DEFAULT_HISTORY_DAYS,
    DEFAULT_INTERVAL,
    FRAIS_PCT,
    SLIPPAGE_PCT,
)
from .db import connect, init_db
from .metrics import summary
from .strategies.base import Strategy


@dataclass
class TradeRecord:
    ts: int
    marche: str
    action: str  # ACHAT / VENTE
    quantite: float
    prix: float
    frais: float
    pnl: float | None
    raison: str


@dataclass
class Position:
    marche: str
    quantite: float = 0.0
    prix_entree: float = 0.0
    cout_entree: float = 0.0  # cash engagé à l'achat (incluant frais)

    @property
    def ouverte(self) -> bool:
        return self.quantite > 0


@dataclass
class Portfolio:
    """Cash global commun à tous les marchés (modèle prod paper_trading.py)."""
    cash: float
    capital_initial: float
    positions: dict[str, Position] = field(default_factory=dict)

    def position(self, marche: str) -> Position:
        if marche not in self.positions:
            self.positions[marche] = Position(marche=marche)
        return self.positions[marche]

    def nb_positions_ouvertes(self) -> int:
        return sum(1 for p in self.positions.values() if p.ouverte)


@dataclass
class BacktestResult:
    run_id: int
    strategy: str
    marches: list[str]
    intervalle: str
    debut: str
    fin: str
    capital_initial: float
    capital_final: float
    pnl_pct: float
    trades: list[TradeRecord]
    equity_curve: pd.Series
    metriques: dict = field(default_factory=dict)


def load_prix(marche: str, intervalle: str) -> pd.DataFrame:
    with connect() as conn:
        df = pd.read_sql_query(
            """SELECT open_time, open, high, low, close, volume
               FROM prix
               WHERE marche=? AND intervalle=?
               ORDER BY open_time""",
            conn,
            params=(marche, intervalle),
        )
    if df.empty:
        return df
    df["ts"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df = df.set_index("ts")
    return df


def run(
    strategy: Strategy,
    marches: list[str],
    intervalle: str = DEFAULT_INTERVAL,
    capital_initial: float | None = None,
    capital_par_marche: float | None = None,  # taille max par position si pas fournie par signal.taille
    frais_pct: float = FRAIS_PCT,
    slippage_pct: float = SLIPPAGE_PCT,
) -> BacktestResult:
    """Execute le backtest avec cash GLOBAL et persiste le résultat.

    - capital_initial : si fourni, montant unique partagé. Sinon = CAPITAL_INITIAL.
    - capital_par_marche : si fourni, plafond max par position (sinon = capital_initial / nb_marchés).
    """
    from .config import CAPITAL_INITIAL

    init_db()
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    capital_initial = capital_initial if capital_initial is not None else CAPITAL_INITIAL
    plafond_position = (
        capital_par_marche
        if capital_par_marche is not None
        else capital_initial / max(1, len(marches))
    )

    # Charger les données
    data: dict[str, pd.DataFrame] = {}
    for m in marches:
        df = load_prix(m, intervalle)
        if df.empty:
            raise RuntimeError(
                f"Aucune donnée pour {m}/{intervalle}. "
                "Lance d'abord : python -m bot.cli download-data"
            )
        data[m] = df

    # Index commun
    common_index = None
    for df in data.values():
        common_index = df.index if common_index is None else common_index.intersection(df.index)
    if common_index is None or len(common_index) == 0:
        raise RuntimeError("Index commun vide entre les marchés.")

    portfolio = Portfolio(cash=capital_initial, capital_initial=capital_initial)
    trades: list[TradeRecord] = []
    equity_history: list[tuple[int, float, float]] = []  # (ts_ms, equity, cash)

    warmup = strategy.warmup()
    for i, ts in enumerate(common_index):
        if i < warmup:
            continue

        for m in marches:
            df = data[m].loc[:ts]
            pos = portfolio.position(m)
            signal = strategy.decide(df, pos.ouverte)

            prix_close = float(df.iloc[-1]["close"])
            ts_ms = int(ts.timestamp() * 1000)

            if signal.action == "BUY" and not pos.ouverte and portfolio.cash > 0:
                prix_exec = prix_close * (1 + slippage_pct)
                # Taille demandée par la stratégie (fraction de plafond) ; bornée au cash dispo
                cash_demande = plafond_position * max(0.0, min(1.0, signal.taille))
                cash_a_engager = min(portfolio.cash, cash_demande)
                if cash_a_engager <= 0:
                    continue
                frais = cash_a_engager * frais_pct
                montant_net = cash_a_engager - frais
                qty = montant_net / prix_exec
                pos.quantite = qty
                pos.prix_entree = prix_exec
                pos.cout_entree = cash_a_engager
                portfolio.cash -= cash_a_engager
                trades.append(TradeRecord(
                    ts=ts_ms, marche=m, action="ACHAT",
                    quantite=qty, prix=prix_exec, frais=frais, pnl=None,
                    raison=signal.raison,
                ))
            elif signal.action == "SELL" and pos.ouverte:
                prix_exec = prix_close * (1 - slippage_pct)
                montant_brut = pos.quantite * prix_exec
                frais = montant_brut * frais_pct
                montant_net = montant_brut - frais
                pnl = montant_net - pos.cout_entree
                portfolio.cash += montant_net
                trades.append(TradeRecord(
                    ts=ts_ms, marche=m, action="VENTE",
                    quantite=pos.quantite, prix=prix_exec, frais=frais, pnl=pnl,
                    raison=signal.raison,
                ))
                pos.quantite = 0.0
                pos.prix_entree = 0.0
                pos.cout_entree = 0.0

        # Snapshot equity (cash global + valeur des positions au close)
        equity = portfolio.cash + sum(
            p.quantite * float(data[p.marche].loc[ts]["close"])
            for p in portfolio.positions.values()
            if p.ouverte
        )
        equity_history.append((int(ts.timestamp() * 1000), equity, portfolio.cash))

    # Construit les séries
    if not equity_history:
        raise RuntimeError("Backtest sans aucune bougie après warmup. Données insuffisantes ?")
    eq_df = pd.DataFrame(equity_history, columns=["ts_ms", "equity", "cash"])
    eq_df["ts"] = pd.to_datetime(eq_df["ts_ms"], unit="ms", utc=True)
    eq_df = eq_df.set_index("ts")
    equity_curve = eq_df["equity"]

    capital_final = float(equity_curve.iloc[-1])
    pnl_pct = (capital_final / capital_initial - 1.0) * 100

    trade_pnls = [t.pnl for t in trades if t.pnl is not None]
    metriques = summary(equity_curve, trade_pnls, intervalle)

    finished_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    debut = equity_curve.index[0].isoformat()
    fin = equity_curve.index[-1].isoformat()

    # Persistance
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO backtest_runs
               (started_at, finished_at, strategy, params_json, marches_json,
                intervalle, debut, fin, capital_initial, capital_final, pnl_pct,
                sharpe, sortino, max_drawdown, win_rate, nb_trades, cagr)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                started_at, finished_at, strategy.name,
                json.dumps(strategy.params), json.dumps(marches),
                intervalle, debut, fin, capital_initial, capital_final, pnl_pct,
                metriques["sharpe"], metriques["sortino"],
                metriques["max_drawdown"], metriques["win_rate"],
                metriques["nb_trades"], metriques["cagr"],
            ),
        )
        run_id = cur.lastrowid

        conn.executemany(
            """INSERT INTO backtest_trades
               (run_id, ts, marche, action, quantite, prix, frais, pnl, raison)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            [
                (run_id, t.ts, t.marche, t.action, t.quantite, t.prix,
                 t.frais, t.pnl, t.raison)
                for t in trades
            ],
        )
        conn.executemany(
            "INSERT INTO backtest_equity (run_id, ts, equity, cash) VALUES (?,?,?,?)",
            [(run_id, ts_ms, equity, cash) for ts_ms, equity, cash in equity_history],
        )

    return BacktestResult(
        run_id=run_id,
        strategy=strategy.name,
        marches=marches,
        intervalle=intervalle,
        debut=debut,
        fin=fin,
        capital_initial=capital_initial,
        capital_final=capital_final,
        pnl_pct=pnl_pct,
        trades=trades,
        equity_curve=equity_curve,
        metriques=metriques,
    )
