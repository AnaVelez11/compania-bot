from app.services import memoria


def test_rechazo_previo_se_mantiene():
    memoria.reset("u1")
    memoria.registrar_turno("u1", "no quiero hablar", "Tristeza", "Dar espacio", "rechazo_tema")
    est = memoria.obtener("u1")
    assert est.rechazo_previo is True
    assert est.estrategia_anterior == "Dar espacio"


def test_rechazo_previo_se_limpia_si_retoma():
    memoria.reset("u2")
    memoria.registrar_turno("u2", "no quiero", "Tristeza", "Dar espacio", "rechazo_tema")
    memoria.registrar_turno("u2", "bueno, te cuento", "Tristeza", "Desahogo", "contar_experiencia")
    assert memoria.obtener("u2").rechazo_previo is False