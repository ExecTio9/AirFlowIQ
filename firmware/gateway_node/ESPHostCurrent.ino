// ===== ESP32-C6 Gateway Host (AP + optional proxy + telnet + optional LoRa) =====
#include <WiFi.h>
#include <WebServer.h>
#include <WiFiClient.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <RH_RF95.h>

// --- IDF Wi-Fi control (needed for TX power, bandwidth, country)
extern "C" {
  #include "esp_wifi.h"
}

// ---------------- Build-time switches ----------------
#define LORA_ENABLED        0     // 1 if the RFM95 is wired
#define BACKHAUL_ENABLED    0     // 1 to also join an upstream WiFi for internet proxy
#define PROXY_TO_GOOGLE     1     // if backhaul connected, forward to Google and then return "OK"

// ---------------- Wi-Fi AP (sensor connects here) ----------------
#define WIFI_AP_SSID  "ESP32_HOST_GW"
#define WIFI_AP_PASS  "FiltSure_Rules"   // keep it simple; sensor just needs to join

// ---------------- Optional backhaul STA (for proxy) ----------------
#define BACKHAUL_SSID  "YourBackhaulSSID"
#define BACKHAUL_PASS  "YourBackhaulPass"
#define USE_PC_RELAY   1
#define PC_RELAY_IP    "192.168.4.2"   // set to your computer’s IP on the ESP AP
#define PC_RELAY_PORT  8080

// ---------------- SPI & LoRa pins (C6) ----------------
// Only used if LORA_ENABLED == 1
#define SPI_SCK     4
#define SPI_MISO    5
#define SPI_MOSI   15
#define RFM95_CS    2
#define RFM95_IRQ  18
#define RF95_FREQ  915.0

// ---------------- Globals ----------------
WebServer   server(80);
WiFiServer  telnetServer(23);
WiFiClient  telnetClient;
#if LORA_ENABLED
RH_RF95 rf95(RFM95_CS, RFM95_IRQ);
#endif

bool     g_pcRelaySet = false;
IPAddress g_pcRelayIP;
uint16_t  g_pcRelayPort = PC_RELAY_PORT;

// Runtime comm flags (manual override via telnet)
bool forceWiFi = true;
bool forceLoRa = false;
bool autoComm  = true;

// ---------------- Helpers ----------------
static inline void telnetPrintln(const String& s) {
  if (telnetClient && telnetClient.connected()) telnetClient.println(s);
}

static String urlDecode(const String& in) {
  String out; out.reserve(in.length());
  for (size_t i=0; i<in.length(); ++i) {
    char c = in[i];
    if (c == '+') { out += ' '; }
    else if (c == '%' && i+2 < in.length()) {
      char h1 = in[i+1], h2 = in[i+2];
      auto hex = [](char ch)->int {
        if (ch>='0'&&ch<='9') return ch-'0';
        if (ch>='a'&&ch<='f') return 10+ch-'a';
        if (ch>='A'&&ch<='F') return 10+ch-'A';
        return -1;
      };
      int hi = hex(h1), lo = hex(h2);
      if (hi>=0 && lo>=0) { out += char((hi<<4)|lo); i+=2; }
      else { out += c; }
    } else {
      out += c;
    }
  }
  return out;
}

// ---------------- HTTP handlers ----------------
void handleRoot() {
  String html =
    "<html><body><h3>ESP32-C6 Host</h3>"
    "<p>Use <code>/data?url=...</code> from the sensor.</p>"
    "<p>AP SSID: <b>" + String(WIFI_AP_SSID) + "</b></p>"
    "<p>Backhaul: " + String(
      (BACKHAUL_ENABLED && WiFi.status()==WL_CONNECTED) ? "Connected" : "Not connected"
    ) + "</p>"
    "</body></html>";
  server.send(200, "text/html", html);
}

void handleRegisterRelay() {
  g_pcRelayIP = server.client().remoteIP();
  g_pcRelaySet = true;
  if (server.hasArg("port")) g_pcRelayPort = server.arg("port").toInt();
  String msg = "PC relay registered: " + g_pcRelayIP.toString() + ":" + String(g_pcRelayPort);
  Serial.println("[/register-relay] " + msg);
  server.send(200, "text/plain", msg);
}

void handleStatus() {
  String json = "{";
  json += "\"ap_ip\":\"" + WiFi.softAPIP().toString() + "\",";
  json += "\"sta_connected\":" + String((WiFi.status()==WL_CONNECTED) ? "true":"false") + ",";
  json += "\"force_wifi\":" + String(forceWiFi ? "true":"false") + ",";
  json += "\"force_lora\":" + String(forceLoRa ? "true":"false") + ",";
  json += "\"auto_comm\":"  + String(autoComm  ? "true":"false") + ",";
#if LORA_ENABLED
  json += "\"lora\":\"enabled\"";
#else
  json += "\"lora\":\"disabled\"";
#endif
  json += "}";
  server.send(200, "application/json", json);
}

