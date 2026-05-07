"""Schéma SQLite + helpers de connexion."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS prix (
    marche      TEXT NOT NULL,
    intervalle  TEXT NOT NULL,
    open_time   INTEGER NOT NULL,
    open        REAL NOT NULL,
    high        REAL NOT NULL,
    low         REAL NOT NULL,
    close       REAL NOT NULL,
    volume      REAL NOT NULL,
    close_time  INTEGER NOT NULL,
    PRIMARY KEY (marche, intervalle, open_time)
);

CREATE INDEX IF NOT EXISTS idx_prix_marche_time
    ON prix (marche, intervalle, open_time);

CREATE TABLE IF NOT EXISTS backtest_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at      TEXT NOT NULL,
    finished_at     TEXT,
    strategy        TEXT NOT NULL,
    params_json     TEXT,
    marches_json    TEXT NOT NULL,
    intervalle      TEXT NOT NULL,
    debut           TEXT NOT NULL,
    fin             TEXT NOT NULL,
    capital_initial REAL NOT NULL,
    capital_final   REAL,
    pnl_pct         REAL,
    sharpe          REAL,
    sortino         REAL,
    max_drawdown    REAL,
    win_rate        REAL,
    nb_trades       INTEGER,
    cagr            REAL,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS backtest_trades (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      INTEGER NOT NULL,
    ts          INTEGER NOT NULL,
    marche      TEXT NOT NULL,
    action      TEXT NOT NULL CHECK(action IN ('ACHAT','VENTE')),
    quantite    REAL NOT NULL,
    prix        REAL NOT NULL,
    frais       REAL NOT NULL,
    pnl         REAL,
    raison      TEXT,
    FOREIGN KEY (run_id) REFERENCES backtest_runs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_bt_trades_run ON backtest_trades (run_id);

CREATE TABLE IF NOT EXISTS backtest_equity (
    run_id      INTEGER NOT NULL,
    ts          INTEGER NOT NULL,
    equity      REAL NOT NULL,
    cash        REAL NOT NULL,
    PRIMARY KEY (run_id, ts),
    FOREIGN KEY (run_id) REFERENCES backtest_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS decisions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          INTEGER NOT NULL,
    marche      TEXT NOT NULL,
    agent       TEXT NOT NULL,
    decision    TEXT NOT NULL,
    raisonnement TEXT,
    contexte_json TEXT,
    run_id      INTEGER,
    FOREIGN KEY (run_id) REFERENCES backtest_runs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_decisions_run ON decisions (run_id);
"""


@contextmanager
def connect(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Connexion SQLite avec foreign keys + row factory dict-like."""
    db = path or DB_PATH
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(path: Path | None = None) -> None:
    """Crée toutes les tables si elles n'existent pas."""
    with connect(path) as conn:
        conn.executescript(SCHEMA)


if __name__ == "__main__":
    init_db()
    print(f"DB initialisée : {DB_PATH}")
