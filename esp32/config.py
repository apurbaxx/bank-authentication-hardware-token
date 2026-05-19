# esp32/config.py — BankGuard ESP32 configuration
# Fill these in before flashing to the device.

WIFI_SSID     = "YOUR_WIFI_NAME"          # ← your WiFi network name
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"      # ← your WiFi password
SERVER_URL    = "http://192.168.X.X:5000" # ← your laptop's local IP (run `ipconfig` on Windows)

POLL_INTERVAL_MS = 2000   # how often to check for pending alerts (milliseconds)

# Hardware pin assignments (NodeMCU ESP32 30-pin, CP2102)
PIN_OLED_SCL = 22
PIN_OLED_SDA = 21
PIN_BTN_YES  = 12   # YES button → GPIO12 to GND
PIN_BTN_NO   = 14   # NO  button → GPIO14 to GND
PIN_BUZZER   = 26   # Passive buzzer or LED for alert feedback
