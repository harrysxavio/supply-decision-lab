# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = [
#     "laya==0.3.23",
# ]
#
# [tool.uv]
# [[tool.uv.index]]
# name = "pytorch-cpu"
# url = "https://download.pytorch.org/whl/cpu"
# explicit = false
# ///
"""Fase 1 — ¿cambia el juicio del modelo si el estado ya trae las cuentas hechas?

El script hace cuatro cosas, en este orden:

    1. toma los datos del caso (tres números),
    2. calcula tres hechos: cobertura, faltante y unidades faltantes,
    3. arma dos estados: la narrativa cruda y la misma narrativa más los hechos,
    4. le pregunta lo mismo al modelo sobre los dos estados.

La frontera de la fase está en el paso 2: el software calcula **hechos** (cuentas que
siempre dan lo mismo), nunca **juicios** (riesgo alto, qué área, qué hacer). Los juicios
quedan del lado del modelo.

Se ejecuta con:

    uv run --python 3.12 enrich.py

Los tests de la aritmética corren aparte y no necesitan el modelo:

    uv run --python 3.12 test_enrich.py
"""

# ---------------------------------------------------------------------------
# PARTE 1 — Los datos del caso
# ---------------------------------------------------------------------------
# Tres números, nada más. Todo lo demás (la narrativa y los hechos) se deriva de
# acá, así los números no pueden contradecirse entre sí.
#
# Es la diferencia central con la Fase 0: allá el caso era un párrafo escrito a
# mano; acá es un dato estructurado del que se puede calcular.
CASE = {
    "supplier_delay_days": 12,   # el proveedor avisa que llega 12 días tarde
    "stock_units": 500,          # unidades disponibles hoy en el almacén
    "daily_demand_units": 100,   # unidades que consume la línea por día
}

# Las dos formulaciones de la misma pregunta. Se prueban las dos para separar
# dos causas posibles: "el modelo no entendió el texto" (redacción) de "al modelo
# le faltó el cálculo" (información).
#
#   retraso_mencionado -> pregunta por lo que el correo DICE explícitamente.
#   riesgo_parada      -> pide una CONCLUSIÓN sobre lo que el correo implica.
#
# En las dos, `noul` devuelve P(verdadero): un número entre 0 y 1.
QUESTIONS = {
    "retraso_mencionado": {
        "type": "noul",
        "instructions": "¿El correo menciona un retraso en la llegada del material?",
    },
    "riesgo_parada": {
        "type": "noul",
        "instructions": "¿El correo reporta un riesgo concreto de detener la producción?",
    },
}


# ---------------------------------------------------------------------------
# PARTE 2 — La aritmética: hechos, no juicios
# ---------------------------------------------------------------------------
# Estas tres funciones son la única lógica propia de la fase. Cada una responde
# una cuenta que se puede verificar con papel y lápiz, y que siempre da lo mismo.
#
# Los datos inválidos se rechazan en vez de calcularse: si el consumo diario es
# cero, "días de cobertura" sería una división por cero, que no es un hecho sino
# un error del dato de entrada.

def coverage_days(stock_units: float, daily_demand_units: float) -> float:
    """Cuántos días de producción alcanza el stock actual."""
    if daily_demand_units <= 0:
        raise ValueError("daily_demand_units debe ser mayor que cero")
    if stock_units < 0:
        raise ValueError("stock_units no puede ser negativo")
    return stock_units / daily_demand_units


def shortage_days(supplier_delay_days: float, coverage: float) -> float:
    """Cuántos días quedan sin material, si el retraso supera la cobertura."""
    if supplier_delay_days < 0:
        raise ValueError("supplier_delay_days no puede ser negativo")
    return max(0.0, supplier_delay_days - coverage)


def missing_units(shortage: float, daily_demand_units: float) -> float:
    """Cuántas unidades faltarían para cubrir esos días sin material."""
    return shortage * daily_demand_units


def compute_facts(case: dict) -> dict:
    """Los tres hechos de la operación, redondeados a un decimal.

    El diccionario devuelto tiene exactamente tres claves. Esa es la frontera de
    la fase, y hay un test que la sostiene: si mañana alguien agrega acá un
    "risk_level" o un "recomendacion", el test falla. Ese día el software habrá
    empezado a opinar, y la fase dejará de medir lo que dice medir.
    """
    coverage = coverage_days(case["stock_units"], case["daily_demand_units"])
    shortage = shortage_days(case["supplier_delay_days"], coverage)
    return {
        "coverage_days": round(coverage, 1),
        "shortage_days": round(shortage, 1),
        "missing_units": round(missing_units(shortage, case["daily_demand_units"]), 1),
    }


