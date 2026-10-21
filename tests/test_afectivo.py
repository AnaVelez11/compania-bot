import pytest
from unittest.mock import AsyncMock, patch

from app.services import afectivo


@pytest.mark.asyncio
async def test_rechazo_es_cotidianidad():
    r = await afectivo.clasificar_emocion("no quiero hablar de eso", "rechazo_tema")
    assert r["emocion"] == "Neutralidad"


@pytest.mark.asyncio
async def test_clasifica_tristeza():
    fake = '{"emocion": "Tristeza", "confianza": 0.9}'
    with patch("app.services.afectivo.chat_completion", new=AsyncMock(return_value=fake)):
        r = await afectivo.clasificar_emocion("extraño a mi esposo", "expresar_emocion")
    assert r["emocion"] == "Tristeza"
    assert r["confianza"] == 0.9