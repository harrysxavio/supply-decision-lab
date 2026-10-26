# Aprendizajes — `phase_01_enriched_state`

Registro técnico y evidencia de la fase. La explicación para aprender, en
[`lesson.md`](lesson.md).

> Estado de este documento: **corrida ejecutada, dos veces, con resultados idénticos**. La
> hipótesis de la fase **no se confirmó**, y eso quedó registrado como resultado.

## Qué probamos

La hipótesis: *si el estado incluye explícitamente la cobertura y el faltante, el modelo debería
juzgar el riesgo de parada de forma distinta que con la narrativa sola.*

El diseño mínimo para probarlo:

- tres datos de entrada (`supplier_delay_days = 12`, `stock_units = 500`, `daily_demand_units = 100`);
- tres hechos calculados en Python: cobertura `5.0` días, faltante `7.0` días, unidades faltantes
  `700.0`;
- dos estados: el **crudo** (narrativa con los números de entrada, sin la división hecha) y el
  **enriquecido** (la misma narrativa entera + un bloque con los tres hechos);
- dos formulaciones de la misma pregunta, para separar redacción de información:
  `retraso_mencionado` (lo que el texto dice explícitamente) y `riesgo_parada` (una conclusión que
  el texto no enuncia con esas palabras);
- dos llamadas al modelo, una por estado, cada una con las dos preguntas en el mismo paso.

## Qué ocurrió

### Verificado antes de la corrida

- La aritmética es determinística y se testea sin modelo: **10 tests, 0.001 s**, incluidos los
  bordes (sin stock → faltante de 12 días y 1200 unidades; stock de sobra → faltante 0) y el rechazo
  de datos inválidos (consumo cero o negativo, stock negativo, retraso negativo).
- Un test protege la frontera de la fase: el diccionario de hechos tiene **exactamente** tres claves.
  Si alguien agrega un veredicto ("riesgo alto"), el test falla.
- Los tests corrieron **en rojo antes** de existir la implementación (`ModuleNotFoundError: enrich`),
  y en verde después. Ese es el primer ciclo test-first real del proyecto.
- El modelo no se carga al importar el archivo: `laya` se importa dentro de la función que predice.
  Es lo que permite que los tests corran en milisegundos sin PyTorch.

### Observado en la corrida

Dos corridas completas, separadas, con resultados **idénticos**:

| Estado | `retraso_mencionado` (noul) | `answer_confidence` | `riesgo_parada` (noul) | `answer_confidence` |
| --- | --- | --- | --- | --- |
| crudo | 0.9947 | 0.9947 | **0.0** | 1.0 |
| enriquecido | 0.989 | 0.989 | **0.0** | 1.0 |

Enrutado, en las dos corridas y en los dos estados: *checkpoint* `multilingual`, con la razón
impresa `"Latin script but language looks like 'es', not English"` e idioma detectado `es`.

### El veredicto, con números

**El enriquecimiento no cambió el juicio:** `riesgo_parada` pasó de `0.0` a `0.0`. Literalmente, sin
movimiento, aunque el texto enriquecido enuncia que hay 7 días sin cobertura y 700 unidades
faltantes.

Al mismo tiempo, la pregunta literal **sí** obtuvo una probabilidad alta en los dos estados
(`0.9947` y `0.989`). Es decir: el modelo lee correctamente que el correo reporta un retraso.

La combinación de las dos filas es el hallazgo de la fase: **el modelo entiende el texto y aun así
responde "no" a la pregunta de conclusión, y agregarle la cuenta hecha no lo mueve.**

## Qué funcionó

- La separación estricta entre **hechos calculados** y **juicios**: el software produjo tres números
  verificables y no opinó en ningún momento.
- El test-first en la aritmética: los tests se escribieron antes y fallaron antes. 10 casos en 1 ms.
- Comparar dos formulaciones en la misma corrida: sin la pregunta literal, habríamos concluido que
  el modelo "no entiende el texto", y sería falso.
