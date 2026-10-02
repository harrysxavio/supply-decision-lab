# Aprendizajes — `phase_00_laya_hello`

Registro de lo que se probó, lo que ocurrió y lo que se aprendió en esta fase.

> Estado de este documento: **primera corrida ejecutada**. Lo que está marcado como *verificado*
> se comprobó con evidencia reproducible (un comando ejecutado o el código fuente de la versión
> instalada); lo que está marcado como *pendiente* todavía no se observó. No se anota aquí ningún
> resultado que no se haya observado.

## Qué probamos

Una hipótesis: **Laya 0.3.23 puede leer un estado de supply chain en español y devolver respuestas
tipadas con probabilidades, sin generar texto.**

Para probarla se preparó lo mínimo indispensable:

- un entorno reproducible: `uv` administrando Python 3.12 y la dependencia `laya==0.3.23`;
- un estado de prueba: un correo interno en español sobre un lote de acero que llega tarde, con una
  línea de producción y un pedido de cliente en riesgo;
- tres preguntas, una de cada tipo del contrato de Laya (`choice`, `score`, `noul`);
- una sola llamada a `Router.predict()`, y la impresión de lo que el objeto devuelto contiene.

Nada más: sin KPI, sin reglas de negocio, sin RAG, sin fine-tuning, sin interfaz.

## Qué ocurrió

### Verificado antes de la primera corrida

- **`uv` no estaba instalado** (`uv: command not found`). Se instaló la versión 0.12.22 en
  `~/.local/bin`, como usuario y sin permisos de administrador.
- **Python 3.12.15 quedó disponible para `uv`** sin modificar el Python 3.14 del sistema.
- **`laya==0.3.23` existe, se instala y se importa** en Python 3.12. Resolución observada:
  `laya 0.3.23`, `torch 2.14.1+cpu`, `transformers 5.18.0`, 35 paquetes en total, sin ningún
  paquete `nvidia-*`.
- **El índice CPU de PyTorch funciona desde la cabecera del script.** Se compararon dos formas:
  `[[tool.uv.index]]` con `explicit = false` resuelve `torch==2.14.1+cpu` (10 paquetes);
  `explicit = true` junto con `[tool.uv.sources]` **no** se aplica en metadatos de script y terminó
  descargando la variante CUDA (54 paquetes, `torch 2.14.1` sin sufijo).
- **La forma real del resultado se confirmó leyendo el código de la versión publicada**, no la
  documentación: `answers` (con `type`, `choice`/`score`/`noul`, `probabilities`, `confidence`,
  `answer_confidence`, `action`), `routing` (`model`, `repo`, `reason`, `detection`, `workflow`) y
  `usage` (`input_tokens`, `output_tokens`, `state_tokens`, `state_tokens_dropped`, `truncated`,
  `truncated_questions`).

### Observado en la primera corrida

Salida real de `uv run --python 3.12 hello_laya.py`:

| Dato | Valor observado |
| --- | --- |
| Versión de Laya | 0.3.23 |
| Intérprete | Python 3.12.15 |
| PyTorch | 2.14.1+cpu |
| Checkpoint elegido por el `Router` | `multilingual` |
| Idioma detectado | `es` |
| Tokens del estado (`usage.state_tokens`) | 129 |
| Estado recortado (`usage.truncated`) | `false` |

Respuestas obtenidas:

| Pregunta | Tipo | Respuesta | `answer_confidence` |
| --- | --- | --- | --- |
| `area` | `choice` | `logistica` | 0.908 |
| `severidad` | `score` | 1.7808, con el nivel `crítico` concentrando el 79.02% de la masa | — |
| `riesgo_parada` | `noul` | 0.0044 (0.44% de probabilidad de que la afirmación sea verdadera) | 0.9956 |

Lectura de estos valores, ya con el código fuente a la vista:

