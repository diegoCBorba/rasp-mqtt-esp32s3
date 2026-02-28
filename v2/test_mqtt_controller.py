import json
import time
import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()

BROKER      = os.getenv("MQTT_BROKER")
PORT        = int(os.getenv("MQTT_PORT"))
MQTT_USER   = os.getenv("MQTT_USER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

DEVICE_ID = os.getenv("DEVICE_ID", "esp32_01")

TOPIC_TELEMETRY = "irrigacao/+/telemetry"
TOPIC_STATUS    = "irrigacao/+/status"
TOPIC_COMMAND   = f"irrigacao/{DEVICE_ID}/command"

# Estado local dos dispositivos
devices: dict[str, dict] = {}

def update_device(device_id: str, data: dict):
    if device_id not in devices:
        devices[device_id] = {}
    devices[device_id].update(data)

def get_device(device_id: str) -> dict:
    return devices.get(device_id, {})

# Callbacks MQTT
def on_connect(client, userdata, flags, rc):
    codes = {
        0: "Conectado com sucesso",
        1: "Versão de protocolo incorreta",
        2: "Identificador inválido",
        3: "Servidor indisponível",
        4: "Usuário ou senha incorretos",
        5: "Não autorizado",
    }
    print(f"{'✅' if rc == 0 else '❌'} Broker: {codes.get(rc, f'Código {rc}')}")

    if rc == 0:
        client.subscribe(TOPIC_TELEMETRY)
        client.subscribe(TOPIC_STATUS)
        print(f"📡 Inscrito em: {TOPIC_TELEMETRY}")
        print(f"📡 Inscrito em: {TOPIC_STATUS}")

def on_disconnect(client, userdata, rc):
    if rc == 0:
        print("🔌 Desconectado normalmente.")
    else:
        print(f"⚠️  Desconexão inesperada (rc={rc}). Reconectando...")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        print(f"❌ Payload inválido em {msg.topic}: {msg.payload}")
        return

    parts = msg.topic.split("/")
    if len(parts) < 3:
        print(f"⚠️  Tópico inesperado: {msg.topic}")
        return

    device_id  = parts[1]
    topic_type = parts[2]   # telemetry | status

    if topic_type == "status":
        _handle_status(device_id, data)

    elif topic_type == "telemetry":
        _handle_telemetry(device_id, data)

def _handle_status(device_id: str, data: dict):
    online = data.get("online", True)
    pump   = data.get("pump", "?")

    update_device(device_id, {"online": online, "pump": pump})

    if not online:
        print(f"🔴 [{device_id}] OFFLINE (LWT recebido)")
    else:
        print(f"🟢 [{device_id}] Online — bomba: {pump}")

def _handle_telemetry(device_id: str, data: dict):
    update_device(device_id, {"last_telemetry": data})

    flow1     = data.get("flow1", 0)
    flow2     = data.get("flow2", 0)
    diff_abs  = data.get("diff_abs", 0)
    vol_total = data.get("vol_total", 0)

    print(
        f"📊 [{device_id}] "
        f"flow1={flow1:.2f}  flow2={flow2:.2f}  "
        f"diff={diff_abs:.2f}  vol={vol_total}"
    )

# Comandos
def send_command(client, device_id: str, action: str, **kwargs):
    topic   = f"irrigacao/{device_id}/command"
    payload = {"action": action, **kwargs}
    result  = client.publish(topic, json.dumps(payload), qos=1)

    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"🚀 Comando enviado → {topic}: {payload}")
    else:
        print(f"❌ Falha ao enviar comando (rc={result.rc})")

def pump_on(client, device_id: str, duration: int = 10):
    send_command(client, device_id, "pump_on", duration=duration)

def pump_off(client, device_id: str):
    send_command(client, device_id, "pump_off")

# Main
def main():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_message    = on_message

    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    # Aguarda conexão estabilizar
    time.sleep(2)

    # ── Teste: liga bomba por 10s ──
    pump_on(client, DEVICE_ID, duration=10)

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n⛔ Encerrando...")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()