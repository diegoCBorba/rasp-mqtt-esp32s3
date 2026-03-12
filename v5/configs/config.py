import os
from dotenv import load_dotenv

load_dotenv()

# Raiz do projeto — pasta onde está o main.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Caminhos absolutos
IMAGE_SAVE_PATH = os.path.join(BASE_DIR, "captured_images", "current_capture.jpg")
LOG_SAVE_PATH   = os.path.join(BASE_DIR, "logs", "results_log.txt")

# Modelo ONNX
MODEL_PATH      = os.path.join(BASE_DIR, "models", "best_nano.onnx")

# ESP32-CAM
ESP32_CAM_URL = os.getenv("ESP32_CAM_URL", "http://192.168.1.14/capture")

# MQTT
MQTT_BROKER   = os.getenv("MQTT_BROKER")
MQTT_PORT     = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER     = os.getenv("MQTT_USER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
DEVICE_ID     = os.getenv("DEVICE_ID", "esp32_01")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Heartbeat watchdog
HEARTBEAT_TIMEOUT = 45  # segundos

# Loop de inferência
LOOP_INTERVAL_SECONDS = 120# 3600  # 1 hora

# ─────────────────────────────────────────────
# Duração de irrigação por fase (em segundos)
# Valores provisórios — ajustar conforme
# calibração empírica
# ─────────────────────────────────────────────
IRRIGATION_DURATION = {
    "fase_1": 10,   # germinação
    "fase_2": 20,   # crescimento vegetativo
    "fase_3": 30,   # maturação
}
IRRIGATION_DEFAULT_DURATION = 15  # segurança — nenhuma fase detectada