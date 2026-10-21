from app.llm_client import chat_completion, safe_json_parse

_NECESIDADES_VALIDAS = {
    "desahogo",
    "compania",
    "escucha",
    "exploracion",
    "orientacion",
    "reminiscencia",
    "distraccion",
    "dar_espacio",
    "conversacion_cotidiana",
    "celebracion",
}

# Tabla estática del protocolo §3 (estado → candidatas en contexto típico)
_CANDIDATAS_POR_ESTADO = {
    "Tristeza": ["compania", "desahogo", "escucha", "conversacion_cotidiana", "dar_espacio"],
    "Alegria": ["celebracion", "compania", "conversacion_cotidiana", "reminiscencia"],
    "Preocupacion": ["exploracion", "orientacion", "escucha"],
    "Frustracion": ["exploracion", "orientacion", "dar_espacio", "desahogo"],
    "Cotidianidad": ["conversacion_cotidiana", "compania", "reminiscencia", "exploracion"],
}

_PROMPT_NECESIDADES = """Eres un analista de necesidades conversacionales para un chatbot de acompañamiento de adultos mayores.

Recibirás un texto y el estado afectivo aparente. Debes:
1. Elegir hasta 3 necesidades candidatas de la lista:
   desahogo, compania, escucha, exploracion, orientacion, reminiscencia,
   distraccion, dar_espacio, conversacion_cotidiana, celebracion
2. Elegir UNA necesidad hipotética principal.
3. Indicar confianza (0.0-1.0).

Si la evidencia es ambigua y varias necesidades son igualmente plausibles, la necesidad hipotética debe ser "exploracion".

Devuelve EXCLUSIVAMENTE JSON:
{"necesidades_candidatas": ["..."], "necesidad_hipotetica": "...", "confianza": 0.0}
"""


async def inferir_necesidad(
    texto_limpio: str,
    emocion: str,
    intencion: str,
) -> dict:
    # Regla dura: rechazo → dar_espacio
    if intencion == "rechazo_tema":
        return {
            "necesidades_candidatas": ["dar_espacio", "distraccion"],
            "necesidad_hipotetica": "dar_espacio",
            "confianza": 0.9,
        }

    # Atajo: texto vacío o ambiguo → exploracion
    if not texto_limpio or len(texto_limpio) < 8:
        return {
            "necesidades_candidatas": _CANDIDATAS_POR_ESTADO.get(
                emocion, ["exploracion", "conversacion_cotidiana"]
            ),
            "necesidad_hipotetica": "exploracion",
            "confianza": 0.3,
        }

    raw = await chat_completion(
        system_prompt=_PROMPT_NECESIDADES,
        user_prompt=(
            f"Estado afectivo aparente: {emocion}\n"
            f'Texto del adulto mayor:\n"{texto_limpio}"'
        ),
        json_mode=True,
    )
    data = safe_json_parse(
        raw,
        fallback={
            "necesidades_candidatas": _CANDIDATAS_POR_ESTADO.get(emocion, ["exploracion"]),
            "necesidad_hipotetica": "exploracion",
            "confianza": 0.4,
        },
    )

    candidatas = [
        c for c in data.get("necesidades_candidatas", []) if c in _NECESIDADES_VALIDAS
    ] or _CANDIDATAS_POR_ESTADO.get(emocion, ["exploracion"])

    hipotetica = data.get("necesidad_hipotetica", "exploracion")
    if hipotetica not in _NECESIDADES_VALIDAS:
        hipotetica = "exploracion"

    try:
        confianza = float(data.get("confianza", 0.5))
    except (TypeError, ValueError):
        confianza = 0.5

    return {
        "necesidades_candidatas": candidatas,
        "necesidad_hipotetica": hipotetica,
        "confianza": max(0.0, min(1.0, confianza)),
    }