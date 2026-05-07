"""Paper-trading orchestrateur."""

import os
import requests
from datetime import datetime

from crypto_indicateurs import analyser_crypto
from portefeuille import (
    charger_portefeuille,
    acheter,
    vendre,
    calculer_valeur_totale,
    afficher_portefeuille,
)
from strategie import decider


CRYPTOS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]


def charger_env(fichier=".env"):
    if not os.path.exists(fichier):
        return
    with open(fichier, "r", encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#"):
                continue
            if "=" in ligne:
                cle, _, val = ligne.partition("=")
                os.environ[cle.strip()] = val.strip()


charger_env()
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID")


def envoyer_telegram(message):
    if not TG_TOKEN or not TG_CHAT:
        return False
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": TG_CHAT, "text": message}, timeout=10)
        return r.json().get("ok", False)
    except Exception:
        return False


def trouver_position(portefeuille, crypto):
    for p in portefeuille["positions"]:
        if p["crypto"] == crypto:
            return p
    return None


def cycle_trading():
    print(f"\n{'=' * 60}")
    print(f"  CYCLE TRADING - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'=' * 60}\n")

    portefeuille = charger_portefeuille()
    actions_executees = []
    prix_actuels = {}

    for crypto in CRYPTOS:
        try:
            data = analyser_crypto(crypto)
            prix_actuels[crypto] = data["prix"]
            position = trouver_position(portefeuille, crypto)

            action, raison, montant = decider(
                data,
                position_ouverte=position,
                nb_positions=len(portefeuille["positions"]),
                cash_dispo=portefeuille["cash"],
            )

            print(f"  {crypto:8} @ {data['prix']:>10.2f}$ | {action:9} | {raison}")

            if action == "ACHETER":
                ok, msg = acheter(portefeuille, crypto, data["prix"], montant, raison=raison)
                if ok:
                    print(f"           >>> {msg}")
                    actions_executees.append(("ACHAT", crypto, msg))

            elif action == "VENDRE":
                ok, msg, gain = vendre(portefeuille, crypto, data["prix"], raison=raison)
                if ok:
                    print(f"           >>> {msg}")
                    actions_executees.append(("VENTE", crypto, msg))

        except Exception as e:
            print(f"  {crypto}: erreur ({e})")
    afficher_portefeuille(portefeuille, prix_actuels=prix_actuels)

    if actions_executees:
        valeur_totale = calculer_valeur_totale(portefeuille, prix_actuels)
        gain_total = valeur_totale - portefeuille["capital_initial"]
        pct_total = (gain_total / portefeuille["capital_initial"]) * 100
        signe = "+" if gain_total >= 0 else ""

        message = "PAPER-TRADING\n\n"
        for type_action, crypto, msg in actions_executees:
            icone = "[ACHAT]" if type_action == "ACHAT" else "[VENTE]"
            message += f"{icone} {msg}\n\n"

        message += f"Valeur totale: {valeur_totale:.2f}$ ({signe}{gain_total:.2f}$ / {signe}{pct_total:.2f}%)\n"
        message += f"Cash: {portefeuille['cash']:.2f}$"

        envoyer_telegram(message)
        print(f"\n  >>> Notification Telegram envoyee ({len(actions_executees)} action(s))")
    else:
        print(f"\n  Aucune action ce cycle")


if __name__ == "__main__":
    cycle_trading()
