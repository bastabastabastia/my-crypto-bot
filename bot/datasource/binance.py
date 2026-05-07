"""Téléchargement de bougies Binance (klines publiques, sans clé API).

Endpoint : https://api.binance.com/api/v3/klines
Doc : https://github.com/binance/binance-spec-api-docs/blob/master/rest-api.md#klinecandlestick-data
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Iterable

import requests

from ..config import MARKETS
from ..db import connect, init_db

BINANCE_API = "https://api.binance.com/api/v3/klines"
MAX_LIMIT = 1000  # bougies max par appel

INTERVAL_MS = {
    "1m": 60_000,
    "5m": 5 * 60_000,
    "15m": 15 * 60_000,
    "30m": 30 * 60_000,
    "1h": 60 * 60_000,
    "4h": 4 * 60 * 60_000,
    "1d": 24 * 60 * 60_000,
}


def _fetch_chunk(
    symbol: str, interval: str, start_ms: int, end_ms: int
) -> list[list]:
    """Un appel REST Binance, jusqu'à 1000 bougies."""
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_ms,
        "endTime": end_ms,
        "limit": MAX_LIMIT,
    }
    r = requests.get(BINANCE_API, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def fetch_klines(
    symbol: str, interval: str, days: int
) -> Iterable[tuple]:
    """Yield (open_time, open, high, low, close, volume, close_time) sur `days` jours."""
    if interval not in INTERVAL_MS:
        raise ValueError(f"Intervalle non supporté : {interval}")
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - days * 24 * 3_600_000

    cursor = start_ms
    step = INTERVAL_MS[interval] * MAX_LIMIT
    while cursor < end_ms:
        chunk_end = min(cursor + step, end_ms)
        data = _fetch_chunk(symbol, interval, cursor, chunk_end)
        if not data:
            cursor = chunk_end
            continue
        for k in data:
            yield (
                int(k[0]),       # open_time (ms)
                float(k[1]),     # open
                float(k[2]),     # high
                float(k[3]),     # low
                float(k[4]),     # close
                float(k[5]),     # volume
                int(k[6]),       # close_time
            )
        # repartir juste après la dernière bougie reçue
        last_close = int(data[-1][6])
        cursor = last_close + 1
        # politesse rate-limit
        time.sleep(0.1)


def download_market(market_alias: str, interval: str, days: int) -> int:
    """Télécharge un marché et l'insère dans SQLite. Renvoie le nb de lignes insérées."""
    if market_alias not in MARKETS:
        raise ValueError(f"Marché inconnu : {market_alias} (connus : {list(MARKETS)})")
    symbol = MARKETS[market_alias]
    init_db()
    n_inserted = 0
    rows: list[tuple] = []
    for kline in fetch_klines(symbol, interval, days):
        rows.append(
            (market_alias, interval, kline[0], kline[1], kline[2], kline[3],
             kline[4], kline[5], kline[6])
        )
        if len(rows) >= 500:
            n_inserted += _insert_rows(rows)
            rows.clear()
    if rows:
        n_inserted += _insert_rows(rows)
    return n_inserted


def _insert_rows(rows: list[tuple]) -> int:
    with connect() as conn:
        before = conn.execute("SELECT COUNT(*) FROM prix").fetchone()[0]
        conn.executemany(
            """INSERT OR IGNORE INTO prix
               (marche, intervalle, open_time, open, high, low, close, volume, close_time)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            rows,
        )
        after = conn.execute("SELECT COUNT(*) FROM prix").fetchone()[0]
    return after - before


def latest_price(market_alias: str, interval: str) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            """SELECT open_time, close FROM prix
               WHERE marche=? AND intervalle=? ORDER BY open_time DESC LIMIT 1""",
            (market_alias, interval),
        ).fetchone()
    if not row:
        return None
    return {
        "open_time": row["open_time"],
        "ts": datetime.fromtimestamp(row["open_time"] / 1000, tz=timezone.utc).isoformat(),
        "close": row["close"],
    }
