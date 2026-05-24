import network, urequests, ujson, time
from machine import Pin, PWM, I2C
import ssd1306, config

i2c  = I2C(0, scl=Pin(config.PIN_OLED_SCL), sda=Pin(config.PIN_OLED_SDA), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
btn  = Pin(config.PIN_BTN, Pin.IN, Pin.PULL_UP)

try:
    buzzer = PWM(Pin(config.PIN_BUZZER), freq=1000, duty=0)
    HAS_BUZZER = True
except:
    HAS_BUZZER = False


def show(lines):
    oled.fill(0)
    for i, line in enumerate(lines[:8]):
        oled.text(str(line)[:16], 0, i * 8)
    oled.show()


def beep(times=1, ms=150):
    if not HAS_BUZZER:
        return
    for _ in range(times):
        buzzer.duty(512)
        time.sleep_ms(ms)
        buzzer.duty(0)
        time.sleep_ms(100)


def connect_wifi():
    show(["BankGuard", "Connecting...", config.WIFI_SSID[:16]])
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        for _ in range(20):
            if wlan.isconnected():
                break
            time.sleep_ms(500)
    if wlan.isconnected():
        show(["BankGuard", "Ready", wlan.ifconfig()[0], "Waiting..."])
        return True
    show(["WiFi FAILED", "Check config.py"])
    return False


def wait_for_press(timeout_ms=60000):
    """
    Wait for button press. Returns:
      'approve' — short press  (< 2 seconds)
      'reject'  — long press   (>= 2 seconds)
      'timeout' — no press within timeout
    """
    deadline = time.ticks_add(time.ticks_ms(), timeout_ms)

    # Wait for button down
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        if btn.value() == 0:
            break
        time.sleep_ms(20)
    else:
        return 'timeout'

    # Measure how long it's held
    press_start = time.ticks_ms()
    while btn.value() == 0:
        time.sleep_ms(20)
    held_ms = time.ticks_diff(time.ticks_ms(), press_start)

    return 'reject' if held_ms >= 2000 else 'approve'


def send_response(txn_id, decision):
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


def handle_alert(txn):
    amt       = txn.get("amount", 0)
    recipient = str(txn.get("recipient_upi", ""))[:14]
    txn_id    = txn.get("transaction_id", "")

    beep(3)
    show(["!! ALERT !!", "Rs." + str(int(amt)), "To:" + recipient, "Hold=Reject", "Tap=Approve"])

    result = wait_for_press(60000)

    if result == 'timeout':
        send_response(txn_id, "rejected")
        show(["TIMEOUT", "Auto-rejected"])
    elif result == 'approve':
        send_response(txn_id, "approved")
        beep(1, 200)
        show(["", "  APPROVED", "", "Rs." + str(int(amt))])
    else:  # reject
        send_response(txn_id, "rejected")
        beep(3, 80)
        show(["", "  REJECTED", "", "Rs." + str(int(amt))])

    time.sleep_ms(2000)


def main():
    if not connect_wifi():
        time.sleep_ms(5000)
        import machine; machine.reset()

    show(["BankGuard", "Ready", "Waiting..."])

    while True:
        try:
            r = urequests.get(config.SERVER_URL + "/api/token/pending")
            data = r.json()
            r.close()
            if data.get("pending") and data.get("transaction"):
                handle_alert(data["transaction"])
                show(["BankGuard", "Ready", "Waiting..."])
        except Exception as e:
            show(["Poll error", str(e)[:16], "Retrying..."])
            time.sleep_ms(3000)

        time.sleep_ms(config.POLL_INTERVAL_MS)


try:
    main()
except Exception as e:
    show(["FATAL ERROR", str(e)[:16], "Rebooting..."])
    time.sleep_ms(10000)
    import machine; machine.reset()
