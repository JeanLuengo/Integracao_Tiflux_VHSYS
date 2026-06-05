import httpx

from src.config import Settings
from src.mapping.canonical import CompanyPayload
from src.mapping.vhsys_mapper import to_vhsys_payload


class VhsysApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None, body: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


def _is_not_found_response(response: httpx.Response) -> bool:
    if response.status_code == 404:
        return True
    if response.status_code != 403:
        return False
    text = response.text.lower()
    return "nenhum cliente encontrado" in text


class VhsysClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._base = settings.vhsys_base_url.rstrip("/")

    def _auth_headers(self) -> dict[str, str]:
        return {
            "access-token": self._settings.vhsys_access_token,
            "secret-access-token": self._settings.vhsys_secret_access_token,
            "User-Agent": self._settings.user_agent,
            "Accept": "application/json",
        }

    def _json_headers(self) -> dict[str, str]:
        return {**self._auth_headers(), "Content-Type": "application/json"}

    def _parse_response(self, response: httpx.Response) -> dict:
        if response.status_code == 401:
            raise VhsysApiError("Tokens VHSYS inválidos.", 401, response.text)
        if response.status_code >= 400:
            raise VhsysApiError(
                f"Erro HTTP VHSYS: {response.status_code}.",
                response.status_code,
                response.text,
            )

        data = response.json()
        if not isinstance(data, dict):
            return {"data": data}

        code = data.get("code")
        if code is not None and int(code) >= 400:
            message = data.get("message") or data.get("data") or "Erro VHSYS."
            raise VhsysApiError(str(message), int(code), response.text)

        return data

    async def _list_clientes(self, params: dict) -> list[dict]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self._base}/clientes",
                headers=self._auth_headers(),
                params=params,
            )

        if response.status_code == 401:
            raise VhsysApiError("Tokens VHSYS inválidos.", 401)
        if _is_not_found_response(response):
            return []
        if response.status_code >= 400:
            raise VhsysApiError(
                f"Erro ao listar clientes VHSYS: {response.status_code}.",
                response.status_code,
                response.text,
            )

        data = response.json()
        if isinstance(data, dict) and int(data.get("code", 200)) == 403:
            return []

        if isinstance(data, dict):
            code = data.get("code")
            if code is not None and int(code) >= 400:
                message = data.get("message") or data.get("data") or "Erro VHSYS."
                raise VhsysApiError(str(message), int(code), response.text)

        return _extract_vhsys_clients(data)

    async def find_by_cnpj(self, cnpj_formatted: str) -> dict | None:
        clients = await self.find_matches_by_cnpj(cnpj_formatted, limit=5)
        return clients[0] if clients else None

    async def find_matches_by_cnpj(self, cnpj_formatted: str, limit: int = 10) -> list[dict]:
        return await self._list_clientes(
            {"cnpj_cliente": cnpj_formatted, "lixeira": "Nao", "limit": min(limit, 250)}
        )

    async def find_by_name(self, name: str, limit: int = 10) -> list[dict]:
        term = (name or "").strip()
        if not term:
            return []

        seen: dict[int, dict] = {}
        for param_key in ("razao_cliente", "fantasia_cliente"):
            items = await self._list_clientes(
                {param_key: term, "lixeira": "Nao", "limit": 250}
            )
            for item in items:
                cid = item.get("id_cliente")
                if cid is None:
                    continue
                key = int(cid)
                if key not in seen:
                    seen[key] = item
                if len(seen) >= limit:
                    break
            if len(seen) >= limit:
                break
        return list(seen.values())[:limit]

    async def delete_client(self, id_cliente: int | str) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{self._base}/clientes/{id_cliente}",
                headers=self._auth_headers(),
            )

        if response.status_code == 401:
            raise VhsysApiError("Tokens VHSYS inválidos.", 401, response.text)
        if response.status_code == 404:
            raise VhsysApiError("Cliente não encontrado no VHSYS.", 404, response.text)
        if response.status_code >= 400:
            raise VhsysApiError(
                f"Erro ao excluir cliente VHSYS: {response.status_code}.",
                response.status_code,
                response.text,
            )
        return self._parse_response(response)

    async def create_client(self, company: CompanyPayload) -> dict:
        payload = to_vhsys_payload(company)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._base}/clientes",
                headers=self._json_headers(),
                json=payload,
            )

        return self._parse_response(response)


def _extract_vhsys_clients(data: object) -> list[dict]:
    if isinstance(data, dict):
        inner = data.get("data")
        if isinstance(inner, list):
            return [x for x in inner if isinstance(x, dict)]
        if isinstance(inner, dict):
            return [inner]
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []

