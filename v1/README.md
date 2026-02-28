# README — Teste de Comunicação MQTT

**Projeto:** Sistema Automatizado de Irrigação Hidropônica
**Arquitetura:** Raspberry Pi 3B + ESP32-S3 + Broker MQTT

---

# 1️ - Objetivo do Teste

Validar a comunicação MQTT entre:

* **Raspberry Pi 3B (Python)** — controlador
* **ESP32-S3 (AsyncMqttClient)** — nó sensor/atuador
* Broker MQTT local rodando no Raspberry

Este teste simula:

* Publicação de telemetria mockada pelo ESP32
* Recebimento da telemetria pelo Raspberry
* Envio de comando `pump_on`
* Execução e desligamento automático no ESP32

---

# 2️ - Arquitetura Atual

```
ESP32-S3
  ├─ Publica: irrigacao/telemetry
  └─ Assina:  irrigacao/command
           ↓
      MQTT Broker (Mosquitto)
           ↓
Raspberry Pi (Python)
  ├─ Assina: irrigacao/telemetry
  └─ Publica: irrigacao/command
```

Broker utilizado: **Eclipse Mosquitto**

---

# 3️ - Estrutura de Tópicos

| Tópico                | Direção         | Função                          |
| --------------------- | --------------- | ------------------------------- |
| `irrigacao/telemetry` | ESP → Raspberry | Envio de dados simulados        |
| `irrigacao/command`   | Raspberry → ESP | Comando de acionamento da bomba |

---

# 4️ - Formato das Mensagens

## Telemetria (ESP → Broker)

```json
{
  "flow1": 1.45,
  "flow2": 1.20,
  "diff_raw": 0.12,
  "diff_abs": 0.12,
  "diff_ma": 0.10,
  "vol_total": 7
}
```

Publicação com:

* QoS 0
* Não-retained

---

## Comando (Raspberry → Broker)

```json
{
  "action": "pump_on",
  "duration": 10
}
```

Publicação com:

* QoS 1
* Garantia de entrega ao menos uma vez

---

# 5️ - Funcionamento Validado

### ✔ ESP32-S3

* Conexão WiFi automática
* Reconexão automática MQTT
* Publicação periódica mock
* Assinatura do tópico de comando
* Controle interno de temporização da bomba
* Desligamento automático após duração definida

### ✔ Raspberry (Python)

* Conexão ao broker
* Assinatura de telemetria
* Decodificação JSON
* Envio de comando de teste

---

# 6️ - Fluxo de Execução do Teste

1. ESP conecta ao WiFi
2. ESP conecta ao broker
3. ESP publica telemetria a cada 1 segundo
4. Raspberry recebe e imprime dados
5. Após 5 segundos, Raspberry envia `pump_on`
6. ESP ativa bomba
7. Após `duration`, bomba é desligada automaticamente

---

# 7️ - Tecnologias Utilizadas

## Raspberry

* Python 3
* Biblioteca `paho-mqtt`

## ESP32

* Arduino Framework
* Biblioteca **AsyncMqttClient**
* ArduinoJson
* Ticker

---

# 8️ - O Que Já Está Validado Arquiteturalmente

* Comunicação bidirecional via MQTT
* Serialização e desserialização JSON
* QoS 1 funcional
* Reconexão automática WiFi/MQTT
* Controle remoto de atuador
* Independência do ESP após comando recebido

---

# 9️ O Que Ainda Falta Implementar

Agora entramos na fase de maturidade do sistema.

---

## 1. Segurança

* [ ] Autenticação no broker (usuário/senha)
* [ ] Desativar acesso anônimo
* [ ] Definir ACL para tópicos
* [ ] Possível uso de TLS (se necessário)

---

## 2. Robustez

* [ ] Implementar LWT (Last Will and Testament)

  * Publicar `irrigacao/status = offline`
* [ ] Implementar heartbeat periódico
* [ ] Criar tópico `irrigacao/status`
* [ ] Implementar watchdog interno

---

## 3. Integração com Sistema Real

* [ ] Substituir valores mock pelos sensores YF-S201
* [ ] Calcular vazão real (L/min)
* [ ] Implementar média móvel real
* [ ] Calcular volume acumulado corretamente

---

## 4. Integração com YOLO

* [ ] Receber fase da planta
* [ ] Mapear fase → tempo de irrigação
* [ ] Criar política automática de irrigação
* [ ] Evitar irrigação duplicada

---

## 5. Persistência e Logs

* [ ] Publicar estado atual da bomba
* [ ] Logar comandos enviados
* [ ] Registrar tempo total de irrigação por ciclo
* [ ] Integrar com Supabase

---

## 6. Evolução da Arquitetura

Futuro recomendado:

* Criar namespace:

  ```
  irrigacao/device01/telemetry
  irrigacao/device01/command
  ```
* Permitir múltiplos nós ESP
