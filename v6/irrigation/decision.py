from configs.config import IRRIGATION_DURATION, IRRIGATION_DEFAULT_DURATION


def decide_duration(detected_phases: list[str]) -> tuple[int, str]:
    """
    Recebe a lista de fases detectadas e retorna
    (duração_em_minutos, fase_usada).

    - Se nenhuma fase detectada → duração padrão (fase_2)
    - Se múltiplas fases detectadas → usa a primeira
    """
    if not detected_phases:
        print(
            f"⚠️  Nenhuma fase detectada — "
            f"usando duração padrão: fase_2 ({IRRIGATION_DEFAULT_DURATION} min)"
        )
        return IRRIGATION_DEFAULT_DURATION, "padrão (fase_2)"

    phase    = detected_phases[0]
    duration = IRRIGATION_DURATION.get(phase, IRRIGATION_DEFAULT_DURATION)
    print(f"🌿 Fase detectada: {phase} → duração: {duration} min")
    return duration, phase