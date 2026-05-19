"""
risk_engine.py — BankGuard transaction risk scoring engine.

Scoring model (weighted):
  Factor 1 — Transaction Pattern   (30%)
  Factor 2 — Device Fingerprint    (25%)
  Factor 3 — Recipient Intelligence(30%)
  Factor 4 — Velocity              (15%)

Improvements over spec:
  - Continuous amount scoring (sigmoid-like) instead of hard thresholds
  - Velocity factor as a separate dimension
  - Partial credit for "recently seen" recipients vs "never seen"
  - Score clamped to [0, 100] with integer output
"""

import math
from datetime import datetime, timedelta
from database import (
    get_user, get_known_devices, get_known_recipients,
    is_flagged_recipient, get_velocity_count
)
from explainer import explain_risk


# ── Individual factor scorers ─────────────────────────────────────────────────

def _score_transaction_pattern(amount: float, user_avg: float, hour: int) -> float:
    """
    Continuous amount score using a soft curve so small deviations don't
    spike the score, but large ones escalate quickly.
    """
    ratio = amount / max(user_avg, 1)

    # Soft sigmoid mapped to 0–80 range for amount alone
    # ratio=1 → ~0, ratio=2 → ~30, ratio=3 → ~55, ratio=5 → ~75, ratio=10 → ~80
    amount_score = 80 / (1 + math.exp(-1.2 * (ratio - 2.5)))

    # Night-time penalty (11pm–5am)
    time_penalty = 20 if (hour >= 23 or hour <= 4) else 0

    return min(100, amount_score + time_penalty)


def _score_device_fingerprint(
    user_id: str, device_id: str, location: str,
    known_devices: dict, user_location: str
) -> tuple[float, bool, bool]:
    """
    Returns (score, known_device, known_location).
    known_devices: {device_id: location}
    """
    known_device   = device_id in known_devices
    known_location = False

    if known_device:
        # Check if this device's registered location matches current
        device_home = known_devices[device_id]
        known_location = (device_home.lower() == location.lower())
        if known_location:
            score = 5   # fully trusted
        else:
            score = 40  # known device, different location
    else:
        # Unknown device — check if location is at least familiar
        all_locations = {v.lower() for v in known_devices.values()}
        if location.lower() in all_locations:
            score = 55  # new device but familiar city
        else:
            score = 80  # new device + new location = high risk

    return min(100, score), known_device, known_location


def _score_recipient(
    user_id: str, recipient_upi: str, known_recipients: dict
) -> tuple[float, bool, bool, int | None]:
    """
    Returns (score, known_recipient, flagged, days_since_last).
    """
    flagged = is_flagged_recipient(recipient_upi)
    if flagged:
        return 95, False, True, None

    if recipient_upi not in known_recipients:
        return 65, False, False, None

    # Known recipient — score by recency
    last_used_str = known_recipients[recipient_upi]
    try:
        last_used = datetime.strptime(last_used_str, "%Y-%m-%d")
        days = (datetime.now() - last_used).days
    except Exception:
        days = 0

    if days <= 30:
        score = 5
    elif days <= 90:
        score = 20
    else:
        score = 40  # known but stale

    return score, True, False, days


def _score_velocity(user_id: str) -> float:
    count = get_velocity_count(user_id, minutes=60)
    if count >= 8:
        return 90
    if count >= 5:
        return 70
    if count >= 3:
        return 40
    return 0


# ── Main scoring function ─────────────────────────────────────────────────────

def score_transaction(txn: dict) -> dict:
    """
    txn keys: user_id, amount, recipient_upi, device_id, location, hour

    Returns:
    {
        score, decision, factors: {transaction_pattern, device_fingerprint,
                                   recipient_intelligence, velocity},
        reason, transaction_data (enriched)
    }
    """
    user_id      = txn["user_id"]
    amount       = float(txn["amount"])
    recipient    = txn["recipient_upi"]
    device_id    = txn["device_id"]
    location     = txn["location"]
    hour         = int(txn.get("hour", datetime.now().hour))

    # Load user context
    user = get_user(user_id)
    user_avg      = user["avg_amount"] if user else 2500
    user_location = user["home_location"] if user else "Unknown"

    known_devices    = get_known_devices(user_id)
    known_recipients = get_known_recipients(user_id)

    # Score each factor
    f_pattern = _score_transaction_pattern(amount, user_avg, hour)
    f_device, known_device, known_location = _score_device_fingerprint(
        user_id, device_id, location, known_devices, user_location
    )
    f_recipient, known_recipient, flagged, days_since = _score_recipient(
        user_id, recipient, known_recipients
    )
    f_velocity = _score_velocity(user_id)

    # Weighted final score
    final = (
        f_pattern   * 0.30 +
        f_device    * 0.25 +
        f_recipient * 0.30 +
        f_velocity  * 0.15
    )
    final = round(min(100, max(0, final)), 1)

    factors = {
        "transaction_pattern":    round(f_pattern, 1),
        "device_fingerprint":     round(f_device, 1),
        "recipient_intelligence": round(f_recipient, 1),
        "velocity":               round(f_velocity, 1),
    }

    # Decision thresholds
    if final <= 40:
        decision = "approved"
    elif final <= 70:
        decision = "otp_challenge"
    else:
        decision = "pending_token"   # → triggers hardware token alert

    # Build enriched context for explainer
    transaction_data = {
        "amount":               amount,
        "recipient_upi":        recipient,
        "user_avg":             user_avg,
        "known_device":         known_device,
        "known_location":       known_location,
        "known_recipient":      known_recipient,
        "flagged_recipient":    flagged,
        "hour":                 hour,
        "location":             location,
        "user_location":        user_location,
        "velocity_count":       get_velocity_count(user_id, 60),
        "days_since_last_recipient": days_since,
    }

    risk_factors = {**factors, "final_score": final}
    reason = explain_risk(transaction_data, risk_factors)

    return {
        "score":            final,
        "decision":         decision,
        "factors":          factors,
        "reason":           reason,
        "transaction_data": transaction_data,
    }
