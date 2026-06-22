from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.config import clear_settings_cache
from src.main import app
from src.orchestrator import (
    fetch_consult_detail,
    fetch_tiflux_catalog,
    preview_consult_client,
    update_consult_tiflux_bindings,
)

client = TestClient(app)

ENV = {
    "TIFLUX_API_TOKEN": "t",
    "VHSYS_ACCESS_TOKEN": "a",
    "VHSYS_SECRET_ACCESS_TOKEN": "s",
}


@pytest.fixture
def env():
    with patch.dict("os.environ", ENV):
        clear_settings_cache()
        yield
    clear_settings_cache()


@pytest.mark.asyncio
async def test_preview_consult_by_cnpj(env):
    from src.config import Settings

    tf_match = {"id": 10, "name": "Fan", "social": "Razao", "social_revenue": "19131243000197"}
    vh_active = {"id_cliente": 20, "razao_cliente": "Razao", "fantasia_cliente": "Fan", "cnpj_cliente": "19.131.243/0001-97"}
    vh_trash = {"id_cliente": 21, "razao_cliente": "Old", "fantasia_cliente": "Old", "cnpj_cliente": "19.131.243/0001-97"}

    with patch("src.orchestrator.TifluxClient") as tf_cls, patch("src.orchestrator.VhsysClient") as vh_cls:
        tf_cls.return_value.find_matches_by_cnpj = AsyncMock(return_value=[tf_match])
        vh_cls.return_value.find_matches_active_and_trash_by_cnpj = AsyncMock(
            return_value=([vh_active], [vh_trash])
        )

        result = await preview_consult_client("19.131.243/0001-97", Settings())

    assert result.search_mode == "cnpj"
    assert result.tiflux.found is True
    assert result.tiflux.matches_active[0]["id"] == 10
    assert result.vhsys.found is True
    assert len(result.vhsys.matches_active) == 1
    assert len(result.vhsys.matches_trash) == 1


@pytest.mark.asyncio
async def test_preview_consult_by_name(env):
    from src.config import Settings

    with patch("src.orchestrator.TifluxClient") as tf_cls, patch("src.orchestrator.VhsysClient") as vh_cls:
        tf_cls.return_value.find_by_name = AsyncMock(return_value=[{"id": 1, "name": "A", "social": "B", "social_revenue": ""}])
        vh_cls.return_value.find_matches_active_and_trash_by_name = AsyncMock(return_value=([], []))

        result = await preview_consult_client("Empresa Teste", Settings())

    assert result.search_mode == "name"
    assert result.tiflux.found is True
    assert result.vhsys.found is False


@pytest.mark.asyncio
async def test_fetch_consult_detail(env):
    from src.config import Settings

    profile = {
        "client": {"id": 10, "name": "Fan", "social_revenue": "19131243000197", "status": True},
        "entities": [],
        "desks": [{"id": 1, "name": "Mesa", "display_name": "Mesa"}],
        "technical_groups": [{"id": 2, "name": "Grupo"}],
    }
    vh_data = {"id_cliente": 20, "razao_cliente": "Razao", "categoria": "VIP"}

    with patch("src.orchestrator.TifluxClient") as tf_cls, patch("src.orchestrator.VhsysClient") as vh_cls:
        tf_cls.return_value.get_client_profile = AsyncMock(return_value=profile)
        vh_cls.return_value.get_by_id = AsyncMock(return_value=vh_data)

        result = await fetch_consult_detail(
            "19131243000197",
            Settings(),
            tiflux_client_id=10,
            vhsys_client_id=20,
        )

    assert result.success is True
    assert result.tiflux.data["desks"][0]["name"] == "Mesa"
    assert result.vhsys.data["razao_cliente"] == "Razao"


def test_consulta_preview_route_ok(env):
    with patch("src.main.preview_consult_client", new_callable=AsyncMock) as mock_preview:
        from src.orchestrator import ConsultPreviewResult, ConsultSystemPreview

        mock_preview.return_value = ConsultPreviewResult(
            query="test",
            search_mode="name",
            tiflux=ConsultSystemPreview(found=True, matches_active=[{"id": 1}]),
            vhsys=ConsultSystemPreview(found=False),
        )
        res = client.post("/consulta/preview", json={"query": "Empresa"})
    assert res.status_code == 200
    assert res.json()["success"] is True


def test_consulta_detalhe_route_ok(env):
    with patch("src.main.fetch_consult_detail", new_callable=AsyncMock) as mock_detail:
        from src.orchestrator import ConsultDetailResult, SystemResult

        mock_detail.return_value = ConsultDetailResult(
            query="test",
            success=True,
            tiflux=SystemResult(success=True, data={"client": {}}),
            vhsys=SystemResult(success=True, skipped=True),
        )
        res = client.post(
            "/consulta/detalhe",
            json={"query": "19131243000197", "tiflux_client_id": 10},
        )
    assert res.status_code == 200
    assert res.json()["success"] is True


def test_index_serves_spa_shell(env):
    res = client.get("/")
    assert res.status_code == 200
    assert "AVS Management" in res.text
    assert 'id="root"' in res.text
    assert "/assets/index-" in res.text


@pytest.mark.asyncio
async def test_fetch_tiflux_catalog(env):
    from src.config import Settings

    with patch("src.orchestrator.TifluxClient") as tf_cls:
        tf_cls.return_value.list_desks = AsyncMock(return_value=[{"id": 1, "name": "Mesa"}])
        tf_cls.return_value.list_technical_groups = AsyncMock(return_value=[{"id": 2, "name": "Grupo"}])

        catalog = await fetch_tiflux_catalog(Settings())

    assert catalog["desks"][0]["id"] == 1
    assert catalog["technical_groups"][0]["id"] == 2


@pytest.mark.asyncio
async def test_update_consult_tiflux_bindings(env):
    from src.config import Settings

    updated_profile = {
        "client": {"id": 10, "desk_ids": [1], "technical_group_ids": [2]},
        "desks": [{"id": 1, "name": "Mesa"}],
        "technical_groups": [{"id": 2, "name": "Grupo"}],
        "entities": [],
    }

    with patch("src.orchestrator.TifluxClient") as tf_cls:
        tf_cls.return_value.update_client_bindings = AsyncMock(return_value=updated_profile)

        result = await update_consult_tiflux_bindings(10, [1], [2], Settings())

    assert result["client"]["id"] == 10
    tf_cls.return_value.update_client_bindings.assert_awaited_once_with(
        10,
        desk_ids=[1],
        technical_group_ids=[2],
    )


def test_consulta_tiflux_opcoes_route_ok(env):
    with patch("src.main.fetch_tiflux_catalog", new_callable=AsyncMock) as mock_catalog:
        mock_catalog.return_value = {"desks": [{"id": 1}], "technical_groups": [{"id": 2}]}
        res = client.get("/consulta/tiflux/opcoes")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["desks"][0]["id"] == 1


def test_consulta_tiflux_vinculos_route_ok(env):
    with patch("src.main.update_consult_tiflux_bindings", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {
            "client": {"id": 10},
            "desks": [],
            "technical_groups": [],
            "entities": [],
        }
        res = client.post(
            "/consulta/tiflux/vinculos",
            json={"tiflux_client_id": 10, "desk_ids": [1], "technical_group_ids": [2]},
        )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["tiflux"]["data"]["client"]["id"] == 10
