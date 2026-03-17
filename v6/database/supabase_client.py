from supabase import create_client, Client
from configs.config import SUPABASE_URL, SUPABASE_KEY

_client: Client = None

def get_supabase() -> Client | None:
    """
    Retorna o cliente Supabase inicializado (singleton).
    """
    global _client
    if _client is not None:
        return _client
    try:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _client
    except Exception as e:
        print(f"❌ Erro ao conectar ao Supabase: {e}")
        return None