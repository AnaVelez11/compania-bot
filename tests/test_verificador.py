import pytest
from app.services.verificador import verificar_respuesta


def test_detecta_minimizar():
    r = verificar_respuesta(
        "No pasa nada, no es para tanto.",
        estrategia="Escuchar / validar",
        acciones_a_evitar=["minimizar"],
        es_riesgo=False,
    )
    assert r["ok"] is False
    assert "minimizar" in r["violaciones"]


def test_detecta_falsas_certezas():
    r = verificar_respuesta(
        "Todo va a estar bien, no te preocupes.",
        estrategia="Tranquilizar",
        acciones_a_evitar=["falsas_certezas"],
        es_riesgo=False,
    )
    assert r["ok"] is False
    assert "falsas_certezas" in r["violaciones"]


def test_detecta_comprender_exactamente():
    r = verificar_respuesta(
        "Sé exactamente cómo te sientes.",
        estrategia="Escuchar / validar",
        acciones_a_evitar=["comprender_exactamente"],
        es_riesgo=False,
    )
    assert r["ok"] is False
    assert "comprender_exactamente" in r["violaciones"]


def test_detecta_diagnostico():
    r = verificar_respuesta(
        "Tienes depresión, deberías medicarte.",
        estrategia="Escuchar / validar",
        acciones_a_evitar=["diagnostico", "consejo_no_solicitado"],
        es_riesgo=False,
    )
    assert r["ok"] is False
    assert "diagnostico" in r["violaciones"]


def test_detecta_exageracion_positiva():
    r = verificar_respuesta(
        "¡Qué maravilla! ¡Espectacular noticia!",
        estrategia="Compania",
        acciones_a_evitar=[],
        es_riesgo=False,
    )
    assert r["ok"] is False
    assert "exageracion_positiva" in r["violaciones"]


def test_detecta_multiples_preguntas():
    r = verificar_respuesta(
        "¿Cómo estás? ¿Quieres contarme algo?",
        estrategia="Explorar",
        acciones_a_evitar=["multiples_preguntas"],
        es_riesgo=False,
    )
    assert r["ok"] is False
    assert "multiples_preguntas" in r["violaciones"]


def test_respuesta_valida_pasa():
    r = verificar_respuesta(
        "Entiendo que esto te pesa. Si quieres, cuéntame un poco más.",
        estrategia="Escuchar / validar",
        acciones_a_evitar=["minimizar", "consejo_no_solicitado"],
        es_riesgo=False,
    )
    assert r["ok"] is True


def test_riesgo_permite_diagnostico_para_derivar():
    r = verificar_respuesta(
        "Me preocupa lo que me cuentas. Busca ayuda profesional o llama a emergencias.",
        estrategia="Derivar",
        acciones_a_evitar=["minimizar", "falsas_certezas"],
        es_riesgo=True,
    )
    assert r["ok"] is True