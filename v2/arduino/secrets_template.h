#ifndef SECRETS_H
#define SECRETS_H

#include <IPAddress.h>

#define WIFI_SSID "NOME_DA_SUA_REDE"
#define WIFI_PASSWORD "SUA_SENHA_AQUI"

#define MQTT_HOST IPAddress(0, 0, 0, 0) // Coloque o IP do seu Broker/Raspberry
#define MQTT_PORT 1883

#define MQTT_USER "esp32_01" // Coloque o nome de usuário do seu Broker/Raspberry
#define MQTT_PASSWORD "180803" // Coloque a senha do seu Broker/Raspberry

#endif