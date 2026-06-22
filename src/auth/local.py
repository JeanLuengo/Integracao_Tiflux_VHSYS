from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from starlette.middleware.base import BaseHTTPMiddleware

from src.auth.email import send_password_reset_email
from src.auth.models import AuthDatabase
from src.auth.passwords import (
    hash_password,
    password_needs_rehash,
    validate_password_policy,
    verify_password,
)
from src.config import Settings, get_settings

REMEMBER_COOKIE = "avs_remember"
GENERIC_LOGIN_ERROR = "E-mail ou senha inválidos."
FORGOT_PASSWORD_MESSAGE = (
    "Se o e-mail estiver cadastrado, enviaremos instruções para redefinir a senha."
)

_db: AuthDatabase | None = None


def get_auth_db(settings: Settings | None = None) -> AuthDatabase:
    global _db
    cfg = settings or get_settings()
    if _db is None:
        _db = AuthDatabase(cfg.auth_db_path)
    return _db


def reset_auth_db_cache() -> None:
    global _db
    _db = None


class LoginBody(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class ForgotPasswordBody(BaseModel):
    email: EmailStr


class ResetPasswordBody(BaseModel):
    token: str = Field(min_length=10)
    password: str


class UpdateProfileBody(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    backup_email: str = ""
    phone: str = Field(default="", max_length=40)


class ChangePasswordBody(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


def _require_session_user(request: Request) -> dict[str, Any]:
    settings = get_settings()
    user = request.session.get("user")
    if not user and settings.auth_enabled:
        if not try_remember_login(request):
            raise HTTPException(status_code=401, detail="Não autenticado.")
        user = request.session.get("user")
    if not user:
        if settings.auth_enabled:
            raise HTTPException(status_code=401, detail="Não autenticado.")
        return {"email": "dev@local", "name": "Desenvolvimento", "dev_mode": True}
    return user


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _regenerate_session(request: Request, user: dict[str, Any]) -> None:
    request.session.clear()
    request.session["user"] = user


def _set_remember_cookie(response: JSONResponse | RedirectResponse, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=REMEMBER_COOKIE,
        value=token,
        max_age=settings.remember_me_days * 24 * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.app_base_url.startswith("https://"),
        path="/",
    )


def _clear_remember_cookie(response: JSONResponse | RedirectResponse) -> None:
    response.delete_cookie(REMEMBER_COOKIE, path="/")


def try_remember_login(request: Request) -> bool:
    settings = get_settings()
    if not settings.auth_enabled or settings.auth_provider != "local":
        return False
    if request.session.get("user"):
        return True
    raw = request.cookies.get(REMEMBER_COOKIE)
    if not raw:
        return False
    db = get_auth_db(settings)
    user = db.get_user_by_remember_token(raw)
    if not user:
        return False
    request.session["user"] = user.to_session_dict()
    return True


class RememberMeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try_remember_login(request)
        return await call_next(request)


def build_local_auth_router() -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["auth"])

    @router.get("/login")
    async def login_page():
        return RedirectResponse(url="/login", status_code=302)

    @router.post("/login")
    async def login(request: Request, body: LoginBody):
        settings = get_settings()
        if not settings.auth_enabled:
            request.session["user"] = {
                "email": "dev@local",
                "name": "Desenvolvimento",
                "dev_mode": True,
            }
            return {"ok": True, "redirect": "/"}

        db = get_auth_db(settings)
        email = body.email.strip().lower()
        ip = _client_ip(request)

        allowed = set(settings.allowed_user_email_list)
        if allowed and email not in allowed:
            db.record_login_attempt(email, ip)
            raise HTTPException(status_code=401, detail=GENERIC_LOGIN_ERROR)

        attempts = db.count_recent_login_attempts(
            email,
            ip,
            window_minutes=settings.login_lockout_minutes,
        )
        if attempts >= settings.login_max_attempts:
            raise HTTPException(
                status_code=429,
                detail="Muitas tentativas. Aguarde alguns minutos e tente novamente.",
            )

        user = db.get_user_by_email(email)
        password_ok = bool(user and verify_password(user.password_hash, body.password))
        if not user or not user.is_active or not password_ok:
            db.record_login_attempt(email, ip)
            raise HTTPException(status_code=401, detail=GENERIC_LOGIN_ERROR)

        db.clear_login_attempts(email, ip)
        session_user = user.to_session_dict()
        if password_needs_rehash(user.password_hash):
            db.update_password(user.id, hash_password(body.password))

        _regenerate_session(request, session_user)

        response = JSONResponse({"ok": True, "redirect": "/"})
        if body.remember_me:
            token = db.create_remember_token(user.id, days=settings.remember_me_days)
            _set_remember_cookie(response, token, settings)
        else:
            db.revoke_remember_tokens(user.id)
            _clear_remember_cookie(response)
        return response

    @router.get("/logout")
    async def logout(request: Request):
        settings = get_settings()
        user = request.session.get("user") or {}
        if settings.auth_enabled and user.get("id"):
            get_auth_db(settings).revoke_remember_tokens(int(user["id"]))
        request.session.clear()
        response = RedirectResponse(url="/login", status_code=302)
        _clear_remember_cookie(response)
        return response

    @router.get("/me")
    async def me(request: Request):
        settings = get_settings()
        user = request.session.get("user")
        if not user and settings.auth_enabled:
            if not try_remember_login(request):
                raise HTTPException(status_code=401, detail="Não autenticado.")
            user = request.session.get("user")
        if not user:
            if settings.auth_enabled:
                raise HTTPException(status_code=401, detail="Não autenticado.")
            user = {"email": "dev@local", "name": "Desenvolvimento", "dev_mode": True}
        return {"authenticated": True, "user": user}

    @router.get("/profile")
    async def get_profile(request: Request):
        session_user = _require_session_user(request)
        if session_user.get("dev_mode"):
            return {
                "email": session_user["email"],
                "name": session_user["name"],
                "backup_email": "",
                "phone": "",
            }
        user_id = session_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Não autenticado.")
        db_user = get_auth_db().get_user_by_id(int(user_id))
        if not db_user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        return db_user.to_profile_dict()

    @router.patch("/profile")
    async def patch_profile(request: Request, body: UpdateProfileBody):
        session_user = _require_session_user(request)
        if session_user.get("dev_mode"):
            raise HTTPException(status_code=400, detail="Perfil indisponível em modo desenvolvimento.")
        if body.backup_email.strip():
            try:
                ForgotPasswordBody(email=body.backup_email.strip())
            except Exception:
                raise HTTPException(status_code=400, detail="E-mail de backup inválido.")
        user_id = session_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Não autenticado.")
        db = get_auth_db()
        updated = db.update_profile(
            int(user_id),
            name=body.name,
            backup_email=body.backup_email.strip(),
            phone=body.phone.strip(),
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        session_user["name"] = updated.name
        request.session["user"] = session_user
        return updated.to_profile_dict()

    @router.post("/change-password")
    async def change_password(request: Request, body: ChangePasswordBody):
        session_user = _require_session_user(request)
        if session_user.get("dev_mode"):
            raise HTTPException(status_code=400, detail="Alteração de senha indisponível em modo desenvolvimento.")
        if body.new_password != body.confirm_password:
            raise HTTPException(status_code=400, detail="As senhas não coincidem.")
        policy_errors = validate_password_policy(body.new_password)
        if policy_errors:
            raise HTTPException(status_code=400, detail=policy_errors[0])
        user_id = session_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Não autenticado.")
        db = get_auth_db()
        user = db.get_user_by_id(int(user_id))
        if not user or not verify_password(user.password_hash, body.current_password):
            raise HTTPException(status_code=400, detail="Senha atual incorreta.")
        db.update_password(user.id, hash_password(body.new_password))
        db.revoke_remember_tokens(user.id)
        return {"ok": True, "message": "Senha alterada com sucesso."}

    @router.post("/forgot-password")
    async def forgot_password(request: Request, body: ForgotPasswordBody):
        settings = get_settings()
        if not settings.auth_enabled:
            return {"message": FORGOT_PASSWORD_MESSAGE}

        db = get_auth_db(settings)
        email = body.email.strip().lower()
        user = db.get_user_by_email(email)
        if user and user.is_active:
            raw_token = db.create_password_reset_token(
                user.id,
                hours=settings.password_reset_token_hours,
            )
            reset_url = f"{settings.app_base_url.rstrip('/')}/login/reset?token={raw_token}"
            try:
                send_password_reset_email(
                    settings,
                    to_email=user.email,
                    reset_url=reset_url,
                    user_name=user.name,
                )
            except Exception:
                pass

        return {"message": FORGOT_PASSWORD_MESSAGE}

    @router.post("/reset-password")
    async def reset_password(body: ResetPasswordBody):
        settings = get_settings()
        if not settings.auth_enabled:
            raise HTTPException(status_code=400, detail="Autenticação desabilitada.")

        policy_errors = validate_password_policy(body.password)
        if policy_errors:
            raise HTTPException(status_code=400, detail=policy_errors[0])

        db = get_auth_db(settings)
        user = db.consume_password_reset_token(body.token.strip())
        if not user:
            raise HTTPException(status_code=400, detail="Link inválido ou expirado.")

        db.update_password(user.id, hash_password(body.password))
        db.revoke_remember_tokens(user.id)
        return {"ok": True, "message": "Senha alterada. Faça login com a nova senha."}

    return router
