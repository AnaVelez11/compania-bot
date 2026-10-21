import json
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger("compania-bot.memoria")

_redis: aioredis.Redis | None = None
_MEMORIA_LOCAL: dict[str, "EstadoUsuario"] = {}


@dataclass
class EstadoUsuario:
    turnos: deque = field(default_factory=lambda: deque(maxlen=10))
    estrategia_anterior: str | None = None
    emocion_anterior: str | None = None
    rechazo_previo: bool = False
    turno: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "turnos": list(self.turnos),
            "estrategia_anterior": self.estrategia_anterior,
            "emocion_anterior": self.emocion_anterior,
            "rechazo_previo": self.rechazo_previo,
            "turno": self.turno,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EstadoUsuario":
        est = cls()
        est.turnos = deque(data.get("turnos", []), maxlen=settings.memoria_max_turnos)
        est.estrategia_anterior = data.get("estrategia_anterior")
        est.emocion_anterior = data.get("emocion_anterior")
        est.rechazo_previo = data.get("rechazo_previo", False)
        est.turno = data.get("turno", 0)
        return est


async def _get_redis() -> aioredis.Redis | None:
    global _redis
    if _redis is None:
        try:
            _redis = aioredis.from_url(
                settings.redis_url, encoding="utf-8", decode_responses=True
            )
            await _redis.ping()
            logger.info("Redis conectado para memoria conversacional.")
        except Exception as exc:
            logger.warning("Redis no disponible, usando memoria local: %s", exc)
            _redis = None
    return _redis


def _key(user_id: str) -> str:
    return f"compania:memoria:{user_id}"


async def obtener(user_id: str) -> EstadoUsuario:
    r = await _get_redis()
    if r is not None:
        raw = await r.get(_key(user_id))
        if raw:
            try:
                return EstadoUsuario.from_dict(json.loads(raw))
            except json.JSONDecodeError:
                pass
        return EstadoUsuario()

    if user_id not in _MEMORIA_LOCAL:
        _MEMORIA_LOCAL[user_id] = EstadoUsuario()
    return _MEMORIA_LOCAL[user_id]


async def registrar_turno(
    user_id: str,
    texto_usuario: str,
    emocion: str,
    estrategia: str,
    intencion: str,
) -> EstadoUsuario:
    est = await obtener(user_id)
    est.turno += 1
    est.turnos.append(
        {
            "turno": est.turno,
            "texto": texto_usuario,
            "emocion": emocion,
            "estrategia": estrategia,
            "intencion": intencion,
        }
    )
    est.emocion_anterior = emocion
    est.estrategia_anterior = estrategia

    if intencion in {"rechazo_tema", "rechazo_propuesta"}:
        est.rechazo_previo = True
    elif intencion in {"contar_experiencia", "expresar_emocion"} and est.rechazo_previo:
        est.rechazo_previo = False

    r = await _get_redis()
    if r is not None:
        await r.set(
            _key(user_id),
            json.dumps(est.to_dict(), ensure_ascii=False),
            ex=settings.memoria_ttl_seconds,
        )
    else:
        _MEMORIA_LOCAL[user_id] = est
    return est


async def reset(user_id: str) -> None:
    _MEMORIA_LOCAL.pop(user_id, None)
    r = await _get_redis()
    if r is not None:
        await r.delete(_key(user_id))