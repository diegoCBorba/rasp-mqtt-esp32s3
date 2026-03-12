import paho.mqtt.client as mqtt

from configs.config import MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASSWORD, DEVICE_ID
from mqtt.handlers import on_message

_client: mqtt.Client = None


def get_client() -> mqtt.Client:
    return _client


def build_client() -> mqtt.Client:
    global _client

    _client = mqtt.Client()
    _client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    _client.on_connect    = _on_connect
    _client.on_disconnect = _on_disconnect
    _client.on_message    = on_message

    return _client


def connect(client: mqtt.Client):
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()


def _on_connect(client, userdata, flags, rc):
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
        status_topic    = f"irrigacao/{DEVICE_ID}/status"
        heartbeat_topic = f"irrigacao/{DEVICE_ID}/heartbeat"
        client.subscribe(status_topic)
        client.subscribe(heartbeat_topic)
        print(f"📡 Inscrito em: {status_topic}")
        print(f"📡 Inscrito em: {heartbeat_topic}")


def _on_disconnect(client, userdata, rc):
    if rc == 0:
        print("🔌 Desconectado normalmente.")
    else:
        print(f"⚠️  Desconexão inesperada (rc={rc}). Reconectando...")