void handleData() {
  if (!server.hasArg("url")) { 
    server.send(400, "text/plain", "Missing 'url'"); 
    return; 
  }

  // 'url' is the percent-encoded Google path we wrapped earlier.
  const String encoded = server.arg("url");
  const String decoded = urlDecode(encoded);                // "/macros/s/.../exec?sts=write&..."

  // Print a tagged line for the PC to catch and forward.
  // (Don't keep Serial Monitor open while the PC script is running.)
  const String httpUrl = "http://script.google.com" + decoded;
  Serial.print("[SERIALFWD]");
  Serial.println(httpUrl);
  Serial.flush();

  // Immediately acknowledge the sensor so it can go to sleep.
  server.send(200, "text/plain", "OK");
}

// ---------------- Telnet commands ----------------
void handleTelnetCommand(String cmd) {
  cmd.trim();
  if (cmd == "status") {
    telnetPrintln("📡 Comm Mode:");
    telnetPrintln(String("  WiFi: ") + (forceWiFi ? "ENABLED" : "DISABLED"));
    telnetPrintln(String("  LoRa: ") + (forceLoRa ? "ENABLED" : "DISABLED"));
    telnetPrintln(String("  Auto: ") + (autoComm  ? "ENABLED" : "DISABLED"));
#if LORA_ENABLED
  } else if (cmd == "diag_ping") {
    telnetPrintln("📟 Sending LoRa diagnostic ping...");
    const char* pingMsg = "ping";
    rf95.send((uint8_t*)pingMsg, strlen(pingMsg));
    rf95.waitPacketSent();
    uint8_t buf[RH_RF95_MAX_MESSAGE_LEN]; uint8_t len = sizeof(buf);
    if (rf95.waitAvailableTimeout(1000) && rf95.recv(buf, &len)) {
      String response; response.reserve(len);
      for (uint8_t i = 0; i < len; ++i) response += (char)buf[i];
      telnetPrintln(response == "pong" ? "✅ Pong received from node!" : ("⚠️ Unexpected: " + response));
    } else {
      telnetPrintln("❌ No pong received");
    }
#else
  } else if (cmd == "diag_ping") {
    telnetPrintln("ℹ️ LoRa disabled (LORA_ENABLED=0).");
#endif
  } else if (cmd == "force_wifi") {
    forceWiFi = true; forceLoRa = false; autoComm = false; telnetPrintln("✅ WiFi forced");
  } else if (cmd == "force_lora") {
    forceWiFi = false; forceLoRa = true; autoComm = false; telnetPrintln("✅ LoRa forced");
  } else if (cmd == "auto_comm") {
    forceWiFi = false; forceLoRa = false; autoComm = true; telnetPrintln("✅ Auto comm mode enabled");
  } else if (cmd == "reboot") {
    telnetPrintln("🔁 Rebooting..."); delay(300); ESP.restart();
  } else if (cmd == "sleep") {
    telnetPrintln("💤 Going to sleep..."); delay(100); esp_deep_sleep_start();
  } else {
    telnetPrintln("❌ Unknown command");
  }
}

// ---------------- NEW: Apply RF “range” hints (C6-safe, IDF-level) ----------------
static void applyWiFiRFHints() {
  // Keep RF fully awake (STA side). AP has no PS.
  WiFi.setSleep(false);

  // Max TX power cap: units are 0.25 dBm -> 78 = 19.5 dBm
  esp_wifi_set_max_tx_power(78);

  // Regulatory domain / power table
  wifi_country_t country = {
    .cc = "US",
    .schan = 1,
    .nchan = 11,
    .max_tx_power = 78,
    .policy = WIFI_COUNTRY_POLICY_MANUAL
  };
  esp_wifi_set_country(&country);

  // Prefer 20 MHz on both STA and AP for better SNR in crowded bands
  esp_wifi_set_bandwidth(WIFI_IF_STA, WIFI_BW_HT20);
  esp_wifi_set_bandwidth(WIFI_IF_AP,  WIFI_BW_HT20);

  // Optional: allow legacy rates for long-range robustness
  // esp_wifi_set_protocol(WIFI_IF_STA, WIFI_PROTOCOL_11B | WIFI_PROTOCOL_11G | WIFI_PROTOCOL_11N);

  // ---- Diagnostics (so you can confirm the settings took) ----
  int8_t q = 0;
  if (esp_wifi_get_max_tx_power(&q) == ESP_OK) {
    Serial.printf("[RF] Max TX power: %.2f dBm\n", q / 4.0f);
  }
  wifi_country_t cur{};
  if (esp_wifi_get_country(&cur) == ESP_OK) {
    Serial.printf("[RF] Country: %c%c, ch=%d..%d, policy=%d\n",
      cur.cc[0], cur.cc[1], cur.schan, cur.schan + cur.nchan - 1, cur.policy);
  }
  wifi_bandwidth_t bw;
  if (esp_wifi_get_bandwidth(WIFI_IF_AP, &bw) == ESP_OK) {
    Serial.printf("[RF] AP  bandwidth: %s\n", (bw==WIFI_BW_HT40)?"HT40":"HT20");
  }
  if (esp_wifi_get_bandwidth(WIFI_IF_STA, &bw) == ESP_OK) {
    Serial.printf("[RF] STA bandwidth: %s\n", (bw==WIFI_BW_HT40)?"HT40":"HT20");
  }
}