- La hipótesis secundaria **se confirma**: sin indicarle el modelo, el `Router` detectó `es` y envió
  el estado al checkpoint `multilingual`.
- `area = logistica` y una severidad alta son las respuestas que un lector humano esperaría para
  este correo. El punto que no cierra es el `noul` (ver el caso abajo).
- Los tres números de `riesgo_parada` son consistentes entre sí y con lo que hace el código:
  `noul = P(verdadero) = 0.0044`, y con dos opciones `confidence` y `answer_confidence` son el mismo
  número, `max(p) = 0.9956`.

### Caso `riesgo_parada`: observación e hipótesis

> En esta prueba, Laya no reflejó en la respuesta `noul` la consecuencia que puede inferirse de 12
> días de retraso frente a 5 días de stock. Con una sola observación no sabemos si la causa es la
> formulación de la pregunta, el comportamiento del checkpoint multilingual o una limitación más
> general del modelo.

Queda registrado como observación con hipótesis abiertas, no como conclusión: una sola corrida no
permite atribuir la causa. Lo que sí se puede afirmar, con el código a la vista, es qué significa
el número: es el juicio del modelo sobre el texto, y la confianza alta (0.9956) indica que el modelo
está decidido, no que esté en lo correcto.

### Sigue pendiente

- Tamaño y tiempo reales de la descarga del checkpoint, y latencia de la respuesta en CPU: no se
  midieron.
- Si una segunda corrida inmediata reproduce los mismos valores, es decir, si el resultado depende
  de la red o de la caché fría.

## Qué funcionó

- Instalar `uv` sin privilegios y sin tocar el Python del sistema.
- Fijar el intérprete y las dependencias dentro del propio script (metadatos PEP 723): un archivo,
  un comando, cero archivos de configuración en el repositorio.
- Seleccionar la variante CPU de PyTorch desde la cabecera del script, con el índice de PyTorch
  declarado como índice adicional.

## Qué limitaciones encontramos

- **El Python del sistema no tiene `pip` ni `ensurepip`.** Un `python3 -m venv` convencional no
  habría funcionado; de ahí que el entorno se resuelva con `uv`.
- **Python 3.14 es demasiado nuevo para este ecosistema.** Se fijó 3.12; no se intentó 3.14.
- **`[tool.uv.sources]` no sirve en metadatos de script.** Es la forma "estricta" de apuntar solo
  `torch` al índice CPU, y se ignora. La alternativa que sí funciona (`explicit = false`) deja ese
  índice disponible para cualquier paquete de la resolución; en nuestro caso no hubo ambigüedad
  (los 35 paquetes resueltos fueron los esperados, sin `nvidia-*`), pero es un compromiso, no una
  configuración ideal.
- **El pin es de `laya`, no de su árbol de dependencias.** `transformers` quedó libre y resolvió a
  la versión 5.18.0, una línea mayor distinta de la que aparece en los ejemplos de la
  documentación de Laya. Hoy importa sin errores; la calidad de inferencia con esa versión todavía
  no está observada.
- **La primera corrida no es instantánea:** hay que descargar el checkpoint desde Hugging Face.
  Eso introduce red y un caché externo al repositorio en el camino crítico de una prueba de humo.
- **Sin tests automatizados.** Un test aquí solo podría afirmar "respondió *compras*", que depende
  de descargar un modelo y de su criterio. Es frágil como test y útil como observación: por eso se
  registra en este documento y no en código.
- **El script no aporta ninguna regla de negocio.** Todo lo que el programa hace con el estado es
  entregarlo al modelo: no hay aritmética, ni umbrales, ni verificación determinística. Es por
  diseño de la fase, y tiene una consecuencia directa: si el modelo yerra en algo que el propio
  texto permite calcular, hoy nada lo detecta ni lo corrige.

## Qué aprendizaje obtuvimos

- **Un modelo de decisión es más chico de lo que parece.** El contrato entero son tres tipos de
  pregunta y respuestas con probabilidad; no hay texto que parsear ni *prompt* que ajustar.
