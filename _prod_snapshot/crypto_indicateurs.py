import requests
import pandas as pd
from datetime import datetime


def get_historique(symbole, intervalle="15m", limite=100):
    """
    Recupere l'historique des prix d'une crypto.

    intervalle : '1m', '5m', '15m', '1h', '4h', '1d'
    limite     : nombre de bougies a recuperer (max 1000)
    """
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbole,
        "interval": intervalle,
        "limit": limite,
    }
    response = requests.get(url, params=params, timeout=10)
    data = response.json()

    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_base", "taker_quote", "ignore"
    ])

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col])

    df["date"] = pd.to_datetime(df["open_time"], unit="ms")

    return df[["date", "open", "high", "low", "close", "volume"]]


def calculer_rsi(df, periode=14):
    """Calcule le RSI - mesure de surachat (>70) ou survente (<30)."""
    variation = df["close"].diff()
    gains = variation.where(variation > 0, 0)
    pertes = -variation.where(variation < 0, 0)

    moy_gains = gains.rolling(window=periode).mean()
    moy_pertes = pertes.rolling(window=periode).mean()

    rs = moy_gains / moy_pertes
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculer_moyennes_mobiles(df):
    """Calcule les moyennes mobiles 20 et 50."""
    df["mm20"] = df["close"].rolling(window=20).mean()
    df["mm50"] = df["close"].rolling(window=50).mean()
    return df


def analyser_crypto(symbole):
    """Fait une analyse complete d'une crypto."""
    df = get_historique(symbole, intervalle="15m", limite=100)
    df["rsi"] = calculer_rsi(df)
    df = calculer_moyennes_mobiles(df)

    derniere = df.iloc[-1]
    avant_derniere = df.iloc[-2]
    variation_pct = ((derniere["close"] - avant_derniere["close"]) / avant_derniere["close"]) * 100

    signaux = []
    if derniere["rsi"] < 30:
        signaux.append(f"[RSI={derniere['rsi']:.1f}] SURVENTE - Possible rebond")
    elif derniere["rsi"] > 70:
        signaux.append(f"[RSI={derniere['rsi']:.1f}] SURACHAT - Possible repli")

    if avant_derniere["mm20"] < avant_derniere["mm50"] and derniere["mm20"] > derniere["mm50"]:
        signaux.append("[CROISEMENT] MM20 passe AU-DESSUS de MM50 - Signal HAUSSIER")
    elif avant_derniere["mm20"] > avant_derniere["mm50"] and derniere["mm20"] < derniere["mm50"]:
        signaux.append("[CROISEMENT] MM20 passe EN DESSOUS de MM50 - Signal BAISSIER")

    if abs(variation_pct) > 2:
        direction = "HAUSSE" if variation_pct > 0 else "BAISSE"
        signaux.append(f"[MOMENTUM] {direction} rapide de {variation_pct:+.2f}% en 15min")

    return {
        "symbole": symbole,
        "prix": derniere["close"],
        "rsi": derniere["rsi"],
        "mm20": derniere["mm20"],
        "mm50": derniere["mm50"],
        "variation_15min_pct": variation_pct,
        "signaux": signaux,
    }
