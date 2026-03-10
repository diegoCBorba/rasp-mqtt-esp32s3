# README — Sistema IoT de Irrigação (versão 4)

**Projeto:** Sistema Automatizado de Irrigação com ESP32-S3 + Backend Python + Dashboard Web
**Arquitetura:** ESP32-S3 + Broker MQTT (Mosquitto) + Raspberry Pi (Python) + Supabase + Next.js

---

# 1 - Objetivo desta Versão

Adicionar uma camada de observabilidade ao sistema com um dashboard web em tempo real.
O Raspberry Pi passa a escrever o estado do dispositivo no Supabase a cada evento recebido
via MQTT, e o Next.js exibe essas informações ao vivo via Supabase Realtime — sem polling,
sem recarregar a página.

---

# 2 - Arquitetura
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
  ├─ Publica: command
  └─ Escreve: Supabase (upsert em device_state)
              ↓
          Supabase
  ├─ Tabela device_state (1 linha por dispositivo)
  └─ Realtime emite evento a cada upsert
              ↓
      Next.js (Dashboard)
  ├─ Leitura inicial da tabela ao abrir a página
  └─ Realtime mantém estado atualizado em memória
```

Broker utilizado: **Eclipse Mosquitto** com autenticação e ACL configuradas.

---

# 3 - Estrutura de Tópicos

| Tópico                            | Direção       | Função / Observações                                  |
| --------------------------------- | ------------- | ----------------------------------------------------- |
| `irrigacao/{device_id}/status`    | ESP → Broker  | Estado atual da bomba (`{"pump":"on/off",…}`) retain |
| `irrigacao/{device_id}/heartbeat` | ESP → Backend | Uptime em segundos a cada 30 s                        |
| `irrigacao/{device_id}/command`   | Backend → ESP | Backend envia `pump_on`/`pump_off` com QoS 1          |

---

# 4 - Funcionalidades

## Segurança e Controle de Acesso

* Usuários `esp32_01` e `backend` definidos no Mosquitto
* Acesso anônimo desativado
* ACL que permite somente leitura/escrita nos tópicos específicos por usuário

## Controle da Bomba com Relé

* Relé de 1 canal (ativo-baixo) conectado ao **pino 4** do ESP32-S3
* `backend` envia `pump_on` com duração em segundos ou `pump_off`
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

## Persistência de Estado — Supabase

* Raspberry escreve via `supabase-py` usando `service_role` key
* Upsert em `device_state` a cada evento de status ou heartbeat
* Tabela mantém sempre **1 linha por dispositivo** — dado antigo é sobrescrito
* Consumo estimado: ~87.000 requests/mês, bem abaixo do limite free (500.000)

## Dashboard Web em Tempo Real — Next.js

* Leitura inicial da tabela `device_state` ao abrir a página
* Canal Realtime aberto via WebSocket — atualiza sem recarregar
* Exibe: status online/offline, estado da bomba, uptime e horário da última atualização
* Credenciais do frontend usam `anon key` (somente leitura)
* [link_repositorio_front](https://github.com/diegoCBorba/irrigacao-dashboard)

---

# 5 - Fluxo de Operação

1. ESP conecta ao Wi-Fi com credenciais de `esp32_01`
2. Estabelece sessão MQTT autenticada com o broker
3. Publica status inicial `{"pump":"off","online":true}` com retain
4. Publica heartbeat imediato e a cada 30 s
5. Raspberry recebe os eventos e faz upsert no Supabase
6. Supabase Realtime emite evento via WebSocket para o Next.js
7. Dashboard atualiza em tempo real sem recarregar a página
8. Backend envia `pump_on` com duração → ESP aciona o relé e publica status
9. Após duração expirar, ESP desaciona o relé e publica `pump: off`
10. Se o ESP cair abruptamente, broker dispara LWT → Raspberry persiste offline no Supabase → dashboard exibe 🔴
11. Se heartbeat não chegar em 45 s, watchdog emite alerta no terminal

---

# 6 - Tecnologias

* **Broker:** Eclipse Mosquitto (com usuários/ACL configurados)
* **ESP32:** Arduino Framework, AsyncMqttClient, ArduinoJson, Ticker
* **Backend:** Python 3, paho-mqtt, supabase-py
* **Banco de dados:** Supabase (PostgreSQL + Realtime)
* **Frontend:** Next.js, @supabase/supabase-js

---

# 7 - Estrutura do Projeto Web
```
├── app/
│   └── page.tsx              ← dashboard principal
├── hooks/
│   └── useDeviceState.ts     ← carga inicial + canal Realtime
├── lib/
│   └── supabase.ts           ← cliente Supabase centralizado
├── types/
│   └── device.ts             ← tipo DeviceState
└── .env.local                ← SUPABASE_URL + ANON_KEY
```

---

# 8 - Itens Concluídos

* Autenticação MQTT
* ACL por tópico
* Controle de bomba com duração via relé (pino 4)
* LWT com retain state
* Heartbeat + watchdog
* Persistência de estado no Supabase via upsert
* Dashboard web em tempo real com Supabase Realtime

## Em aberto

* Integrar lógica de acionamento automático via YOLO (Raspberry Pi)
* Adicionar TLS ao broker MQTT
* Implementar histórico de eventos (pump on/off, quedas, alertas)
* Expandir o dashboard com histórico e controle manual

---

**Use esta pasta (`v4/`) para a versão com dashboard web e persistência em tempo real.**