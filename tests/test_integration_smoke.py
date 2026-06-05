import pytest



from src.config import Settings, clear_settings_cache

from src.cnpj.brasilapi_client import fetch_cnpj

from src.cnpj.validator import validate_cnpj

from src.mapping.canonical import from_brasilapi



pytestmark = pytest.mark.integration



SMOKE_CNPJ = "19131243000197"

TARGET_CNPJ = "65074067000116"





def _has_tokens() -> bool:

    clear_settings_cache()

    s = Settings()

    return bool(

        s.tiflux_api_token.strip()

        and s.vhsys_access_token.strip()

        and s.vhsys_secret_access_token.strip()

    )





@pytest.mark.asyncio

async def test_brasilapi_fetch_smoke():

    clear_settings_cache()

    settings = Settings()

    assert validate_cnpj(SMOKE_CNPJ)

    data = await fetch_cnpj(SMOKE_CNPJ, settings)

    company = from_brasilapi(data)

    assert company.legal_name

    assert company.cnpj_digits == SMOKE_CNPJ





@pytest.mark.asyncio

async def test_integrate_target_cnpj_both_systems():

    """@tester — CNPJ 65.074.067/0001-16 deve constar em TiFlux e VHSYS."""

    if not _has_tokens():

        pytest.skip("Tokens não configurados no .env")



    from src.integrations.tiflux_client import TifluxClient

    from src.integrations.vhsys_client import VhsysClient

    from src.orchestrator import integrate_cnpj



    clear_settings_cache()

    settings = Settings()

    assert settings.vhsys_base_url.rstrip("/") == "https://api.vhsys.com/v2"



    result = await integrate_cnpj(TARGET_CNPJ, settings)



    assert result.company is not None

    assert result.company.cnpj_digits == TARGET_CNPJ

    assert result.tiflux.success, result.tiflux.error or result.tiflux.message

    assert result.vhsys.success, result.vhsys.error or result.vhsys.message

    assert result.success is True

    assert result.partial is False



    tiflux_found = await TifluxClient(settings).find_by_cnpj(TARGET_CNPJ)

    assert tiflux_found is not None, (

        "Cliente não encontrado no TiFlux via API após integração (falso positivo)."

    )

    assert tiflux_found.get("id"), "Resposta TiFlux sem id de cliente."



    vhsys_found = await VhsysClient(settings).find_by_cnpj(result.company.cnpj_formatted)

    assert vhsys_found is not None, "Cliente não encontrado no VHSYS via API após integração."

    assert vhsys_found.get("id_cliente"), "Resposta VHSYS sem id_cliente."


CONSULT_CNPJ = "57610713000194"

CONSULT_CNPJ_FMT = "57.610.713/0001-94"





@pytest.mark.asyncio

async def test_consult_flow_e2e_cnpj_57610713000194():

    """@tester — fluxo completo de consulta: preview, seleção e detalhe."""

    if not _has_tokens():

        pytest.skip("Tokens não configurados no .env")



    from fastapi.testclient import TestClient

    from src.main import app

    from src.orchestrator import fetch_consult_detail, preview_consult_client



    clear_settings_cache()

    settings = Settings()



    preview = await preview_consult_client(CONSULT_CNPJ_FMT, settings)

    assert preview.search_mode == "cnpj"

    assert preview.tiflux.found is True

    assert preview.vhsys.found is True

    assert len(preview.tiflux.matches_active) >= 1

    assert len(preview.vhsys.matches_active) >= 1



    tf_id = preview.tiflux.matches_active[0]["id"]

    vh_id = preview.vhsys.matches_active[0]["id"]



    detail = await fetch_consult_detail(

        CONSULT_CNPJ_FMT,

        settings,

        tiflux_client_id=tf_id,

        vhsys_client_id=vh_id,

    )

    assert detail.success is True

    assert detail.tiflux.success is True

    assert detail.vhsys.success is True

    assert detail.tiflux.data["client"]["social_revenue"] == CONSULT_CNPJ

    assert isinstance(detail.tiflux.data.get("entities"), list)

    assert len(detail.tiflux.data["desks"]) >= 1

    assert detail.vhsys.data["situacao_cliente"] == "Ativo"

    assert CONSULT_CNPJ_FMT in detail.vhsys.data["cnpj_cliente"]



    tc = TestClient(app)

    r_preview = tc.post("/consulta/preview", json={"query": CONSULT_CNPJ_FMT})

    assert r_preview.status_code == 200

    assert r_preview.json()["success"] is True



    r_detail = tc.post(

        "/consulta/detalhe",

        json={"query": CONSULT_CNPJ_FMT, "tiflux_client_id": tf_id, "vhsys_client_id": vh_id},

    )

    assert r_detail.status_code == 200

    body = r_detail.json()

    assert body["success"] is True

    assert body["tiflux"]["data"]["client"]["name"]

    assert body["vhsys"]["data"]["razao_cliente"]