- Dos preguntas en una sola llamada: dos llamadas al modelo en total en vez de cuatro.
- La corrida repetida: el resultado es estable, así que no es ruido de muestreo.

## Qué limitaciones encontramos

- **La hipótesis no se confirmó.** Un resultado negativo es un resultado, pero deja la pregunta
  original abierta: si no era falta de información, ¿qué es?
- **Los dos estados no son "el mismo texto más datos" en sentido estricto.** El estado enriquecido es
  más largo, y eso cambia la entrada del modelo en más de un aspecto (longitud, posición del bloque,
  densidad numérica). El experimento aisla *una* diferencia grande, no todas.
- **El texto crudo de esta fase no es idéntico al correo de la Fase 0.** Acá los números aparecen
  separados (500 unidades, 100 por día) y no como "existencia para 5 días". Por eso el `0.0` de hoy
  y el `0.0044` de la Fase 0 **no son comparables directamente**: son dos textos distintos.
- **`noul = 0.0` con `answer_confidence = 1.0` es un extremo.** El *checkpoint* `multilingual` no
  trae temperaturas calibradas, así que 1.0 significa "la distribución quedó pegada a un extremo",
  no "certeza validada".
- **Un caso, un modelo, un idioma.** Nada de esto dice cómo se comporta el sistema en otro tipo de
  correo ni en otro *checkpoint*.

## Qué aprendizaje obtuvimos

- **Faltar información no era el problema.** Con los números ya calculados y escritos en el texto, la
  respuesta no se movió. La explicación "al modelo le faltaba la cuenta" queda descartada para este
  caso.
- **La redacción de la pregunta manda.** La misma situación, preguntada como hecho ("¿menciona un
  retraso?") da ~0.99; preguntada como conclusión ("¿reporta un riesgo concreto de detener la
  producción?") da `0.0`. El correo no dice que la producción se detiene: dice que habrá que decidir.
  Un `noul` parece estar respondiendo, literalmente, sobre lo que el texto **reporta**.
- **Un resultado negativo también cierra una puerta.** Ahora sabemos qué no explicar, y el próximo
  experimento se puede diseñar sobre lo que quedó en pie.
- **La ingeniería que rodea al modelo importa más que el modelo en esta etapa.** Tests rápidos,
  aritmética aislada, una sola variable por experimento: eso fue lo que hizo legible el resultado.

## Qué justificaría avanzar a la Fase 2

1. Está aceptado que la hipótesis de la Fase 1 no se confirmó, y el registro lo dice sin matices.
2. La frontera "hechos vs juicios" sigue intacta y testeada.
3. Está decidido qué se mide en la Fase 2 **a partir del resultado de esta**, no a partir del plan
   original. Candidatos, en orden de evidencia:
   - **Una pregunta de conclusión que el texto sí sostiene** (por ejemplo: "¿el correo indica que
     puede faltar material para producir?"). Si esa sube, el problema era la formulación; si no sube,
     el problema es más profundo.
   - **Comparar checkpoints** con el mismo estado (el `typed-decisions` existe y está pensado para
     preguntas de decisión).
   - **Pasar a la capa de decisión**, aceptando que el juicio de riesgo queda en manos del software y
     dejando al modelo la lectura del texto.
4. La fase nueva no necesita tocar nada de esta: el módulo de hechos y sus tests sirven tal cual.
5. Nada de la Fase 1 quedó pendiente de verificación.

## Experimentos pendientes (registrados, no ejecutados)

- **Formulación que el texto sí sostiene.** Repetir con una pregunta de conclusión redactada sobre lo
  que el correo afirma ("puede faltar material"), para separar "el modelo no infiere" de "la pregunta
  pedía algo que el texto no dice".
- **Mismo estado, otro *checkpoint*.** Probar `typed-decisions` (pensado para preguntas de decisión)
  con estos mismos dos estados y estas mismas dos preguntas.
- **Estado enriquecido con orden distinto.** Poner el bloque de hechos al principio en vez del final,
  para descartar que la posición del bloque sea lo que lo vuelve invisible.
