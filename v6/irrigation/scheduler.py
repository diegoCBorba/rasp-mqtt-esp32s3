import time
from datetime import datetime

from configs.config import (
    IRRIGATION_START_HOUR,
    IRRIGATION_END_HOUR,
    IRRIGATION_REST_DURATION,
    LOOP_INTERVAL_SECONDS,
)
from mqtt.commands import pump_on, pump_off
from utils.logger  import log_results


def is_within_operating_window() -> bool:
    """Retorna True se o horário atual está entre 6h e 18h."""
    hour = datetime.now().hour
    return IRRIGATION_START_HOUR <= hour < IRRIGATION_END_HOUR


def seconds_until_start() -> float:
    """Retorna quantos segundos faltam para as 6h."""
    now   = datetime.now()
    start = now.replace(hour=IRRIGATION_START_HOUR, minute=0, second=0, microsecond=0)
    if now >= start:
        # Já passou das 6h hoje — próximo início é amanhã
        from datetime import timedelta
        start += timedelta(days=1)
    return (start - now).total_seconds()


def run_irrigation_cycles(client, device_id: str, duration_min: int, phase_used: str):
    """
    Roda ciclos de irrigação (ativo + descanso) durante LOOP_INTERVAL_SECONDS.
    Cada ciclo: pump_on por duration_min, pump_off, descanso por IRRIGATION_REST_DURATION.
    Interrompe se sair da janela de operação (18h).
    """
    duration_s = duration_min * 60
    rest_s     = IRRIGATION_REST_DURATION * 60
    cycle      = 1
    elapsed    = 0

    print(f"\n💧 Iniciando ciclos de irrigação — fase: {phase_used} | ativo: {duration_min}min | descanso: {IRRIGATION_REST_DURATION}min")

    while elapsed < LOOP_INTERVAL_SECONDS:

        # Verifica janela antes de cada ciclo
        if not is_within_operating_window():
            print("🌙 Fora da janela de operação (18h) — encerrando ciclos")
            pump_off(client, device_id)
            log_results(status="INFO", data="Ciclos encerrados — fora da janela de operação")
            return

        print(f"\n▶️  Ciclo {cycle} — ligando bomba por {duration_min} min")
        pump_on(client, device_id, duration=duration_s)
        time.sleep(duration_s)

        pump_off(client, device_id)
        elapsed += duration_s

        # Verifica se ainda há tempo para o descanso + próximo ciclo
        if elapsed + rest_s >= LOOP_INTERVAL_SECONDS:
            print("⏱️  Sem tempo para novo ciclo — aguardando próxima inferência")
            break

        print(f"😴 Descanso por {IRRIGATION_REST_DURATION} min")
        time.sleep(rest_s)
        elapsed += rest_s
        cycle   += 1

    log_results(
        status="INFO",
        data=f"Ciclos concluídos — fase: {phase_used} | ciclos: {cycle} | tempo total: {elapsed//60} min"
    )