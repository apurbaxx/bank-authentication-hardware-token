"""
seed_data.py — Populate demo data for BankGuard
Run once before first demo: python seed_data.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, get_conn
from datetime import datetime, timedelta
import random
import json
import uuid

def seed():
    init_db()
    with get_conn() as conn:
        # ── Users ────────────────────────────────────────────────────────────
        conn.execute("DELETE FROM users")
        conn.execute("DELETE FROM known_devices")
        conn.execute("DELETE FROM known_recipients")
        conn.execute("DELETE FROM flagged_recipients")
        conn.execute("DELETE FROM transactions")
        conn.execute("DELETE FROM transaction_velocity")

        users = [
            ("user_001", "Arjun Sharma",   2500.0, "Kolkata"),
            ("user_002", "Priya Mehta",    8000.0, "Mumbai"),
            ("user_003", "Rahul Verma",    1200.0, "Delhi"),
        ]
        conn.executemany("INSERT INTO users VALUES (?,?,?,?)", users)

        # ── Known devices ────────────────────────────────────────────────────
        devices = [
            ("user_001", "device_abc",   "Kolkata"),
            ("user_001", "device_phone1","Kolkata"),
            ("user_002", "device_xyz",   "Mumbai"),
            ("user_002", "device_tab1",  "Mumbai"),
            ("user_003", "device_del1",  "Delhi"),
        ]
        conn.executemany("INSERT INTO known_devices VALUES (?,?,?)", devices)

        # ── Known recipients ─────────────────────────────────────────────────
        recipients = [
            ("user_001", "friend1@okaxis",      "2026-05-10"),
            ("user_001", "mom@ybl",             "2026-05-15"),
            ("user_001", "electricity@paytm",   "2026-04-30"),
            ("user_001", "groceries@okhdfc",    "2026-05-18"),
            ("user_002", "husband@okaxis",      "2026-05-17"),
            ("user_002", "rent@ybl",            "2026-05-01"),
            ("user_003", "college@paytm",       "2026-05-12"),
        ]
        conn.executemany("INSERT INTO known_recipients VALUES (?,?,?)", recipients)

        # ── Flagged recipients ───────────────────────────────────────────────
        flagged = [
            ("fraud99@ybl",    "Reported in 47 fraud cases"),
            ("scam@okicici",   "Phishing UPI linked to fake bank portal"),
            ("fake@paytm",     "Mass refund fraud scheme"),
            ("lottery@upi",    "Lottery scam operator"),
        ]
        conn.executemany("INSERT INTO flagged_recipients VALUES (?,?)", flagged)

        # ── Historical transactions (12 months of realistic history) ─────────
        base_date = datetime(2025, 5, 1)
        txn_rows = []
        velocity_rows = []

        recipients_001 = ["friend1@okaxis", "mom@ybl", "electricity@paytm", "groceries@okhdfc"]
        for i in range(60):
            dt = base_date + timedelta(days=random.randint(0, 365))
            amt = random.gauss(2500, 600)
            amt = max(200, round(amt, -1))
            r = random.choice(recipients_001)
            txn_id = f"hist_{i:04d}"
            txn_rows.append((
                txn_id, "user_001", amt, r, "device_abc", "Kolkata",
                dt.hour, 12.0, "approved", "approved",
                "Normal transaction", json.dumps({}),
                dt.strftime("%Y-%m-%d %H:%M:%S")
            ))

        conn.executemany("""
            INSERT INTO transactions
              (transaction_id, user_id, amount, recipient_upi, device_id, location,
               hour, risk_score, decision, status, reason, factors, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, txn_rows)

    print("Seed data loaded successfully.")
    print("   Users:      user_001 (Arjun, avg Rs.2500, Kolkata)")
    print("               user_002 (Priya, avg Rs.8000, Mumbai)")
    print("               user_003 (Rahul, avg Rs.1200, Delhi)")
    print("   Flagged:    fraud99@ybl, scam@okicici, fake@paytm, lottery@upi")
    print("   History:    60 transactions for user_001")
    print()
    print("Demo scenarios:")
    print("  LOW  -> amount=500,   recipient=mom@ybl,       device=device_abc, location=Kolkata")
    print("  MED  -> amount=6000,  recipient=newshop@hdfc,  device=device_abc, location=Kolkata")
    print("  HIGH -> amount=75000, recipient=fraud99@ybl,   device=new_device, location=Delhi")


if __name__ == "__main__":
    seed()
