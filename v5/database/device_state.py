from database.supabase_client import get_supabase


def upsert_device(device_id: str, data: dict):
    """
    Atualiza o estado atual do dispositivo na tabela device_state.
    Sempre sobrescreve a linha existente (upsert).
    """
    sb = get_supabase()
    if sb is None:
        return
    try:
        sb.table("device_state").upsert({
            "device_id":  device_id,
            "updated_at": "now()",
            **data
        }).execute()
    except Exception as e:
        print(f"❌ Erro ao atualizar device_state: {e}")