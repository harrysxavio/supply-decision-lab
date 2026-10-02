# Fase 0 — `phase_00_laya_hello`

Prueba de humo mínima. La pregunta que responde esta fase es una sola:

> ¿Puede **Laya**, en esta máquina, leer un estado de supply chain en español y devolver
> respuestas **tipadas** con probabilidades, sin generar texto?

Nada más. Si esto funciona, las fases siguientes tienen una base comprobada sobre la cual
construir; si no funciona, conviene saberlo antes de escribir cualquier otra cosa.

> **Lección didáctica:** si prefieres la explicación en lenguaje sencillo, con ejemplos y sin dar por
> sabido nada de *machine learning*, empieza por [`lesson.md`](lesson.md).

## Objetivo

Demostrar el contrato mínimo de Laya de punta a punta, con el menor número de piezas posible:

1. existe un **estado** (el texto que describe una situación),
2. existe una **pregunta tipada** (`choice`, `score` o `noul`),
3. existe una **respuesta tipada** con su confianza, producida por un modelo local,
4. y sabemos **cuál checkpoint** eligió el enrutador y por qué.

## Hipótesis

Si Laya 0.3.23 se instala y responde correctamente un caso de retraso de proveedor en español,
entonces el motor de decisiones funciona en este entorno y la Fase 1 puede agregar dominio
(datos, reglas, métricas) encima del contrato ya verificado — en lugar de seguir discutiendo
supuestos sobre él.

Hipótesis secundaria: un estado escrito en español hace que el `Router` elija el checkpoint
**multilingual** en vez de **english**, sin que nosotros lo indiquemos.

## Entrada

Un solo estado de prueba: un correo interno en español sobre un lote de acero que llega tarde,
con una línea de producción y un pedido de cliente en riesgo (el texto está dentro de
`hello_laya.py`).

Tres preguntas, una de cada tipo que Laya soporta:

| Id | Tipo | Pregunta | Forma de la respuesta |
| --- | --- | --- | --- |
| `area` | `choice` | ¿Qué área debe atender el caso? | una opción entre `compras`, `logistica`, `calidad`, `servicio_cliente` |
| `severidad` | `score` | ¿Qué tan severo es para la operación? | un número entre 0 y 2, sobre la escala `informativo / manejable / crítico` |
| `riesgo_parada` | `noul` | ¿Reporta un riesgo concreto de detener la producción? | una probabilidad entre 0 y 1 |

`noul` significa "probability that the answer is yes": el valor devuelto es siempre **P(verdadero)**.

## Salida esperada

El script imprime **solo lo que el objeto devuelto contiene de verdad**, agrupado en tres bloques.
Esta es la forma real de Laya 0.3.23 (verificada leyendo el código de la versión publicada, no
copiada de un tutorial):

```
result["answers"][<id>]     respuesta por pregunta
    choice -> type, choice, probabilities, confidence, answer_confidence, action
    score  -> type, score, legend, probabilities, confidence, answer_confidence, action
    noul   -> type, noul, confidence, answer_confidence, action

result["routing"]           la decisión de enrutado
    model, repo, reason, detection, workflow

result["usage"]             cuánto texto se procesó y si hubo recorte
    input_tokens, output_tokens, state_tokens, state_tokens_dropped,
    truncated, truncated_questions
```

Cuatro detalles que conviene entender bien desde el principio:

- **`score` no es una etiqueta, es una posición esperada.** Con la escala de tres niveles, un
  `score` de `1.62` significa "entre *manejable* y *crítico*". El campo `legend` trae el texto de
  cada nivel para traducir ese número a palabras. Y `probabilities` muestra el peso de cada nivel.
- **Hay dos campos `model` que no significan lo mismo.** `result["model"]` es la familia del
  modelo (`laya-rl-agent`) y es igual siempre. El checkpoint realmente usado está en
  `result["routing"]["model"]` (`english`, `multilingual` o `typed-decisions`).
  El script imprime los dos, justamente para que la diferencia quede visible.
- **`confidence` y `answer_confidence` miden cosas distintas.** `answer_confidence` es la **masa de
  probabilidad sobre la respuesta elegida** (`max(p)`: la probabilidad que el modelo le asignó a la
  opción que reportó). Está en la misma escala para los tres tipos de pregunta y es el número sobre
  el que se ajusta la calibración y el que se usaría para un umbral; **no garantiza exactitud**:
  que el modelo esté muy decidido no significa que esté en lo correcto. `confidence` es otra cosa
  según el tipo: en `noul` coincide con `answer_confidence` (con dos opciones son el mismo número),
  mientras que en `choice` y `score` es la entropía normalizada de la distribución (`1 - H / log k`),
  que no es comparable entre preguntas con distinta cantidad de opciones.
