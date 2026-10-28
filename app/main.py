import logging
import os
import tempfile

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.models import (
    ChatMeta,
    ChatRequest,
    ChatResponse,
    Verificacion,
    VUIConfig,
)
from app.rate_limit import limiter, rate_limit_exceeded_handler
from app.services.afectivo import clasificar_emocion
from app.services.estrategias import seleccionar_estrategia
from app.services.generador import generar_respuesta
from app.services.memoria import obtener, registrar_turno, reset
from app.services.middleware import procesar_transcripcion
from app.services.necesidades import inferir_necesidad
from app.services.riesgo import detectar_riesgo
from app.services.stt import cargar_modelo, transcribir
from app.utils.logging import setup_logging

setup_logging()
logger = logging.getLogger("compania-bot")

# ---------------------------------------------------------------------------
# 1) Crear la app ANTES de usar @app.algo
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Chatbot de compañía para adultos mayores",
    version="2.2.0",
    description="Servidor alineado al Protocolo de comportamiento conversacional afectivo.",
)

# ---------------------------------------------------------------------------
# 2) Middlewares y handlers (también antes de los endpoints)
# ---------------------------------------------------------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://vincula-app.netlify.app", "http://localhost:5500"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# ---------------------------------------------------------------------------
# 3) Startup: cargar Whisper una sola vez
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup() -> None:
    try:
        cargar_modelo()
    except Exception as exc:
        logger.warning(
            "Whisper no se pudo cargar, /api/chat/audio no estará disponible: %s",
            exc,
        )

# ---------------------------------------------------------------------------
# 4) Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
@limiter.exempt
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/reset/{user_id}")
async def reset_usuario(user_id: str) -> dict:
    await reset(user_id)
    return {"status": "ok", "user_id": user_id}


@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit(f"{settings.rate_limit_chat_por_minuto}/minute")
async def chat(request: Request, req: ChatRequest) -> ChatResponse:
    try:
        estado = await obtener(req.user_id)
        rechazo_previo = estado.rechazo_previo
        estrategia_anterior = estado.estrategia_anterior

        mw = await procesar_transcripcion(req.texto)
        texto_limpio = mw["texto_limpio"]
        intencion = mw["intencion"]

        riesgo = await detectar_riesgo(texto_limpio)
        af = await clasificar_emocion(texto_limpio, intencion)
        emocion = af["emocion"]
        nec = await inferir_necesidad(texto_limpio, emocion, intencion)

        if riesgo["riesgo"]:
            sel = {
                "estrategia": "Derivar",
                "motivo": f"riesgo:{riesgo['tipo']}",
                "tono": "calmado, claro, protector",
                "estructura": "reconocimiento + recomendación de buscar ayuda + acompañamiento",
                "acciones_a_evitar": ["diagnostico", "minimizar", "falsas_certezas"],
            }
        else:
            sel = seleccionar_estrategia(
                emocion=emocion,
                necesidad_hipotetica=nec["necesidad_hipotetica"],
                confianza_necesidad=nec["confianza"],
                intencion=intencion,
                rechazo_previo=rechazo_previo,
                estrategia_anterior=estrategia_anterior,
            )

        gen = await generar_respuesta(
            texto_limpio=texto_limpio,
            emocion=emocion,
            intencion=intencion,
            necesidad=nec["necesidad_hipotetica"],
            estrategia=sel["estrategia"],
            avatar=req.avatar,
            es_riesgo=riesgo["riesgo"],
            acciones_a_evitar=sel["acciones_a_evitar"],
        )
        respuesta = gen["respuesta"]
        verif = gen["verificacion"]

        if riesgo["riesgo"]:
            quick_replies = ["Necesito ayuda", "Estoy bien, sigamos"]
        elif sel["estrategia"] == "Dar espacio":
            quick_replies = ["Hablemos de otra cosa", "Prefiero seguir"]
        elif sel["estrategia"] == "Distraer":
            quick_replies = ["Hablemos de algo ligero", "Cuéntame algo bonito"]
        elif sel["estrategia"] in {"Explorar", "Orientar"}:
            quick_replies = ["Quiero contar más", "Prefiero otra cosa"]
        else:
            quick_replies = ["Quiero contar más", "Prefiero cambiar de tema"]

        await registrar_turno(
            user_id=req.user_id,
            texto_usuario=req.texto,
            emocion=emocion,
            estrategia=sel["estrategia"],
            intencion=intencion,
        )

        return ChatResponse(
            respuesta_texto=respuesta,
            emocion_detectada=emocion,
            quick_replies=quick_replies,
            vui_config=VUIConfig(
                tts_speed=settings.tts_speed,
                vad_silence_sec=settings.vad_silence_sec,
            ),
            verificacion_ok=verif.get("ok", True),
            meta=ChatMeta(
                evidencia=texto_limpio[:160],
                estado_hipotetico=emocion,
                confianza_emocional=af["confianza"],
                necesidades_candidatas=nec["necesidades_candidatas"],
                necesidad_hipotetica=nec["necesidad_hipotetica"],
                estrategia=sel["estrategia"],
                motivo_estrategia=sel["motivo"],
                tono=sel["tono"],
                estructura=sel["estructura"],
                acciones_a_evitar=sel["acciones_a_evitar"],
                rechazo_previo=rechazo_previo,
                riesgo=riesgo["riesgo"],
                tipo_riesgo=riesgo["tipo"],
                texto_limpio=texto_limpio,
                intencion=intencion,
                turno=estado.turno,
                verificacion=Verificacion(
                    ok=verif.get("ok", True),
                    violaciones=verif.get("violaciones", []),
                    intentos_regeneracion=verif.get("intentos_regeneracion", 0),
                ),
            ),
        )
    except Exception as exc:
        logger.exception("Error procesando /api/chat: %s", exc)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


@app.post("/api/chat/audio", response_model=ChatResponse)
async def chat_audio(
    request: Request,
    user_id: str = Form(...),
    avatar: str = Form("Neutro"),
    audio: UploadFile = File(...),
) -> ChatResponse:
    suffix = os.path.splitext(audio.filename or "audio.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        contenido = await audio.read()
        tmp.write(contenido)
        ruta = tmp.name

    try:
        texto = transcribir(ruta, idioma="es")
        if not texto:
            raise HTTPException(
                status_code=422, detail="No se pudo transcribir el audio."
            )
        req = ChatRequest(user_id=user_id, texto=texto, avatar=avatar)
        return await chat(request, req)
    finally:
        try:
            os.unlink(ruta)
        except OSError:
            pass