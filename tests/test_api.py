from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.services import memoria

client = TestClient(app)


def _mockear_pipeline(
    texto="me siento mal",
    intencion="expresar_emocion",
    emocion="Tristeza",
    necesidad="desahogo",
    respuesta="Entiendo que esto te pesa. Cuéntame un poco más.",
    violaciones=None,
):
    return {
        "app.main.procesar_transcripcion": AsyncMock(
            return_value={"texto_limpio": texto, "intencion": intencion}),
        "app.main.detectar_riesgo": AsyncMock(
            return_value={"riesgo": False, "tipo": "ninguno", "confianza": 0.9}),
        "app.main.clasificar_emocion": AsyncMock(
            return_value={"emocion": emocion, "confianza": 0.9}),
        "app.main.inferir_necesidad": AsyncMock(
            return_value={
                "necesidades_candidatas": [necesidad],
                "necesidad_hipotetica": necesidad,
                "confianza": 0.9,
            }),
        "app.main.generar_respuesta": AsyncMock(
            return_value={
                "respuesta": respuesta,
                "verificacion": {
                    "ok": not violaciones,
                    "violaciones": violaciones or [],
                    "intentos_regeneracion": 0,
                },
            }),
    }


def test_meta_incluye_razonamiento_completo():
    memoria.reset("u-meta")
    mocks = _mockear_pipeline()
    with patch.multiple("app.main", **mocks):
        r = client.post("/api/chat", json={
            "user_id": "u-meta", "texto": "me siento mal", "avatar": "Serena",
        })
    data = r.json()
    meta = data["meta"]
    assert meta["estrategia"]
    assert meta["motivo_estrategia"]
    assert meta["tono"]
    assert meta["estructura"]
    assert isinstance(meta["acciones_a_evitar"], list)
    assert "verificacion" in meta
    assert data["verificacion_ok"] is True


def test_rechazo_propuesta_fuerza_dar_espacio():
    memoria.reset("u-prop")
    mocks = _mockear_pipeline(
        texto="no, mejor otra cosa",
        intencion="rechazo_propuesta",
        emocion="Cotidianidad",
        necesidad="dar_espacio",
        respuesta="Está bien, hablemos de otra cosa cuando quieras.",
    )
    with patch.multiple("app.main", **mocks):
        r = client.post("/api/chat", json={
            "user_id": "u-prop", "texto": "no, mejor otra cosa", "avatar": "Serena",
        })
    data = r.json()
    assert data["meta"]["estrategia"] == "Dar espacio"
    assert data["meta"]["motivo_estrategia"] == "rechazo_actual:rechazo_propuesta"


def test_verificacion_fallida_se_refleja_en_meta():
    memoria.reset("u-viol")
    mocks = _mockear_pipeline(
        respuesta="No pasa nada, todo va a estar bien.",
        violaciones=["minimizar", "falsas_certezas"],
    )
    with patch.multiple("app.main", **mocks):
        r = client.post("/api/chat", json={
            "user_id": "u-viol", "texto": "me siento mal", "avatar": "Serena",
        })
    data = r.json()
    assert data["verificacion_ok"] is False
    assert "minimizar" in data["meta"]["verificacion"]["violaciones"]