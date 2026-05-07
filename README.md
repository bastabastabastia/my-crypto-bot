# 🤖 Crypto Agent — Système de trading automatisé

Système de surveillance crypto et paper-trading automatisé tournant sur un serveur DigitalOcean.

## 🎯 Vue d'ensemble

Deux bots Python tournent en parallèle via **cron** (toutes les 15 minutes) :

| Bot | Fichier | Log | Rôle |
|-----|---------|-----|------|
| Alertes | `crypto_alerte.py` | `crypto.log` | Surveille les marchés et envoie des alertes Telegram |
| Paper-trading | `paper_trading.py` | `paper.log` | Simule des trades sur 3000$ virtuels |

## 🔗 Accès rapides

- **Serveur SSH** : `ssh root@164.92.173.210`
- **Dashboard web** : http://164.92.173.210:5000
- **Telegram** : bot configuré (notifications automatiques)
- **Console Anthropic** : https://console.anthropic.com → Usage
- **DigitalOcean** : https://cloud.digitalocean.com → Billing

## 💼 Capital virtuel

- **Total** : 3000$
- **Répartition** : 1000$ par marché
- **État en temps réel** : `cat portefeuille.json` sur le serveur

## 📁 Structure du dossier

```
crypto-agent/
├── README.md              # Ce fichier
├── MANUEL.md              # Manuel utilisateur complet
├── COMMANDES.md           # Aide-mémoire des commandes
├── scripts/
│   ├── connect.sh         # Se connecter au serveur
│   ├── status.sh          # Voir l'état rapide du système
│   └── logs.sh            # Voir les logs récents
└── notes/
    └── journal.md         # Journal de bord (à remplir)
```

## 🚀 Démarrage rapide

1. Pour se connecter au serveur : `bash scripts/connect.sh`
2. Pour vérifier l'état : voir `COMMANDES.md`
3. Pour comprendre le système : lire `MANUEL.md`
