import pytest
from unittest.mock import AsyncMock, patch

from app.services import generador


@pytest.mark.asyncio
async def test_regla_no_insistencia_en_prompt():
    captured = {}

    async def fake_chat(system_prompt, user_prompt, json_mode=True):
        captured["user_prompt"] = user_prompt
        return "Está bien, hablemos de algo tranquilo. ¿Prefieres el clima o la música?"

    with patch("app.services.generador.chat_completion", new=fake_chat):
        r = await generador.generar_respuesta(
            texto_limpio="no quiero hablar de mi hijo",
            emocion="Neutralidad",
            intencion="rechazo_tema",
            avatar="Serena",
        )
    assert "rechazó el tema" in captured["user_prompt"]
    assert "Está bien" in r


@pytest.mark.asyncio
async def test_fallback_si_llm_falla():
    with patch("app.services.generador.chat_completion", new=AsyncMock(side_effect=Exception("boom"))):
        r = await generador.generar_respuesta(
            texto_limpio="me siento triste",
            emocion="Tristeza",
            intencion="expresar_emocion",
            avatar="Serena",
        )
    assert isinstance(r, str) and len(r) > 0