- **La confianza es parte de la respuesta, no un extra.** Cada respuesta trae números
  (`probabilities`, `confidence`, `answer_confidence`): se puede decidir *si* confiar en la
  respuesta, no solo *qué* respondió. Eso es lo que habilita, más adelante, un umbral o una revisión
  humana (con el cuidado de que ese número viene de un checkpoint sin temperaturas ajustadas, según
  el README de la fase).
- **La misma palabra puede nombrar dos cosas distintas.** `result["model"]` es la familia del modelo
  y `result["routing"]["model"]` es el checkpoint usado. Imprimirlos juntos evita un malentendido
  costoso más adelante.
- **`score` devuelve una posición esperada, no una etiqueta**, y `legend` es lo que la traduce a
  palabras. Confundir ambos habría producido "severidad = 1.62" sin sentido para un lector humano.
- **El enrutamiento por idioma es automático y explicable.** No se le indica el modelo: el `Router`
  detecta y justifica (`reason`, `detection`). Para un proyecto en español, esto es una pieza de
  arquitectura que no hay que construir.
- **La reproducibilidad se paga con un archivo de configuración.** En este caso el precio fue una
  cabecera PEP 723 más larga de lo habitual: la recompensa es que no hay ningún `requirements.txt`
  ni entorno que mantener dentro del repositorio.

## Qué justificaría avanzar a la Fase 1

Avanzar tiene sentido cuando se cumplan **todas** estas condiciones:

1. La corrida imprime las tres respuestas tipadas y el bloque `routing`, sin errores de entorno.
   → **Cumplido** en la primera corrida.
2. El checkpoint elegido para el estado en español es `multilingual` y la razón impresa lo explica
   (la hipótesis secundaria se confirma), o bien queda documentado por qué eligió otro.
   → **Cumplido**: `multilingual`, con `es` como idioma detectado.
3. Las respuestas son razonables para el caso, leídas por una persona: el área tiene sentido, la
   severidad corresponde al texto y la probabilidad de parada es coherente con "5 días de
   existencia" y "12 días de retraso".
   → **Parcial**: el área y la severidad sí; la probabilidad de parada es el punto abierto del caso
   `riesgo_parada`.
4. `usage["truncated"]` es `false`: la respuesta se calculó sobre el estado completo.
   → **Cumplido**: 129 tokens de estado, sin recorte.
5. La primera corrida y una segunda corrida inmediata dan resultados equivalentes, es decir, el
   resultado no depende de condiciones externas (red, caché fría).
   → **Pendiente**: no se intentó una segunda corrida.
6. Está claro qué se agrega en la Fase 1 (el siguiente incremento de dominio) y ese incremento no
   necesita tocar nada de esta fase.
   → **Pendiente**: todavía no está definido.

Si algo de lo anterior falla, lo que corresponde no es avanzar sino ajustar esta fase: acotar una
versión, cambiar el tipo de pregunta o reducir el estado de prueba.

## Experimento pendiente (registrado, no ejecutado todavía)

Comparar distintas formulaciones de la pregunta `riesgo_parada`, con el mismo estado y el mismo
checkpoint, para separar dos causas posibles del resultado observado:

- **Sensibilidad al texto de la pregunta.** Por ejemplo, una versión que pregunte por lo que el
  correo dice explícitamente ("¿el correo menciona un retraso en la llegada del material?") frente
  a la formulación actual, que pide algo más cercano a una conclusión ("¿reporta un riesgo concreto
  de detener la producción?").
- **Capacidad de inferencia.** Si aun con formulaciones explícitas el modelo no refleja la
  consecuencia que se desprende del texto, la causa probablemente no sea la redacción.

No se ejecuta en esta fase: la Fase 0 se cierra con una sola observación registrada. El experimento
queda anotado para cuando se decida qué mide la Fase 1.
