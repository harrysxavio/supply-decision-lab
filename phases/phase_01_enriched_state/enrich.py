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

El script hace cinco cosas, en este orden:

    1. toma los datos del caso (tres números),
    2. calcula tres hechos: cobertura, faltante y unidades faltantes,
    3. arma dos textos: la narrativa cruda y la misma narrativa más los hechos,
    4. le pregunta lo mismo al modelo sobre los dos textos,
    5. imprime la tabla comparativa.

Se ejecuta con:

    uv run --python 3.12 enrich.py

Los tests de la aritmética corren aparte, sin usar el modelo:

    uv run --python 3.12 test_enrich.py

QUÉ ES EL BLOQUE DE ARRIBA (las líneas que empiezan con "# /// script")

Es el manifiesto del script, en un formato llamado PEP 723. No es código: es
configuración que lee la herramienta `uv` antes de ejecutar nada. Gracias a él no
hace falta un `requirements.txt` ni un entorno virtual dentro del repositorio.

    requires-python -> la versión de Python necesaria (3.12)
    dependencies    -> las librerías a instalar, con versión exacta
    [tool.uv]       -> configuración extra para uv; acá, el catálogo de PyTorch
                       para CPU, porque esta máquina no tiene GPU

LAS CINCO PARTES DEL ARCHIVO

    1. los datos del caso          (PARTE 1)
    2. la aritmética               (PARTE 2)
    3. los dos textos              (PARTE 3)
    4. las preguntas al modelo     (PARTE 4)
    5. la impresión de la salida   (PARTE 5)

CUATRO PALABRAS QUE SE REPITEN

    DATO       un número de entrada: el retraso, el stock, el consumo diario.
    HECHO      una cuenta que se deduce de los datos y siempre da lo mismo
               (cobertura, faltante). Es lo que calcula el software.
    JUICIO     una opinión: "riesgo alto", "esto es urgente", "qué área lo atiende".
               Es lo que NUNCA calcula el software en esta fase.
    ESTADO     el texto que el modelo lee. Acá hay dos: el crudo y el enriquecido.

CÓMO LEER LA SALIDA

    estado         pregunta                 noul   answer_confidence
    crudo          riesgo_parada             0.0                 1.0

    * `noul` es la probabilidad de que la respuesta sea VERDADERA (0 a 1).
    * `answer_confidence` dice cuán decidido está el modelo, no si acertó.
