from app.llm_client import chat_completion, safe_json_parse
from app.prompts import MIDDLEWARE_SYSTEM_PROMPT

_INTENCIONES_VALIDAS = {
    "contar_experiencia",
    "expresar_emocion",
    "rechazo_tema",
    "rechazo_propuesta",
    "saludo",
    "otro",
}


async def procesar_transcripcion(texto_crudo: str) -> dict:
    texto_crudo = (texto_crudo or "").strip()
    if not texto_crudo:
        return {"texto_limpio": "", "intencion": "otro"}

    raw = await chat_completion(
        system_prompt=MIDDLEWARE_SYSTEM_PROMPT,
        user_prompt=f'Transcripción cruda:\n"{texto_crudo}"',
        json_mode=True,
    )
    data = safe_json_parse(
        raw, fallback={"texto_limpio": texto_crudo, "intencion": "otro"}
    )

    texto_limpio = (data.get("texto_limpio") or "").strip() or texto_crudo
    intencion = data.get("intencion", "otro")
    if intencion not in _INTENCIONES_VALIDAS:
        intencion = "otro"

    return {"texto_limpio": texto_limpio, "intencion": intencion}