# AirFlowIQ

> **Full-Stack HVAC Monitoring Platform**  
> Embedded Hardware • Edge Firmware • Cloud Dashboard

AirFlowIQ is an integrated HVAC monitoring system designed to provide real-time environmental visibility, airflow analytics, and filter identification inside residential and commercial HVAC systems.

The platform combines embedded sensing hardware, dual-transport communication (WiFi + LoRa), and cloud-connected dashboard infrastructure for reliable field deployment and remote monitoring.

---

## 🚀 Platform Overview

AirFlowIQ integrates:

- 📡 **Dual Communication** — WiFi with automatic LoRa fallback  
- 🌡️ **Environmental Monitoring** — Temperature, Humidity, Pressure  
- 🌬️ **Airflow Velocity Measurement**  
- 🪪 **RFID-Based Filter Identification**  
- 🔋 **Battery Voltage Monitoring**  
- 🟢 **Embedded RGB Diagnostic System**  
- ☁️ **Cloud Logging & Dashboard Infrastructure**

Designed for:

- Residential HVAC monitoring  
- Commercial service deployments  
- Technician-friendly installation  
- Remote fleet management  

---

## 🏗 System Architecture
Sensors → ESP32 Sensor Node → WiFi / LoRa → ESP32 Hotspot Gateway → Cloud Backend → Dashoboard


### Sensor Node

- ESP32-C6
- BME280 (Temperature / Humidity / Pressure)
- MFRC522 (RFID Filter Identification)
- Brushless fan airflow sensor
- ADC-based battery monitoring
- RFM95 LoRa module
- RGB LED diagnostics
- USB service mode

### Gateway Node

- ESP32-C3 / C6
- WiFi Access Point
- LoRa Receiver
- Cloud forwarding service
- Diagnostic handshake capability

---

## 📁 Repository Structure
```text
AirFlowIQ/
├── firmware/
│ ├── sensor_node/
│ ├── gateway_node/
│
├── hardware/
│ ├── pcb/
│ ├── schematics/
│ └── bom/
│
├── dashboard/
│
├── google_scripts/
│
├── docs/
│ ├── architecture/
│ ├── testing/
│ ├── compliance/
│ └── archive/
│
└── README.md
```

---

## 📊 Data Model

| Field | Description |
|--------|------------|
| `id` | Device identifier |
| `boot_count` | Power cycle counter |
| `battery_voltage` | Battery level (V) |
| `sensor_status` | Sensor health indicator |
| `temperature` | °C |
| `humidity` | % Relative Humidity |
| `pressure` | hPa |
| `wind_speed` | Derived airflow velocity |
| `rfid` | Filter UID |

---

## 🛠 Field Installation

1. Mount Sensor Node inside HVAC unit.
2. Install airflow sensor across duct path.
3. Attach RFID tag to filter.
4. Power node (battery or USB).
5. Pair with Gateway (WiFi or LoRa).
6. Confirm data visibility on dashboard.

---

## 🟢 Embedded Diagnostics

Diagnostic mode is triggered via USB connection.

### Sensor Status

| Color | Meaning |
|-------|----------|
| Green | All sensors operational |
| Yellow | Environmental sensor only |
| Blue | RFID only |
| Red | Sensor failure |

### Battery Status

| Color | Meaning |
|-------|----------|
| Green | > 75% |
| Yellow | 40–75% |
| Red | < 40% |

### Communication Status

| Color | Meaning |
|-------|----------|
| Green | WiFi active |
| Blue | LoRa active |
| Red | Offline |

---

## 💻 Development Setup

### Requirements

- Arduino IDE or PlatformIO  
- ESP32 board support (C3 / C6)  
- Required libraries:
  - Adafruit_BME280  
  - MFRC522  
  - RadioHead (RH_RF95)  
  - WiFiManager (optional)

### Flashing Firmware

```bash
esptool.py --port COMx --baud 460800 write_flash 0x10000 firmware.bin
