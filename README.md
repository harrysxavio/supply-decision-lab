# Supply Decision Lab

Laboratorio de decisiones de supply chain, construido por fases. Cada fase es un incremento
pequeño y verificable: se prueba una hipótesis, se registra la evidencia y recién entonces se pasa a
la siguiente. El objetivo es aprender el comportamiento del sistema con cambios acotados, no
construir una arquitectura completa de una sola vez.

## Fases

| Fase | Qué prueba | Estado |
| --- | --- | --- |
| [`phase_00_laya_hello`](phases/phase_00_laya_hello/README.md) | Que Laya puede leer un estado de supply en español y devolver respuestas tipadas con probabilidades, sin generar texto | corrida ejecutada · cierre parcial |

Cada fase vive en su propia carpeta bajo `phases/` y contiene cuatro archivos: el script, su
`README.md` (objetivo, hipótesis, entrada, salida esperada y límites), `learnings.md` (qué se probó,
qué ocurrió y qué justificaría avanzar) y `lesson.md` (la misma fase explicada en lenguaje sencillo,
para quien recién empieza).

## Convenciones

Las reglas de formato y contenido — idioma, comentarios del código, documentos que debe llevar cada
fase, verificación y alcance — están en [`AGENTS.md`](AGENTS.md). Son las que permiten escribir una
fase nueva sin volver a discutirlas, y están armadas para copiarse a otro proyecto cambiando solo el
dominio.

## Cómo se ejecuta una fase

Las fases se ejecutan con `uv`, que resuelve el intérprete y las dependencias declaradas dentro del
propio script. Por ejemplo, la Fase 0:

```bash
cd phases/phase_00_laya_hello
uv run --python 3.12 hello_laya.py
```

No hace falta instalar nada a mano ni crear un entorno virtual dentro del repositorio.

## Alcance

Este laboratorio es deliberadamente incremental. En la Fase 0 no hay KPI, ni lógica determinística
de negocio, ni RAG, ni fine-tuning, ni interfaz gráfica, ni arquitectura por capas. Cada una de esas
piezas se agrega, si corresponde, en una fase posterior y con su propia justificación.
