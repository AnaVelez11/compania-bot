import re

from app.llm_client import chat_completion, safe_json_parse

# Patrones léxicos de alta prioridad (evitan depender solo del LLM)
_PATRONES_RIESGO = {
    "ideacion_suicida": [
        r"\b(no quiero|ya no quiero) (vivir|estar aquí|seguir)\b",
        r"\bquitarme la vida\b",
        r"\bsuicid\w*\b",
        r"\bmejor (me muero|desaparecer)\b",
    ],
    "emergencia_medica": [
        r"\b(me caí|caída|no puedo respirar|me duele (mucho|fuerte) el pecho)\b",
        r"\b(desmay|infarto|derrame|sangr\w+)\b",
        r"\b(me siento muy mal|necesito (un )?médico)\b",
    ],
    "violencia_abuso": [
        r"\b(me (golpe|pega|maltrata)|abusan? de mí|me amenaz\w+)\b",
    ],
    "desorientacion_severa": [
        r"\bno sé (dónde estoy|quién soy|qué día es)\b",
        r"\bme perdí\b",
    ],
}

_PROMPT_RIESGO = """Eres un detector de riesgo para un chatbot de compañía de adultos mayores.

Analiza el texto y decide si contiene señales de:
- "ideacion_suicida": deseo de morir, autolesión, desesperanza extrema.
- "emergencia_medica": caída, dolor agudo, dificultad para respirar, desmayo, sangrado.
- "violencia_abuso": golpes, amenazas, abuso.
- "desorientacion_severa": no saber dónde está, quién es o qué día es.
- "ninguno": sin señales de riesgo.

Sé conservador: ante duda razonable, marca "riesgo": true.
Devuelve EXCLUSIVAMENTE JSON:
{"riesgo": true/false, "tipo": "ideacion_suicida|emergencia_medica|violencia_abuso|desorientacion_severa|ninguno", "confianza": 0.0}
"""


def _detectar_por_reglas(texto: str) -> str | None:
    t = (texto or "").lower()
    for tipo, patrones in _PATRONES_RIESGO.items():
        for pat in patrones:
            if re.search(pat, t, flags=re.IGNORECASE):
                return tipo
    return None


async def detectar_riesgo(texto_limpio: str) -> dict:
    """Devuelve {"riesgo": bool, "tipo": str, "confianza": float}."""
    if not texto_limpio:
        return {"riesgo": False, "tipo": "ninguno", "confianza": 0.0}

    tipo_regla = _detectar_por_reglas(texto_limpio)
    if tipo_regla:
        return {"riesgo": True, "tipo": tipo_regla, "confianza": 0.95}

    # Verificación por LLM solo si no hay match léxico
    raw = await chat_completion(
        system_prompt=_PROMPT_RIESGO,
        user_prompt=f'Texto del adulto mayor:\n"{texto_limpio}"',
        json_mode=True,
    )
    data = safe_json_parse(
        raw, fallback={"riesgo": False, "tipo": "ninguno", "confianza": 0.5}
    )
    return {
        "riesgo": bool(data.get("riesgo", False)),
        "tipo": data.get("tipo", "ninguno"),
        "confianza": float(data.get("confianza", 0.5)),
    }