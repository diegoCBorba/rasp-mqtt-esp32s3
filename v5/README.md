# README — Sistema IoT de Irrigação (versão 5)

**Projeto:** Sistema Automatizado de Irrigação com ESP32-S3 + Backend Python + Visão Computacional
**Arquitetura:** ESP32-S3 + ESP32-CAM + Broker MQTT (Mosquitto) + Raspberry Pi (Python) + Supabase + Next.js

---

# 1 - Objetivo desta Versão

Integrar o pipeline de visão computacional ao sistema de controle MQTT, formando um sistema
completo e autônomo. O Raspberry Pi passa a orquestrar todo o fluxo: captura imagem da
ESP32-CAM, roda inferência com o modelo YOLO (ONNX), decide a duração de irrigação com base
na fase de crescimento detectada e envia o comando diretamente para o ESP32-S3 via MQTT.

---

# 2 - Arquitetura

```
ESP32-CAM
  └─ Fornece imagem via HTTP (/capture)
              ↓
ESP32-S3
  ├─ Publica: irrigacao/{device_id}/status      (com retain)
  ├─ Publica: irrigacao/{device_id}/heartbeat
  ├─ Assina:  irrigacao/{device_id}/command
  └─ Aciona:  Relé (pino 4) via transistor BC547
              ↑↓
      MQTT Broker (Mosquitto)
  ├─ ACL restringe tópicos por usuário
  └─ LWT mantém "status" em offline se o ESP cair
              ↓
Raspberry Pi — main.py (orquestrador)
  ├─ Captura imagem da ESP32-CAM
  ├─ Inferência ONNX (YOLO Nano)
  ├─ Decide duração de irrigação por fase
  ├─ Publica pump_on/pump_off via MQTT
  ├─ Persiste detecção no Supabase
  ├─ Monitora heartbeat (watchdog)
  └─ Escreve estado em tempo real no Supabase
              ↓
          Supabase
  ├─ Tabela device_state  — estado em tempo real (upsert)
  ├─ Tabela registro      — histórico de detecções (insert)
  └─ Bucket registros     — imagens capturadas
              ↓
      Next.js (Dashboard)
  ├─ Leitura inicial da tabela ao abrir a página
  └─ Realtime mantém estado atualizado via WebSocket
```

---

# 3 - Estrutura de Tópicos MQTT

| Tópico                            | Direção       | Função / Observações                                  |
| --------------------------------- | ------------- | ----------------------------------------------------- |
| `irrigacao/{device_id}/status`    | ESP → Broker  | Estado atual da bomba (`{"pump":"on/off",…}`) retain |
| `irrigacao/{device_id}/heartbeat` | ESP → Backend | Uptime em segundos a cada 30 s                        |
| `irrigacao/{device_id}/command`   | Backend → ESP | Backend envia `pump_on`/`pump_off` com QoS 1          |

---

# 4 - Estrutura do Projeto

```
v5/
├── main.py                        ← orquestrador único
├── .env.example
├── configs/
│   └── config.py                  ← todas as variáveis centralizadas
├── mqtt/
│   ├── client.py                  ← conexão e callbacks
│   ├── handlers.py                ← _handle_status(), _handle_heartbeat()
│   ├── commands.py                ← pump_on(), pump_off()
│   └── watchdog.py                ← check_heartbeat_watchdog()
├── vision/
│   ├── capture.py                 ← captura de imagem da ESP32-CAM
│   └── detector.py                ← ONNXDetector — inferência + NMS
├── irrigation/
│   └── decision.py                ← fase detectada → duração de irrigação
├── database/
│   ├── supabase_client.py         ← cliente Supabase singleton
│   ├── device_state.py            ← upsert de estado em tempo real
│   └── registry.py                ← upload de imagem + registro de detecção
├── utils/
│   └── logger.py                  ← logs locais em arquivo
├── models/
│   └── best_nano.onnx
├── captured_images/
└── logs/
```

---

# 5 - Funcionalidades

## Visão Computacional

* ESP32-CAM fornece imagem via requisição HTTP (`/capture`)
* Imagem pré-processada: rotação 90° anti-horária, redimensionamento 640×640, normalização
* Modelo YOLO Nano exportado em ONNX, rodando via `onnxruntime` no Raspberry Pi
* Detecta 3 fases do ciclo de cultivo do coentro hidropônico:
  * `fase_1` — germinação
  * `fase_2` — crescimento vegetativo
  * `fase_3` — maturação

