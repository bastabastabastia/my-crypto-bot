"""
Gestion du portefeuille virtuel pour le paper-trading.

Sauvegarde l'etat dans portefeuille.json pour persistance.
"""

import json
import os
from datetime import datetime

FICHIER_PORTEFEUILLE = "portefeuille.json"
CAPITAL_INITIAL = 1000.0  # $


def charger_portefeuille():
    if not os.path.exists(FICHIER_PORTEFEUILLE):
        portefeuille = {
            "capital_initial": CAPITAL_INITIAL,
            "cash": CAPITAL_INITIAL,
            "positions": [],
            "historique": [],
            "date_creation": datetime.now().isoformat(),
        }
        sauver_portefeuille(portefeuille)
        return portefeuille

    with open(FICHIER_PORTEFEUILLE, "r", encoding="utf-8") as f:
        return json.load(f)


def sauver_portefeuille(portefeuille):
    with open(FICHIER_PORTEFEUILLE, "w", encoding="utf-8") as f:
        json.dump(portefeuille, f, indent=2, ensure_ascii=False)


def acheter(portefeuille, crypto, prix_actuel, montant_usd, raison=""):
    if portefeuille["cash"] < montant_usd:
        return False, f"Cash insuffisant ({portefeuille['cash']:.2f}$ < {montant_usd}$)"

    for pos in portefeuille["positions"]:
        if pos["crypto"] == crypto:
            return False, f"Position deja ouverte sur {crypto}"

    if len(portefeuille["positions"]) >= 3:
        return False, "Limite de 3 positions ouvertes atteinte"

    quantite = montant_usd / prix_actuel
    nouvelle_position = {
        "crypto": crypto,
        "quantite": quantite,
        "prix_achat": prix_actuel,
        "montant_invest": montant_usd,
        "date_achat": datetime.now().isoformat(),
        "raison_achat": raison,
    }

    portefeuille["positions"].append(nouvelle_position)
    portefeuille["cash"] -= montant_usd

    sauver_portefeuille(portefeuille)
    return True, f"ACHAT {crypto} : {quantite:.6f} @ {prix_actuel:.2f}$ ({montant_usd}$)"


def vendre(portefeuille, crypto, prix_actuel, raison=""):
    position = None
    for pos in portefeuille["positions"]:
        if pos["crypto"] == crypto:
            position = pos
            break

    if not position:
        return False, f"Aucune position ouverte sur {crypto}", 0

    valeur_actuelle = position["quantite"] * prix_actuel
    montant_invest = position["montant_invest"]
    gain_perte = valeur_actuelle - montant_invest
    pourcentage = (gain_perte / montant_invest) * 100

    trade_complete = {
        **position,
        "prix_vente": prix_actuel,
        "date_vente": datetime.now().isoformat(),
        "valeur_finale": valeur_actuelle,
        "gain_perte_usd": gain_perte,
        "gain_perte_pct": pourcentage,
        "raison_vente": raison,
    }
    portefeuille["historique"].append(trade_complete)

    portefeuille["positions"].remove(position)
    portefeuille["cash"] += valeur_actuelle

    sauver_portefeuille(portefeuille)

    icone = "+" if gain_perte >= 0 else ""
    return True, (
        f"VENTE {crypto} : {position['quantite']:.6f} @ {prix_actuel:.2f}$ | "
        f"P&L: {icone}{gain_perte:.2f}$ ({icone}{pourcentage:.2f}%)"
    ), gain_perte


def calculer_valeur_totale(portefeuille, prix_actuels):
    valeur = portefeuille["cash"]
    for pos in portefeuille["positions"]:
        if pos["crypto"] in prix_actuels:
            valeur += pos["quantite"] * prix_actuels[pos["crypto"]]
        else:
            valeur += pos["montant_invest"]
    return valeur


def afficher_portefeuille(portefeuille, prix_actuels=None):
    pass  # voir le fichier original sur le serveur pour la version complète
