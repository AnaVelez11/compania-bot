import re

from app.prompts import PROHIBICIONES_ETIQUETAS

# Etiquetas que aplican a cualquier estrategia (prohibiciones globales)
_GLOBALES = {
    "minimizar",
    "falsas_certezas",
    "comprender_exactamente",
    "exageracion_positiva",
    "diagnostico",
    "consejo_no_solicitado",
    "multiples_preguntas",
}


def _detectar_violaciones_lexicas(texto: str, etiquetas: set[str]) -> list[str]:
    violaciones = []
    t = texto.lower()
    for etiqueta in etiquetas:
        patrones = PROHIBICIONES_ETIQUETAS.get(etiqueta, [])
        for pat in patrones:
            if re.search(pat, t, flags=re.IGNORECASE):
                violaciones.append(etiqueta)
                break
    return violaciones


def _contar_preguntas(texto: str) -> int:
    aperturas = texto.count("¿")
    if aperturas > 0:
        return aperturas
    return texto.count("?")


def verificar_respuesta(
    respuesta: str,
    estrategia: str,
    acciones_a_evitar: list[str],
    es_riesgo: bool,
) -> dict:
    """Devuelve {"ok": bool, "violaciones": [str]}."""
    if not respuesta:
        return {"ok": False, "violaciones": ["respuesta_vacia"]}

    # Conjunto de etiquetas aplicables
    etiquetas = set(_GLOBALES) | set(acciones_a_evitar)

    # Si hay riesgo, permitimos "diagnostico" solo si el mensaje deriva,
    # pero prohibimos falsas certezas y minimización en cualquier caso.
    if es_riesgo:
        etiquetas.discard("diagnostico")

    violaciones = _detectar_violaciones_lexicas(respuesta, etiquetas)

    # Prohibición estructural: máximo una pregunta
    if _contar_preguntas(respuesta) > 1 and "multiples_preguntas" in etiquetas:
        if "multiples_preguntas" not in violaciones:
            violaciones.append("multiples_preguntas")

    return {"ok": len(violaciones) == 0, "violaciones": violaciones}