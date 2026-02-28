import json
import time
import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

# Carrega variáveis do .env
load_dotenv()

BROKER = os.getenv("MQTT_BROKER")
PORT = int(os.getenv("MQTT_PORT"))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

TOPIC_TELEMETRY = "irrigacao/telemetry"
TOPIC_COMMAND = "irrigacao/command"

def on_connect(client, userdata, flags, rc):
    print("Conectado ao broker:", rc)
    client.subscribe(TOPIC_TELEMETRY)

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    print("📡 Telemetria recebida:", data)

def send_test_command(client):
    payload = {
        "action": "pump_on",
        "duration": 10
    }
    client.publish(TOPIC_COMMAND, json.dumps(payload), qos=1)
    print("🚀 Comando pump_on enviado")

client = mqtt.Client()

# Autenticação via .env
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)

client.loop_start()
time.sleep(5)

send_test_command(client)

while True:
    time.sleep(1)