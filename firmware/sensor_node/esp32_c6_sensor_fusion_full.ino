#include <WiFi.h>
#include <WiFiManager.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <MFRC522.h>
#include <RH_RF95.h>
#include <esp32-hal-rgb-led.h>
#include <driver/usb_serial_jtag.h>
#include <esp_sleep.h>
// ---------- Pin Definitions ----------
#define BATTERY_PIN       0
#define DIAG_PIN          2
#define WIND_PIN          3
#define SCK               4
#define MOSI              5
#define REGULATOR_EN_PIN  7
#define RGB_BUILTIN       8
#define MISO              15
#define BME_CS            23
#define RFID_CS           22
#define LORA_CS           21
#define LORA_RST          20
#define RFID_RST          18
#define us_S              1000000ULL
#define sleep_Time        60
#define TIMEOUT_MS        30000
// ---------- Hardware Object Setup ----------
Adafruit_BME280 bme(BME_CS,5,15,4);
RH_RF95 radio(LORA_CS);
MFRC522 rfid(RFID_CS,RFID_RST);
RTC_DATA_ATTR int bootCount = 0;
// ---------- Global State Variables ----------
String ID = "Test";
String Web_App_Path = "/macros/s/AKfycby0Y0FUDXrrgpBRS0fGOVgzpTs0XwQK9daSMbiqvNdLIBRZrIXhGrmlCXVB0VWVd-vP/exec";
String DataURL = "", Status_Read_Sensor = "", rfidUID = "";
float Temp, Humd, Prs;
float batteryVoltage = 0.0, batteryPercent = 0.0, windSpeed = 0.0;
bool isEncodedHost = false;
bool tryEncodedHostFallback = true;
volatile bool diagRequested = false;
byte nuidPICC[4] = {0, 0, 0, 0}; // For comparing last UID
void deselectAllSPI() {
  digitalWrite(BME_CS, HIGH);
  digitalWrite(RFID_CS, HIGH);
  digitalWrite(LORA_CS, HIGH);
}
// ---------- Interrupt for Diagnostic Button ----------
void IRAM_ATTR onDiagButton() {
  diagRequested = true;
}
// ---------- RGB Diagnostic LED Control ----------
void flashRGB(uint8_t r, uint8_t g, uint8_t b, int count = 1, int delayMs = 300) {
  for (int i = 0; i < count; i++) {
    rgbLedWrite(RGB_BUILTIN, r, g, b);
    delay(delayMs);
    rgbLedWrite(RGB_BUILTIN, 0, 0, 0);
    delay(delayMs);
  }
}
// ---------- Visual Diagnostic Output ----------
void runDiagnostics(bool bmeOK, bool rfidOK, float battPct, bool wifiOK, bool loraOK) {
  flashRGB(255, 255, 255, 2, 150); // Entry flash
  if (bmeOK && rfidOK) flashRGB(0, 255, 0);
  else if (bmeOK) flashRGB(255, 255, 0);
  else if (rfidOK) flashRGB(0, 0, 255);
  else flashRGB(255, 0, 0);
  if (battPct >= 75) flashRGB(0, 255, 0);
  else if (battPct >= 40) flashRGB(255, 255, 0);
  else flashRGB(255, 0, 0);
  if (wifiOK && loraOK) flashRGB(0, 255, 0);
  else if (wifiOK) flashRGB(255, 255, 0);
  else if (loraOK) flashRGB(0, 0, 255);
  else flashRGB(255, 0, 0);
  diagRequested = false;
}
// ---------- Trigger Diagnostic Mode via USB or Button ----------
void checkDiagnosticsMode(bool bmeOK, bool rfidOK, float battPct, bool wifiOK, bool loraOK) {
  pinMode(DIAG_PIN, INPUT_PULLUP);
  if (usb_serial_jtag_is_connected()) {
    runDiagnostics(bmeOK, rfidOK, battPct, wifiOK, loraOK);
    delay(2000);
  } else if (digitalRead(DIAG_PIN) == LOW) {
    delay(2000);
    if (digitalRead(DIAG_PIN) == LOW) {
      runDiagnostics(bmeOK, rfidOK, battPct, wifiOK, loraOK);
    }
  }
}
// ---------- Compute Battery Percentage from Voltage ----------
float getBatteryPercentage(float voltage) {
  voltage = constrain(voltage, 2.0, 3.0);
  return (voltage - 2.0) * 100.0;
}
// ---------- Encode URL Parameters ----------
String urlEncode(const String& s) {
  String encoded = "";
  const char* hex = "0123456789ABCDEF";
  for (char c : s) {
    if (isalnum(c)) encoded += c;
    else {
      encoded += '%';
      encoded += hex[(c >> 4) & 0xF];
      encoded += hex[c & 0xF];
    }
  }
  return encoded;
}
// ---------- Build Upload URL Depending on Target ----------
void buildURL() {
  if (isEncodedHost) {
    String encodedParams = "?sts=write";
    encodedParams += "&id=" + ID;
    encodedParams += "&bc=" + String(bootCount);
    encodedParams += "&bat=" + String(batteryPercent, 2);
    encodedParams += "&srs=" + Status_Read_Sensor;
    encodedParams += "&temp=" + String(Temp);
    encodedParams += "&humd=" + String(Humd);
    encodedParams += "&Prs=" + String(Prs);
    encodedParams += "&wind=" + String(windSpeed, 2);
    encodedParams += "&rfid=" + rfidUID;
    DataURL = "http://192.168.4.1/data?url=" + urlEncode(Web_App_Path + encodedParams);
  } else {
    DataURL = "https://script.google.com" + Web_App_Path;
    DataURL += "?sts=write";
    DataURL += "&id=" + ID;
    DataURL += "&bc=" + String(bootCount);
    DataURL += "&bat=" + String(batteryPercent, 2);
    DataURL += "&srs=" + Status_Read_Sensor;
    DataURL += "&temp=" + String(Temp);
    DataURL += "&humd=" + String(Humd);
    DataURL += "&Prs=" + String(Prs);
    DataURL += "&wind=" + String(windSpeed, 2);
    DataURL += "&rfid=" + rfidUID;
  }
}
// ---------- Sensor Data Acquisition ----------
void readSensors() {
  // --- BME280 Read ---
  deselectAllSPI();
  digitalWrite(BME_CS, LOW);
  Temp = bme.readTemperature();
  Humd = bme.readHumidity();
  Prs  = bme.readPressure() / 100.0F;
  digitalWrite(BME_CS, HIGH);
  Status_Read_Sensor = (isnan(Temp) || isnan(Humd) || isnan(Prs)) ? "Failed" : "Success";
  // --- RFID Read (confirmed logic) ---
  rfidUID = "";
  deselectAllSPI();
  delay(1000);
  digitalWrite(RFID_CS, LOW);
  Serial.println("🔍 Starting RFID scan...");
  rfid.PCD_StopCrypto1();
  rfid.PCD_Init();
  delay(50);
  if (!rfid.PICC_IsNewCardPresent()) {
    Serial.println("📭 No card present.");
  } else if (!rfid.PICC_ReadCardSerial()) {
    Serial.println("⚠️ Card detected but UID read failed.");
  } else {
    // Show tag type
    Serial.print("📟 RFID Type: ");
    MFRC522::PICC_Type piccType = rfid.PICC_GetType(rfid.uid.sak);
    Serial.println(rfid.PICC_GetTypeName(piccType));
    if (piccType == MFRC522::PICC_TYPE_MIFARE_MINI ||
        piccType == MFRC522::PICC_TYPE_MIFARE_1K ||
        piccType == MFRC522::PICC_TYPE_MIFARE_4K) {
      Serial.print("📟 UID HEX: ");
      for (byte i = 0; i < rfid.uid.size; i++) {
        if (rfid.uid.uidByte[i] < 0x10) Serial.print("0");
        Serial.print(rfid.uid.uidByte[i], HEX);
        if (rfid.uid.uidByte[i] < 0x10) rfidUID += "0";
        rfidUID += String(rfid.uid.uidByte[i], HEX);
      }
      Serial.println();
    } else {
      Serial.println("⚠️ Unsupported card type.");
    }
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
  }
  digitalWrite(RFID_CS, HIGH);
  // --- Wind Sensor Read ---
  windSpeed = analogRead(WIND_PIN) * (5.0 / 4095.0);
}
// ---------- Attempt Upload via HTTP ----------
bool HTTP_send() {
  const int maxAttempts = 3;
  for (int attempt = 1; attempt <= maxAttempts; ++attempt) {
    HTTPClient http;
    http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);  // 🛠️ Key fix
    http.setTimeout(20000);
    Serial.printf("🌐 Attempt %d: %s\n", attempt, DataURL.c_str());
    http.begin(DataURL);
    int httpCode = http.GET();
    if (httpCode > 0) {
      Serial.printf("📡 HTTP Response Code: %d\n", httpCode);
      String payload = http.getString();
      Serial.print("📄 Response payload: ");
      Serial.println(payload);
      if (httpCode == HTTP_CODE_OK && payload.indexOf("OK") >= 0) {
        http.end();
        return true;
      } else {
        Serial.println("⚠️ Server responded but not as expected.");
      }
    } else {
      Serial.printf("❌ HTTP GET failed. Error: %s\n", http.errorToString(httpCode).c_str());
    }
    http.end();
    delay(500);
  }
  return false;
}
// ---------- LoRa Transmission with ACK ----------
bool LoRa_sendAndVerify() {
  digitalWrite(LORA_RST, LOW); delay(10);
  digitalWrite(LORA_RST, HIGH); delay(10);
  if (!radio.init()) return false;
  radio.setFrequency(915.0);
  radio.setTxPower(20, false);
  radio.send((uint8_t *)DataURL.c_str(), DataURL.length());
  radio.waitPacketSent();
  uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
  uint8_t len = sizeof(buf);
  if (radio.waitAvailableTimeout(1000)) {
    if (radio.recv(buf, &len)) return true;
  }
  return false;
}
// ---------- Hold Regulator On During Deep Sleep ----------
void prepareRegulatorPin() {
  pinMode(REGULATOR_EN_PIN, OUTPUT);
  digitalWrite(REGULATOR_EN_PIN, HIGH);
  gpio_hold_dis((gpio_num_t)REGULATOR_EN_PIN);
  gpio_hold_en((gpio_num_t)REGULATOR_EN_PIN);
}
// ---------- Main Entry ----------
void setup() {
  Serial.begin(115200);
  delay(200);
  ++bootCount;
  Serial.printf("🔄 Boot #%d\n", bootCount);
  unsigned long startMillis = millis();
  pinMode(BME_CS, OUTPUT);    digitalWrite(BME_CS, HIGH);
  pinMode(RFID_CS, OUTPUT);   digitalWrite(RFID_CS, HIGH);
  pinMode(DIAG_PIN, INPUT_PULLUP);
  pinMode(REGULATOR_EN_PIN, OUTPUT); digitalWrite(REGULATOR_EN_PIN, HIGH);
  pinMode(LORA_RST, OUTPUT);  digitalWrite(LORA_RST, HIGH);
  gpio_hold_dis((gpio_num_t)REGULATOR_EN_PIN);
  gpio_hold_en((gpio_num_t)REGULATOR_EN_PIN);
  SPI.begin(SCK, MISO, MOSI);
deselectAllSPI();
delay(500);
digitalWrite(BME_CS, LOW);
if (!bme.begin(BME_CS)) {
  Serial.println("❌ BME280 init failed");
} else {
  Serial.println("✅ BME280 ready");
}
digitalWrite(BME_CS, HIGH);
  rfid.PCD_Init();
  byte version = rfid.PCD_ReadRegister(rfid.VersionReg);
Serial.print("🔧 RFID VersionReg: 0x");
Serial.println(version, HEX);
if (version == 0x00) {
  Serial.println("❌ ERROR: RFID not responding. Check CS line, SPI wiring, or MISO pull-up.");
} else if (version == 0x91 || version == 0x92) {
  Serial.println("✅ MFRC522 detected.");
} else {
  Serial.println("⚠️ Unknown MFRC522 version — may still function.");
}
// Try connecting to previously saved network
WiFi.mode(WIFI_STA);
WiFi.begin();
Serial.println("📶 Attempting WiFi connection...");
unsigned long wifiStart = millis();
while (WiFi.status() != WL_CONNECTED && millis() - wifiStart < 10000) {
  delay(250);
  Serial.print(".");
}
Serial.println();
// Check connection status
if (WiFi.status() == WL_CONNECTED) {
  Serial.println("✅ Connected to saved WiFi");
  wifiOK = true;
  String ssid = WiFi.SSID();
  isEncodedHost = ssid.startsWith("ESP32_HOST") || ssid.startsWith("FiltSure");
} else {
  Serial.println("❌ Failed to connect to saved WiFi — switching to encoded fallback.");
  isEncodedHost = true;
}
  batteryVoltage = analogRead(BATTERY_PIN) * (3.0 / 4095.0) * 2.0;
  batteryPercent = getBatteryPercentage(batteryVoltage);
  windSpeed = analogRead(WIND_PIN) * (3.0 / 4095.0);
  readSensors();
  buildURL();
  bool bmeOK = !isnan(Temp);
  bool rfidOK = !rfidUID.isEmpty();
  bool loraOK = radio.init();
  checkDiagnosticsMode(bmeOK, rfidOK, batteryPercent, wifiOK, loraOK);
  // ---------- Upload Logic with Timeout Handling ----------
  bool uploadSuccess = false;
  if (wifiOK) {
    uploadSuccess = HTTP_send();
    if (!uploadSuccess && tryEncodedHostFallback && millis() - startMillis < TIMEOUT_MS) {
      Serial.println("⚠️ Upload to Sheets failed, trying encoded host fallback...");
      isEncodedHost = true;
      buildURL();
      uploadSuccess = HTTP_send();
    }
    if (!uploadSuccess && millis() - startMillis >= TIMEOUT_MS) {
      Serial.println("⚠️ Timeout exceeded or fallback disabled.");
    }
  }
  if (!uploadSuccess && millis() - startMillis < TIMEOUT_MS) {
    Serial.println("📡 Trying LoRa fallback...");
    uploadSuccess = LoRa_sendAndVerify();
    Serial.println(uploadSuccess ? "✅ LoRa upload success" : "❌ LoRa upload failed");
  } else if (!uploadSuccess) {
    Serial.println("🚫 Upload attempts exceeded timeout — aborting transmission.");
  }
  esp_sleep_enable_timer_wakeup(sleep_Time * us_S);
  prepareRegulatorPin();
  Serial.println("💤 Going to deep sleep...");
  Serial.flush();
  esp_deep_sleep_start();
}
void loop() {}