#!/bin/bash
# Affiche les logs récents du système
# À exécuter une fois connecté au serveur

echo "============================================"
echo "  📜 LOGS RÉCENTS"
echo "============================================"
echo ""
echo "--- 🚨 CRYPTO.LOG (50 dernières lignes) ---"
tail -50 /root/crypto.log 2>/dev/null || echo "❌ crypto.log introuvable"
echo ""
echo "--- 💼 PAPER.LOG (50 dernières lignes) ---"
tail -50 /root/paper.log 2>/dev/null || echo "❌ paper.log introuvable"
echo "============================================"
