# ⚡ Aide-mémoire — Commandes essentielles

## 🟢 Quotidien (à utiliser souvent)

```bash
ssh root@164.92.173.210         # Connexion au serveur
cat portefeuille.json           # État du portefeuille
tail -100 paper.log             # Derniers cycles de trading
tail -f paper.log               # Suivi en direct (Ctrl+C pour quitter)
exit                            # Quitter le serveur
```

## 🟡 Vérifications hebdomadaires

```bash
crontab -l                      # Vérifier les tâches planifiées
systemctl status cron           # Vérifier que cron tourne
grep "ALERTE" crypto.log        # Toutes les alertes envoyées
grep "VENTE\|ACHAT" paper.log   # Tous les trades exécutés
```

## 🔴 Actions d'administration (avec précaution)

```bash
crontab -e                      # Éditer les tâches (pause avec #)
python3 paper_trading.py        # Forcer un cycle manuel
python3 crypto_alerte.py        # Forcer une analyse manuelle
crontab -r                      # ⚠️ Supprime TOUT
```

## 🌐 URLs importantes

| Quoi | URL |
|------|-----|
| Dashboard | http://164.92.173.210:5000 |
| Coûts Anthropic | https://console.anthropic.com |
| Coûts DigitalOcean | https://cloud.digitalocean.com |

## 💡 Combo utile : statut complet en une fois

Une fois connecté au serveur :

```bash
echo "=== PORTEFEUILLE ===" && cat portefeuille.json && \
echo "=== DERNIÈRES ALERTES ===" && grep "ALERTE" crypto.log | tail -5 && \
echo "=== DERNIERS TRADES ===" && grep "VENTE\|ACHAT" paper.log | tail -5
```
