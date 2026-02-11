#include <WiFi.h>
#include <WiFiManager.h>
#include <HTTPClient.h>
/* ===================== */
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <MFRC522.h>
#include <RH_RF95.h>
/* ========================= */
#include <esp32-hal-rgb-led.h>
#include <driver/usb_serial_jtag.h>
#include <esp_sleep.h>

extern "C" {
  #include "esp_wifi.h"
  #include "esp_system.h"
}

/* ===================== FEATURE FLAGS ===================== */
#define USE_BME 1

/* ===================== PINS ===================== */
#define BATTERY_PIN       0
#define DIAG_PIN          2
#define WIND_PIN          3
#define SCK               4
#define MOSI              5
#define REGULATOR_EN_PIN  7
#define RGB_BUILTIN       8
#define MISO              15
#define RFID_RST          14
#define RFID_CS           22
#define BME_CS            23
#define LORA_CS           21
#define LORA_RST          20
#define LORA_INT          18

/* ===================== TIMING ===================== */
#define us_S              1000000ULL
#define sleep_Time        60
#define TIMEOUT_MS        30000
#define RFID_TIMEOUT_MS   15000

/* ===================== SUPABASE ===================== */
static const char* SUPABASE_INGEST_URL = "";
static const char* SUPABASE_ANON_KEY = "";
#define LOG(x) Serial.println(x)

/* ===================== HOST RELAY ===================== */
#define HOST_SSID ""
#define HOST_PASS ""
#define HOST_URL  ""

/* ===================== OBJECTS ===================== */
#if USE_BME
Adafruit_BME280 bme(BME_CS, MOSI, MISO, SCK);
#endif

MFRC522 rfid(RFID_CS, RFID_RST);
RH_RF95 radio(LORA_CS, LORA_INT);

RTC_DATA_ATTR int bootCount = 0;

/* ===================== STATE ===================== */
String ID;
String Status_Read_Sensor = "Init";
String rfidUID = "";

float Temp = -1, Humd = -1, Prs = -1;
float batteryVoltage = 0;
float batteryPercent = 0;
float windSpeed = 0;

/* ===================== WIND ===================== */
float Vref = 3.3;
float dividerGain = 2.0;
int ADCMax = 4095;
int WIND_OVERSAMPLES = 16;
float kMvPerRPM = 0.9;
float kVPerRPM = kMvPerRPM / 1000.0;
float ema_rpm = 0;
float alpha_ema = 0.2;
float RPM_TO_MPS = 0.002094;
float lambda_TSR = 2.5;
float D = 0.1; // Diameter

/* ===================== LORA METRICS (UNCHANGED) ===================== */
int16_t g_lastLoRaRssi = INT16_MIN;
float   g_lastLoRaSnr  = NAN;

/* ===================== HELPERS ===================== */
inline void deselectAllSPI() {
  digitalWrite(BME_CS, HIGH);
  digitalWrite(RFID_CS, HIGH);
  digitalWrite(LORA_CS, HIGH);
}

inline float pctFromBatt(float v) {
  v = (v - 2.0f);  // remove dead voltage
  float pct = v * 100.0f; // convert to percentage
  return constrain(pct, 0, 100);
}

String makeDeviceIdFromMac() {
  uint8_t mac[6];

  // Force WiFi init so MAC is populated
  WiFi.mode(WIFI_STA);
  WiFi.begin();
  delay(100);

  // Read station MAC (this is derived from base MAC)
  WiFi.macAddress(mac);

  char buf[24];
  snprintf(buf, sizeof(buf),
           "%02X%02X%02X%02X%02X%02X",
           mac[0], mac[1], mac[2],
           mac[3], mac[4], mac[5]);

  return String(buf);
}

/* ===================== RFID ===================== */
bool waitForRFID_WithTimeout(String &uidHex, uint32_t timeout_ms) {
  uidHex = "";
  unsigned long t0 = millis();

  while (millis() - t0 < timeout_ms) {
    if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {  // check for Card, new or previous
      for (byte i = 0; i < rfid.uid.size; i++) {  // for each byte read in the chain
        if (rfid.uid.uidByte[i] < 0x10) uidHex += "0"; // convert to zero if less than 16
        uidHex += String(rfid.uid.uidByte[i], HEX); // compile all bytes into hex string
      }
      uidHex.toUpperCase(); // ensure upper case format
      rfid.PICC_HaltA(); // stop running antenna
      rfid.PCD_StopCrypto1(); // stop rfid process
      return true;
    }
    delay(50);
  }
  return false;
}

