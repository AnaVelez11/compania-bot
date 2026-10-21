import pytest
from unittest.mock import AsyncMock, patch
from app.services import riesgo


@pytest.mark.asyncio
async def test_regla_lexica_ideacion():
    r = await riesgo.detectar_riesgo("ya no quiero vivir")
    assert r["riesgo"] is True
    assert r["tipo"] == "ideacion_suicida"


@pytest.mark.asyncio
async def test_regla_lexica_caida():
    r = await riesgo.detectar_riesgo("me caí en el baño y me duele mucho")
    assert r["riesgo"] is True
    assert r["tipo"] == "emergencia_medica"


@pytest.mark.asyncio
async def test_sin_riesgo_llm():
    fake = '{"riesgo": false, "tipo": "ninguno", "confianza": 0.9}'
    with patch("app.services.riesgo.chat_completion", new=AsyncMock(return_value=fake)):
        r = await riesgo.detectar_riesgo("hoy tomé café con mi vecina")
    assert r["riesgo"] is False