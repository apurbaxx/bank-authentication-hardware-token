"""
database.py — SQLite helpers for BankGuard
All DB access goes through this module.
Hardware integration point: token_status table tracks ESP32 state.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "bankguard.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                avg_amount  REAL NOT NULL DEFAULT 2500,
                home_location TEXT NOT NULL DEFAULT 'Kolkata'
            );

            CREATE TABLE IF NOT EXISTS known_devices (
                user_id   TEXT NOT NULL,
                device_id TEXT NOT NULL,
                location  TEXT NOT NULL,
                PRIMARY KEY (user_id, device_id)
            );

            CREATE TABLE IF NOT EXISTS known_recipients (
                user_id       TEXT NOT NULL,
                recipient_upi TEXT NOT NULL,
                last_used     TEXT NOT NULL,
                PRIMARY KEY (user_id, recipient_upi)
            );

            CREATE TABLE IF NOT EXISTS flagged_recipients (
                recipient_upi TEXT PRIMARY KEY,
                reason        TEXT
            );

            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,
                user_id        TEXT NOT NULL,
                amount         REAL NOT NULL,
                recipient_upi  TEXT NOT NULL,
                device_id      TEXT NOT NULL,
                location       TEXT NOT NULL,
                hour           INTEGER NOT NULL,
                risk_score     REAL NOT NULL,
                decision       TEXT NOT NULL,
                status         TEXT NOT NULL DEFAULT 'pending',
                reason         TEXT,
                factors        TEXT,
                created_at     TEXT NOT NULL DEFAULT (datetime('now'))
            );

            -- Hardware integration: tracks ESP32 token state
            -- When hardware arrives, this table drives the polling endpoint
            CREATE TABLE IF NOT EXISTS token_status (
                id                 INTEGER PRIMARY KEY CHECK (id = 1),
                pending_txn_id     TEXT,
                hardware_connected INTEGER NOT NULL DEFAULT 0,
                last_seen          TEXT
            );

            INSERT OR IGNORE INTO token_status (id, pending_txn_id, hardware_connected)
            VALUES (1, NULL, 0);

            CREATE TABLE IF NOT EXISTS transaction_velocity (
                user_id    TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_velocity ON transaction_velocity(user_id, created_at);
        """)


# ── User helpers ─────────────────────────────────────────────────────────────

def get_user(user_id: str):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()


def get_known_devices(user_id: str):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT device_id, location FROM known_devices WHERE user_id=?", (user_id,)
        ).fetchall()
        return {r["device_id"]: r["location"] for r in rows}


def get_known_recipients(user_id: str):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT recipient_upi, last_used FROM known_recipients WHERE user_id=?", (user_id,)
        ).fetchall()
        return {r["recipient_upi"]: r["last_used"] for r in rows}


def is_flagged_recipient(recipient_upi: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM flagged_recipients WHERE recipient_upi=?", (recipient_upi,)
        ).fetchone()
        return row is not None


def get_velocity_count(user_id: str, minutes: int = 60) -> int:
    """Count transactions by user in the last `minutes` minutes."""
    with get_conn() as conn:
        row = conn.execute(
            """SELECT COUNT(*) as cnt FROM transaction_velocity
               WHERE user_id=? AND created_at >= datetime('now', ?)""",
            (user_id, f"-{minutes} minutes")
        ).fetchone()
        return row["cnt"] if row else 0


# ── Transaction helpers ───────────────────────────────────────────────────────

def save_transaction(txn: dict):
    import json
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO transactions
              (transaction_id, user_id, amount, recipient_upi, device_id, location,
               hour, risk_score, decision, status, reason, factors)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            txn["transaction_id"], txn["user_id"], txn["amount"],
            txn["recipient_upi"], txn["device_id"], txn["location"],
            txn["hour"], txn["risk_score"], txn["decision"],
            txn.get("status", "pending"), txn.get("reason"),
            json.dumps(txn.get("factors", {}))
        ))
        conn.execute(
            "INSERT INTO transaction_velocity (user_id, created_at) VALUES (?, datetime('now'))",
            (txn["user_id"],)
        )


def get_all_transactions():
    import json
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM transactions ORDER BY created_at DESC"
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["factors"] = json.loads(d["factors"] or "{}")
            result.append(d)
        return result


def get_transaction(txn_id: str):
    import json
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM transactions WHERE transaction_id=?", (txn_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["factors"] = json.loads(d["factors"] or "{}")
        return d


def update_transaction_status(txn_id: str, status: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE transactions SET status=? WHERE transaction_id=?",
            (status, txn_id)
        )


def get_dashboard_stats():
    with get_conn() as conn:
        row = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status='approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN status='rejected' THEN 1 ELSE 0 END) as blocked,
                SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status='otp_challenge' THEN 1 ELSE 0 END) as otp
            FROM transactions
        """).fetchone()
        return dict(row)


# ── Hardware token helpers ────────────────────────────────────────────────────
# These functions are the integration seam for the ESP32 hardware token.
# When hardware arrives, the ESP32 polls get_pending_token_txn() and
# calls set_token_response() after button press.

def set_pending_token_txn(txn_id: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE token_status SET pending_txn_id=? WHERE id=1", (txn_id,)
        )


def clear_pending_token_txn():
    with get_conn() as conn:
        conn.execute(
            "UPDATE token_status SET pending_txn_id=NULL WHERE id=1"
        )


def get_pending_token_txn():
    with get_conn() as conn:
        row = conn.execute(
            "SELECT pending_txn_id FROM token_status WHERE id=1"
        ).fetchone()
        return row["pending_txn_id"] if row else None


def mark_hardware_seen():
    """Called when ESP32 polls — marks it as online."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE token_status SET hardware_connected=1, last_seen=datetime('now') WHERE id=1"
        )


def get_token_status():
    with get_conn() as conn:
        return dict(conn.execute("SELECT * FROM token_status WHERE id=1").fetchone())