"""

# ---------------------------------------------------------------------------
# PARTE 1 — Los datos del caso
# ---------------------------------------------------------------------------
# `CASE` es un DICCIONARIO: una colección de pares "nombre -> valor", escrita
# entre llaves { }. Cada par va con la forma "clave": valor y se separa con comas.
# Se lee indicando la clave entre corchetes: CASE["stock_units"] devuelve 500.
#
# Tres números, nada más. Todo lo demás (el texto y las cuentas) se deriva de acá,
# así los números no pueden contradecirse entre sí: si mañana el stock pasa a 800,
# cambia en un solo lugar y el texto y las cuentas se ajustan solos.
#
# Es la diferencia central con la Fase 0: allá el caso era un párrafo escrito a
# mano; acá es un dato estructurado del que se puede calcular.
CASE = {
    "supplier_delay_days": 12,   # el proveedor avisa que llega 12 días tarde
    "stock_units": 500,          # unidades disponibles hoy en el almacén
    "daily_demand_units": 100,   # unidades que consume la línea por día
}

# `QUESTIONS` es un diccionario de diccionarios: cada pregunta tiene un nombre
# (la clave: "retraso_mencionado") y un contenido que a su vez es otro
# diccionario con dos datos: el tipo de pregunta y el texto de la pregunta.
#
# Se prueban dos formulaciones distintas del mismo asunto para separar dos causas
# posibles: "el modelo no entendió" (redacción) de "al modelo le faltó la cuenta"
# (información).
#
#   retraso_mencionado -> pregunta por lo que el correo DICE explícitamente.
#   riesgo_parada      -> pide una CONCLUSIÓN que el correo no enuncia con esas
#                         palabras.
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
# Estas cuatro funciones son la única lógica propia de la fase.
#
# QUÉ ES UNA FUNCIÓN, en corto: un bloque de código con nombre que recibe datos
# (los "parámetros"), hace algo con ellos y devuelve un resultado (la palabra
# `return`). Se usa escribiendo su nombre con los datos entre paréntesis.
#
# MIRÁ LOS DETALLES DE SINTAXIS:
#
#   def coverage_days(stock_units: float, daily_demand_units: float) -> float:
#       ^nombre          ^parámetro : ^su tipo esperado         ^lo que devuelve
#
# Esos `: float` y `-> float` se llaman ANOTACIONES DE TIPO. Son una promesa para
# quien lee (y para el editor): "esto espera números decimales y devuelve uno".
# Python NO las controla al ejecutar: si le pasás texto, no avisa; por eso además
# validamos a mano un poco más abajo.
#
# Los datos inválidos se rechazan en vez de calcularse. Si el consumo diario es
# cero, "días de cobertura" sería una división por cero: eso no es un hecho, es un
# error del dato de entrada, y conviene que el programa se detenga y lo diga.

def coverage_days(stock_units: float, daily_demand_units: float) -> float:
    """Cuántos días de producción alcanza el stock actual."""
    if daily_demand_units <= 0:
        # `raise ValueError(...)` LANZA UN ERROR y corta la ejecución del programa
        # en ese punto. El texto entre paréntesis es el mensaje que verá la persona.
        # Es preferible a devolver un número inventado: un resultado silencioso y
        # equivocado es peor que un error claro.
        raise ValueError("daily_demand_units debe ser mayor que cero")
    if stock_units < 0:
        raise ValueError("stock_units no puede ser negativo")
    # `return` devuelve el resultado y termina la función.
    return stock_units / daily_demand_units


def shortage_days(supplier_delay_days: float, coverage: float) -> float:
    """Cuántos días quedan sin material, si el retraso supera la cobertura."""
    if supplier_delay_days < 0:
        raise ValueError("supplier_delay_days no puede ser negativo")
    # `max(0.0, ...)` elige el mayor de los dos valores. Está ahí porque el
    # "faltante" no puede ser negativo: si el retraso es de 3 días y hay stock para
    # 5, no falta nada (0), no sobran 2 días de faltante. Sin este `max`, la cuenta
    # devolvería -2, un número que no significa nada.
    return max(0.0, supplier_delay_days - coverage)


def missing_units(shortage: float, daily_demand_units: float) -> float:
    """Cuántas unidades faltarían para cubrir esos días sin material."""
    return shortage * daily_demand_units


def compute_facts(case: dict) -> dict:
    """Los tres hechos de la operación, redondeados a un decimal.

    `case: dict` dice que recibe un diccionario; `-> dict` que devuelve otro.

    El diccionario devuelto tiene exactamente tres claves. Esa es la frontera de
    la fase, y hay un test que la sostiene: si mañana alguien agrega acá un
    "risk_level" o una "recomendacion", ese test falla. Ese día el software habrá
    empezado a opinar, y la fase dejará de medir lo que dice medir.
    """
    # Cada línea lee datos del diccionario `case` (con corchetes y la clave entre
    # comillas) y guarda el resultado en una variable nueva.
    coverage = coverage_days(case["stock_units"], case["daily_demand_units"])
    shortage = shortage_days(case["supplier_delay_days"], coverage)
    # `round(numero, 1)` redondea a un decimal: 5.0 en vez de 5.000000000000001.
    # Se redondea al final, no en cada paso, para no arrastrar errores de redondeo.
    return {
        "coverage_days": round(coverage, 1),
        "shortage_days": round(shortage, 1),
        "missing_units": round(missing_units(shortage, case["daily_demand_units"]), 1),
    }


# ---------------------------------------------------------------------------
# PARTE 3 — Los dos textos que el modelo va a leer
# ---------------------------------------------------------------------------
# Las dos funciones devuelven TEXTO (por eso `-> str`). Nada de esto se imprime
# todavía: se arma el texto en memoria y se devuelve.

def render_narrative(case: dict) -> str:
    """El estado CRUDO: los hechos de la operación tal como llegan, sin cuentas.

    Fijate en lo que NO dice: no dice "hay stock para 5 días". Dice las dos
    cantidades por separado (500 unidades, 100 por día) y deja la división sin
    hacer. Eso es justamente lo que la fase quiere poner a prueba.
    """
    # Los paréntesis agrupan varios pedazos de texto y Python los une en uno solo.
    # Se escribe así para no tener una línea de 400 caracteres.
    #
    # La `f` antes de las comillas crea una "f-string": todo lo que está entre
    # llaves se reemplaza por su valor. Por ejemplo {case['stock_units']} se
    # convierte en 500 cuando el texto se arma.
    #
    # `\n` significa "salto de línea"; `\n\n` deja un renglón en blanco, como en
    # un correo de verdad.
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

    Recibe dos diccionarios: los datos del caso y los hechos calculados.

    La narrativa se conserva entera y el bloque se agrega al final: así la única
    diferencia entre los dos textos es la información calculada. Cualquier otra
    diferencia (otro saludo, otro orden) sería una variable más, y el experimento
    dejaría de medir lo que queremos medir.
    """
    # Acá los pedazos de texto se unen con `+` (suma de textos = concatenación).
    # `render_narrative(case)` devuelve el correo completo, y a eso se le pega el
    # bloque nuevo: empezar por esa llamada es lo que garantiza que la narrativa
    # sea idéntica en los dos estados.
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
    """Le pregunta lo mismo al modelo sobre cada texto y devuelve las respuestas.

    `states` es un diccionario nombre -> texto, por ejemplo
    {"crudo": "...", "enriquecido": "..."}.

    Dos detalles que importan:

    * `from laya import Router` está ACÁ ADENTRO y no arriba del archivo. Un
      `import` carga una librería en memoria; `laya` arrastra PyTorch, que tarda
      segundos y ocupa cientos de megas. Al dejarlo dentro de la función, el
      archivo se puede importar (por ejemplo desde los tests) sin cargar nada de
      eso: la librería se carga solo cuando alguien realmente va a predecir.
    * Cada texto recibe las DOS preguntas en la misma llamada, porque Laya contesta
      todas las preguntas de un diccionario en un solo paso interno. Son dos
      llamadas en total (una por texto), no cuatro.
    """
    from laya import Router

    # `Router()` crea el enrutador: el objeto que decide qué checkpoint usar según
    # el idioma del texto. No descarga nada al crearse.
    router = Router()

    # `results = {}` crea un diccionario vacío, que se va llenando en el bucle.
    results = {}
    # `for ... in diccionario.items()` recorre el diccionario y entrega, en cada
    # vuelta, la clave y el valor por separado: el nombre del estado y su texto.
    for state_name, state_text in states.items():
        result = router.predict(state_text, QUESTIONS)
        # Se guarda solo lo que nos interesa de cada respuesta: las respuestas y el
        # registro de enrutado. `results[state_name] = ...` agrega el par al
        # diccionario que empezó vacío.
        results[state_name] = {
            "answers": result["answers"],
            "routing": result["routing"],
        }
    return results


