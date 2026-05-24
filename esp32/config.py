# esp32/config.py — BankGuard ESP32 configuration

WIFI_SSID = "Fibrsol-278FA8"
WIFI_PASSWORD = "12345678"
SERVER_URL = "http://192.168.1.2:5000"  # your laptop's IP from ipconfig

POLL_INTERVAL_MS = 2000

# Pin assignments
PIN_OLED_SCL = 22
PIN_OLED_SDA = 21
PIN_BTN = 13  # single button: short press = approve, long press = reject
PIN_BUZZER = 26