# ---------------------------------------------------------------------------
# PARTE 3 — Los dos estados que el modelo va a leer
# ---------------------------------------------------------------------------

def render_narrative(case: dict) -> str:
    """El estado CRUDO: los hechos de la operación tal como llegan, sin cuentas.

    Fijate en lo que NO dice: no dice "hay stock para 5 días". Dice las dos
    cantidades por separado (500 unidades, 100 por día) y deja la división sin
    hacer. Eso es justamente lo que la fase quiere poner a prueba.
    """
    return (
        "Asunto: Retraso del lote 4412 y entrega comprometida\n\n"
        f"Hola equipo: el proveedor Andina Metales confirmó hoy que el lote 4412 de "
        f"lámina de acero saldrá {case['supplier_delay_days']} días tarde por una falla "
        f"en su planta de Lima. Hoy tenemos {case['stock_units']} unidades de lámina en "
        f"el almacén y la línea 3 consume {case['daily_demand_units']} unidades por día. "
        "Ese lote abastece el pedido del cliente Vértice, con entrega el 30 de octubre. "
        "Si el material no llega a tiempo tendremos que elegir entre comprar a un "
        "proveedor alterno más caro o avisarle al cliente de un retraso. Necesito que "
        "alguien revise esto hoy."
    )


def render_enriched(case: dict, facts: dict) -> str:
    """El estado ENRIQUECIDO: la misma narrativa, más los hechos calculados.

    La narrativa se conserva entera y el bloque se agrega al final: así la única
    diferencia entre los dos estados es la información calculada. Cualquier otra
    diferencia (otro saludo, otro orden) sería una variable más, y el experimento
    dejaría de medir lo que queremos medir.
    """
    return (
        render_narrative(case)
        + "\n\nDatos calculados de la operación:\n"
        + f"- Cobertura del stock actual: {facts['coverage_days']} días de producción.\n"
        + f"- Retraso confirmado del proveedor: {case['supplier_delay_days']} días.\n"
        + f"- Días sin cobertura de material: {facts['shortage_days']} días.\n"
        + f"- Unidades faltantes estimadas: {facts['missing_units']} unidades."
    )


# ---------------------------------------------------------------------------
# PARTE 4 — Las preguntas al modelo
# ---------------------------------------------------------------------------

def predict_both_states(states: dict) -> dict:
    """Le pregunta lo mismo al modelo sobre cada estado.

    Dos detalles que importan:

    * `laya` se importa ACÁ ADENTRO, no arriba del archivo. Así los tests de la
      aritmética corren en un segundo, sin cargar PyTorch ni tocar el modelo.
    * Cada estado recibe las DOS preguntas en la misma llamada: Laya contesta
      todas las preguntas de un diccionario en un solo paso interno. Dos
      llamadas en total (una por estado), no cuatro.
    """
    from laya import Router

    router = Router()
    results = {}
    for state_name, state_text in states.items():
        result = router.predict(state_text, QUESTIONS)
        results[state_name] = {
            "answers": result["answers"],
            "routing": result["routing"],
        }
    return results


def print_table(results: dict) -> None:
    """Imprime la tabla comparativa: es la evidencia de la fase."""
    print(f"{'estado':<14} {'pregunta':<20} {'noul':>8} {'answer_confidence':>19}")
    print("-" * 64)
    for state_name, payload in results.items():
        for question_id in QUESTIONS:
            answer = payload["answers"][question_id]
            print(
                f"{state_name:<14} {question_id:<20} "
                f"{answer['noul']:>8} {answer['answer_confidence']:>19}"
            )


def main() -> None:
    facts = compute_facts(CASE)
    print("datos del caso:", CASE)
    print("hechos calculados:", facts)

    states = {
        "crudo": render_narrative(CASE),
        "enriquecido": render_enriched(CASE, facts),
    }

    print("\n--- ¿qué lee el modelo en cada caso? ---")
    print("\n[crudo]\n" + states["crudo"])
    print("\n[enriquecido]\n" + states["enriquecido"])

    results = predict_both_states(states)

    print("\n--- respuestas ---")
    print_table(results)

    print("\n--- detalle por pregunta (todo lo que devolvió el modelo) ---")
    for state_name, payload in results.items():
        print(f"\n[{state_name}]")
        for question_id, answer in payload["answers"].items():
            print(f"  {question_id}: {answer}")
        print(f"  routing: {payload['routing']}")


if __name__ == "__main__":
    main()
