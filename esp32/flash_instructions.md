# ESP32 Flash Instructions — BankGuard Hardware Token

## Prerequisites
- Windows laptop with USB port
- NodeMCU ESP32 (CP2102, 30-pin)
- USB Micro cable

---

## Step 1 — Install CP2102 driver
Download from: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers  
Install and reboot. The ESP32 should appear as a COM port in Device Manager.

## Step 2 — Install esptool
```
pip install esptool==4.7.0
```

## Step 3 — Download MicroPython firmware
Go to: https://micropython.org/download/ESP32_GENERIC/  
Download the latest `.bin` file (e.g. `ESP32_GENERIC-20241129-v1.24.1.bin`)

## Step 4 — Find your COM port
Open Device Manager → Ports (COM & LPT) → look for "Silicon Labs CP210x" → note the COM number (e.g. COM5)

## Step 5 — Erase flash
```
esptool.py --chip esp32 --port COM5 erase_flash
```
Replace COM5 with your actual port.

## Step 6 — Flash MicroPython
```
esptool.py --chip esp32 --port COM5 --baud 460800 write_flash -z 0x1000 ESP32_GENERIC-20241129-v1.24.1.bin
```

## Step 7 — Install Thonny IDE
Download from: https://thonny.org  
Open Thonny → Tools → Options → Interpreter → MicroPython (ESP32) → select your COM port

## Step 8 — Upload ssd1306 library
Download `ssd1306.py` from:  
https://raw.githubusercontent.com/micropython/micropython-lib/master/micropython/drivers/display/ssd1306/ssd1306.py  
In Thonny: File → Open → select `ssd1306.py` → File → Save as → MicroPython device → save as `ssd1306.py`

## Step 9 — Configure and upload firmware
1. Edit `config.py`:
   - Set `WIFI_SSID` and `WIFI_PASSWORD` to your WiFi
   - Run `ipconfig` on your laptop, find the `192.168.X.X` address, set as `SERVER_URL`
2. In Thonny, upload `config.py` to ESP32 root
3. Upload `main.py` to ESP32 root

## Step 10 — Boot and verify
Press the **EN** (reset) button on the ESP32.  
OLED should show:
```
BankGuard
Connecting...
[your WiFi name]
```
Then after connecting:
```
BankGuard
Ready
192.168.X.X
Polling...
```

## Step 11 — Test end-to-end
1. Start Flask backend: `python app.py`
2. Start React frontend: `npm run dev`
3. Send a HIGH risk transaction (amount=75000, recipient=fraud99@ybl, device=new_device, location=Delhi)
4. ESP32 should beep 3 times and show the alert on OLED
5. Press YES or NO — dashboard updates in real time

---

## Wiring Reference
```
ESP32 Pin  →  Component
─────────────────────────────────────────────
3.3V       →  OLED VCC
GND        →  OLED GND
GPIO 22    →  OLED SCL
GPIO 21    →  OLED SDA
GPIO 12    →  YES Button (other leg to GND)
GPIO 14    →  NO  Button (other leg to GND)
GPIO 26    →  Buzzer + (other leg to GND)
```