/* ===================== WIND ===================== */
float readWindSpeed_mps(float &outRPM) {
  uint32_t acc = 0;
  for (int i = 0; i < WIND_OVERSAMPLES; ++i) {
    acc += analogRead(WIND_PIN);
    delayMicroseconds(150);
  }

  float adc = acc / float(WIND_OVERSAMPLES); // compile average of oversamples
  float volts = (adc / ADCMax) * Vref * dividerGain; // convert adc oversample average to voltage
  float rpm = (kVPerRPM > 0.0f) ? (volts / kVPerRPM) : 0.0f; // convert voltage to rpm
  ema_rpm = alpha_ema * rpm + (1.0f - alpha_ema) * ema_rpm; // compile rpm based on motor
  outRPM = ema_rpm;

  return RPM_TO_MPS * ema_rpm; // return estimated speed
}

/* ===================== SENSORS ===================== */
void readSensors() {
  rfid.PCD_Init(); // start rfid
  rfid.PCD_AntennaOn(); // ensure max power antenna
  waitForRFID_WithTimeout(rfidUID, RFID_TIMEOUT_MS); // run timeout sequence

#if USE_BME
  if (bme.begin(BME_CS)) { // start bme using bme_cs pin
    Temp = bme.readTemperature(); // read temperature "C"
    Humd = bme.readHumidity(); // read humidity "RH"
    Prs  = bme.readPressure() / 100.0f; // read pressure "Pa"
    Status_Read_Sensor = "Success"; // determines read succes
  } else {
    Status_Read_Sensor = "Failed"; // else determines fail
  }
#endif

  float rpm; // grab RPM adc value from fan
  windSpeed = readWindSpeed_mps(rpm); // convert to meter per second
}

/* ===================== JSON ===================== */
String buildIngestJson() { // compile string for URL data
  Serial.println("\n[JSON] Building ingest payload...");

  String json = "{";

  Serial.printf("[JSON] device_mac: %s\n", ID.c_str());
  json += "\"device_mac\":\"" + ID + "\",";

  Serial.printf("[JSON] boot: %d\n", bootCount);
  json += "\"boot\":" + String(bootCount) + ",";

  Serial.printf("[JSON] battery: %.3f V\n", batteryVoltage);
  json += "\"battery\":" + String(batteryVoltage, 3) + ",";

  Serial.printf("[JSON] temp_c: %.2f C\n", Temp);
  json += "\"temp_c\":" + String(Temp, 2) + ",";

  Serial.printf("[JSON] humidity: %.2f %%\n", Humd);
  json += "\"humidity\":" + String(Humd, 2) + ",";

  Serial.printf("[JSON] pressure_pa: %.1f Pa\n", Prs * 100.0f);
  json += "\"pressure_pa\":" + String(Prs * 100.0f, 1) + ",";

  Serial.printf("[JSON] windSpeed: %.2f\n", windSpeed);
  json += "\"windSpeed\":" + String(windSpeed, 2) + ",";

  Serial.printf("[JSON] rfid: %s\n", rfidUID.c_str());
  json += "\"rfid\":\"" + rfidUID + "\",";

  Serial.printf("[JSON] filter_status: %s\n", Status_Read_Sensor.c_str());
  json += "\"filter_status\":\"" + Status_Read_Sensor + "\",";

  Serial.println("[JSON] massAirFlow: null");
  json += "\"massAirFlow\":null";

  json += "}";

  Serial.println("[JSON] Final payload:");
  Serial.println(json);
  Serial.println("[JSON] Payload length: " + String(json.length()));
  Serial.println("[JSON] Build complete\n");

  return json;
}

/* ===================== SUPABASE ===================== */
bool postToIngest(const String& json) { // URL inject
  if (WiFi.status() != WL_CONNECTED) return false; // if the wifi is not connected defer

  HTTPClient http; //
  http.begin(SUPABASE_INGEST_URL); // begin URL injection
  http.addHeader("Content-Type", "application/json"); // add application type for sensor log injection
  http.addHeader("apikey", SUPABASE_ANON_KEY); // lable anon key for SupaBase access
  http.addHeader("Authorization", String("Bearer ") + SUPABASE_ANON_KEY); // give string SupaBase key for injection access

  int code = http.POST(json); // pull upoad code from injection result
  http.end(); // kill http access

  return (code >= 200 && code < 300);
}

/* ===================== WIFI ===================== */
static void applyWiFiRFHints() {
  WiFi.setSleep(false); // force wifi to awake 
  esp_wifi_set_max_tx_power(30); // set dB level for wifi power 1 = .25dB
}

