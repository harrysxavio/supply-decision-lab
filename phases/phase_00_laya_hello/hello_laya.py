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
"""Fase 0 — un estado de supply chain entra, respuestas tipadas salen.

Este archivo es un script: Python lo ejecuta de arriba hacia abajo, línea por línea.
No hay clases propias ni funciones propias, porque en esta fase queremos que se vea
el camino completo de una sola lectura: entrada -> preguntas -> llamada al modelo
-> impresión del resultado.

Se ejecuta así, desde esta carpeta:

    uv run --python 3.12 hello_laya.py


QUÉ ES EL BLOQUE DE ARRIBA (las líneas que empiezan con "# /// script")

Ese bloque es el "manifiesto" del script, en un formato que se llama PEP 723. No es
código Python: es configuración que lee la herramienta `uv` antes de ejecutar nada.
Gracias a él este script no necesita un `requirements.txt` ni un entorno virtual
dentro del repositorio: `uv` lee ese bloque, prepara un entorno aparte y recién
entonces ejecuta el código.

    requires-python  -> la versión de Python que necesita el script (3.12)
    dependencies     -> las librerías que hay que instalar; acá fijamos la versión
                        exacta, `laya==0.3.23`, para que la fase sea reproducible
    [tool.uv]        -> configuración extra SOLO para la herramienta uv
    [[tool.uv.index]]-> un catálogo adicional de paquetes; el de PyTorch con
                        variantes de CPU. Está ahí porque esta máquina no tiene
                        GPU: sin esa línea, uv bajaría la variante CUDA de torch
                        más unos 20 paquetes `nvidia-*` (varios GB inútiles acá)


LAS CUATRO PARTES DE ESTE SCRIPT

    1. El ESTADO    : el texto que describe la situación que el modelo debe leer.
    2. Las PREGUNTAS: qué queremos saber del estado, una pregunta de cada tipo.
    3. La LLAMADA   : una sola línea que enruta el texto y responde todo junto.
    4. La SALIDA    : imprimir lo que el modelo devolvió, sin inventar nada.


TRES PALABRAS QUE SE REPITEN

    ESTADO          Un texto (o JSON/diccionario) con la evidencia: un correo, un
                    ticket, un reporte. Es lo que el modelo "lee".
    PREGUNTA TIPADA Una pregunta con respuesta de forma fija: elegir una opción
                    (`choice`), ubicarse en una escala (`score`) o una probabilidad
                    de sí/no (`noul`). Laya no escribe texto libre: siempre responde
                    con estos tipos.
    CHECKPOINT      El "modelo" propiamente dicho: un juego de pesos entrenados.
                    Laya trae tres y el `Router` elige el que corresponde al idioma
                    o a la tarea del texto de entrada.
"""

# ---------------------------------------------------------------------------
# LAS HERRAMIENTAS QUE TRAEMOS DE AFUERA (los `import`)
# ---------------------------------------------------------------------------

# Los `import` van juntos y sin comentarios en el medio, porque la convención de
# Python agrupa primero lo que viene de la biblioteca estándar (lo que ya trae el
# lenguaje) y después lo que viene de paquetes instalados. La explicación de cada
# uno está justo abajo de la lista.
import sys
from importlib.metadata import version

import laya
from laya import Router

#   sys                       De la biblioteca estándar de Python. Lo usamos solo
#                             para imprimir la versión del intérprete que está
#                             corriendo, y así dejar registrado con qué Python se
#                             obtuvo este resultado.
#
#   version()                 De la biblioteca estándar también. Lee el número de
#                             versión de un paquete ya instalado. Es más liviano
#                             que importar el paquete entero: para imprimir la
#                             versión de `torch` no hace falta cargar PyTorch en
#                             memoria.
#
#   laya                      El paquete del modelo de decisiones: ahí adentro vive
#                             todo lo demás. Lo importamos como módulo porque
#                             necesitamos `laya.__version__` (su versión).
#
#   Router                    La clase que hace el trabajo: decide QUÉ checkpoint
#                             usar y responde las preguntas. Es la puerta de
#                             entrada recomendada cuando no sabemos de antemano en
#                             qué idioma viene el texto.


