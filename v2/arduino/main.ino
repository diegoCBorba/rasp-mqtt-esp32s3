#include <WiFi.h>
#include <AsyncMqttClient.h>
#include <ArduinoJson.h>
#include <Ticker.h>

#include "secrets.h"

AsyncMqttClient mqttClient;
Ticker mqttReconnectTimer;
Ticker wifiReconnectTimer;

bool pumpState = false;
unsigned long pumpStartTime  = 0;
unsigned long pumpDuration   = 0;
unsigned long lastPublish    = 0;
unsigned long lastHeartbeat  = 0;

const unsigned long HEARTBEAT_INTERVAL = 30000; // 30s

char topicTelemetry[64];
char topicCommand[64];
char topicStatus[64];
char topicHeartbeat[64];

// WiFi

void connectToWifi() {
  Serial.println("Conectando ao WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
}

void connectToMqtt() {
  Serial.println("Conectando ao MQTT...");
  mqttClient.connect();
}

void onWifiConnect(const WiFiEvent_t event, const WiFiEventInfo_t info) {
  Serial.println("WiFi conectado.");
  connectToMqtt();
}

void onWifiDisconnect(const WiFiEvent_t event, const WiFiEventInfo_t info) {
  Serial.println("WiFi desconectado.");
  mqttReconnectTimer.detach();
  wifiReconnectTimer.once(2, connectToWifi);
}

// MQTT

void publishStatus() {
  StaticJsonDocument<128> doc;
  doc["pump"]   = pumpState ? "on" : "off";
  doc["online"] = true;
  char buffer[128];
  size_t n = serializeJson(doc, buffer);
  mqttClient.publish(topicStatus, 1, true, buffer, n);
  Serial.println("📤 Status enviado");
}

void publishHeartbeat() {
  StaticJsonDocument<128> doc;
  doc["uptime_s"] = millis() / 1000;
  doc["online"]   = true;

  char buffer[128];
  size_t n = serializeJson(doc, buffer);
  mqttClient.publish(topicHeartbeat, 1, false, buffer, n);
  Serial.println("💓 Heartbeat enviado");
}

void onMqttConnect(bool sessionPresent) {
  Serial.println("MQTT conectado.");

  const char* onlinePayload = "{\"pump\":\"off\",\"online\":true}";
  mqttClient.publish(topicStatus, 1, true, onlinePayload);

  mqttClient.subscribe(topicCommand, 1);
  Serial.println("✅ Inscrito em: " + String(topicCommand));

  // Heartbeat imediato ao conectar
  publishHeartbeat();
  lastHeartbeat = millis();
}

void onMqttDisconnect(AsyncMqttClientDisconnectReason reason) {
  Serial.println("MQTT desconectado.");
  if (WiFi.isConnected()) {
    mqttReconnectTimer.once(2, connectToMqtt);
  }
}

void onMqttMessage(char* topic,
                   char* payload,
                   AsyncMqttClientMessageProperties properties,
                   size_t len,
                   size_t index,
                   size_t total) {

  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, payload, len);

  if (err) {
    Serial.println("❌ Erro ao parsear JSON: " + String(err.c_str()));
    return;
  }

  const char* action = doc["action"];
  if (!action) return;

  if (strcmp(action, "pump_on") == 0) {
    pumpDuration  = doc["duration"] | 5;
    pumpState     = true;
    pumpStartTime = millis();
    Serial.printf("💧 Bomba LIGADA por %lu segundos\n", pumpDuration);
    publishStatus();
  }

  else if (strcmp(action, "pump_off") == 0) {
    pumpState = false;
    Serial.println("🛑 Bomba DESLIGADA");
    publishStatus();
  }

  else {
    Serial.println("⚠️ Ação desconhecida: " + String(action));
  }
}

// Telemetria mock

void publishMockTelemetry() {
  StaticJsonDocument<256> doc;
  doc["flow1"]     = random(100, 200) / 100.0;
  doc["flow2"]     = random(80,  180) / 100.0;
  doc["diff_raw"]  = 0.12;
  doc["diff_abs"]  = 0.12;
  doc["diff_ma"]   = 0.10;
  doc["vol_total"] = random(1, 10);

  char buffer[256];
  size_t n = serializeJson(doc, buffer);
  mqttClient.publish(topicTelemetry, 0, false, buffer, n);
  Serial.println("📤 Telemetria enviada");
}

// Setup

void setup() {
  Serial.begin(115200);

  snprintf(topicTelemetry, sizeof(topicTelemetry), "irrigacao/%s/telemetry", DEVICE_ID);
  snprintf(topicCommand,   sizeof(topicCommand),   "irrigacao/%s/command",   DEVICE_ID);
  snprintf(topicStatus,    sizeof(topicStatus),    "irrigacao/%s/status",    DEVICE_ID);
  snprintf(topicHeartbeat, sizeof(topicHeartbeat), "irrigacao/%s/heartbeat", DEVICE_ID);

  WiFi.onEvent(onWifiConnect,    WiFiEvent_t::ARDUINO_EVENT_WIFI_STA_GOT_IP);
  WiFi.onEvent(onWifiDisconnect, WiFiEvent_t::ARDUINO_EVENT_WIFI_STA_DISCONNECTED);

  mqttClient.onConnect(onMqttConnect);
  mqttClient.onDisconnect(onMqttDisconnect);
  mqttClient.onMessage(onMqttMessage);

  mqttClient.setServer(MQTT_HOST, MQTT_PORT);
  mqttClient.setCredentials(MQTT_USER, MQTT_PASSWORD);
  mqttClient.setKeepAlive(10);
  mqttClient.setWill(topicStatus, 1, true, "{\"pump\":\"offline\",\"online\":false}");

  connectToWifi();
}

// Loop

void loop() {
  if (pumpState && millis() - pumpStartTime >= pumpDuration * 1000UL) {
    pumpState = false;
    Serial.println("⏱️ Bomba DESLIGADA automaticamente");
    publishStatus();
  }

  if (millis() - lastPublish > 1000 && mqttClient.connected()) {
    publishMockTelemetry();
    lastPublish = millis();
  }

  if (millis() - lastHeartbeat > HEARTBEAT_INTERVAL && mqttClient.connected()) {
    publishHeartbeat();
    lastHeartbeat = millis();
  }
}