bool trySavedWiFi(uint32_t ms_window = 8000) {
  WiFi.mode(WIFI_STA); // set mode to station (wifi terminal)
  applyWiFiRFHints();
  WiFi.begin(); // start wifi 

  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < ms_window) { // create connection timeout
    delay(250);
  }
  return (WiFi.status() == WL_CONNECTED); // display connection status
}

bool tryWiFiManagerPortal(uint16_t portal_seconds = 180) {
  WiFiManager wm; // begin wifi changer protocol
  wm.setConfigPortalTimeout(portal_seconds); // allow for connection to portal for X seconds
  return wm.autoConnect("FiltSure-Setup"); // display wifi name
}

/* ===================== UPLINK ADDITIONS ===================== */
enum UplinkMode { UPLINK_NONE, UPLINK_DIRECT, UPLINK_RELAY };
UplinkMode g_uplinkUsed = UPLINK_NONE; 

bool postToHostRelay(const String& json) {
  WiFi.mode(WIFI_OFF); // restart WiFi
  delay(200);

  WiFi.disconnect(true);
  delay(200);

  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  
  int n = WiFi.scanNetworks(); // find designated router services
  Serial.printf("🔍 %d networks found\n", n);
  for (int i = 0; i < n; i++) {
    Serial.printf("  %s (%d dBm)\n", WiFi.SSID(i).c_str(), WiFi.RSSI(i));
  }
  delay(1000);
  WiFi.begin(HOST_SSID, HOST_PASS); // connect to router if available

  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < 6000) {
    delay(250);
  }
  if (WiFi.status() != WL_CONNECTED) return false;

  Serial.printf("📡 Host WiFi status: %d\n", WiFi.status());

  HTTPClient http;
  http.begin(HOST_URL);
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");
  int code = http.POST("json=" + json);
  http.end();

  if (code == 200) { // if router not available change to relay mode
    g_uplinkUsed = UPLINK_RELAY;
    return true;
  }
  return false;
}

bool sendUplinkAuto(const String& json) {
  LOG("🌐 Uplink decision started");

  LOG("➡️ Trying direct internet (Supabase)...");
  if (postToIngest(json)) {
    LOG("✅ Direct internet upload succeeded");
    g_uplinkUsed = UPLINK_DIRECT;
    return true;
  }
  LOG("❌ Direct internet failed");

  LOG("➡️ Trying host relay...");
  if (postToHostRelay(json)) {
    LOG("✅ Host relay upload succeeded");
    g_uplinkUsed = UPLINK_RELAY;
    return true;
  }

  LOG("❌ Host relay failed");
  LOG("🛑 All uplink paths exhausted");
  g_uplinkUsed = UPLINK_NONE;
  return false;
}

/* ===================== POWER ===================== */
void enableRegulator() {
  pinMode(REGULATOR_EN_PIN, OUTPUT);
  digitalWrite(REGULATOR_EN_PIN, HIGH);
}

void disableRegulatorForSleep() {
  digitalWrite(REGULATOR_EN_PIN, LOW);
}

/* ===================== SETUP ===================== */
void setup() {
  Serial.begin(115200);
  delay(200);
  enableRegulator();

  ++bootCount;
  ID = makeDeviceIdFromMac();
  Serial.println("===== IDENTITY CHECK =====");
  Serial.print("ID (from ESP.getEfuseMac): "); Serial.println(ID);

  uint64_t mac = ESP.getEfuseMac();
  Serial.printf("eFuse raw 64-bit: 0x%llX\n", (unsigned long long)mac);

  Serial.print("WiFi STA MAC: "); Serial.println(WiFi.macAddress());
  Serial.print("WiFi AP  MAC: "); Serial.println(WiFi.softAPmacAddress());

  Serial.printf("Chip model: %s\n", ESP.getChipModel());
  Serial.printf("Chip rev: %d\n", ESP.getChipRevision());
  Serial.printf("Flash size: %u\n", ESP.getFlashChipSize());
  Serial.println("==========================");

  batteryVoltage =
    analogRead(BATTERY_PIN) * (Vref / ADCMax) * dividerGain;
  batteryPercent = pctFromBatt(batteryVoltage);

  readSensors();

  bool wifiOK = trySavedWiFi(8000);
  if (!wifiOK) wifiOK = tryWiFiManagerPortal(180);

  String json = buildIngestJson();
  bool sent = sendUplinkAuto(json);

  Serial.printf("📤 Uplink: %s\n",
    sent ? (g_uplinkUsed == UPLINK_DIRECT ? "DIRECT" : "RELAY")
         : "FAILED");

  disableRegulatorForSleep();
  esp_sleep_enable_timer_wakeup((uint64_t)sleep_Time * us_S);
  esp_deep_sleep_start();
}

void loop() {}