## Decisão de Irrigação

* Cada fase mapeada para uma duração de irrigação em segundos (`IRRIGATION_DURATION`)
* Se nenhuma fase for detectada, irriga com duração padrão de segurança (`IRRIGATION_DEFAULT_DURATION`)
* Valores provisórios — ajustar conforme calibração empírica em andamento

## Controle da Bomba com Relé

* Relé de 1 canal acionado via transistor BC547 conectado ao **pino 4** do ESP32-S3
* Lógica ativo-alto: `HIGH` liga, `LOW` desliga
* Backend envia `pump_on` com duração em segundos ou `pump_off`
* ESP32 desliga automaticamente após a duração expirar

## Segurança e Controle de Acesso MQTT

* Usuários `esp32_01` e `backend` com ACL por tópico no Mosquitto
* Acesso anônimo desativado

## LWT e Heartbeat

* LWT publica `{"pump":"offline","online":false}` com retain em caso de queda abrupta
* Heartbeat a cada 30 s com uptime do ESP32
* Watchdog no backend alerta se heartbeat não chegar em 45 s

## Persistência — Supabase

| Destino | Responsável | Frequência | Conteúdo |
|---|---|---|---|
| `device_state` | `database/device_state.py` | A cada status/heartbeat | Estado em tempo real — 1 linha sobrescrita |
| `registro` | `database/registry.py` | A cada ciclo de inferência | Fase detectada, fase usada, duração, URL da imagem |
| bucket `registros` | `database/registry.py` | A cada ciclo de inferência | Imagem capturada pela ESP32-CAM |

---

# 6 - Fluxo de Operação

1. Raspberry inicializa: carrega modelo ONNX e conecta ao broker MQTT
2. ESP32-S3 conecta, publica status inicial e heartbeat imediato
3. Raspberry aguarda conexão estabilizar e inicia o loop principal
4. A cada `LOOP_INTERVAL_SECONDS` (padrão: 1 hora):
   - Captura imagem da ESP32-CAM
   - Roda inferência YOLO
   - Decide duração de irrigação pela fase detectada
   - Envia `pump_on` com duração ao ESP32 via MQTT
   - ESP32 aciona o relé e publica status
   - Raspberry persiste detecção e imagem no Supabase
   - Raspberry grava log local
5. Watchdog roda a cada 15 s em paralelo
6. Supabase Realtime propaga mudanças ao dashboard Next.js

---

# 7 - Tecnologias

* **Broker:** Eclipse Mosquitto (com usuários/ACL configurados)
* **ESP32:** Arduino Framework, AsyncMqttClient, ArduinoJson, Ticker
* **Backend:** Python 3, paho-mqtt, onnxruntime, opencv-python, supabase-py
* **Modelo:** YOLO Nano exportado em ONNX
* **Banco de dados:** Supabase (PostgreSQL + Storage + Realtime)
* **Frontend:** Next.js, @supabase/supabase-js

---

# 8 - Variáveis de Ambiente

```
MQTT_BROKER=192.168.x.x
MQTT_PORT=1883
MQTT_USER=backend
MQTT_PASSWORD=sua_senha
DEVICE_ID=esp32_01

ESP32_CAM_URL=http://192.168.x.x/capture

SUPABASE_URL=https://xxxxxxxxxxx.supabase.co
SUPABASE_KEY=sua_service_role_key
```

---

# 9 - Itens Concluídos

* Autenticação MQTT e ACL por tópico
* Controle de bomba com relé via transistor BC547 (pino 4)
* LWT com retain state
* Heartbeat + watchdog
* Captura de imagem via ESP32-CAM
* Inferência YOLO Nano em ONNX
* Decisão de irrigação por fase detectada
* Persistência de estado em tempo real no Supabase
* Histórico de detecções e imagens no Supabase
* Dashboard web em tempo real com Supabase Realtime

## Em aberto

* Calibração empírica das durações de irrigação por fase
* Integrar alertas de watchdog ao dashboard
* Adicionar TLS ao broker MQTT
* Expandir dashboard com histórico de detecções e imagens
