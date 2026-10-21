from app.prompts import ACCIONES_A_EVITAR

_ESTRATEGIA_POR_NECESIDAD = {
    "desahogo": "Desahogo",
    "compania": "Compania",
    "escucha": "Escuchar / validar",
    "exploracion": "Explorar",
    "orientacion": "Orientar",
    "reminiscencia": "Reminiscencia",
    "distraccion": "Distraer",
    "dar_espacio": "Dar espacio",
    "conversacion_cotidiana": "Conversacion cotidiana",
    "celebracion": "Compania",
}

_ESTRATEGIAS_POR_ESTADO = {
    "Tristeza": {"Escuchar / validar", "Desahogo", "Compania", "Dar espacio", "Distraer"},
    "Alegria": {"Compania", "Explorar", "Reminiscencia", "Conversacion cotidiana"},
    "Preocupacion": {"Tranquilizar", "Escuchar / validar", "Explorar", "Orientar"},
    "Frustracion": {"Escuchar / validar", "Desahogo", "Explorar", "Orientar", "Dar espacio"},
    "Cotidianidad": {"Conversacion cotidiana", "Compania", "Explorar", "Reminiscencia"},
}

# Tono y estructura por estrategia (protocolo §6)
_METADATOS_ESTRATEGIA = {
    "Escuchar / validar": ("cálido, tranquilo, respetuoso", "reconocimiento + contexto + invitación opcional"),
    "Desahogo": ("cálido, paciente, receptivo", "reconocimiento + invitación a expresar + seguimiento opcional"),
    "Compania": ("cercano, natural, ligero", "reconocimiento + propuesta de conversación + elección"),
    "Explorar": ("curioso, respetuoso, paciente", "contexto + pregunta pertinente + opciones"),
    "Orientar": ("claro, colaborativo, no impositivo", "comprensión + alternativas + elección del usuario"),
    "Reminiscencia": ("cálido, interesado, respetuoso", "referencia al recuerdo + pregunta abierta + seguimiento"),
    "Tranquilizar": ("calmado, seguro, empático", "reconocimiento + perspectiva + posible siguiente paso"),
    "Distraer": ("ligero, amigable, natural", "reconocimiento + propuesta + elección"),
    "Dar espacio": ("respetuoso, breve, no invasivo", "reconocimiento + respeto de la decisión + disponibilidad opcional"),
    "Conversacion cotidiana": ("natural, cercano, amigable", "tema cotidiano + pregunta abierta + continuidad"),
    "Derivar": ("calmado, claro, protector", "reconocimiento + recomendación de buscar ayuda + acompañamiento"),
}


def _resultado(estrategia: str, motivo: str) -> dict:
    tono, estructura = _METADATOS_ESTRATEGIA.get(estrategia, ("", ""))
    return {
        "estrategia": estrategia,
        "motivo": motivo,
        "tono": tono,
        "estructura": estructura,
        "acciones_a_evitar": ACCIONES_A_EVITAR.get(estrategia, []),
    }


def seleccionar_estrategia(
    emocion: str,
    necesidad_hipotetica: str,
    confianza_necesidad: float,
    intencion: str,
    rechazo_previo: bool,
    estrategia_anterior: str | None,
) -> dict:
    # Regla 1: rechazo actual (tema o propuesta) → Dar espacio
    if intencion in {"rechazo_tema", "rechazo_propuesta"}:
        return _resultado("Dar espacio", f"rechazo_actual:{intencion}")

    # Regla 2: rechazo previo no resuelto → mantener Dar espacio/Distraer
    if rechazo_previo and estrategia_anterior in {"Dar espacio", "Distraer"}:
        return _resultado(estrategia_anterior, "rechazo_previo")

    # Regla 3: ambigüedad alta → Explorar
    if confianza_necesidad < 0.45:
        return _resultado("Explorar", "ambiguedad")

    # Regla 4: necesidad → estrategia
    estrategia = _ESTRATEGIA_POR_NECESIDAD.get(necesidad_hipotetica, "Explorar")

    # Regla 5: si no es válida para el estado, caer a Explorar
    permitidas = _ESTRATEGIAS_POR_ESTADO.get(emocion, {"Explorar"})
    if estrategia not in permitidas:
        return _resultado("Explorar", f"estrategia_no_valida_para_{emocion}")

    return _resultado(estrategia, "necesidad")