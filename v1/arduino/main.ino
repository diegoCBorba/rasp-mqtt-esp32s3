#include <WiFi.h>
#include <AsyncMqttClient.h>
#include <ArduinoJson.h>
#include <Ticker.h>

// Substitua os antigos #define por:
#include "secrets.h"

AsyncMqttClient mqttClient;
Ticker mqttReconnectTimer;
Ticker wifiReconnectTimer;

bool pumpState = false;
unsigned long pumpStartTime = 0;
unsigned long pumpDuration = 0;

unsigned long lastPublish = 0;

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

void onMqttConnect(bool sessionPresent) {
  Serial.println("MQTT conectado.");
  mqttClient.subscribe("irrigacao/command", 1);
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
  deserializeJson(doc, payload, len);

  const char* action = doc["action"];

  if (strcmp(action, "pump_on") == 0) {
    pumpDuration = doc["duration"] | 5;
    pumpState = true;
    pumpStartTime = millis();
    Serial.println("💧 Bomba LIGADA");
  }

  if (strcmp(action, "pump_off") == 0) {
    pumpState = false;
    Serial.println("🛑 Bomba DESLIGADA");
  }
}

void publishMockTelemetry() {

  StaticJsonDocument<256> doc;

  doc["flow1"] = random(100, 200) / 100.0;
  doc["flow2"] = random(80, 180) / 100.0;
  doc["diff_raw"] = 0.12;
  doc["diff_abs"] = 0.12;
  doc["diff_ma"] = 0.10;
  doc["vol_total"] = random(1, 10);

  char buffer[256];
  size_t n = serializeJson(doc, buffer);

  mqttClient.publish("irrigacao/telemetry", 0, false, buffer, n);

  Serial.println("📤 Telemetria enviada");
}

void setup() {
  Serial.begin(115200);

  WiFi.onEvent(onWifiConnect, WiFiEvent_t::ARDUINO_EVENT_WIFI_STA_GOT_IP);
  WiFi.onEvent(onWifiDisconnect, WiFiEvent_t::ARDUINO_EVENT_WIFI_STA_DISCONNECTED);

  mqttClient.onConnect(onMqttConnect);
  mqttClient.onDisconnect(onMqttDisconnect);
  mqttClient.onMessage(onMqttMessage);

  mqttClient.setServer(MQTT_HOST, MQTT_PORT);

  connectToWifi();
}

void loop() {
  // Controle automático da bomba
  if (pumpState && millis() - pumpStartTime >= pumpDuration * 1000) {
    pumpState = false;
    Serial.println("⏱️ Bomba DESLIGADA automaticamente");
  }

  // Publicação periódica mock
  if (millis() - lastPublish > 1000 && mqttClient.connected()) {
    publishMockTelemetry();
    lastPublish = millis();
  }
}