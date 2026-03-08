# README — Sistema IoT de Irrigação (versão 3)

**Projeto:** Sistema Automatizado de Irrigação com ESP32-S3 + Backend Python
**Arquitetura:** ESP32-S3 + Broker MQTT (Mosquitto) + Raspberry Pi (Python)

---

# 1 - Objetivo desta Versão

Simplificar o sistema removendo a telemetria de sensores de fluxo, que foi substituída
por cálculo empírico de vazão feito offline. O ESP32-S3 passa a ter uma responsabilidade
única e clara: acionar o relé que controla a bomba d'água, respondendo a comandos do
Raspberry Pi via MQTT.

---

# 2 - Arquitetura Atualizada
```
ESP32-S3
  ├─ Publica: irrigacao/{device_id}/status      (com retain)
  ├─ Publica: irrigacao/{device_id}/heartbeat
  └─ Assina:  irrigacao/{device_id}/command
              ↑
      MQTT Broker (Mosquitto)
  ├─ ACL restringe tópicos por usuário
  └─ LWT mantém "status" em offline se o ESP cair
              ↓
Backend Python (Raspberry Pi)
  ├─ Assina: status, heartbeat
  └─ Publica: command
```

Broker utilizado: **Eclipse Mosquitto** com autenticação e ACL configuradas.

---

# 3 - Estrutura de Tópicos

| Tópico                            | Direção       | Função / Observações                                   |
| --------------------------------- | ------------- | ------------------------------------------------------ |
| `irrigacao/{device_id}/status`    | ESP → Broker  | Estado atual da bomba (`{"pump":"on/off",…}`) retain  |
| `irrigacao/{device_id}/heartbeat` | ESP → Backend | Uptime em segundos a cada 30 s                         |
| `irrigacao/{device_id}/command`   | Backend → ESP | Backend envia `pump_on`/`pump_off` com QoS 1           |

*Tópico de telemetria removido nesta versão — vazão controlada por cálculo empírico.*

---

# 4 - Funcionalidades

## Segurança e Controle de Acesso

* Usuários `esp32_01` e `backend` definidos no Mosquitto
* Acesso anônimo desativado
* ACL que permite somente leitura/escrita nos tópicos específicos por usuário

## Controle da Bomba com Relé

* Relé de 1 canal (ativo-baixo) conectado ao **pino 4** do ESP32-S3
* `backend` envia:
  * `pump_on` com duração em segundos
  * `pump_off`
* ESP32 aciona/desaciona o relé diretamente e monitora o tempo, desligando
  automaticamente quando o período expira
* Relé inicializado em estado **desligado** no boot, antes de qualquer conexão

## Last Will and Testament (LWT)

* Configurado no cliente ESP32 antes de conectar
* Broker publica automaticamente `{"pump":"offline","online":false}`
  no tópico `irrigacao/{device_id}/status` com `retain=true` caso o ESP desconecte
  abruptamente
* Mensagem retida garante que qualquer novo inscrito saiba do estado real do dispositivo

## Heartbeat

* ESP32 publica uptime (`{"uptime_s": 123, "online": true}`) a cada 30 s
* Heartbeat imediato ao conectar ao broker
* Backend executa watchdog interno (rodando a cada 15 s) e dispara aviso se
  nenhum heartbeat for recebido em 45 s — cobre travamentos silenciosos que o LWT
  não detecta

---

# 5 - Fluxo de Operação

1. ESP conecta ao Wi-Fi com credenciais de `esp32_01`
2. Estabelece sessão MQTT autenticada com o broker
3. Publica status inicial `{"pump":"off","online":true}` com retain
4. Publica heartbeat imediato e a cada 30 s
5. Backend envia `pump_on` com duração
6. ESP aciona o relé (pino 4) e publica `status` com `pump: on`
7. Após a duração expirar, ESP desaciona o relé e publica `pump: off`
8. Se o ESP cair de forma abrupta, broker dispara LWT e backend notifica offline
9. Se o backend não receber heartbeat por 45 s, watchdog emite alerta

---

# 6 - Tecnologias

* **Broker:** Eclipse Mosquitto (com usuários/ACL configurados)
* **ESP32:** Arduino Framework, AsyncMqttClient, ArduinoJson, Ticker
* **Backend:** Python 3, paho-mqtt

---

# 7 - Itens Concluídos

* Autenticação MQTT
* ACL por tópico
* Controle de bomba com duração via relé (pino 4)
* LWT com retain state
* Heartbeat + watchdog
* Remoção da telemetria mock e dos sensores de fluxo

## Em aberto

* Integrar lógica de acionamento automático via YOLO (Raspberry Pi)
* Adicionar TLS
* Implementar persistência de eventos (banco de dados)
* Desenvolver dashboard web

---

**Use esta pasta (`v3/`) para a versão de controle direto de relé sem telemetria de fluxo.**