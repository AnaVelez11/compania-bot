from app.services.estrategias import seleccionar_estrategia


def test_rechazo_actual_fuerza_dar_espacio():
    r = seleccionar_estrategia(
        "Tristeza", "desahogo", 0.8, "rechazo_tema", False, None
    )
    assert r["estrategia"] == "Dar espacio"


def test_ambiguedad_fuerza_explorar():
    r = seleccionar_estrategia(
        "Preocupacion", "orientacion", 0.3, "expresar_emocion", False, None
    )
    assert r["estrategia"] == "Explorar"


def test_estrategia_valida_por_estado():
    r = seleccionar_estrategia(
        "Tristeza", "desahogo", 0.8, "contar_experiencia", False, None
    )
    assert r["estrategia"] == "Desahogo"


def test_estrategia_no_valida_para_estado_cae_a_explorar():
    # Orientar no está permitido para Alegria
    r = seleccionar_estrategia(
        "Alegria", "orientacion", 0.9, "expresar_emocion", False, None
    )
    assert r["estrategia"] == "Explorar"