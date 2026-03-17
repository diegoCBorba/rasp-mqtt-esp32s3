import json
import paho.mqtt.client as mqtt


def send_command(client, device_id: str, action: str, **kwargs):
    topic   = f"irrigacao/{device_id}/command"
    payload = {"action": action, **kwargs}
    result  = client.publish(topic, json.dumps(payload), qos=1)

    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"🚀 Comando enviado → {topic}: {payload}")
    else:
        print(f"❌ Falha ao enviar comando (rc={result.rc})")


def pump_on(client, device_id: str, duration: int):
    send_command(client, device_id, "pump_on", duration=duration)


def pump_off(client, device_id: str):
    send_command(client, device_id, "pump_off")