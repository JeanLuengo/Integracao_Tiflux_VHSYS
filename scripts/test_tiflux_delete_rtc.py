"""Teste E2E TiFlux: inativa RTC ACADEMIA (CNPJ 50.149.208/0001-45).

Uso: python scripts/test_tiflux_delete_rtc.py
Exit code 0 apenas se o cliente ficar com status=false na API.
"""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import Settings, clear_settings_cache
from src.integrations.tiflux_client import TifluxApiError, TifluxClient

DEFAULT_CNPJ = "50149208000145"


async def main() -> int:
    cnpj_arg = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CNPJ
    cnpj_digits = "".join(c for c in cnpj_arg if c.isdigit())
    clear_settings_cache()
    settings = Settings()
    if not settings.tiflux_api_token:
        print("ERRO: TIFLUX_API_TOKEN ausente no .env")
        return 1

    client = TifluxClient(settings)
    found = await client.find_by_cnpj(cnpj_digits)
    if not found or not found.get("id"):
        print(f"ERRO: Cliente CNPJ {cnpj_digits} não encontrado no TiFlux")
        return 1

    client_id = int(found["id"])
    print(f"Cliente id={client_id} name={found.get('name')!r}")

    try:
        await client.delete_client(client_id)
    except TifluxApiError as exc:
        print(f"ERRO: {exc}")
        return 1

    verified = await client.get_by_id(client_id)
    if verified and verified.get("status") is False:
        print("OK: cliente inativo no TiFlux (status=false)")
        return 0

    print("ERRO: PUT concluiu mas status ainda não é false na API")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
