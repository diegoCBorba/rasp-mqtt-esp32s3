import os
import time

from configs.config import LOG_SAVE_PATH


def log_results(status: str, data: str):
    """
    Registra resultado de processamento ou erro em arquivo de log local.
    """
    os.makedirs(os.path.dirname(LOG_SAVE_PATH), exist_ok=True)

    with open(LOG_SAVE_PATH, "a") as log:
        log_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        message  = f"[{log_date}] - {status} - {data}\n"
        log.write(message)