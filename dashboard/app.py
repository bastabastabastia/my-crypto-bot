import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request

app = Flask(__name__)

DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent / "data"))
HISTORY_FILE = Path(
    os.environ.get("HISTORY_FILE", DATA_DIR / "historique_portefeuille.jsonl")
)
PORTFOLIO_FILE = DATA_DIR / "portefeuille.json"
PAPER_LOG = DATA_DIR / "paper.log"
CRYPTO_LOG = DATA_DIR / "crypto.log"

DASHBOARD_USER = os.environ.get("DASHBOARD_USER", "admin")
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "change-me")

BOT_DB_PATH = Path(
    os.environ.get(
        "BOT_DB_PATH",
        Path(__file__).parent.parent / "bot" / "data" / "bot.sqlite3",
    )
)


def check_auth(username: str, password: str) -> bool:
    return username == DASHBOARD_USER and password == DASHBOARD_PASSWORD


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response(
                "Authentification requise.\n",
                401,
                {"WWW-Authenticate": 'Basic realm="Crypto Dashboard"'},
            )
        return f(*args, **kwargs)

    return decorated


def read_portfolio() -> dict:
    if not PORTFOLIO_FILE.exists():
        return {}
    try:
        return json.loads(PORTFOLIO_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def normalize_portfolio(raw: dict) -> dict:
    """Tolerant parser: handles a few plausible portefeuille.json shapes."""
    if not raw:
        return {
            "cash": 0.0,
            "capital_initial": 3000.0,
            "positions": [],
            "valeur_totale": 0.0,
            "pnl": 0.0,
            "pnl_pct": 0.0,
            "updated_at": None,
        }

    cash = float(raw.get("cash", raw.get("solde", raw.get("liquidites", 0.0))) or 0.0)
    capital_initial = float(
        raw.get("capital_initial", raw.get("initial", 3000.0)) or 3000.0
    )

    positions_raw = raw.get("positions", raw.get("ouvertures", []))
    if isinstance(positions_raw, dict):
        positions_raw = [{"marche": k, **v} for k, v in positions_raw.items()]

    positions = []
    valeur_positions = 0.0
    for p in positions_raw or []:
        marche = p.get("marche") or p.get("symbol") or p.get("paire") or "?"
        quantite = float(p.get("quantite", p.get("qty", p.get("amount", 0))) or 0)
        prix_achat = float(
            p.get("prix_achat", p.get("entry", p.get("buy_price", 0))) or 0
        )
        prix_actuel = float(
            p.get("prix_actuel", p.get("price", p.get("current", prix_achat))) or 0
        )
        valeur = quantite * prix_actuel
        cout = quantite * prix_achat
        pnl_pos = valeur - cout
        pnl_pct = (pnl_pos / cout * 100) if cout else 0.0
        positions.append(
            {
                "marche": marche,
                "quantite": quantite,
                "prix_achat": prix_achat,
                "prix_actuel": prix_actuel,
                "valeur": valeur,
                "pnl": pnl_pos,
                "pnl_pct": pnl_pct,
            }
        )
        valeur_positions += valeur

    valeur_totale = cash + valeur_positions
    pnl = valeur_totale - capital_initial
    pnl_pct = (pnl / capital_initial * 100) if capital_initial else 0.0

    return {
        "cash": cash,
        "capital_initial": capital_initial,
        "positions": positions,
        "valeur_positions": valeur_positions,
        "valeur_totale": valeur_totale,
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "updated_at": raw.get("updated_at") or raw.get("timestamp"),
    }


TRADE_RE = re.compile(
    r"(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})?.*?(?P<action>ACHAT|VENTE)\s*"
    r"(?P<marche>[A-Z0-9/_-]+)?.*?(?:qty[=: ]?(?P<qty>[\d.]+))?.*?"
    r"(?:(?:prix|price)[=: ]?(?P<prix>[\d.]+))?",
    re.IGNORECASE,
)


def tail_lines(path: Path, n: int) -> list[str]:
    if not path.exists():
        return []
    try:
        with path.open("rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            chunk = min(size, max(n * 200, 4096))
            f.seek(size - chunk)
            data = f.read().decode("utf-8", errors="replace")
        return data.splitlines()[-n:]
    except OSError:
        return []


def parse_trades(limit: int = 25) -> list[dict]:
    trades = []
    for line in tail_lines(PAPER_LOG, 500):
        if "ACHAT" not in line.upper() and "VENTE" not in line.upper():
            continue
        m = TRADE_RE.search(line)
        if not m:
            continue
        trades.append(
            {
                "ts": m.group("ts") or "",
                "action": (m.group("action") or "").upper(),
                "marche": m.group("marche") or "",
                "quantite": m.group("qty") or "",
                "prix": m.group("prix") or "",
                "raw": line.strip(),
            }
        )
    return list(reversed(trades))[:limit]


ALERT_RE = re.compile(r"\[ALERTE\]|\bALERTE\b(?!S)", re.IGNORECASE)


def parse_alerts(limit: int = 20) -> list[dict]:
    alerts = []
    for line in tail_lines(CRYPTO_LOG, 500):
        if not ALERT_RE.search(line):
            continue
        ts_match = re.match(r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})", line)
        alerts.append(
            {
                "ts": ts_match.group(1) if ts_match else "",
                "message": line.strip(),
            }
        )
    return list(reversed(alerts))[:limit]


def append_history(snapshot: dict) -> None:
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "valeur_totale": snapshot["valeur_totale"],
            "cash": snapshot["cash"],
            "pnl": snapshot["pnl"],
        }
        with HISTORY_FILE.open("a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def read_history(limit: int = 500) -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        lines = HISTORY_FILE.read_text().strip().splitlines()
    except OSError:
        return []
    out = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def system_status() -> dict:
    def file_info(p: Path) -> dict:
        if not p.exists():
            return {"exists": False}
        st = p.stat()
        return {
            "exists": True,
            "size_kb": round(st.st_size / 1024, 1),
            "mtime": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(
                timespec="seconds"
            ),
        }

    return {
        "data_dir": str(DATA_DIR),
        "portefeuille": file_info(PORTFOLIO_FILE),
        "paper_log": file_info(PAPER_LOG),
        "crypto_log": file_info(CRYPTO_LOG),
        "history": file_info(HISTORY_FILE),
        "now": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


@app.route("/")
@requires_auth
def index():
    snapshot = normalize_portfolio(read_portfolio())
    append_history(snapshot)
    return render_template(
        "index.html",
        snapshot=snapshot,
        trades=parse_trades(),
        alerts=parse_alerts(),
        status=system_status(),
    )


@app.route("/api/snapshot")
@requires_auth
def api_snapshot():
    snapshot = normalize_portfolio(read_portfolio())
    return jsonify(
        {
            "snapshot": snapshot,
            "history": read_history(),
            "trades": parse_trades(),
            "alerts": parse_alerts(),
            "status": system_status(),
        }
    )


def _bot_db_query(sql: str, params: tuple = ()) -> list[dict]:
    if not BOT_DB_PATH.exists():
        return []
    conn = sqlite3.connect(BOT_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


@app.route("/backtest")
@requires_auth
def backtest_index():
    runs = _bot_db_query(
        """SELECT id, started_at, strategy, marches_json, intervalle, debut, fin,
                  capital_initial, capital_final, pnl_pct, sharpe, sortino,
                  max_drawdown, win_rate, nb_trades, cagr
           FROM backtest_runs ORDER BY id DESC LIMIT 50"""
    )
    for r in runs:
        try:
            r["marches"] = json.loads(r["marches_json"])
        except (json.JSONDecodeError, TypeError):
            r["marches"] = []
    return render_template("backtest.html", runs=runs, status=system_status())


@app.route("/backtest/<int:run_id>")
@requires_auth
def backtest_detail(run_id: int):
    runs = _bot_db_query("SELECT * FROM backtest_runs WHERE id=?", (run_id,))
    if not runs:
        return f"Run #{run_id} introuvable", 404
    run = runs[0]
    try:
        run["marches"] = json.loads(run["marches_json"])
        run["params"] = json.loads(run["params_json"] or "{}")
    except json.JSONDecodeError:
        run["marches"], run["params"] = [], {}

    trades = _bot_db_query(
        "SELECT * FROM backtest_trades WHERE run_id=? ORDER BY ts LIMIT 200",
        (run_id,),
    )
    return render_template("backtest_detail.html", run=run, trades=trades, status=system_status())


@app.route("/api/backtest/<int:run_id>/equity")
@requires_auth
def api_backtest_equity(run_id: int):
    rows = _bot_db_query(
        "SELECT ts, equity, cash FROM backtest_equity WHERE run_id=? ORDER BY ts",
        (run_id,),
    )
    return jsonify(rows)


@app.route("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    app.run(host=host, port=port, debug=False)
