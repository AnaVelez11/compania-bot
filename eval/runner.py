"""
Runner de evaluación del LLM contra el golden set del protocolo.

Uso:
    python -m eval.runner

Mide:
- % de acierto en emoción (E1-E5)
- % de acierto en estrategia
- % de acierto en necesidad
- similitud semántica media vs reference_answer
- % de respuestas que contienen forbidden_phrases
"""
import asyncio
import json
import sys
from pathlib import Path

from sentence_transformers import SentenceTransformer, util

from app.config import settings
from app.services.afectivo import clasificar_emocion
from app.services.estrategias import seleccionar_estrategia
from app.services.generador import generar_respuesta
from app.services.middleware import procesar_transcripcion
from app.services.necesidades import inferir_necesidad
from app.services.riesgo import detectar_riesgo

GOLDEN_PATH = Path(__file__).parent / "golden_set.json"


def _contiene_forbidden(respuesta: str, forbidden: list[str]) -> bool:
    t = respuesta.lower()
    return any(f.lower() in t for f in forbidden)


async def evaluar_caso(caso: dict, embedder: SentenceTransformer) -> dict:
    texto = caso["input"]
    mw = await procesar_transcripcion(texto)
    intencion = mw["intencion"]
    texto_limpio = mw["texto_limpio"]

    riesgo = await detectar_riesgo(texto_limpio)
    af = await clasificar_emocion(texto_limpio, intencion)
    nec = await inferir_necesidad(texto_limpio, af["emocion"], intencion)

    if riesgo["riesgo"]:
        sel = {
            "estrategia": "Derivar",
            "acciones_a_evitar": ["diagnostico", "minimizar", "falsas_certezas"],
        }
    else:
        sel = seleccionar_estrategia(
            emocion=af["emocion"],
            necesidad_hipotetica=nec["necesidad_hipotetica"],
            confianza_necesidad=nec["confianza"],
            intencion=intencion,
            rechazo_previo=False,
            estrategia_anterior=None,
        )

    gen = await generar_respuesta(
        texto_limpio=texto_limpio,
        emocion=af["emocion"],
        intencion=intencion,
        necesidad=nec["necesidad_hipotetica"],
        estrategia=sel["estrategia"],
        avatar="Alma",
        es_riesgo=riesgo["riesgo"],
        acciones_a_evitar=sel["acciones_a_evitar"],
    )

    emb_ref = embedder.encode(caso["reference_answer"], convert_to_tensor=True)
    emb_gen = embedder.encode(gen["respuesta"], convert_to_tensor=True)
    similitud = float(util.cos_sim(emb_ref, emb_gen))

    return {
        "id": caso["id"],
        "emocion_ok": af["emocion"] == caso["expected_emocion"],
        "estrategia_ok": sel["estrategia"] == caso["expected_estrategia"],
        "necesidad_ok": nec["necesidad_hipotetica"] == caso["expected_necesidad"],
        "similitud": similitud,
        "similitud_ok": similitud >= settings.evaluacion_similitud_min,
        "forbidden_ok": not _contiene_forbidden(gen["respuesta"], caso["forbidden_phrases"]),
        "verificacion_ok": gen["verificacion"].get("ok", True),
        "respuesta": gen["respuesta"],
        "emocion": af["emocion"],
        "estrategia": sel["estrategia"],
    }


async def main() -> int:
    casos = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    print(f"Cargando embedder: {settings.evaluacion_embedding_model}")
    embedder = SentenceTransformer(settings.evaluacion_embedding_model)

    resultados = []
    for caso in casos:
        print(f"  evaluando {caso['id']}...")
        r = await evaluar_caso(caso, embedder)
        resultados.append(r)
        print(
            f"    emoción={r['emocion']} estrategia={r['estrategia']} "
            f"sim={r['similitud']:.3f} forbidden_ok={r['forbidden_ok']}"
        )

    total = len(resultados)
    print("\n===== RESUMEN =====")
    print(f"Casos: {total}")
    print(f"Emoción OK:      {sum(r['emocion_ok'] for r in resultados)}/{total}")
    print(f"Estrategia OK:   {sum(r['estrategia_ok'] for r in resultados)}/{total}")
    print(f"Necesidad OK:    {sum(r['necesidad_ok'] for r in resultados)}/{total}")
    print(f"Similitud media: {sum(r['similitud'] for r in resultados)/total:.3f}")
    print(f"Similitud OK:    {sum(r['similitud_ok'] for r in resultados)}/{total}")
    print(f"Forbidden OK:    {sum(r['forbidden_ok'] for r in resultados)}/{total}")
    print(f"Verificación OK: {sum(r['verificacion_ok'] for r in resultados)}/{total}")

    # Salida CI: falla si algo crítico está mal
    fallos = [
        r for r in resultados
        if not (r["emocion_ok"] and r["estrategia_ok"] and r["similitud_ok"] and r["forbidden_ok"])
    ]
    if fallos:
        print(f"\n❌ {len(fallos)} caso(s) fallaron:")
        for f in fallos:
            print(f"  - {f['id']}: {f}")
        return 1
    print("\n✅ Todos los casos pasaron.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))