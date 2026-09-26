/*
 * SafeDrive Edge — Motor-Only Alert Controller (buzzer skipped for now)
 * -----------------------------------------------------------------------
 * Drives ONE vibration motor through relay channel 1 (GPIO 26).
 * Receives simple on/off commands from the laptop over Wi-Fi/HTTP.
 *
 * Endpoints:
 *   GET /alert/on   -> start pulsing the motor (drowsy)
 *   GET /alert/off  -> stop the motor (safe)
 *   GET /status     -> "OK" + uptime, for a connection check
 */

#include <WiFi.h>
#include <WebServer.h>

// ---------------- USER CONFIG ----------------
const char* WIFI_SSID     = "NIRMAAN-2026";
const char* WIFI_PASSWORD = "Nirmaan25hr";

const int PIN_RELAY_MOTOR = 26;          // the channel you already wired and tested

// Flip this to false if your relay clicked ON during the HIGH phase of your earlier test
const bool RELAY_ACTIVE_LOW = true;

// Motor pulse pattern while alert is "on" (buzz-pause-buzz-pause...)
const unsigned long PULSE_ON_MS  = 400;
const unsigned long PULSE_OFF_MS = 300;

// If no command arrives for this long while alert is "on", auto-shut-off (safety)
const unsigned long HEARTBEAT_TIMEOUT_MS = 5000;

// ---------------- STATE ----------------
WebServer server(80);
bool alertActive = false;
unsigned long lastCommandMillis = 0;
unsigned long lastPulseToggleMillis = 0;
bool pulsePhaseOn = false;

void setRelay(bool energize) {
  bool level = RELAY_ACTIVE_LOW ? !energize : energize;
  digitalWrite(PIN_RELAY_MOTOR, level ? HIGH : LOW);
}

// ---------------- WIFI ----------------
void setupWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(250);
    Serial.print(".");
    attempts++;
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("Connected! ESP32 IP address: ");
    Serial.println(WiFi.localIP());
    Serial.println(">>> Copy this IP into your Python script's ESP32_IP variable <<<");
  } else {
    Serial.println("WiFi failed to connect — check SSID/password, will keep retrying in background.");
  }
}

// ---------------- HTTP HANDLERS ----------------
void handleAlertOn() {
  alertActive = true;
  lastCommandMillis = millis();
  server.send(200, "text/plain", "OK alert=on");
}

void handleAlertOff() {
  alertActive = false;
  setRelay(false);
  server.send(200, "text/plain", "OK alert=off");
}

void handleStatus() {
  server.send(200, "text/plain", "OK uptime_ms=" + String(millis()) + " alert=" + String(alertActive ? "on" : "off"));
}

void handleRoot() {
  String html = "<h2>SafeDrive Edge (motor only)</h2>"
                "<p>Alert is currently: " + String(alertActive ? "ON" : "OFF") + "</p>"
                "<p><a href='/alert/on'>Turn ON</a> | <a href='/alert/off'>Turn OFF</a></p>";
  server.send(200, "text/html", html);
}

void setupWebServer() {
  server.on("/alert/on", handleAlertOn);
  server.on("/alert/off", handleAlertOff);
  server.on("/status", handleStatus);
  server.on("/", handleRoot);
  server.begin();
  Serial.println("Web server started on port 80.");
}

// ---------------- SETUP / LOOP ----------------
void setup() {
  Serial.begin(115200);
  pinMode(PIN_RELAY_MOTOR, OUTPUT);
  setRelay(false); // start off
  setupWiFi();
  setupWebServer();
  lastCommandMillis = millis();
}

void loop() {
  server.handleClient();

  // Safety fail-off: if we haven't heard from Python in a while, stop the motor
  if (alertActive && (millis() - lastCommandMillis > HEARTBEAT_TIMEOUT_MS)) {
    Serial.println("No command received recently — failing safe, motor OFF.");
    alertActive = false;
    setRelay(false);
  }

  if (alertActive) {
    unsigned long period = pulsePhaseOn ? PULSE_ON_MS : PULSE_OFF_MS;
    if (millis() - lastPulseToggleMillis >= period) {
      pulsePhaseOn = !pulsePhaseOn;
      lastPulseToggleMillis = millis();
      setRelay(pulsePhaseOn);
    }
  }

  // Non-blocking WiFi reconnect if it ever drops
  static unsigned long lastWifiCheck = 0;
  if (WiFi.status() != WL_CONNECTED && millis() - lastWifiCheck > 5000) {
    lastWifiCheck = millis();
    Serial.println("WiFi disconnected — reconnecting...");
    WiFi.reconnect();
  }
}
