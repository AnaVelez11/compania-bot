import pytest
from unittest.mock import AsyncMock, patch

from app.services import generador


@pytest.mark.asyncio
async def test_regenera_si_hay_violacion():
    respuestas = iter([
        "No pasa nada, tranquilo.",              # viola "minimizar"
        "Entiendo que esto te pesa. Cuéntame.",  # válida
    ])

    async def fake_chat(system_prompt, user_prompt, json_mode=True):
        return next(respuestas)

    with patch("app.services.generador.chat_completion", new=fake_chat):
        out = await generador.generar_respuesta(
            texto_limpio="me siento mal",
            emocion="Tristeza",
            intencion="expresar_emocion",
            necesidad="desahogo",
            estrategia="Escuchar / validar",
            avatar="Serena",
            es_riesgo=False,
            acciones_a_evitar=["minimizar"],
        )
    assert out["verificacion"]["ok"] is True
    assert out["verificacion"]["intentos_regeneracion"] == 1


@pytest.mark.asyncio
async def test_fallback_tras_agotar_intentos():
    async def fake_chat(system_prompt, user_prompt, json_mode=True):
        return "No pasa nada, todo va a estar bien."  # viola siempre

    with patch("app.services.generador.chat_completion", new=fake_chat):
        out = await generador.generar_respuesta(
            texto_limpio="me siento mal",
            emocion="Tristeza",
            intencion="expresar_emocion",
            necesidad="desahogo",
            estrategia="Escuchar / validar",
            avatar="Serena",
            es_riesgo=False,
            acciones_a_evitar=["minimizar", "falsas_certezas"],
        )
    assert out["verificacion"]["ok"] is False
    assert out["verificacion"].get("fallback_usado") is True
    assert "No pasa nada" not in out["respuesta"]