def print_table(results: dict) -> None:
    """Imprime la tabla comparativa: es la evidencia de la fase.

    `-> None` quiere decir que esta función no devuelve nada: solo imprime.
    """
    # Las f-strings aceptan un formato después de dos puntos. `:<14` alinea a la
    # izquierda en 14 espacios y `:>8` alinea a la derecha en 8: así las columnas
    # quedan prolijas aunque los nombres tengan distinto largo.
    print(f"{'estado':<14} {'pregunta':<20} {'noul':>8} {'answer_confidence':>19}")
    # `"-" * 64` repite el guion 64 veces: la línea separadora.
    print("-" * 64)
    for state_name, payload in results.items():
        for question_id in QUESTIONS:
            answer = payload["answers"][question_id]
            print(
                f"{state_name:<14} {question_id:<20} "
                f"{answer['noul']:>8} {answer['answer_confidence']:>19}"
            )


def main() -> None:
    """El recorrido completo, de los datos a la tabla."""
    # Primero las cuentas: son la parte que se puede verificar sin el modelo.
    facts = compute_facts(CASE)
    # `print` con varios valores separados por comas los imprime en una línea,
    # separados por un espacio.
    print("datos del caso:", CASE)
    print("hechos calculados:", facts)

    # Se arman los dos textos: el mismo caso, con y sin las cuentas adentro.
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

    # Este bloque imprime TODO lo que devolvió el modelo, sin elegir campos: si
    # alguien quiere saber qué trae realmente la respuesta, está acá.
    print("\n--- detalle por pregunta (todo lo que devolvió el modelo) ---")
    for state_name, payload in results.items():
        print(f"\n[{state_name}]")
        for question_id, answer in payload["answers"].items():
            print(f"  {question_id}: {answer}")
        print(f"  routing: {payload['routing']}")


# `if __name__ == "__main__":` es una guarda que significa "hacé esto solo si el
# archivo se ejecuta directamente". Si en cambio otro archivo lo importa —como
# hace test_enrich.py—, la guarda es falsa y `main()` NO se ejecuta: así los tests
# pueden usar las funciones sin lanzar el modelo ni imprimir nada.
if __name__ == "__main__":
    main()