# ---------------------------------------------------------------------------
# PARTE 1 — EL ESTADO: la evidencia que Laya va a leer
# ---------------------------------------------------------------------------
# Esto es solo Python básico: una variable llamada `supply_state` que guarda un
# texto. El texto es un correo interno inventado, pero con los datos que un caso
# real tendría: qué pasó, cuánto retraso, cuánto inventario hay, qué se entrega a
# quién y para cuándo.
#
# Dos detalles de sintaxis, con calma:
#
#   * Los paréntesis agrupan varios pedazos de texto. Python los une en un solo
#     texto, como si los hubiéramos escrito en una línea larguísima. Se hace así
#     para que el código se pueda leer sin desplazar la pantalla hacia el costado.
#
#   * `\n` significa "salto de línea". Un `\n\n` son dos: por eso hay un renglón
#     en blanco entre el asunto y el cuerpo, igual que en un correo real.
#
# Lo importante para esta fase: el estado es UNA variable y UN texto. No hay
# estructuras de datos, ni archivos, ni base de datos.
supply_state = (
    "Asunto: Retraso del lote 4412 y riesgo de parada de línea\n\n"
    "Hola equipo: el proveedor Andina Metales confirmó hoy que el lote 4412 de "
    "lámina de acero saldrá 12 días tarde por una falla en su planta de Lima. "
    "Tenemos existencia para 5 días de producción en la línea 3, que abastece el "
    "pedido del cliente Vértice con entrega el 30 de octubre. Si el material no "
    "llega antes del viernes tendremos que elegir entre comprar a un proveedor "
    "alterno más caro o avisarle al cliente de un retraso. Necesito que alguien "
    "revise esto hoy."
)


# ---------------------------------------------------------------------------
# PARTE 2 — LAS PREGUNTAS: tres formas de preguntar, una de cada tipo
# ---------------------------------------------------------------------------
# `questions` es un diccionario: una colección de pares "nombre -> contenido".
# Se escribe entre llaves { }. Cada par va con la forma "nombre": contenido, y los
# pares se separan con comas.
#
# Acá el nombre de cada pregunta ("area", "severidad", "riesgo_parada") es la
# etiqueta con la que después vamos a recuperar la respuesta. Los elegimos
# nosotros: podríamos haberlos llamado de cualquier otra forma.
#
# Y cada contenido es, a su vez, otro diccionario más chico, con hasta tres claves:
#
#   "type"         -> el tipo de pregunta: "choice", "score" o "noul".
#   "instructions" -> la pregunta escrita en lenguaje natural, tal como se le
#                     muestra al modelo. Es la parte que un humano redactaría.
#   "criteria"     -> las opciones o niveles válidos. Es la forma acotada en la que
#                     el modelo PUEDE responder. Su formato cambia según el tipo.
#
# Que exista `criteria` es la razón por la que estas respuestas son fáciles de
# usar en un programa: no hay texto libre que interpretar, siempre vuelve una de
# estas opciones.
questions = {
    # ---- Tipo 1: "choice" = elegir UNA opción entre varias -----------------
    # En `choice`, `criteria` es un diccionario: la clave es lo que el modelo
    # devuelve (por ejemplo "compras") y el valor es la explicación de esa opción,
    # que es lo que el modelo lee para decidir. Las claves cortas nos convienen
    # porque son las que van a aparecer en la respuesta.
    "area": {
        "type": "choice",
        "instructions": "¿Qué área debe atender este caso?",
        "criteria": {
            "compras": "negociación con proveedores y compra de materiales",
            "logistica": "transporte, almacén y entregas a clientes",
            "calidad": "defectos, especificaciones e inspecciones",
            "servicio_cliente": "relación con el cliente final",
        },
    },
    # ---- Tipo 2: "score" = ubicarse en una ESCALA --------------------------
    # En `score`, `criteria` es una lista (se escribe entre corchetes [ ]) y el
    # orden importa: va de menos a más. Acá la escala tiene tres niveles, así que
    # la respuesta es un número que se mueve entre 0 y 2.
    "severidad": {
        "type": "score",
        "instructions": "¿Qué tan severo es el caso para la operación?",
        "criteria": ["informativo", "manejable", "crítico"],
    },
    # ---- Tipo 3: "noul" = una probabilidad de SÍ/NO ------------------------
    # `noul` responde "¿es verdadero o falso esto?" y devuelve una probabilidad
    # entre 0 y 1, siempre la probabilidad de que la afirmación sea VERDADERA.
    #
    # Acá `criteria` es OPCIONAL (no prohibido): si se omite, Laya usa sus dos
    # opciones semánticas por defecto, falso y verdadero, con los textos
    # "no, the statement does not hold" y "yes, the statement holds", que son los
    # que el modelo lee. Si se quiere cambiar la redacción de esas dos opciones,
    # se pasa `criteria` como diccionario con las claves 'false' y 'true' (el
    # paquete rechaza cualquier otra clave). Eso no cambia las respuestas
    # posibles: cambia cómo se le pregunta al modelo.
    #
    # Nombrar la pregunta con cuidado importa: cuanto más precisa sea la
    # afirmación, más clara va a ser la probabilidad que recibamos.
    "riesgo_parada": {
        "type": "noul",
        "instructions": "¿El correo reporta un riesgo concreto de detener la producción?",
    },
}


