"""
app.py — BankGuard Flask API server

Hardware integration points are clearly marked with # [HARDWARE].
When the ESP32 arrives, those sections activate automatically via the
token_status table — no code changes needed in app.py.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import uuid

from database import (
    init_db,
    save_transaction, get_all_transactions, get_transaction,
    update_transaction_status, get_dashboard_stats,
    set_pending_token_txn, clear_pending_token_txn,
    get_pending_token_txn, mark_hardware_seen, get_token_status
)
from risk_engine import score_transaction

app = Flask(__name__)
CORS(app)

init_db()


# ── POST /api/transaction ─────────────────────────────────────────────────────

@app.route("/api/transaction", methods=["POST"])
def create_transaction():
    body = request.get_json(force=True)

    required = ["amount", "recipient_upi", "user_id", "device_id", "location"]
    missing = [f for f in required if not body.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        amount = float(body["amount"])
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "amount must be a positive number"}), 400

    txn_id = "txn_" + uuid.uuid4().hex[:10]
    hour   = datetime.now().hour

    result = score_transaction({
        "user_id":       body["user_id"],
        "amount":        amount,
        "recipient_upi": body["recipient_upi"].strip().lower(),
        "device_id":     body["device_id"].strip(),
        "location":      body["location"].strip(),
        "hour":          hour,
    })

    decision = result["decision"]
    # Map decision to initial status
    status_map = {
        "approved":      "approved",
        "otp_challenge": "otp_challenge",
        "pending_token": "pending",
    }
    status = status_map[decision]

    txn = {
        "transaction_id": txn_id,
        "user_id":        body["user_id"],
        "amount":         amount,
        "recipient_upi":  body["recipient_upi"].strip().lower(),
        "device_id":      body["device_id"].strip(),
        "location":       body["location"].strip(),
        "hour":           hour,
        "risk_score":     result["score"],
        "decision":       decision,
        "status":         status,
        "reason":         result["reason"],
        "factors":        result["factors"],
    }
    save_transaction(txn)

    # [HARDWARE] When ESP32 is connected, this queues the alert for polling.
    # Works identically with or without hardware — frontend "Simulate" buttons
    # call /api/token/response as a software fallback.
    if decision == "pending_token":
        set_pending_token_txn(txn_id)

    return jsonify({
        "transaction_id": txn_id,
        "decision":       decision,
        "score":          result["score"],
        "factors":        result["factors"],
        "reason":         result["reason"],
    }), 201


# ── GET /api/transactions ─────────────────────────────────────────────────────

@app.route("/api/transactions", methods=["GET"])
def list_transactions():
    return jsonify(get_all_transactions())


# ── GET /api/dashboard/stats ──────────────────────────────────────────────────

@app.route("/api/dashboard/stats", methods=["GET"])
def dashboard_stats():
    return jsonify(get_dashboard_stats())


# ── GET /api/token/pending ────────────────────────────────────────────────────
# [HARDWARE] ESP32 polls this every 2 seconds.
# Returns the pending transaction so the device can display it on OLED.

@app.route("/api/token/pending", methods=["GET"])
def token_pending():
    # [HARDWARE] Mark ESP32 as online whenever it polls
    mark_hardware_seen()

    pending_id = get_pending_token_txn()
    if not pending_id:
        return jsonify({"pending": False, "transaction": None})

    txn = get_transaction(pending_id)
    if not txn:
        clear_pending_token_txn()
        return jsonify({"pending": False, "transaction": None})

    return jsonify({
        "pending": True,
        "transaction": {
            "transaction_id": txn["transaction_id"],
            "amount":         txn["amount"],
            "recipient_upi":  txn["recipient_upi"],
            "risk_score":     txn["risk_score"],
            "reason":         txn["reason"],
        }
    })


# ── POST /api/token/response ──────────────────────────────────────────────────
# [HARDWARE] ESP32 calls this after button press (YES/NO).
# Also called by frontend "Simulate" buttons when hardware is absent.

@app.route("/api/token/response", methods=["POST"])
def token_response():
    body = request.get_json(force=True)
    txn_id   = body.get("transaction_id")
    decision = body.get("decision")  # "approved" | "rejected"

    if not txn_id or decision not in ("approved", "rejected"):
        return jsonify({"error": "transaction_id and decision (approved|rejected) required"}), 400

    txn = get_transaction(txn_id)
    if not txn:
        return jsonify({"error": "Transaction not found"}), 404

    new_status = "approved" if decision == "approved" else "rejected"
    update_transaction_status(txn_id, new_status)
    clear_pending_token_txn()

    return jsonify({"ok": True, "transaction_id": txn_id, "status": new_status})


# ── GET /api/token/status ─────────────────────────────────────────────────────
# [HARDWARE] Frontend polls this to show ESP32 online/offline indicator.

@app.route("/api/token/status", methods=["GET"])
def token_status():
    status = get_token_status()
    # Consider hardware "online" if it polled within the last 10 seconds
    hardware_online = False
    if status.get("last_seen"):
        try:
            last = datetime.strptime(status["last_seen"], "%Y-%m-%d %H:%M:%S")
            hardware_online = (datetime.now() - last).total_seconds() < 10
        except Exception:
            pass

    return jsonify({
        "hardware_connected": hardware_online,
        "pending_txn_id":     status.get("pending_txn_id"),
    })


# ── GET /api/users ────────────────────────────────────────────────────────────

@app.route("/api/users", methods=["GET"])
def list_users():
    from database import get_conn
    with get_conn() as conn:
        rows = conn.execute("SELECT user_id, name, avg_amount, home_location FROM users").fetchall()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    print("BankGuard backend starting on http://localhost:5000")
    print("Hardware token polling endpoint: GET /api/token/pending")
    app.run(host="0.0.0.0", port=5000, debug=True)
