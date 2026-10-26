# Fase 1 — `phase_01_enriched_state`

Una sola pregunta:

> ¿Cambia el juicio del modelo si el estado que lee ya trae las cuentas hechas?

La Fase 0 dejó una observación sin resolver: el correo decía "12 días de retraso" y "5 días de stock",
un lector humano concluye que va a faltar material, y Laya respondió `noul = 0.0044` (0.44% de
probabilidad de que el riesgo de parada fuera verdadero). Esta fase prueba la hipótesis de diseño más
simple que puede explicar esa diferencia: **que el modelo necesite los números ya calculados dentro
del texto**.

## Objetivo

1. Calcular con software tres hechos de la operación: días de cobertura, días sin cobertura y
   unidades faltantes.
2. Construir un **estado enriquecido**: la misma narrativa de la Fase 0, más un bloque con esos
   hechos.
3. Preguntarle al mismo modelo lo mismo sobre el estado crudo y sobre el enriquecido, con dos
   formulaciones distintas de la pregunta.
4. Registrar si el juicio cambia, y si el cambio se debe a la información o a la redacción.

## Hipótesis

> Si el estado incluye explícitamente la cobertura y el faltante, el modelo debería juzgar el riesgo
> de parada de forma distinta que con la narrativa sola.

Y su negación, que también es un resultado válido:

> Si el juicio no cambia, entonces lo que falta no es información calculada, y la causa está en otro
> lado (la formulación de la pregunta, el comportamiento del *checkpoint* en español, o algo más
> general del modelo).

**Los dos resultados son informativos.** Esta fase no puede fracasar: descarta una explicación o la
confirma.

## Entrada

Datos estructurados, mínimos:

| Dato | Valor | Origen |
| --- | --- | --- |
| `supplier_delay_days` | 12 | el aviso del proveedor |
| `stock_units` | 500 | inventario disponible |
| `daily_demand_units` | 100 | consumo diario de la línea |

De ahí se derivan tres hechos: cobertura = 5 días, faltante = 7 días, unidades faltantes = 700.

Dos estados a comparar:

- **crudo**: la narrativa del caso, sin cuentas (equivalente al correo de la Fase 0).
- **enriquecido**: la misma narrativa, más un bloque de hechos calculados.

Dos formulaciones de la misma pregunta, para separar información de redacción:

| Id | Tipo | Pregunta |
| --- | --- | --- |
| `retraso_mencionado` | `noul` | ¿El correo menciona un retraso en la llegada del material? |
| `riesgo_parada` | `noul` | ¿El correo reporta un riesgo concreto de detener la producción? |

## La frontera de la fase

- **El software calcula hechos**: cobertura, faltante, unidades. Resultados que siempre dan lo mismo
  y que se verifican con una cuenta.
- **El software no calcula juicios**: no decide "riesgo alto", no elige áreas, no recomienda
  acciones. Eso queda del lado del modelo.

Si el software empieza a escribir veredictos, ya no se está midiendo qué aporta el cálculo: se está
reemplazando al modelo. Esa línea se cruza recién en una fase posterior, y con evidencia.

## Salida esperada

Dos llamadas al modelo (una por estado), cada una con las dos preguntas en el mismo paso. La salida es
una tabla:

| Estado | `retraso_mencionado` | `riesgo_parada` | `answer_confidence` |
| --- | --- | --- | --- |
| crudo | ? | ? | ? |
| enriquecido | ? | ? | ? |

Más una segunda corrida idéntica, para confirmar que los valores se repiten.

## Cómo se ejecuta

```bash
cd phases/phase_01_enriched_state
uv run --python 3.12 enrich.py
```

Los tests de la aritmética no necesitan el modelo y corren en un segundo:

```bash
uv run --python 3.12 test_enrich.py
```

## Entorno

El mismo de la Fase 0: `uv`, Python 3.12.15, `laya==0.3.23` con `torch 2.14.1+cpu`, *checkpoint*
`multilingual` ya descargado en caché. Esta fase **no** agrega dependencias: los tests usan
`unittest`, que viene con Python.

## Por qué hay un quinto archivo

La convención del proyecto son cuatro archivos por fase. Acá hay cinco, y la razón está escrita:
`test_enrich.py` existe porque, por primera vez, hay código **determinístico** que se puede testear
sin descargar un modelo. Es la primera fase donde un test automatizado tiene sentido real, y sería un
error desaprovecharlo justo acá.

## Límites explícitos

Esta fase **no** hace:

- KPI ni tableros de métricas.
- Reglas de negocio ni veredictos calculados (nada de "riesgo alto" en Python).
- RAG ni base documental.
- Fine-tuning ni calibración propia.
- Otro modelo, ni SLM, ni modelo generativo.
- Interfaz gráfica.
- Base de datos, API, ni configuración externa.
- Más de un caso de prueba.

## Criterio de cierre

1. Los tests de la aritmética pasan, incluidos los casos borde (sin stock, stock de sobra, datos
   inválidos).
2. El estado enriquecido se lee como un texto humano, no como un volcado de datos.
3. Las cuatro respuestas están registradas con su `answer_confidence`.
4. Hay un veredicto explícito y con números: el juicio cambió, o no cambió.
5. La corrida repetida da los mismos valores.
6. `learnings.md` dice qué **no** se puede concluir todavía.

## Si algo falla

- **El modelo no descarga ni carga:** el *checkpoint* ya está en caché desde la Fase 0; si algo se
  perdió, la primera llamada lo vuelve a descargar.
- **La aritmética no da lo esperado:** el test falla antes de tocar el modelo. Es a propósito: la
  cuenta se verifica sola.
- **Los cuatro valores salen iguales:** es un resultado, no un error. Significa que la información
  calculada no cambió el juicio, y hay que anotarlo como tal.