# ---------------------------------------------------------------------------
# PARTE 3 — LA LLAMADA: enrutar y responder
# ---------------------------------------------------------------------------

# `Router()` crea el enrutador. En este momento NO descarga nada y NO lee el
# estado: apenas se prepara para trabajar y aprende qué checkpoints existen.
router = Router()

# Acá pasa todo, en una sola línea. `predict` (predecir) hace tres cosas seguidas:
#
#   1. ENRUTA: mira el estado, detecta el idioma y elige el checkpoint adecuado.
#      Nosotros no le decimos cuál usar: lo decide él, y luego nos cuenta por qué.
#   2. CARGA: pone ese checkpoint en memoria. La primera vez que se usa un
#      checkpoint, esto implica descargarlo de internet (y por eso la primera
#      corrida tarda más que las siguientes).
#   3. RESPONDE: contesta TODAS las preguntas del diccionario en un solo paso
#      interno, no pregunta por pregunta. De ahí la velocidad.
#
# `supply_state` es lo que va a leer; `questions` es lo que queremos saber.
# El resultado queda guardado en una variable llamada `result`.
#
# Fijate que no hay ningún paso de "calcular" ni de "decidir" hecho por nosotros:
# el script no aplica reglas de negocio. Solo entrega el estado y las preguntas.
result = router.predict(supply_state, questions)


# ---------------------------------------------------------------------------
# PARTE 4 — LA SALIDA: imprimir lo que el modelo devolvió
# ---------------------------------------------------------------------------
# Todo lo que viene abajo son `print`, es decir, texto en pantalla. Es la única
# forma de salida de esta fase: no se escribe ningún archivo.
#
# Regla que nos impusimos: imprimir únicamente lo que viene DENTRO de `result`.
# Nada de datos inventados, nada de cálculos propios. Si querés saber qué trae
# realmente el modelo, esto es lo que trae.
#
# Sobre la sintaxis de los `print` de abajo:
#
#   * La `f` antes de las comillas crea una "f-string": permite meter valores de
#     variables dentro del texto usando llaves. Por ejemplo `f"hola {nombre}"`
#     imprime el saludo con el valor de `nombre` ya reemplazado.
#
#   * El `!r` después de un valor (por ejemplo `{supply_state!r}`) muestra el texto
#     "tal cual es", entre comillas y con los caracteres especiales visibles: sirve
#     para comprobar que los saltos de línea `\n` están donde creemos.
#
#   * El `\n` al principio de un texto produce un renglón vacío, para que la salida
#     se lea por bloques y no como un solo chorizo.

# Primera línea: con qué piezas se obtuvo este resultado. Es la parte que hace que
# la corrida sea verificable: `laya.__version__` confirma que se usó la versión
# fijada (0.3.23) y no otra.
print(f"environment: laya={laya.__version__} python={sys.version.split()[0]} torch={version('torch')}")

# El estado que se envió. Se imprime para poder comparar, línea por línea, la
# entrada con la salida que viene después.
print(f"\nstate: {supply_state!r}")

# `sorted(result)` devuelve la lista de los nombres de las claves del diccionario
# `result`, ordenada alfabéticamente. Es una forma rápida de ver "qué trae la
# respuesta" sin abrir el código fuente de la librería.
print(f"\ntop-level keys: {sorted(result)}")

# Acá aparece una trampa de nombres que conviene tener presente desde el principio:
# `result["model"]` NO es el checkpoint que se usó, sino la familia del modelo
# (siempre el mismo texto). El checkpoint real está más abajo, dentro de `routing`.
print(f"result['model'] = {result['model']!r}   (this names the model family, not the checkpoint)")

# Un `for` recorre una colección elemento por elemento. Acá recorre
# `result["answers"]`, que es un diccionario pregunta -> respuesta.
# `.items()` entrega cada par ya separado en dos variables: `question_id` (el
# nombre que le dimos a la pregunta, como "area") y `answer` (la respuesta).
# Se imprimen una debajo de otra, todas con el mismo formato.
print("\nanswers:")
for question_id, answer in result["answers"].items():
    print(f"  {question_id}: {answer}")

# `routing` es el registro de la decisión de enrutado: qué checkpoint se eligió,
# de qué repositorio salió y con qué razón. Imprimimos el diccionario completo
# para no quedarnos solo con los campos que creíamos que existían.
print(f"\nrouting = {result['routing']}")

# `usage` es el registro del trabajo interno: cuántos tokens se procesaron y, muy
# importante, si el estado entró completo (`truncated`). Si `truncated` fuera
# verdadero, la respuesta se calculó sobre un texto recortado y habría que mirarla
# con desconfianza. Es el primer campo que conviene revisar al leer la salida.
print(f"\nusage = {result['usage']}")
