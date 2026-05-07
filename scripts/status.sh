#!/bin/bash
# Affiche un statut rapide du système Crypto Agent
# Usage : ssh root@164.92.173.210 'bash -s' < scripts/status.sh
# OU : copier-coller dans la session SSH

echo "============================================"
echo "  📊 ÉTAT DU CRYPTO AGENT"
echo "============================================"
echo ""
echo "🕒 $(date)"
echo ""
echo "--- 📔 PORTEFEUILLE ---"
cat /root/portefeuille.json 2>/dev/null || echo "❌ Fichier portefeuille.json introuvable"
echo ""
echo "--- 🚨 5 DERNIÈRES ALERTES ---"
grep "ALERTE" /root/crypto.log 2>/dev/null | tail -5 || echo "Aucune alerte récente"
echo ""
echo "--- 💰 5 DERNIERS TRADES ---"
grep "VENTE\|ACHAT" /root/paper.log 2>/dev/null | tail -5 || echo "Aucun trade récent"
echo ""
echo "--- ⏰ TÂCHES CRON ---"
crontab -l 2>/dev/null | grep -v "^#" | grep "."
echo ""
echo "--- 🔧 SERVICE CRON ---"
systemctl is-active cron
echo "============================================"
