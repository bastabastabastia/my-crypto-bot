#!/usr/bin/env bash
# Déploie le dashboard sur le serveur DigitalOcean.
# Usage : ./deploy/deploy.sh [user@host]
#   défaut : root@164.92.173.210

set -euo pipefail

TARGET="${1:-root@164.92.173.210}"
REMOTE_DIR="/root/dashboard"

DASHBOARD_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "→ Cible : $TARGET:$REMOTE_DIR"
echo "→ Source : $DASHBOARD_DIR"

# 1) Synchroniser le code (sans data/, sans .venv)
rsync -avz --delete \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude 'data/historique_portefeuille.jsonl' \
    --exclude 'data/portefeuille.json' \
    --exclude 'data/paper.log' \
    --exclude 'data/crypto.log' \
    "$DASHBOARD_DIR/" "$TARGET:$REMOTE_DIR/"

# 2) Installer venv + dépendances + service
ssh "$TARGET" bash -se <<'REMOTE'
set -euo pipefail
cd /root/dashboard

# .env : créer s'il n'existe pas (tu devras éditer le mot de passe)
if [ ! -f .env ]; then
    cp deploy/env.example .env
    echo "⚠️  /root/dashboard/.env créé depuis env.example — édite-le pour changer le mot de passe."
fi

# venv + deps
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

# Unit systemd
cp deploy/crypto-dashboard.service /etc/systemd/system/crypto-dashboard.service
systemctl daemon-reload
systemctl enable crypto-dashboard.service
systemctl restart crypto-dashboard.service

sleep 1
systemctl --no-pager status crypto-dashboard.service | head -n 12
REMOTE

echo
echo "✅ Déploiement terminé."
echo "→ Dashboard : http://${TARGET#*@}:5000"
echo "→ Edite /root/dashboard/.env sur le serveur pour changer le mot de passe puis :"
echo "    ssh $TARGET 'systemctl restart crypto-dashboard'"
