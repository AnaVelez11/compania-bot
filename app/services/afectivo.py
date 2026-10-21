from app.llm_client import chat_completion, safe_json_parse
from app.prompts import AFECTIVO_SYSTEM_PROMPT

_EMOCIONES_VALIDAS = {
    "Tristeza",
    "Alegria",
    "Preocupacion",
    "Frustracion",
    "Cotidianidad",
}


async def clasificar_emocion(texto_limpio: str, intencion: str) -> dict:
    if intencion == "rechazo_tema":
        return {"emocion": "Cotidianidad", "confianza": 0.5}

    if not texto_limpio:
        return {"emocion": "Cotidianidad", "confianza": 0.3}

    raw = await chat_completion(
        system_prompt=AFECTIVO_SYSTEM_PROMPT,
        user_prompt=f'Texto del adulto mayor:\n"{texto_limpio}"',
        json_mode=True,
    )
    data = safe_json_parse(raw, fallback={"emocion": "Cotidianidad", "confianza": 0.4})

    emocion = data.get("emocion", "Cotidianidad")
    if emocion not in _EMOCIONES_VALIDAS:
        emocion = "Cotidianidad"

    try:
        confianza = float(data.get("confianza", 0.5))
    except (TypeError, ValueError):
        confianza = 0.5

    return {"emocion": emocion, "confianza": max(0.0, min(1.0, confianza))}