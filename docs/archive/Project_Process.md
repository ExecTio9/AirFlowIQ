# FiltSure Project Process & Team Standards

## Purpose

Document internal team processes for managing the FiltSure HVAC Monitor project, ensuring consistency across firmware, hardware, cloud infrastructure, and deployment.

---

## Firmware Releases

- All firmware versions must be approved by [Lead Developer Name] before release to `main` branch.
- All firmware versions must include:
  - Version field sent in LoRa packets
  - Updated `RELEASE.md` or `CHANGELOG.md`

### OTA Update Policy

- OTA updates should be tested on at least one staging Sensor Node before field deployment.
- OTA version compatibility must be documented.

---

## Node ID Assignment

- Node IDs must be assigned manually at this time.
- Node ID registry maintained in this document:

| Node ID | Location / Assignment | Last Firmware Version | Notes |
|---------|-----------------------|----------------------|-------|
| 001     | Test Bench            | v1.0.0               |      |
| 002     | Field Unit HVAC-1     | v1.0.0               |      |
| ...     | ...                   | ...                  |      |

---

## Google Sheets Maintenance

- Google Sheet is structured with one tab per Sensor Node (`UNIT_<DeviceID>`).
- Sheet structure must remain consistent:
  - Columns: ID, Boot Count, Battery Voltage, Sensor Status, Temp, Humidity, Pressure, Wind Speed, RFID UID
- Team members must not reorder or delete columns.

---

## Documentation Updates

- Major changes to system behavior must be reflected in:
  - Main README.md
  - Google Apps Script comments
  - FiltSure HVAC Monitor Guide (DOCX)
- Hardware changes must be documented in `/hardware/README.md`.

---

## Field Deployment Checklist

- Each Sensor Node must pass the Sensor_Node_Test_Checklist before deployment.
- Each Gateway Node must be tested for:
  - LoRa receive success
  - Google Sheet data logging
  - PING → PONG success
  - OTA delivery test (optional)

---

## Future Improvements

- Dynamic Node ID assignment
- Automated OTA update tracking
- MQTT gateway extension
- Full mesh support (planned)

---

## Maintainers

- Lead Developer: [Name / GitHub handle]
- Hardware Lead: [Name / GitHub handle]
- Field Deployment Coordinator: [Name]
