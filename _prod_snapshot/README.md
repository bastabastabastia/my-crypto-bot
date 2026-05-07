# Snapshot prod — 2026-05-07

Copie textuelle des fichiers du serveur DigitalOcean (164.92.173.210)
au moment de la transposition pour le backtester.

Sert de référence figée. **Ne pas modifier** — c'est l'état de la prod
au moment où on a démarré l'évolution dans `bot/`.

| Fichier | Description |
|---|---|
| `paper_trading.py` | Orchestrateur cron (toutes les 15 min) |
| `crypto_indicateurs.py` | Indicateurs (RSI 14, MM20, MM50) + signaux |
| `strategie.py` | Stratégie "Hybride Prudente v1.0" |
| `portefeuille.py` | Gestion JSON du portefeuille virtuel |
