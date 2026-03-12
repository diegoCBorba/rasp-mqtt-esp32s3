import time
from configs.config import HEARTBEAT_TIMEOUT


def check_heartbeat_watchdog(devices: dict):
    now = time.time()
    for device_id, state in devices.items():
        last = state.get("last_heartbeat")
        if last is None:
            continue
        elapsed = now - last
        if elapsed > HEARTBEAT_TIMEOUT:
            print(
                f"⚠️  [{device_id}] Sem heartbeat há {int(elapsed)}s "
                f"(timeout: {HEARTBEAT_TIMEOUT}s) — dispositivo pode estar travado"
            )