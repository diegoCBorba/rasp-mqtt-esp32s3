import time

from database.supabase_client import get_supabase
from utils.logger import log_results


def save_detection(
    image_path: str,
    detected_phases: list[str],
    phase_used: str,
    duration_s: int
):
    """
    Faz upload da imagem capturada para o Storage e registra
    a detecção na tabela 'registro' do Supabase.
    """
    sb = get_supabase()

    if sb is None:
        log_results(status="FALHA", data="Supabase indisponível — detecção não registrada")
        return

    try:
        # Nome único baseado em timestamp
        file_name = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()) + ".jpg"

        # Upload da imagem para o bucket 'registros'
        with open(image_path, "rb") as f:
            sb.storage.from_("registros").upload(
                path=file_name,
                file=f,
                file_options={"content-type": "image/jpeg"}
            )

        image_url = sb.storage.from_("registros").get_public_url(file_name)

        # Inserção do registro na tabela
        novo_registro = {
            "imagem":           image_url,
            "fases_detectadas": f"{detected_phases}",
            "fase_utilizada":   phase_used,
            "duracao_s":        duration_s,
        }

        dados = sb.table("registro").insert(novo_registro).execute()
        print(f"💾 Registro salvo no Supabase: {dados.data}")

    except Exception as e:
        log_results(status="FALHA", data=f"Erro ao salvar detecção no Supabase: {e}")