"""Strategie de trading Hybride Prudente v1.0"""
from datetime import datetime, timezone

RSI_SURVENTE = 35
RSI_SURACHAT = 70
STOP_LOSS_PCT = -3.0
MAX_DUREE_HEURES = 4
MONTANT_PAR_TRADE = 200.0
MAX_POSITIONS = 3


def decider(crypto_data, position_ouverte=None, nb_positions=0, cash_dispo=0):
    if position_ouverte:
        return _vente(crypto_data, position_ouverte)
    return _achat(crypto_data, nb_positions, cash_dispo)


def _vente(d, p):
    prix = d["prix"]
    rsi = d["rsi"]
    var_pct = ((prix - p["prix_achat"]) / p["prix_achat"]) * 100

    if var_pct <= STOP_LOSS_PCT:
        return ("VENDRE", f"STOP-LOSS : {var_pct:+.2f}%", None)

    if rsi >= RSI_SURACHAT:
        return ("VENDRE", f"TAKE-PROFIT : RSI={rsi:.1f} | P&L: {var_pct:+.2f}%", None)

    da = datetime.fromisoformat(p["date_achat"])
    if da.tzinfo is None:
        da = da.replace(tzinfo=timezone.utc)
    h = (datetime.now(timezone.utc) - da).total_seconds() / 3600

    if h >= MAX_DUREE_HEURES:
        return ("VENDRE", f"DUREE MAX : {h:.1f}h | P&L: {var_pct:+.2f}%", None)

    return ("GARDER", f"P&L: {var_pct:+.2f}% | RSI: {rsi:.1f}", None)


def _achat(d, nb, cash):
    rsi = d["rsi"]
    prix = d["prix"]
    mm50 = d["mm50"]

    if nb >= MAX_POSITIONS:
        return ("ATTENDRE", f"Limite {MAX_POSITIONS} positions atteinte", None)
    if cash < MONTANT_PAR_TRADE:
        return ("ATTENDRE", f"Cash insuffisant ({cash:.2f}$)", None)
    if rsi >= RSI_SURVENTE:
        return ("ATTENDRE", f"Pas de survente : RSI={rsi:.1f}", None)
    if prix < mm50:
        return ("ATTENDRE", f"Prix sous MM50 : {prix:.2f} < {mm50:.2f}", None)

    return ("ACHETER", f"OK : RSI={rsi:.1f}, prix>MM50", MONTANT_PAR_TRADE)