// ---------------- Setup ----------------
void setup() {
  Serial.begin(115200);
  unsigned long t0 = millis();
  server.on("/register-relay", HTTP_GET, handleRegisterRelay);
  while (!Serial && millis() - t0 < 1500) {}   // brief wait for USB-CDC
  Serial.printf("\n[BOOT] ESP32-C6 Host | LoRa=%d, Backhaul=%d, Proxy=%d\n",
                LORA_ENABLED, BACKHAUL_ENABLED, PROXY_TO_GOOGLE);

  // WiFi mode first, then apply RF hints, THEN start AP/backhaul
  WiFi.mode(BACKHAUL_ENABLED ? WIFI_MODE_APSTA : WIFI_MODE_AP);
  applyWiFiRFHints();  // <<—— apply before softAP / STA connect

  // WiFi AP (sensor connects here)
  if (WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASS)) {
    Serial.print("[WiFi] AP SSID: "); Serial.println(WIFI_AP_SSID);
    Serial.print("[WiFi] AP IP:   "); Serial.println(WiFi.softAPIP()); // should be 192.168.4.1
  } else {
    Serial.println("[WiFi] softAP start FAILED");
  }

#if BACKHAUL_ENABLED
  // Backhaul STA (optional)
  WiFi.begin(BACKHAUL_SSID, BACKHAUL_PASS);
  Serial.print("[WiFi] Connecting backhaul ");
  Serial.print(BACKHAUL_SSID); Serial.print(" ... ");
  uint32_t w = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - w < 10000) { delay(250); Serial.print("."); }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("[WiFi] Backhaul connected, STA IP: "); Serial.println(WiFi.localIP());
  } else {
    Serial.println("[WiFi] Backhaul not connected (proxy will be skipped).");
  }
#endif

  // HTTP server
  server.on("/", HTTP_GET, handleRoot);
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/data", HTTP_GET, handleData);
  server.begin();
  Serial.println("[HTTP] Server ready: /, /status, /data");

  // Telnet
  telnetServer.begin();
  telnetServer.setNoDelay(true);
  Serial.println("[TELNET] Listening on port 23");

#if LORA_ENABLED
  // LoRa SPI
  SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI);
  pinMode(RFM95_CS, OUTPUT);  digitalWrite(RFM95_CS, HIGH);
  pinMode(RFM95_IRQ, INPUT_PULLUP);

  if (!rf95.init()) {
    Serial.println("[LoRa] Init FAILED (check CS/IRQ/SPI pins & wiring)");
  } else {
    rf95.setFrequency(RF95_FREQ);
    rf95.setTxPower(5, false);
    Serial.println("[LoRa] Ready");
  }
#else
  Serial.println("[LoRa] Disabled at build time");
#endif
}

// ---------------- Loop ----------------
void loop() {
  // HTTP
  server.handleClient();

  // Telnet accept
  if (!telnetClient || !telnetClient.connected()) {
    WiFiClient newClient = telnetServer.available();
    if (newClient) {
      telnetClient = newClient;
      telnetPrintln("Welcome to ESP32-C6 Host Telnet.");
      telnetPrintln("Commands: status | force_wifi | force_lora | auto_comm | diag_ping | reboot | sleep");
    }
  }
  // Telnet read
  if (telnetClient && telnetClient.connected() && telnetClient.available()) {
    String input = telnetClient.readStringUntil('\n');
    handleTelnetCommand(input);
  }

#if LORA_ENABLED
  // LoRa RX pass-through to serial/telnet
  if (rf95.available()) {
    uint8_t buf[RH_RF95_MAX_MESSAGE_LEN]; uint8_t len = sizeof(buf);
    if (rf95.recv(buf, &len)) {
      Serial.print("[LoRa RX] "); Serial.write(buf, len); Serial.println();
      if (telnetClient && telnetClient.connected()) {
        telnetClient.print("[LoRa RX] "); telnetClient.write(buf, len); telnetClient.println();
      }
    }
  }
#endif

  // Heartbeat
  static uint32_t lastBeat = 0;
  if (millis() - lastBeat > 1000) {
    lastBeat = millis();
    Serial.println("[HB] alive");
  }
  delay(2);
}
