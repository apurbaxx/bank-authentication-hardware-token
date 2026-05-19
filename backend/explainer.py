"""
explainer.py — Local rule-based risk explanation generator.
No API calls. No internet. Instant. Uses real transaction values.
"""

from datetime import datetime


def explain_risk(transaction_data: dict, risk_factors: dict) -> str:
    """
    Build a precise, natural-language explanation of why a transaction was flagged.

    transaction_data keys:
        amount, recipient_upi, user_avg, known_device, known_location,
        known_recipient, flagged_recipient, hour, location, user_location,
        velocity_count, days_since_last_recipient

    risk_factors keys:
        transaction_pattern, device_fingerprint, recipient_intelligence,
        velocity, final_score
    """
    parts = []
    amt   = transaction_data.get("amount", 0)
    avg   = transaction_data.get("user_avg", 1) or 1
    hour  = transaction_data.get("hour", 12)

    # ── Transaction pattern ───────────────────────────────────────────────────
    ratio = amt / avg
    if ratio >= 5:
        parts.append(
            f"amount of Rs.{amt:,.0f} is {ratio:.0f}x the user's average of Rs.{avg:,.0f}"
        )
    elif ratio >= 3:
        parts.append(
            f"amount of Rs.{amt:,.0f} is {ratio:.1f}x above the usual average of Rs.{avg:,.0f}"
        )
    elif ratio >= 1.5:
        parts.append(
            f"amount of Rs.{amt:,.0f} is higher than the usual Rs.{avg:,.0f}"
        )

    if hour >= 23 or hour <= 4:
        parts.append(f"transaction initiated at {hour:02d}:00 (unusual hour)")

    # ── Velocity ──────────────────────────────────────────────────────────────
    velocity = transaction_data.get("velocity_count", 0)
    if velocity >= 5:
        parts.append(f"{velocity} transactions sent in the last hour (rapid-fire pattern)")
    elif velocity >= 3:
        parts.append(f"{velocity} transactions in the last hour")

    # ── Device fingerprint ────────────────────────────────────────────────────
    if not transaction_data.get("known_device", True):
        parts.append("login from an unrecognised device")

    location     = transaction_data.get("location", "")
    user_location = transaction_data.get("user_location", "")
    if location and user_location and location.lower() != user_location.lower():
        parts.append(f"access from {location} (usual location: {user_location})")

    # ── Recipient intelligence ────────────────────────────────────────────────
    recipient = transaction_data.get("recipient_upi", "unknown")
    if transaction_data.get("flagged_recipient", False):
        parts.append(f"recipient {recipient} is in the fraud database")
    elif not transaction_data.get("known_recipient", True):
        parts.append(f"recipient {recipient} has never been transacted with before")
    else:
        days = transaction_data.get("days_since_last_recipient")
        if days and days > 90:
            parts.append(f"recipient {recipient} last used {days} days ago")

    # ── Compose ───────────────────────────────────────────────────────────────
    score = risk_factors.get("final_score", 0)

    if not parts:
        return f"Transaction flagged with risk score {score:.0f}/100 due to unusual activity."

    if len(parts) == 1:
        sentence = parts[0][0].upper() + parts[0][1:]
        return f"{sentence}. Risk score: {score:.0f}/100."

    if len(parts) == 2:
        sentence = (parts[0][0].upper() + parts[0][1:] + ", and " + parts[1])
        return f"{sentence}. Risk score: {score:.0f}/100."

    joined = (
        parts[0][0].upper() + parts[0][1:] + "; "
        + "; ".join(parts[1:-1])
        + "; and " + parts[-1]
    )
    return f"{joined}. Risk score: {score:.0f}/100."


def get_risk_label(score: float) -> str:
    if score <= 40:
        return "LOW"
    if score <= 70:
        return "MEDIUM"
    return "HIGH"
