from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.config import Settings, clear_settings_cache
from src.integrations.tiflux_client import (
    TifluxClient,
    _build_inactivate_payload,
    _inactivate_error_message,
)


@pytest.fixture
def env():
    with patch.dict("os.environ", {"TIFLUX_API_TOKEN": "test-token"}):
        clear_settings_cache()
        yield
    clear_settings_cache()


def test_build_inactivate_payload_uses_permitted_fields():
    detail = {
        "id": 1,
        "name": "Fan",
        "social": "Razao",
        "social_revenue": "123",
        "desk_ids": [1],
        "technical_group_ids": [2],
        "status": True,
        "user_ids": [99],
        "form_of_payment": "BOLETO",
    }
    body = _build_inactivate_payload(detail)
    assert body["status"] is False
    assert body["desk_ids"] == [1]
    assert "user_ids" not in body
    assert "form_of_payment" not in body


def test_inactivate_error_message_50004():
    body = '{"error_code":50004,"message":"Cannot execute"}'
    msg = _inactivate_error_message(500, body)
    assert "mesas vinculadas" in msg


@pytest.mark.asyncio
async def test_delete_client_uses_two_step_when_desks_linked(env):
    client = TifluxClient(Settings())
    put_response = MagicMock(status_code=200, text="")
    detail_active = {
        "name": "Fan",
        "social": "Razao",
        "social_revenue": "19131243000197",
        "desk_ids": [1],
        "technical_group_ids": [2],
        "status": True,
    }
    detail_prepared = {**detail_active, "desk_ids": [], "technical_group_ids": []}

    mock_http = AsyncMock()
    mock_http.put = AsyncMock(return_value=put_response)
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=None)

    get_by_id = AsyncMock(
        side_effect=[detail_active, detail_prepared, detail_prepared, detail_prepared]
    )

    with (
        patch.object(client, "get_by_id", get_by_id),
        patch("src.integrations.tiflux_client.httpx.AsyncClient", return_value=mock_http),
    ):
        await client.delete_client(42)

    assert mock_http.put.await_count >= 2
    prep_body = mock_http.put.await_args_list[0].kwargs["json"]
    final_body = mock_http.put.await_args_list[-1].kwargs["json"]
    assert prep_body["desk_ids"] == []
    assert prep_body["status"] is True
    assert final_body["status"] is False
    assert final_body["desk_ids"] == []
    mock_http.delete.assert_not_called()


@pytest.mark.asyncio
async def test_delete_client_already_inactive_skips_put(env):
    client = TifluxClient(Settings())
    detail = {
        "name": "Fan",
        "social": "Razao",
        "social_revenue": "19131243000197",
        "desk_ids": [],
        "technical_group_ids": [],
        "status": False,
    }
    mock_http = AsyncMock()
    with (
        patch.object(client, "get_by_id", AsyncMock(return_value=detail)),
        patch("src.integrations.tiflux_client.httpx.AsyncClient", return_value=mock_http),
    ):
        await client.delete_client(42)
    mock_http.put.assert_not_called()


@pytest.mark.asyncio
async def test_find_by_filter_uses_active_not_status(env):
    client = TifluxClient(Settings())
    get_response = MagicMock(
        status_code=200,
        text="",
        json=MagicMock(
            return_value=[
                {
                    "id": 7,
                    "name": "RTC",
                    "social": "RTC ACADEMIA LTDA",
                    "social_revenue": "50149208000145",
                    "status": True,
                }
            ]
        ),
    )

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=get_response)
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=None)

    with patch("src.integrations.tiflux_client.httpx.AsyncClient", return_value=mock_http):
        found = await client.find_by_cnpj("50149208000145")

    assert found is not None
    assert found["id"] == 7
    first_params = mock_http.get.await_args_list[0].kwargs["params"]
    assert "status" not in first_params
    assert first_params.get("social_revenue") in ("50149208000145", "50.149.208/0001-45")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rtc_academia_delete_e2e():
    """Requer TIFLUX_API_TOKEN no .env. Exit implícito: assert status=false."""
    clear_settings_cache()
    settings = Settings()
    if not settings.tiflux_api_token.strip():
        pytest.skip("TIFLUX_API_TOKEN não configurado")

    client = TifluxClient(settings)
    found = await client.find_by_cnpj("50149208000145")
    assert found and found.get("id"), "RTC ACADEMIA não encontrado no TiFlux"

    await client.delete_client(int(found["id"]))
    verified = await client.get_by_id(int(found["id"]))
    assert verified is not None
    assert verified.get("status") is False
