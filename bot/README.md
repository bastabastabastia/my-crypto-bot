# 🤖 Bot — Sprint 0 (fondations)

Module **séparé** du paper-trading en prod (qui tourne sur DigitalOcean via cron).
Permet de backtester, expérimenter et faire évoluer la stratégie sans toucher
à la prod tant qu'on n'est pas confiant.

## Démarrage rapide

```bash
# 1) Dépendances
pip install -r bot/requirements.txt

# 2) Télécharger 1 an de bougies 15 min depuis Binance (gratuit, sans clé)
python -m bot.cli download-data --jours 365

# 3) Lancer un backtest baseline (RSI < 30 → BUY, RSI > 70 → SELL)
python -m bot.cli backtest --strategy rsi_baseline

# 4) Lister les runs
python -m bot.cli list-runs

# 5) Voir le détail d'un run
python -m bot.cli show-run 1
```

Le dashboard expose un onglet **Backtest** qui affiche tout ça visuellement
(equity curve, trades, métriques) à <http://127.0.0.1:5000/backtest>.

## Architecture

```
bot/
├── config.py             # Constantes : marchés, capital, frais, slippage
├── db.py                 # Schéma SQLite (prix, runs, trades, equity, decisions)
├── datasource/
│   └── binance.py        # Téléchargement klines publiques Binance
├── indicators.py         # SMA, EMA, RSI, MACD, Bollinger, ATR
├── metrics.py            # Sharpe, Sortino, max DD, win rate, profit factor, CAGR
├── strategies/
│   ├── base.py           # ABC Strategy + dataclass Signal
│   └── rsi_baseline.py   # Référence : RSI 14, seuils 30/70
├── backtest.py           # Moteur (boucle bougies, exécution, frais, persistance)
└── cli.py                # `python -m bot.cli ...`
```

## Métriques implémentées

| Nom | Sens | Bon |
|-----|------|-----|
| **Sharpe** | rendement / volatilité globale | > 1 |
| **Sortino** | rendement / volatilité négative seulement | > 1.5 |
| **Max drawdown** | pire baisse depuis un sommet | > -25 % |
| **Win rate** | % de trades gagnants | > 50 % |
| **Profit factor** | somme(gains) / somme(pertes) | > 1.5 |
| **CAGR** | rendement annualisé composé | > 0 |

## Réalisme du backtest

- **Frais** : 0.1 % par trade (Binance spot maker/taker — proche de la réalité)
- **Slippage** : 0.05 % (achat plus cher, vente moins chère qu'au close affiché)
- **Pas de look-ahead** : la stratégie ne voit que les bougies fermées
- **Capital alloué par marché** : `CAPITAL_PAR_MARCHE` × N marchés

Variables d'environnement disponibles : `BOT_FRAIS_PCT`, `BOT_SLIPPAGE_PCT`,
`BOT_CAPITAL`, `BOT_CAPITAL_PAR_MARCHE`.

## Ajouter une stratégie

1. Crée `bot/strategies/ma_strategie.py` qui hérite de `Strategy` et implémente
   `decide(df, position_ouverte) -> Signal`.
2. Ajoute-la au registre dans `bot/strategies/__init__.py`.
3. Lance : `python -m bot.cli backtest --strategy ma_strategie`.

## Limites Sprint 0 — ce qui viendra

- Capital silos par marché → modèle global commun (pour matcher la prod)
- Stop-loss / take-profit dynamiques (Sprint 3)
- Stratégie multi-agent IA (Sprint 1)
- Walk-forward / cross-validation (Sprint 2)
