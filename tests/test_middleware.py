import pytest
from unittest.mock import AsyncMock, patch

from app.services import middleware


@pytest.mark.asyncio
async def test_texto_vacio_devuelve_otro():
    r = await middleware.procesar_transcripcion("")
    assert r == {"texto_limpio": "", "intencion": "otro"}


@pytest.mark.asyncio
async def test_parsea_json_valido():
    fake = '{"texto_limpio": "Mi hija no vino otra vez.", "intencion": "expresar_emocion"}'
    with patch("app.services.middleware.chat_completion", new=AsyncMock(return_value=fake)):
        r = await middleware.procesar_transcripcion("eh... mi hija no vino... otra vez")
    assert r["intencion"] == "expresar_emocion"
    assert "hija" in r["texto_limpio"]


@pytest.mark.asyncio
async def test_intencion_invalida_cae_a_otro():
    fake = '{"texto_limpio": "hola", "intencion": "cantar"}'
    with patch("app.services.middleware.chat_completion", new=AsyncMock(return_value=fake)):
        r = await middleware.procesar_transcripcion("hola")
    assert r["intencion"] == "otro"