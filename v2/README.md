# README — Sistema IoT de Irrigação (versão 2)

**Projeto:** Sistema Automatizado de Irrigação com ESP32-S3 + Backend Python
**Arquitetura:** ESP32-S3 + Broker MQTT (Mosquitto) + Raspberry Pi (Python)

---

# 1️ - Objetivo desta Versão

Evoluir o protótipo inicial (v1) com foco em segurança e robustez de comunicação.
Agora o sistema não apenas troca telemetria e comandos, mas também trata autenticação, ACL,
Last Will, heartbeat e monitoração de estado, preparando o caminho para substituição de
dados mock por sensores reais.

---

# 2️ - Arquitetura Atualizada

```
ESP32-S3                          
  ├─ Publica: irrigacao/{device_id}/telemetry
  ├─ Publica: irrigacao/{device_id}/status      (com retain)
  ├─ Publica: irrigacao/{device_id}/heartbeat   
  └─ Assina:  irrigacao/{device_id}/command     
              ↑                    
      MQTT Broker (Mosquitto)      
  ├─ ACL restringe tópicos por usuário
  └─ LWT mantém "status" em offline se o ESP cair
              ↓                    
Backend Python (Raspberry Pi)     
  ├─ Assina: telemetry, status, heartbeat
  └─ Publica: command
```

Broker utilizado: **Eclipse Mosquitto** com autenticação e ACL configuradas.

---

# 3️ - Estrutura de Tópicos

| Tópico                                       | Direção            | Função / Observações                                      |
| -------------------------------------------- | ------------------ | --------------------------------------------------------- |
| `irrigacao/{device_id}/telemetry`            | ESP → Backend      | Dados de vazão simulados (mock) cada 1 s                  |
| `irrigacao/{device_id}/status`               | ESP → Broker       | Estado atual da bomba (`{"pump":"online",…}`) retain    |
| `irrigacao/{device_id}/heartbeat`            | ESP → Backend      | Uptime em segundos a cada 30 s                            |
| `irrigacao/{device_id}/command`              | Backend → ESP      | Backend envia `pump_on`/`pump_off` com QoS 1              |

*As mensagens TTL e ACL garantem que apenas `esp32_01` e `backend` possam
publicar/assinar seus tópicos correspondentes.*

---

# 4️ - Novas Funcionalidades Implementadas

## Segurança e Controle de Acesso

* Usuários `esp32_01` e `backend` definidos no Mosquitto
* Acesso anônimo desativado
* ACL (Access Control List) que permite somente leitura/escrita nos tópicos específicos

## Controle da Bomba

* `backend` envia:
  * `pump_on` com duração (segundos)
  * `pump_off`
* ESP32 monitora o tempo e desliga a bomba automaticamente quando o período expira

## Last Will and Testament (LWT)

* Configurado no cliente ESP32
* Broker publica automaticamente `{"pump":"offline","online":false}`
  no tópico `irrigacao/{device_id}/status` com `retain=true` caso o ESP desconecte
  abruptamente
* Mensagem retenha garante que qualquer novo inscrito saiba do estado real

## Heartbeat

* ESP32 publica uptime (`{"uptime":123}`) a cada 30 s
* Backend executa watchdog interno (rodando a cada 15 s) e dispara aviso se
  nenhum heartbeat for recebido em 45 s — cobre travamentos silenciosos que o LWT
  não detecta

## Telemetria Mock

* Publica campos de fluxo (`flow1`, `flow2`, `diff`, `volume`) simulados a cada 1 s
* Estrutura JSON idêntica à v1, pronta para substituição por dados reais dos sensores

---

# 5️ - Fluxo de Teste

1. ESP conecta ao Wi‑Fi com credenciais de `esp32_01`
2. Estabelece sessão MQTT autenticada com o broker
3. Publica status inicial `{"pump":"offline","online":false}`
4. Telemetria mock a cada 1 s e heartbeat a cada 30 s
5. Backend recebe mensagens e imprime/analisa
6. Backend envia `pump_on` (com duração)
7. ESP aciona bomba e publica `status` como `online`
8. Após o tempo de duração vence, o ESP publica `pump_off` e altera `status`
9. Se o ESP cair de forma abrupta, broker dispara LWT e clientes notificam falha
10. Se o backend não receber heartbeat por 45 s, alerta watchdog

---

# 6️ - Tecnologias

* **Broker:** Eclipse Mosquitto (com usuários/ACL configurados)
* **ESP32:** Arduino Framework, AsyncMqttClient, ArduinoJson, Ticker
* **Backend:** Python 3, paho-mqtt

---

# 7️ - Lições & Próximos Passos

* Estrutura de tópicos agora por `device_id` suporta múltiplos nós
* Segurança básica (usuário + ACL) aplicada, considerando TLS no futuro
* LWT + Heartbeat tornam o sistema mais confiável contra quedas
* Telemetria mock mantém compatibilidade com leitura futura de sensores

## Itens já concluídos

* Autenticação MQTT
* ACL por tópico
* Controle de bomba com duração
* LWT com retain state
* Heartbeat + watchdog
* Telemetria mock periódica

## Em aberto

* Substituir telemetria por sensores reais YF-S201
* Calcular vazões e volumes precisos
* Integrar com políticas automáticas (ex. YOLO)
* Adicionar TLS e logs persistentes

---

**Use esta pasta (`v2/`) para testar as funcionalidades avançadas descritas acima.**
