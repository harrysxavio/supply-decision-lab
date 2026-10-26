# Supply Decision Lab

Laboratorio de decisiones de supply chain, construido por fases. Cada fase es un incremento
pequeño y verificable: se prueba una hipótesis, se registra la evidencia y recién entonces se pasa a
la siguiente. El objetivo es aprender el comportamiento del sistema con cambios acotados, no
construir una arquitectura completa de una sola vez.

## Fases

| Fase | Qué prueba | Estado |
| --- | --- | --- |
| [`phase_00_laya_hello`](phases/phase_00_laya_hello/README.md) | Que Laya puede leer un estado de supply en español y devolver respuestas tipadas con probabilidades, sin generar texto | completada |
| [`phase_01_enriched_state`](phases/phase_01_enriched_state/README.md) | Si darle al modelo las cuentas ya hechas cambia su juicio sobre el riesgo de parada | completada · hipótesis no confirmada |

Cada fase vive en su propia carpeta bajo `phases/` y contiene cuatro archivos: el script, su
`README.md` (objetivo, hipótesis, entrada, salida esperada y límites), `learnings.md` (qué se probó,
qué ocurrió y qué justificaría avanzar) y `lesson.md` (la misma fase explicada en lenguaje sencillo,
para quien recién empieza). Una fase puede sumar un quinto archivo cuando tiene código determinístico
que se puede testear, y entonces lo justifica por escrito en su `README.md`.

## Convenciones

Las reglas de formato y contenido — idioma, comentarios del código, documentos que debe llevar cada
fase, verificación y alcance — están en [`AGENTS.md`](AGENTS.md). Son las que permiten escribir una
fase nueva sin volver a discutirlas, y están armadas para copiarse a otro proyecto cambiando solo el
dominio.

## Cómo se ejecuta una fase

Las fases se ejecutan con `uv`, que resuelve el intérprete y las dependencias declaradas dentro del
propio script. No hace falta instalar nada a mano ni crear un entorno virtual en el repositorio:

```bash
# Fase 0 — el saludo al motor: un correo, tres preguntas, tres respuestas
cd phases/phase_00_laya_hello
uv run --python 3.12 hello_laya.py

# Fase 1 — ¿alcanza con darle las cuentas hechas? (corre el modelo)
cd phases/phase_01_enriched_state
uv run --python 3.12 enrich.py

# Fase 1 — solo la aritmética: 10 tests, un milisegundo, sin modelo
cd phases/phase_01_enriched_state
uv run --python 3.12 test_enrich.py
```

## Qué sabemos hasta ahora

- **El motor funciona acá.** Laya corre local en CPU, entiende un correo de supply en español y
devuelve respuestas tipadas con probabilidad. Elige solo el *checkpoint* de español, sin que se lo
indiquemos (Fase 0).
- **Darle más información no cambió su juicio.** Escribimos en el texto las cuentas hechas —7 días sin
cobertura, 700 unidades faltantes— y la respuesta sobre el riesgo de parada no se movió ni un decimal
(Fase 1).
- **La pregunta pesa más que la información.** Lo que el correo dice literalmente se responde con
~99% de probabilidad; lo que hay que *concluir* se responde con 0%. Misma situación, dos formas de
preguntar, respuestas opuestas (Fase 1).
- **Pregunta abierta:** si una pregunta de conclusión redactada sobre lo que el texto sí afirma cambia
la respuesta. Si cambia, era la redacción; si no, hay que mirar el *checkpoint*.

## Alcance

El laboratorio es deliberadamente incremental. La Fase 0 no tuvo código propio; la Fase 1 agrega el
primer cálculo determinístico, limitado a **hechos verificables** (cobertura, faltante, unidades) y
nunca a veredictos. Sigue sin haber KPI, ni reglas de negocio, ni RAG, ni fine-tuning, ni interfaz
gráfica, ni arquitectura por capas. Cada una de esas piezas se agrega, si corresponde, en una fase
posterior y con su propia justificación.
