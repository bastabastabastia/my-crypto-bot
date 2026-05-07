"""CLI : python -m bot.cli {download-data, backtest, list-runs, show-run}."""

from __future__ import annotations

import argparse
import json
import sys

from .config import (
    CAPITAL_INITIAL,
    CAPITAL_PAR_MARCHE,
    DEFAULT_HISTORY_DAYS,
    DEFAULT_INTERVAL,
    MARKETS,
)
from .datasource.binance import download_market, latest_price
from .db import connect, init_db


def cmd_download_data(args: argparse.Namespace) -> int:
    init_db()
    marches = args.marches or list(MARKETS.keys())
    interval = args.intervalle
    days = args.jours
    print(f"→ Téléchargement {marches} en {interval} sur {days} jours…")
    for m in marches:
        print(f"  · {m} ({MARKETS[m]}) … ", end="", flush=True)
        n = download_market(m, interval, days)
        last = latest_price(m, interval)
        print(f"+{n} bougies. Dernière : {last['ts']} @ {last['close']:.2f}" if last else f"+{n}")
    return 0


def cmd_backtest(args: argparse.Namespace) -> int:
    from .strategies import REGISTRY
    from .backtest import run as run_backtest

    if args.strategy not in REGISTRY:
        print(f"Stratégie inconnue : {args.strategy}. Disponibles : {list(REGISTRY)}")
        return 2
    strategy_cls = REGISTRY[args.strategy]
    params: dict = {}
    if args.params:
        try:
            params = json.loads(args.params)
        except json.JSONDecodeError:
            print("--params doit être un JSON valide.")
            return 2
    strategy = strategy_cls(**params)

    marches = args.marches or list(MARKETS.keys())

    print(f"→ Backtest {strategy.name}({params}) sur {marches} en {args.intervalle}…")
    result = run_backtest(
        strategy=strategy,
        marches=marches,
        intervalle=args.intervalle,
        capital_initial=args.capital,
        capital_par_marche=args.plafond_position,
    )
    print(f"\n=== Run #{result.run_id} ===")
    print(f"Période       : {result.debut} → {result.fin}")
    print(f"Capital init. : {result.capital_initial:.2f} $")
    print(f"Capital final : {result.capital_final:.2f} $")
    print(f"P&L           : {result.pnl_pct:+.2f} %")
    print(f"Sharpe        : {result.metriques['sharpe']:.2f}")
    print(f"Sortino       : {result.metriques['sortino']:.2f}")
    print(f"Max DD        : {result.metriques['max_drawdown']*100:.2f} %")
    print(f"Win rate      : {result.metriques['win_rate']*100:.1f} %")
    print(f"Profit factor : {result.metriques['profit_factor']:.2f}")
    print(f"Nb trades     : {result.metriques['nb_trades']}")
    print(f"CAGR          : {result.metriques['cagr']*100:.2f} %")
    return 0


def cmd_list_runs(args: argparse.Namespace) -> int:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """SELECT id, strategy, marches_json, intervalle, debut, fin,
                      capital_initial, capital_final, pnl_pct, sharpe,
                      max_drawdown, win_rate, nb_trades
               FROM backtest_runs
               ORDER BY id DESC
               LIMIT ?""",
            (args.limit,),
        ).fetchall()
    if not rows:
        print("Aucun run.")
        return 0
    print(f"{'ID':>3}  {'Strat':<18} {'Marchés':<22} {'P&L %':>8} "
          f"{'Sharpe':>7} {'MDD %':>7} {'WR %':>6} {'Trades':>7}")
    for r in rows:
        marches = ",".join(json.loads(r["marches_json"]))
        print(
            f"{r['id']:>3}  {r['strategy']:<18} {marches:<22} "
            f"{r['pnl_pct']:>+8.2f} {r['sharpe']:>7.2f} "
            f"{r['max_drawdown']*100:>7.2f} {r['win_rate']*100:>6.1f} "
            f"{r['nb_trades']:>7}"
        )
    return 0


def cmd_show_run(args: argparse.Namespace) -> int:
    with connect() as conn:
        run = conn.execute("SELECT * FROM backtest_runs WHERE id=?", (args.run_id,)).fetchone()
        if not run:
            print(f"Run #{args.run_id} introuvable.")
            return 1
        trades = conn.execute(
            "SELECT * FROM backtest_trades WHERE run_id=? ORDER BY ts",
            (args.run_id,),
        ).fetchall()
    print(f"=== Run #{run['id']} ({run['strategy']}) ===")
    print(json.dumps(dict(run), indent=2, default=str))
    print(f"\n{len(trades)} trades :")
    for t in trades[: args.max_trades]:
        pnl = f"{t['pnl']:+.2f}" if t['pnl'] is not None else "—"
        print(f"  {t['ts']} {t['action']:<5} {t['marche']:<5} "
              f"qty={t['quantite']:.6f} prix={t['prix']:.2f} pnl={pnl}  ({t['raison']})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bot", description="Crypto bot CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_dl = sub.add_parser("download-data", help="Télécharger les bougies depuis Binance")
    p_dl.add_argument("--marches", nargs="*", choices=list(MARKETS.keys()))
    p_dl.add_argument("--intervalle", default=DEFAULT_INTERVAL)
    p_dl.add_argument("--jours", type=int, default=DEFAULT_HISTORY_DAYS)
    p_dl.set_defaults(func=cmd_download_data)

    p_bt = sub.add_parser("backtest", help="Lancer un backtest")
    p_bt.add_argument("--strategy", default="rsi_baseline")
    p_bt.add_argument("--params", help='JSON, ex: \'{"window":21}\'')
    p_bt.add_argument("--marches", nargs="*", choices=list(MARKETS.keys()))
    p_bt.add_argument("--intervalle", default=DEFAULT_INTERVAL)
    p_bt.add_argument("--capital", type=float, default=CAPITAL_INITIAL,
                      help="Capital initial GLOBAL (cash partagé entre marchés)")
    p_bt.add_argument("--plafond-position", type=float, default=None,
                      help="Taille max d'une position (par défaut : capital / nb_marchés)")
    p_bt.set_defaults(func=cmd_backtest)

    p_list = sub.add_parser("list-runs", help="Lister les runs précédents")
    p_list.add_argument("--limit", type=int, default=20)
    p_list.set_defaults(func=cmd_list_runs)

    p_show = sub.add_parser("show-run", help="Détail d'un run")
    p_show.add_argument("run_id", type=int)
    p_show.add_argument("--max-trades", type=int, default=50)
    p_show.set_defaults(func=cmd_show_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
