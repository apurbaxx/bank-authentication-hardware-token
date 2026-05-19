"""
esp32/main.py — BankGuard Hardware Token Firmware (MicroPython)

Hardware: NodeMCU ESP32 (CP2102) + SSD1306 OLED + 2 tactile buttons + buzzer
This file runs automatically on boot when flashed to the ESP32.

NOTE: This file is NOT runnable on a PC. It requires MicroPython on ESP32.
      See flash_instructions.md for setup steps.
"""

import network
import urequests
import ujson
import time
from machine import Pin, PWM, I2C
import ssd1306
import config

# ── Hardware setup ────────────────────────────────────────────────────────────

i2c  = I2C(0, scl=Pin(config.PIN_OLED_SCL), sda=Pin(config.PIN_OLED_SDA), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

btn_yes = Pin(config.PIN_BTN_YES, Pin.IN, Pin.PULL_UP)  # LOW when pressed
btn_no  = Pin(config.PIN_BTN_NO,  Pin.IN, Pin.PULL_UP)  # LOW when pressed
buzzer  = PWM(Pin(config.PIN_BUZZER), freq=1000, duty=0)


# ── Display helpers ───────────────────────────────────────────────────────────

def show(lines):
    """Display up to 4 lines on OLED (128x64, 8px per line)."""
    oled.fill(0)
    for i, line in enumerate(lines[:8]):
        oled.text(str(line)[:16], 0, i * 8)
    oled.show()


def beep(times=3, on_ms=100, off_ms=100):
    for _ in range(times):
        buzzer.duty(512)
        time.sleep_ms(on_ms)
        buzzer.duty(0)
        time.sleep_ms(off_ms)


# ── WiFi connection ───────────────────────────────────────────────────────────

def connect_wifi():
    show(["BankGuard", "Connecting...", config.WIFI_SSID])
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        for _ in range(20):          # 10 second timeout
            if wlan.isconnected():
                break
            time.sleep_ms(500)
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        show(["BankGuard", "Ready", ip, "Polling..."])
        return True
    else:
        show(["BankGuard", "WiFi FAILED", "Check config.py"])
        return False


# ── Token response ────────────────────────────────────────────────────────────

def send_response(txn_id, decision):
    """POST the user's button press back to the Flask backend."""
    try:
        payload = ujson.dumps({"transaction_id": txn_id, "decision": decision})
        r = urequests.post(
            config.SERVER_URL + "/api/token/response",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        r.close()
        return True
    except Exception as e:
        show(["Send error", str(e)[:16]])
        time.sleep_ms(2000)
        return False


# ── Alert handler ─────────────────────────────────────────────────────────────

def handle_alert(txn):
    """Display alert on OLED, beep, wait for button press."""
    amt       = txn.get("amount", 0)
    recipient = str(txn.get("recipient_upi", ""))[:12]
    txn_id    = txn.get("transaction_id", "")
    score     = txn.get("risk_score", 0)

    beep(3)
    show(["!! ALERT !!", f"Rs.{int(amt):,}", f"To:{recipient}", "YES=B1  NO=B2"])

    # Wait for button press (up to 60 seconds)
    deadline = time.ticks_add(time.ticks_ms(), 60000)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        if btn_yes.value() == 0:   # LOW = pressed
            time.sleep_ms(50)      # debounce
            if btn_yes.value() == 0:
                send_response(txn_id, "approved")
                show(["", "  APPROVED!", "", f"Rs.{int(amt):,}"])
                beep(1, 200)
                time.sleep_ms(2000)
                return
        if btn_no.value() == 0:
            time.sleep_ms(50)
            if btn_no.value() == 0:
                send_response(txn_id, "rejected")
                show(["", "  BLOCKED!", "", f"Rs.{int(amt):,}"])
                beep(3, 50, 50)
                time.sleep_ms(2000)
                return
        time.sleep_ms(50)

    # Timeout — auto-reject for safety
    send_response(txn_id, "rejected")
    show(["TIMEOUT", "Auto-rejected"])
    time.sleep_ms(2000)


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    if not connect_wifi():
        time.sleep_ms(5000)
        import machine
        machine.reset()   # reboot and retry

    show(["BankGuard", "Ready", "No alerts"])

    while True:
        try:
            r = urequests.get(config.SERVER_URL + "/api/token/pending")
            data = r.json()
            r.close()

            if data.get("pending") and data.get("transaction"):
                handle_alert(data["transaction"])
                show(["BankGuard", "Ready", "No alerts"])
            else:
                # Idle — show ready state
                pass

        except Exception as e:
            show(["Poll error", str(e)[:16], "Retrying..."])
            time.sleep_ms(3000)

        time.sleep_ms(config.POLL_INTERVAL_MS)


# Entry point
try:
    main()
except Exception as e:
    # Never crash — show error and reboot after 10s
    show(["FATAL ERROR", str(e)[:16], "Rebooting..."])
    time.sleep_ms(10000)
    import machine
    machine.reset()
