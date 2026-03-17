import json
import time

from database.device_state import upsert_device

devices: dict[str, dict] = {}


def get_devices() -> dict:
    return devices


def update_device(device_id: str, data: dict):
    if device_id not in devices:
        devices[device_id] = {}
    devices[device_id].update(data)


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
    topic_type = parts[2]

    if topic_type == "status":
        _handle_status(device_id, data)
    elif topic_type == "heartbeat":
        _handle_heartbeat(device_id, data)


def _handle_status(device_id: str, data: dict):
    online = data.get("online", True)
    pump   = data.get("pump", "?")
    update_device(device_id, {"online": online, "pump": pump})
    upsert_device(device_id, {"online": online, "pump": pump})

    if not online:
        print(f"🔴 [{device_id}] OFFLINE (LWT recebido)")
    else:
        print(f"🟢 [{device_id}] Online — bomba: {pump}")


def _handle_heartbeat(device_id: str, data: dict):
    uptime = data.get("uptime_s", 0)
    now    = time.time()
    update_device(device_id, {"last_heartbeat": now, "uptime_s": uptime})
    upsert_device(device_id, {"uptime_s": uptime})

    h = uptime // 3600
    m = (uptime % 3600) // 60
    s = uptime % 60
    print(f"💓 [{device_id}] Heartbeat — uptime: {h:02d}:{m:02d}:{s:02d}")