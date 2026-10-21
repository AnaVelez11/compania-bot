from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings


def _key_por_usuario(request: Request) -> str:
    user_id = request.path_params.get("user_id")
    if user_id:
        return f"user:{user_id}"
    user_id = request.query_params.get("user_id")
    if user_id:
        return f"user:{user_id}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=_key_por_usuario,
    storage_uri=settings.rate_limit_storage_uri,
    enabled=settings.rate_limit_enabled,
    default_limits=[
        f"{settings.rate_limit_chat_por_minuto}/minute",
        f"{settings.rate_limit_chat_por_hora}/hour",
    ],
)


def rate_limit_exceeded_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limit_exceeded",
                "detail": f"Límite excedido: {exc.detail}",
                "retry_after_seconds": 60,
            },
        )
    return JSONResponse(
        status_code=503,
        content={
            "error": "rate_limit_backend_unavailable",
            "detail": "El servicio de rate limiting no está disponible.",
        },
    )