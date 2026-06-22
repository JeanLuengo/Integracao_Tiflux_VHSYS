"""Valida formato do .env e testa APIs (sem imprimir tokens completos)."""
import httpx

from src.config import Settings


def audit(name: str, val: str) -> dict:
    v = val or ""
    inner = v[1:-1] if v.startswith("[") and v.endswith("]") else v
    return {
        "name": name,
        "len": len(v),
        "has_brackets": v.startswith("[") and v.endswith("]"),
        "is_placeholder": "SEU_" in v.upper() or v.upper().startswith("[SEU"),
        "jwt_dots_outer": v.count("."),
        "jwt_dots_inner": inner.count("."),
        "looks_like_jwt": inner.count(".") == 2 and len(inner) > 50,
    }


def test_tiflux(token: str, base: str) -> tuple[int, str]:
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    url = f"{base.rstrip('/')}/clients"
    r = httpx.get(url, headers=headers, params={"page": 1, "per_page": 1}, timeout=30)
    return r.status_code, r.text[:180]


def main() -> None:
    s = Settings()
    audits = [
        audit("TIFLUX_API_TOKEN", s.tiflux_api_token),
        audit("VHSYS_ACCESS_TOKEN", s.vhsys_access_token),
        audit("VHSYS_SECRET_ACCESS_TOKEN", s.vhsys_secret_access_token),
    ]
    for a in audits:
        print(a)

    tf = s.tiflux_api_token
    status, _ = test_tiflux(tf, s.tiflux_base_url)
    print(f"TIFLUX_with_env_value: HTTP {status}")

    if tf.startswith("[") and tf.endswith("]"):
        clean = tf[1:-1]
        status2, _ = test_tiflux(clean, s.tiflux_base_url)
        print(f"TIFLUX_without_brackets: HTTP {status2}")


if __name__ == "__main__":
    main()
