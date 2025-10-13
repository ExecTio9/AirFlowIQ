# FiltSure HVAC Monitor

*Internal Project — FiltSure Team*

FiltSure is an IoT-based environmental monitoring system for HVAC systems. It collects real-time environmental data and filter identity information, logging to a cloud service via dual WiFi and LoRa communication.  
The system is designed for reliable field operation and simple installation by HVAC technicians or homeowners.

---

## System Overview

- 📡 Dual Communication: **WiFi** with **LoRa fallback**
- 🌡️ Tracks **Temperature**, **Humidity**, **Pressure**
- 🪪 Identifies Filters via **RFID**
- 🔋 Logs **Battery Voltage** and **Wind Speed**
- 🟢 Displays system health via **RGB LED Diagnostics**
- 🛠️ Designed for **easy installation** inside HVAC units

---

## Architecture

Sensors → ESP32 Sensor Node → WiFi / LoRa → ESP32 Hotspot Gateway → Google Apps Script → Google Sheets (Cloud Logging)

### Sensor Node

- **ESP32-C6 DevKitM-1**
- **BME280** — Temp / Humidity / Pressure
- **MFRC522** — RFID Filter Sensor
- **14-bit ADC** — Battery Monitor
- **5.5V Brushless Fan** — Wind Speed Sensor
- **RFM95** — LoRa Module
- **RGB LED** — Diagnostics
- **USB** — Power & Diagnostics Mode

### Gateway Node

- **ESP32-C3 or C6**
- **WiFi AP (ESP32 Hotspot)**
- **LoRa Receiver (RFM95)**
- **Google Apps Script Forwarding**
- **Diagnostic Ping Capability**

---

## Suggested Repo Structure

```text
FiltSure-HVAC-Monitor/
├── README.md                 # Project documentation (this file)
├── LICENSE.md                # Internal License
├── docs/                     # Architecture diagrams, setup guides
├── firmware/
│   ├── sensor_node/          # Source code for Sensor Node (ESP32-C6)
│   │   ├── src/
│   │   ├── include/
│   │   ├── platformio.ini    # or arduino config
│   ├── gateway_node/         # Source code for Gateway Node (ESP32-C3/C6)
│   │   ├── src/
│   │   ├── include/
│   │   ├── platformio.ini    # or arduino config
├── google_scripts/           # Google Apps Script for cloud logging
├── hardware/                 # Schematics, PCB files (KiCad)
├── testing/                  # Test scripts, diagnostic tools
└── images/                   # Project images, architecture diagrams

```
Data Fields

| Field             | Description               |
| ----------------- | ------------------------- |
| `id`              | Device ID                 |
| `boot count`      | Power cycle count         |
| `battery voltage` | Battery level (V)         |
| `sensor status`   | Sensor health status      |
| `temperature`     | Temperature in °C         |
| `humidity`        | Relative Humidity (%)     |
| `pressure`        | Pressure (hPa)            |
| `wind speed`      | Derived air flow velocity |
| `rfid`            | Filter RFID Tag UID       |

### Installation Guide For Technicians
- Mount Sensor Node inside HVAC unit (side wall recommended).
- Install Wind Sensor across airflow path.
- Attach RFID Tag to HVAC filter.
- Power the Node via battery or USB.
- Verify Gateway Connection (WiFi pairing).
- Confirm Data Logging in the FiltSure Google Sheet.

### Maintenance
- Replace battery pack periodically (check logged voltage).
- Trigger Diagnostic Mode when servicing units.
- OTA firmware updates via Gateway (WIP).

### Developer Setup
- Prerequisites
  - Arduino IDE or PlatformIO
  - ESP32 Board Support (ESP32-C3, C6)
- Required Libraries:
  - Adafruit_BME280
  - MFRC522
  - RadioHead (RH_RF95)
  - WiFiManager (if used)
  - Google Apps Script URL configured

## Flashing the Node
esptool.py --port COMx --baud 460800 write_flash 0x10000 firmware.bin

## Configuration
Edit these parameters in your code:
```text
#define WIFI_SSID     "ESP32_HOTSPOT"
#define WIFI_PASS     "FiltSure_Rules"
#define RF95_FREQ     915.0
#define NODE_ID       X
#define DEST_ID       Y
#define GOOGLE_SHEET_URL "https://script.google.com/macros/..."
```

# Diagnostic Mode (RGB LED)
##Trigger:
USB Plug-In

## LED Codes
### Sensor Status Pulse
Color	Meaning
- Green	All sensors working
- Yellow	Only BME280 working
- Blue	Only RFID working
- Red	Neither sensor working

### Battery Level Pulse
Color	Meaning
- Green	> 75%
- Yellow	40–75%
- Red	< 40%

### Communication Mode Pulse
Color	Meaning
Green	WiFi active
Blue	LoRa active
Red	Offline / No communication

# Roadmap / TODO
- Dynamic LoRa Node ID assignment
- Full OTA update pipeline via Gateway

# Internal Links
- [FiltSure_Watch monitoring sheet](https://docs.google.com/spreadsheets/d/1jLbKlstPxHlD7kHZhQn0Z-8PDUdkm7ZQxHZjDr8VWqw/edit?gid=1254838656#gid=1254838656)
- [Google App Script Code](https://script.google.com/home/projects/1kvNN4aTYOBjVC-IF9PAhh4AED5QBl2EmA35dcaVsej_4SW3x39zN_HsJ/edit)
- [Documentation Guide](docs\FiltSure_HVAC_Monitor_Guide_v1_FULL_Draft_v2.docx)
