# README — Sistema IoT de Irrigação (versão 6)

**Projeto:** Sistema Automatizado de Irrigação com ESP32-S3 + Backend Python + Visão Computacional
**Arquitetura:** ESP32-S3 + ESP32-CAM + Broker MQTT (Mosquitto) + Raspberry Pi (Python) + Supabase + Next.js

---

# 1 - Objetivo desta Versão

Implementar o cálculo empírico de irrigação com janela de operação e ciclos automáticos de
ativação e descanso da bomba. O sistema passa a operar de forma completamente autônoma dentro
da janela de 6h às 18h, rodando ciclos contínuos de irrigação baseados na fase de crescimento
detectada pelo modelo YOLO, sem intervenção manual.

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
  ├─ Verifica janela de operação (06:00–18:00)
  ├─ Captura imagem da ESP32-CAM
  ├─ Inferência ONNX (YOLO Nano)
  ├─ Decide duração de irrigação por fase
  ├─ Controla ciclos de ativação + descanso por 1h
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
v6/
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
│   ├── decision.py                ← fase detectada → duração de irrigação
│   └── scheduler.py               ← janela de horário + ciclos ativo/descanso
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

## Decisão de Irrigação — Cálculo Empírico

* Cada fase mapeada para uma duração de ativação em minutos:

| Fase | Duração ativa | Descanso |
|---|---|---|
| `fase_1` — germinação | 10 min | 10 min |
| `fase_2` — crescimento vegetativo | 15 min | 10 min |
| `fase_3` — maturação | 20 min | 10 min |
| padrão (sem detecção) | 15 min (= fase_2) | 10 min |

* Se nenhuma fase for detectada, usa duração padrão igual à fase_2

## Janela de Operação e Ciclos Automáticos

* Sistema opera exclusivamente entre **06:00 e 18:00**
* Fora da janela, o Raspberry aguarda dormindo até as 06:00 do dia seguinte
* A cada hora, o Raspberry:
  1. Captura imagem e roda inferência YOLO
  2. Determina duração de irrigação pela fase detectada
  3. Roda ciclos contínuos de ativação + descanso durante 1h
  4. Interrompe os ciclos automaticamente ao atingir 18:00
* O Raspberry mantém controle total dos ciclos — cada `pump_on` e `pump_off` gera evento MQTT, atualizando o dashboard em tempo real

## Controle da Bomba com Relé

* Relé de 1 canal acionado via transistor BC547 conectado ao **pino 4** do ESP32-S3
* Lógica ativo-alto: `HIGH` liga, `LOW` desliga
* Backend envia `pump_on` com duração em segundos ou `pump_off`
* ESP32 desliga automaticamente após a duração expirar como camada de segurança adicional

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
| `registro` | `database/registry.py` | A cada ciclo de inferência (1h) | Fase detectada, fase usada, duração, URL da imagem |
| bucket `registros` | `database/registry.py` | A cada ciclo de inferência (1h) | Imagem capturada pela ESP32-CAM |

---

# 6 - Fluxo de Operação

1. Raspberry inicializa: carrega modelo ONNX e conecta ao broker MQTT
2. ESP32-S3 conecta, publica status inicial e heartbeat imediato
3. Raspberry verifica janela de operação — se fora do horário, dorme até 06:00
4. Dentro da janela (06:00–18:00), a cada hora:
   - Captura imagem da ESP32-CAM
   - Roda inferência YOLO
   - Decide duração de irrigação pela fase detectada
   - Persiste detecção e imagem no Supabase
   - Inicia ciclos de ativação + descanso:
     - Envia `pump_on` com duração → ESP aciona relé → publica status
     - Aguarda tempo de ativação
     - Envia `pump_off` → ESP desliga relé → publica status
     - Aguarda 10 min de descanso
     - Repete até completar 1h ou atingir 18:00
5. Às 18:00, encerra ciclos e aguarda 06:00 do dia seguinte
6. Watchdog roda a cada 15 s em paralelo durante todo o processo
7. Supabase Realtime propaga mudanças ao dashboard Next.js

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
* Decisão de irrigação por fase com cálculo empírico
* Janela de operação 06:00–18:00
* Ciclos automáticos de ativação + descanso controlados pelo Raspberry
* Persistência de estado em tempo real no Supabase
* Histórico de detecções e imagens no Supabase
* Dashboard web em tempo real com Supabase Realtime

## Em aberto

* Calibração final das durações de irrigação por fase
* Integrar alertas de watchdog ao dashboard
* Adicionar TLS ao broker MQTT
* Expandir dashboard com histórico de detecções e imagens
