from app.llm_client import chat_completion
from app.prompts import (
    GENERADOR_USER_TEMPLATE,
    INSTRUCCION_RECHAZO,
    INSTRUCCION_REGENERACION,
    construir_system_prompt,
)
from app.services.verificador import verificar_respuesta

_FALLBACK = {
    "Escuchar / validar": "Te escucho y me imagino que esto te pesa. Gracias por compartirlo. ¿Quieres contarme un poco más?",
    "Desahogo": "Parece que esto ha sido difícil para ti. Si quieres, puedes contarme qué fue lo que más te afectó.",
    "Compania": "Me gusta acompañarte. ¿Te gustaría contarme algo de tu día?",
    "Explorar": "Quiero entenderte mejor. ¿Lo que más te pesa es lo que pasó o lo que podría venir después?",
    "Orientar": "Podemos pensar juntos algunas opciones. ¿Prefieres algo tranquilo, salir un poco o hablar con alguien?",
    "Reminiscencia": "Me encanta que compartas esos recuerdos. ¿Hay algún momento que recuerdes con especial cariño?",
    "Tranquilizar": "Es comprensible que te preocupe. Podemos revisar con calma qué sabes hasta ahora y qué opciones tienes.",
    "Distraer": "Si quieres descansar de ese tema, podemos hablar de otra cosa. ¿Música, una película o algo que te guste?",
    "Dar espacio": "Está bien, no tenemos que hablar de eso. Podemos cambiar de tema cuando quieras.",
    "Conversacion cotidiana": "¿Cómo estuvo tu día? ¿Hiciste algo que hayas disfrutado especialmente?",
    "Derivar": (
        "Me preocupa lo que me cuentas y quiero que estés bien. "
        "Por favor, busca a alguien de confianza o llama a un servicio de emergencia. "
        "No estás solo en esto."
    ),
}

_MAX_INTENTOS = 3  # intento original + 2 regeneraciones


async def generar_respuesta(
    texto_limpio: str,
    emocion: str,
    intencion: str,
    necesidad: str,
    estrategia: str,
    avatar: str,
    es_riesgo: bool,
    acciones_a_evitar: list[str],
) -> dict:
    """
    Devuelve {
      "respuesta": str,
      "verificacion": {"ok": bool, "violaciones": [...], "intentos_regeneracion": int}
    }
    """
    if es_riesgo:
        estrategia = "Derivar"

    system_prompt = construir_system_prompt(estrategia, es_riesgo)

    instruccion_extra = ""
    if intencion in {"rechazo_tema", "rechazo_propuesta"}:
        instruccion_extra = INSTRUCCION_RECHAZO

    user_prompt_base = GENERADOR_USER_TEMPLATE.format(
        avatar=avatar,
        emocion=emocion,
        necesidad=necesidad,
        estrategia=estrategia,
        texto_limpio=texto_limpio or "(sin texto claro)",
    )
    if instruccion_extra:
        user_prompt_base += f"\n\n{instruccion_extra}"

    ultima_verificacion = {"ok": False, "violaciones": ["sin_intento"]}
    ultima_respuesta = ""

    for intento in range(_MAX_INTENTOS):
        try:
            user_prompt = user_prompt_base
            if intento > 0:
                user_prompt += "\n\n" + INSTRUCCION_REGENERACION.format(
                    violaciones=", ".join(ultima_verificacion["violaciones"])
                )

            respuesta = await chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                json_mode=False,
            )
            respuesta = (respuesta or "").strip()
            if not respuesta:
                ultima_verificacion = {"ok": False, "violaciones": ["respuesta_vacia"]}
                continue

            verificacion = verificar_respuesta(
                respuesta=respuesta,
                estrategia=estrategia,
                acciones_a_evitar=acciones_a_evitar,
                es_riesgo=es_riesgo,
            )
            ultima_respuesta = respuesta
            ultima_verificacion = verificacion

            if verificacion["ok"]:
                return {
                    "respuesta": respuesta,
                    "verificacion": {**verificacion, "intentos_regeneracion": intento},
                }
        except Exception:
            ultima_verificacion = {"ok": False, "violaciones": ["error_llm"]}
            continue

    # Tras N intentos: fallback seguro
    return {
        "respuesta": _FALLBACK.get(estrategia, _FALLBACK["Explorar"]),
        "verificacion": {
            "ok": False,
            "violaciones": ultima_verificacion.get("violaciones", []),
            "intentos_regeneracion": _MAX_INTENTOS - 1,
            "fallback_usado": True,
            "ultima_respuesta_descartada": ultima_respuesta[:200],
        },
    }