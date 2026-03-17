import os
import cv2
import numpy as np
import requests

from configs.config import IMAGE_SAVE_PATH
from utils.logger import log_results


def capture_and_save_image(url: str, save_path: str) -> bool:
    """
    Faz requisição HTTP para a ESP32-CAM, decodifica e salva a imagem.
    Retorna True se bem-sucedido, False caso contrário.
    """
    print(f"📸 Tentando capturar imagem de: {url}")

    try:
        os.makedirs(os.path.dirname(IMAGE_SAVE_PATH), exist_ok=True)

        response = requests.get(url, timeout=5)
        response.raise_for_status()

        image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        image       = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            raise Exception("Não foi possível decodificar a imagem recebida.")

        cv2.imwrite(save_path, image)
        print(f"✅ Imagem capturada e salva em: {save_path}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição HTTP (ESP32-CAM): {e}")
        log_results(status="FALHA", data=f"Erro na requisição HTTP (ESP32-CAM): {e}")
        return False

    except Exception as e:
        print(f"❌ Erro ao processar/salvar a imagem: {e}")
        log_results(status="FALHA", data=f"Erro ao processar/salvar a imagem: {e}")
        return False