- **El checkpoint usado en esta corrida no trae temperaturas calibradas.** El estado está en
  español, así que el `Router` elige el checkpoint `multilingual`, y ese checkpoint se distribuye
  **sin temperaturas ajustadas** (así lo dice el propio paquete). Consecuencia práctica: los valores
  de `answer_confidence` de la salida se leen como "cuán concentrada está la respuesta del modelo",
  no como "probabilidad de acertar".
- **`usage["truncated"]` evita una conclusión falsa.** Si el estado no cupo en el presupuesto de
  tokens, la respuesta se calculó sobre un texto recortado. Antes de juzgar la calidad de una
  respuesta, hay que mirar ese campo.

Los valores concretos (qué área, qué severidad, qué probabilidad) no se fijan de antemano: son la
salida del modelo y se registran en `learnings.md` después de la primera corrida.

## Cómo se ejecuta

Desde `phases/phase_00_laya_hello/`:

```bash
uv run --python 3.12 hello_laya.py
```

No hace falta activar ningún entorno, ni `pip install`, ni crear un `.venv`. La cabecera del
propio script (formato PEP 723) declara Python 3.12 y la dependencia `laya==0.3.23`; `uv` la lee
de ahí y construye un entorno en su caché, fuera del repositorio.

La primera corrida hace tres cosas: instala las dependencias (unos 35 paquetes), descarga el
checkpoint desde Hugging Face la primera vez que se usa, y responde. Las corridas siguientes usan
la caché y tardan segundos.

## Entorno

| Pieza | Valor | Cómo se obtuvo |
| --- | --- | --- |
| `uv` | 0.12.22 | se instaló en `~/.local/bin` (no estaba en la máquina) |
| Python | 3.12.15 | `uv python install 3.12`, sin tocar el Python 3.14 del sistema |
| `laya` | 0.3.23 | fijado en la cabecera del script |
| `torch` | 2.14.1+cpu | variante CPU, por el índice extra declarado en la cabecera |

Tres decisiones de entorno, y por qué:

- **`uv` en lugar de `pip`.** El Python del sistema no tiene `pip` ni `ensurepip`, y `uv` resuelve
  eso sin permisos de administrador y sin dependencias.
- **Python 3.12 y no 3.14.** PyTorch suele publicar sus ruedas con retraso para versiones nuevas de
  Python; 3.12 es el rango donde el ecosistema está probado.
- **Índice de PyTorch CPU.** Esta máquina no tiene GPU. Sin ese índice, `uv` resuelve la variante
  CUDA de `torch` y descarga alrededor de 20 paquetes `nvidia-*` inútiles aquí (varios GB en vez de
  unos 200 MB).

## Límites explícitos

Esta fase **no** hace, y no debe hacer, lo siguiente:

- No calcula KPI ni métricas de negocio.
- No agrega lógica determinística en Python (reglas, cálculos, validaciones de negocio).
- No usa RAG ni base documental.
- No usa otro modelo local, ni SLM, ni modelo generativo.
- No hace fine-tuning ni calibración propia.
- No tiene interfaz gráfica: la salida es texto en la terminal.
- No tiene arquitectura por capas, ni configuración externa, ni CLI con argumentos.
- No tiene tests automatizados: la verificación de la fase es una prueba de humo observada, y la
  evidencia queda en `learnings.md`.
- No hay automatización ni integración con nada.

La razón de fondo: en la Fase 0 queremos un solo camino visible entre la entrada y la salida. Cada
pieza agregada ahora sería una pieza que ocultaría si el problema, cuando aparezca, está en Laya o
en lo que construimos encima.

## Criterio de cierre

La fase se considera cerrada cuando una sola corrida, con el comando de arriba, imprime:

1. la versión de `laya` y de `torch`,
2. las tres respuestas tipadas (`area`, `severidad`, `riesgo_parada`),
3. el bloque `routing` con el checkpoint elegido y la razón, y
4. el bloque `usage` con el estado sin recortes (`truncated = false`).

Y cuando esas respuestas se pueden leer y discutir como razonables para el caso planteado.

## Si algo falla

- **Error 401/403 al descargar el checkpoint:** el repositorio del modelo pediría autenticación.
  Se resuelve iniciando sesión con Hugging Face y volviendo a correr el script.
- **Se descargan paquetes `nvidia-*`:** el índice CPU de la cabecera no se aplicó. La corrida
  funciona igual, pero desperdicia varios GB de descarga.
- **Problemas de versión en `transformers`:** `laya==0.3.23` no fija la versión de sus
  dependencias transitivas, así que `transformers` queda libre. Si aparece un error de
  incompatibilidad, se acota esa versión y el hallazgo se registra en `learnings.md`.
