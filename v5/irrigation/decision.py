from configs.config import IRRIGATION_DURATION, IRRIGATION_DEFAULT_DURATION


def decide_duration(detected_phases: list[str]) -> tuple[int, str]:
    """
    Recebe a lista de fases detectadas e retorna
    (duração_em_segundos, fase_usada).

    - Se nenhuma fase detectada → duração padrão de segurança
    - Se múltiplas fases detectadas → usa a primeira
    """
    if not detected_phases:
        print(
            f"⚠️  Nenhuma fase detectada — "
            f"irrigando com duração padrão ({IRRIGATION_DEFAULT_DURATION}s)"
        )
        return IRRIGATION_DEFAULT_DURATION, "padrão"

    phase    = detected_phases[0]
    duration = IRRIGATION_DURATION.get(phase, IRRIGATION_DEFAULT_DURATION)
    print(f"🌿 Fase detectada: {phase} → duração: {duration}s")
    return duration, phase