# Contexte projet pour Claude Code

## Qu'est-ce que ce projet ?

Système de **trading crypto automatisé** tournant sur un serveur **DigitalOcean distant** (Ubuntu, IP `164.92.173.210`). Le code Python n'est PAS dans ce dossier local — il est sur le serveur. Ce dossier contient uniquement la documentation et des scripts d'aide pour interagir avec le serveur.

## Architecture

- **Serveur** : DigitalOcean Droplet, Ubuntu, accès SSH `root@164.92.173.210`
- **Bot 1 — Alertes** : `/root/crypto_alerte.py` → log dans `/root/crypto.log`
- **Bot 2 — Paper-trading** : `/root/paper_trading.py` → log dans `/root/paper.log`
- **État du portefeuille** : `/root/portefeuille.json` (cash, positions, historique)
- **Planification** : `cron` toutes les 15 minutes
- **Notifications** : Telegram (déjà configuré)
- **Dashboard web** : http://164.92.173.210:5000 (Flask, port 5000)
- **API LLM** : Anthropic (les bots appellent Claude pour analyser)

## Capital virtuel

- Total : **3000 USD**
- Réparti : 1000 USD par marché (3 marchés)

## Comment Claude Code peut aider

1. **Diagnostiquer un problème** : suggérer des commandes SSH à exécuter pour inspecter logs/cron/processus
2. **Améliorer les scripts d'aide** dans `scripts/`
3. **Rédiger** ou modifier la documentation (`MANUEL.md`, `COMMANDES.md`)
4. **Proposer du code** pour de nouveaux bots ou améliorations (à déployer ensuite manuellement sur le serveur)
5. **Analyser les logs** que l'utilisateur copie-colle ici

## Limites importantes

- Claude Code **n'a PAS d'accès direct au serveur** (pas de clé SSH configurée par défaut). L'utilisateur doit copier-coller les sorties depuis sa session SSH.
- Le code source des bots `crypto_alerte.py` et `paper_trading.py` n'est **pas dans ce dossier**. Si l'utilisateur veut le modifier, il doit soit le rapatrier via `scp`, soit le copier-coller ici.
- Toute modification faite localement doit être **redéployée manuellement** sur le serveur.

## Commandes serveur les plus utiles

```bash
ssh root@164.92.173.210         # Se connecter
cat portefeuille.json           # État portefeuille
tail -100 paper.log             # Activité récente
grep "ALERTE" crypto.log        # Alertes envoyées
crontab -l                      # Voir tâches planifiées
crontab -e                      # Éditer (pause avec #)
```

## Précautions

- **NE JAMAIS suggérer** `crontab -r` sans avertissement explicite (supprime tout sans confirmation).
- **NE JAMAIS suggérer** la destruction du Droplet sans confirmation (action définitive).
- Toujours rappeler que les bots **continuent de tourner** après `exit` du SSH.
