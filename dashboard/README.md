# 📊 Dashboard Crypto Agent

Dashboard Flask qui affiche l'état du paper-trading et des alertes, en lecture
seule sur les fichiers `portefeuille.json`, `paper.log`, `crypto.log`.

## Lancer en local

```bash
cd dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Mot de passe pour l'auth basique HTTP
export DASHBOARD_PASSWORD=monpass

python3 app.py
# → http://127.0.0.1:5000  (admin / monpass)
```

Les fichiers d'exemple dans `data/` permettent de voir le dashboard avec des
données réalistes sans toucher à la prod.

## Variables d'environnement

| Variable | Défaut | Rôle |
|----------|--------|------|
| `DATA_DIR` | `./data` | Dossier où lire `portefeuille.json`, `paper.log`, `crypto.log` |
| `HISTORY_FILE` | `$DATA_DIR/historique_portefeuille.jsonl` | Fichier d'historique alimenté par le dashboard à chaque visite |
| `DASHBOARD_USER` | `admin` | Login HTTP basique |
| `DASHBOARD_PASSWORD` | `change-me` | Mot de passe HTTP basique — **change-le** |
| `HOST` | `0.0.0.0` | Interface d'écoute |
| `PORT` | `5000` | Port d'écoute |

## Déployer sur le serveur DigitalOcean

Une seule commande depuis ta machine :

```bash
./dashboard/deploy/deploy.sh
# ou avec un autre hôte :
./dashboard/deploy/deploy.sh root@164.92.173.210
```

Ce script :

1. `rsync` du dossier `dashboard/` vers `/root/dashboard/` sur le serveur (sans
   les fichiers de données — il lit ceux qui sont déjà dans `/root/`).
2. Crée un venv, installe les dépendances.
3. Copie l'unit systemd (`crypto-dashboard.service`) et active le service.
4. Crée `/root/dashboard/.env` depuis `env.example` si absent.

**Après le premier déploiement**, édite le mot de passe :

```bash
ssh root@164.92.173.210 'nano /root/dashboard/.env'
ssh root@164.92.173.210 'systemctl restart crypto-dashboard'
```

Puis ouvre <http://164.92.173.210:5000>.

## Logs et statut

```bash
ssh root@164.92.173.210 'systemctl status crypto-dashboard'
ssh root@164.92.173.210 'tail -f /root/dashboard.error.log'
```

## Points importants

- **Lecture seule** : le dashboard ne modifie jamais `portefeuille.json` ni les
  logs. Il maintient son propre fichier d'historique
  (`historique_portefeuille.jsonl`) qu'il alimente à chaque visite de la page.
- **Auth basique HTTP** : suffisante pour un usage perso. Pour plus de sécurité,
  tu peux à terme passer le service en `127.0.0.1:5000` et accéder via tunnel
  SSH (`ssh -L 5000:localhost:5000 root@...`).
- **Format `portefeuille.json`** : le parseur est tolérant sur les noms de
  champs (`cash`/`solde`, `quantite`/`qty`, `prix_achat`/`entry`, etc.). Si
  certains champs manquent dans ton vrai fichier, ouvre une issue ou édite
  `normalize_portfolio()` dans `app.py`.
