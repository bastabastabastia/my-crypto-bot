# 📚 Manuel utilisateur — Crypto Agent

Tout ce que vous devez savoir pour vivre avec votre système au quotidien.

---

## 🔌 Se reconnecter au serveur

Depuis votre PC :

```bash
ssh root@164.92.173.210
```

Vous reverrez le prompt `root@ubuntu-...:~#`.

---

## 📊 Voir les logs

| Commande | Ce que ça fait |
|----------|----------------|
| `cat crypto.log` | Tout le log de l'agent d'alertes (peut être long) |
| `cat paper.log` | Tout le log du paper-trading |
| `tail -50 crypto.log` | Les 50 dernières lignes des alertes |
| `tail -50 paper.log` | Les 50 dernières lignes du paper-trading |
| `tail -100 paper.log` | Les 100 dernières lignes (utile pour voir la journée) |
| `tail -f crypto.log` | Suivi en direct (Ctrl+C pour quitter) |
| `tail -f paper.log` | Suivi en direct du paper-trading |

---

## 📔 État du portefeuille virtuel

```bash
cat portefeuille.json
```

→ Affiche cash, positions ouvertes, historique. C'est votre comptabilité virtuelle.

---

## 🔍 Filtres utiles

```bash
grep "ALERTE" crypto.log              # Voir uniquement les alertes envoyées
grep "VENTE\|ACHAT" paper.log         # Voir uniquement les trades exécutés
```

---

## 📅 Vérifier que cron tourne

```bash
crontab -l                # Liste vos tâches planifiées
systemctl status cron     # Vérifie que le service est actif (active running en vert)
```

---

## ⏸️ Mettre un bot EN PAUSE

```bash
crontab -e
```

Trouvez la ligne du bot, ajoutez `#` au début pour la commenter :

```
#*/15 * * * * cd /root && /usr/bin/python3 /root/crypto_alerte.py >> /root/crypto.log 2>&1
```

Sauvegardez : `Ctrl+O` → `Entrée` → `Ctrl+X`.

## ▶️ Réactiver un bot

`crontab -e`, enlevez le `#`, sauvegardez.

## 🛑 Tout arrêter (effacer toutes les tâches)

```bash
crontab -r
```

⚠️ Supprime **toutes** les tâches cron sans confirmation.

---

## 🔄 Forcer un cycle manuellement (debug)

```bash
cd /root
python3 paper_trading.py     # Cycle de paper-trading
python3 crypto_alerte.py     # Cycle d'alertes
```

---

## 💰 Suivre les coûts

- **Anthropic** : https://console.anthropic.com → Usage
- **DigitalOcean** : https://cloud.digitalocean.com → avatar → Billing (crédit restant ~205$)

---

## 🚪 Quitter le serveur

```bash
exit
```

Vous revenez sur votre PC. **Les bots continuent de tourner** sur le serveur.

---

## 💥 Détruire complètement le serveur

https://cloud.digitalocean.com/droplets → cliquez sur votre serveur → **Destroy** (en bas).

⚠️ **Action définitive** : votre agent disparaît à jamais. À ne faire que si vous voulez vraiment tout arrêter.

---

## 🎯 Routine recommandée

**Tous les jours**, en vous reconnectant :

```bash
ssh root@164.92.173.210
cat portefeuille.json        # État du portefeuille
tail -100 paper.log          # Activité récente
grep "ALERTE" crypto.log | tail -20   # Dernières alertes
exit
```

**Une fois par semaine** : vérifier les coûts Anthropic et DigitalOcean.
