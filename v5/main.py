import time
import os

from configs.config import (
    ESP32_CAM_URL, IMAGE_SAVE_PATH, MODEL_PATH,
    DEVICE_ID, LOOP_INTERVAL_SECONDS
)
from mqtt.client         import build_client, connect
from mqtt.commands       import pump_on
from mqtt.handlers       import get_devices
from mqtt.watchdog       import check_heartbeat_watchdog
from vision.capture      import capture_and_save_image
from vision.detector     import ONNXDetector
from irrigation.decision import decide_duration
from database.registry   import save_detection
from utils.logger        import log_results


def run_inference_cycle(client, detector: ONNXDetector):
    print("\n🔄 Iniciando ciclo de inferência...")

    # 1. Captura da ESP32-CAM
    image_saved = capture_and_save_image(ESP32_CAM_URL, IMAGE_SAVE_PATH)
    if not image_saved:
        log_results(status="FALHA", data="Ciclo abortado — falha na captura de imagem")
        return

    # 2. Inferência ONNX
    try:
        detected_phases = detector.detect(IMAGE_SAVE_PATH)
        print(f"📈 Fases detectadas: {detected_phases}")
    except Exception as e:
        log_results(status="FALHA", data=f"Erro na inferência: {e}")
        return

    # 3. Decisão de irrigação
    duration, phase_used = decide_duration(detected_phases)

    # 4. Comando MQTT → ESP32
    pump_on(client, DEVICE_ID, duration=duration)

    # 5. Persistência no Supabase
    save_detection(
        image_path=IMAGE_SAVE_PATH,
        detected_phases=detected_phases,
        phase_used=phase_used,
        duration_s=duration
    )

    # 6. Log local
    log_results(
        status="SUCESSO",
        data=f"Fases: {detected_phases} | Fase usada: {phase_used} | Duração: {duration}s"
    )


def main():
    os.makedirs("captured_images", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Carrega modelo ONNX
    try:
        detector = ONNXDetector(MODEL_PATH)
        print("✅ Modelo ONNX carregado")
    except Exception as e:
        print(f"❌ Fatal: não foi possível carregar o modelo: {e}")
        return

    # Conecta ao broker MQTT
    client = build_client()
    try:
        connect(client)
        print(f"🔗 Conectado ao broker MQTT")
    except Exception as e:
        print(f"❌ Fatal: não foi possível conectar ao broker: {e}")
        return

    # Aguarda conexão estabilizar
    time.sleep(2)

    last_watchdog = time.time()
    last_cycle    = 0  # força execução imediata no primeiro loop

    try:
        while True:
            now = time.time()

            # Watchdog a cada 15s
            if now - last_watchdog >= 15:
                check_heartbeat_watchdog(get_devices())
                last_watchdog = now

            # Ciclo de inferência + irrigação
            if now - last_cycle >= LOOP_INTERVAL_SECONDS:
                run_inference_cycle(client, detector)
                last_cycle = time.time()

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n⛔ Encerrando...")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()