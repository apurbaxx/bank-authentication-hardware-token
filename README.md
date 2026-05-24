# BankGuard

AI-powered fraud prevention system for digital banking. Every transaction is scored in real time — low risk gets approved instantly, high risk is sent to a physical hardware token for manual approval.

Built for NIT Allahabad Hackathon by team finVerse.

---

## How it works

1. A transaction is submitted via the dashboard
2. The risk engine scores it across 4 factors: transaction pattern, device fingerprint, recipient intelligence, and velocity
3. Based on the score:
   - **0–40** → Auto approved
   - **41–70** → OTP challenge
   - **71–100** → Alert sent to ESP32 hardware token
4. The ESP32 beeps and displays the transaction on an OLED screen
5. The user taps the button to approve or holds it for 2 seconds to reject
6. The dashboard updates in real time

---

## Project Structure

```
bankguard/
├── backend/
│   ├── app.py            Flask API server
│   ├── risk_engine.py    4-factor risk scoring engine
│   ├── explainer.py      Local NLP reason generator
│   ├── database.py       SQLite helpers
│   ├── seed_data.py      Demo data seeder
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── Dashboard.jsx
│       ├── TransactionForm.jsx
│       ├── RiskBadge.jsx
│       └── TokenWidget.jsx
└── esp32/
    ├── main.py           MicroPython firmware
    ├── config.py         WiFi + server config
    ├── ssd1306.py        OLED driver
    └── flash_instructions.md
```

---

## Running the software

**Backend**
```bash
cd bankguard/backend
pip install -r requirements.txt
python seed_data.py      # first time only
python app.py
```

**Frontend**
```bash
cd bankguard/frontend
npm install              # first time only
npm run dev
```

Open http://localhost:3000

---

## Hardware (ESP32 Token)

**Components**
- NodeMCU ESP32 (CP2102, 30-pin)
- SSD1306 0.96" OLED display (I2C)
- 1x tactile push button

**Wiring**
```
OLED VCC  →  ESP32 3V3
OLED GND  →  ESP32 GND
OLED SCL  →  ESP32 GPIO 22
OLED SDA  →  ESP32 GPIO 21
Button    →  ESP32 GPIO 13 + GND
```

**Button behaviour**
- Short press → Approve
- Hold 2 seconds → Reject
- No press in 60 seconds → Auto-rejected

**Setup**
1. Flash MicroPython onto ESP32 (see `esp32/flash_instructions.md`)
2. Upload `ssd1306.py`, `config.py`, `main.py` via Thonny
3. Edit `config.py` with your WiFi credentials and laptop IP (`ipconfig`)
4. Press EN to boot — OLED shows "BankGuard / Ready"

---

## Risk Scoring

| Factor | Weight | What it checks |
|---|---|---|
| Transaction pattern | 30% | Amount vs user average, time of day |
| Device fingerprint | 25% | Known device, known location |
| Recipient intelligence | 30% | New recipient, flagged recipient, recency |
| Velocity | 15% | Number of transactions in last hour |

---

## Demo Scenarios

| Scenario | Settings | Expected result |
|---|---|---|
| Normal | Amount=500, recipient=mom@ybl, device=device_abc, location=Kolkata | Approved |
| Medium | Amount=6000, recipient=newshop@hdfc, device=device_abc, location=Kolkata | OTP Challenge |
| High risk | Amount=75000, recipient=fraud99@ybl, device=new_device, location=Delhi | Hardware token alert |
