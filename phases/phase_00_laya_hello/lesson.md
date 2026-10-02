# Lección de la Fase 0 — Conociendo a Laya

Esta lección cuenta, en lenguaje sencillo, lo que aprendimos al construir la Fase 0. No hace falta
saber nada de *machine learning* para leerla. Si necesitás el registro técnico y la evidencia, están en
[`learnings.md`](learnings.md); acá está la explicación para entender.

## 1. Qué construimos realmente

Construimos **una sola cosa**: un pedido y una respuesta.

```text
estado  ->  preguntas tipadas  ->  Router  ->  modelo  ->  respuestas
```

Qué es cada pieza, en palabras simples:

- **estado**: un texto. En nuestro caso, un correo interno de 129 tokens donde un proveedor avisa
  que un lote llega 12 días tarde y hay stock para 5 días. Es la evidencia que el modelo va a leer.
- **preguntas tipadas**: tres preguntas escritas por nosotros, cada una con una forma de respuesta
  fija (elegir una opción, ubicarse en una escala, o decir sí/no con una probabilidad).
- **Router** (enrutador): la pieza que mira el texto, detecta el idioma y decide *qué modelo* usar.
  No lo elegimos nosotros.
- **modelo**: el *checkpoint*, es decir los pesos entrenados que hacen el trabajo real.
- **respuestas**: valores con forma conocida, cada uno con un número de confianza.

En la práctica, todo eso son **unas 90 líneas de código** en un archivo, sin clases ni funciones
propias: la lógica vive en la librería, y el script solo conecta las piezas e imprime lo que recibe.
La corrida devolvió: `area = logistica`, `severidad = 1.7808` (escala de 3 niveles) y
`riesgo_parada = 0.0044`.

**Lo que todavía NO construimos**: un agente que decide por su cuenta varios pasos, herramientas,
memoria, búsqueda en documentos, reglas de negocio, cálculos, base de datos o interfaz gráfica.
Nada de eso existe en esta fase, y es a propósito: primero queríamos comprobar que el motor de
decisiones funciona, sin nada alrededor que oculte un problema.

## 2. Las tres formas de preguntar a Laya

Laya no escribe texto libre. Solo responde de tres formas, y eso es una ventaja: no hay que
interpretar párrafos, siempre vuelve un valor con una forma esperada.

### `choice` — elegir una opción

Como una pregunta con casilleros y una sola marca permitida.

> ¿Qué área debe atender este caso?
> `compras` · `logistica` · `calidad` · `servicio_cliente`

Nosotros definimos la lista de opciones (las claves cortas como `compras`) y una descripción de cada
una, que es lo que el modelo lee para decidir. La respuesta trae la opción elegida **y** el peso de
todas las demás, así que también se ve si la decisión fue ajustada o clara. En nuestra corrida:
`logistica`, con `answer_confidence` de 0.908.

### `score` — ubicarse en una escala

Como un control deslizante entre varios niveles ordenados.

> ¿Qué tan severo es el caso para la operación?
> `informativo` · `manejable` · `crítico`

Acá el orden importa: la escala va de menos a más. La respuesta **no** es una etiqueta sino una
**posición** en esa escala: `1.7808` sobre un rango de 0 a 2. Además trae el peso de cada nivel: en
nuestra corrida el nivel `crítico` concentró el 79.02% de la masa. Es decir: "claramente crítico,
pero no en el extremo absoluto".

### `noul` — una pregunta de sí o no, con probabilidad

> ¿El correo reporta un riesgo concreto de detener la producción?

Se responde con un número entre 0 y 1, y ese número es siempre **P(verdadero)**: la probabilidad que
el modelo le asigna a que la afirmación sea cierta. Un `0` sería "falso con toda seguridad" y un `1`,
"verdadero con toda seguridad". En nuestra corrida devolvió `0.0044`, que es casi el extremo del
"falso". Este tipo de pregunta es el protagonista de la próxima sección.

| Tipo | Qué le pedimos | Qué recibimos |
| --- | --- | --- |
| `choice` | una opción entre varias | la opción elegida + el peso de cada opción |
| `score` | un lugar en una escala ordenada | un número decimal + el peso de cada nivel |
| `noul` | un sí o no | P(verdadero) entre 0 y 1 |

## 3. El aprendizaje más importante de la fase: `noul`

En el correo escribimos que:

- el proveedor se retrasa **12 días**;
- hay stock para **5 días** de producción.

Una persona que lee eso hace una cuenta simple: `12 − 5 = 7`, y piensa "va a faltar material: hay un
riesgo real de que la línea se detenga". Entonces esperaría que la pregunta "¿el correo reporta un
riesgo concreto de detener la producción?" se respondiera **verdadero**.

Laya respondió:

```text
noul = 0.0044

P(verdadero) = 0.44%
P(falso)     = 99.56%
```

### Qué significa exactamente ese 0.0044

Significa que **dado el texto y la pregunta, Laya juzgó que la afirmación era verdadera con 0.44% de
probabilidad**. La frase completa importa: "dado el texto y la pregunta". El número es el juicio del
modelo sobre *ese* texto y *esa* pregunta.

### Qué NO significa

**No** significa "hay solo 0.44% de riesgo real de parada". El modelo no nos está informando sobre el
mundo, ni sobre la fábrica, ni sobre el proveedor. Nos está informando sobre **su lectura del texto**.
Son dos cosas distintas, y confundirlas es el error más fácil de cometer con un número como este.

### La diferencia que este caso deja ver

| | Qué hace |
| --- | --- |
| Un humano (o una regla) | Toma dos datos del texto (12 y 5), **los compara con aritmética** y deduce un hueco de 7 días |
| Laya en esta prueba | Recibe **solo el texto y una pregunta**, y respondió que la afirmación era casi falsa |

O sea: aparece una diferencia entre **lo que el modelo interpreta del texto** y **una consecuencia que
puede calcularse con reglas o aritmética**. Nuestra pregunta pedía algo más cerca de una *conclusión*
("¿reporta un riesgo **concreto** de detener la producción?") que de una *lectura literal* ("¿el correo
menciona un retraso en la entrega?"). Ese cambio de redacción puede importar, y todavía no lo sabemos.

**Lo que no podemos concluir:** con **una sola prueba** no sabemos si la causa es la formulación de la
pregunta, el comportamiento del *checkpoint* en español, o una limitación más general del modelo. Por
eso **no** afirmamos que "Laya no puede razonar" ni que "`noul` no infiere": eso sería sacar una
conclusión grande de un solo dato. Queda anotado como **experimento pendiente** en
[`learnings.md`](learnings.md): comparar varias formulaciones de la misma pregunta para separar la
sensibilidad al texto de la capacidad de inferencia.

## 4. Confianza no significa estar en lo correcto

La misma respuesta traía otro número:

```text
answer_confidence = 0.9956
```

Es tentador leerlo como "99.56% de probabilidad de estar en lo correcto". **No significa eso.**
Significa que el modelo estaba **muy decidido** por una de las dos alternativas: el 99.56% de la
probabilidad que repartió se fue al "falso".

La analogía más simple: **una persona puede estar completamente segura de una respuesta y aun así
equivocarse.** La seguridad no es lo mismo que la exactitud. Y al revés también: alguien puede dudar
mucho y acertar (si el modelo reparte 50% y 50%, su confianza es 0.5 aunque la respuesta pueda ser
correcta).

Por eso son dos números distintos y miden dos cosas distintas:

- **`noul` = 0.0044** → *qué cree* el modelo.
- **`answer_confidence` = 0.9956** → *cuánto se juega* por eso.

Un detalle más que aprendimos leyendo el código del paquete: el *checkpoint* en español (el que se
usó acá) se distribuye **sin temperaturas de calibración ajustadas**. En la práctica, eso significa
que su confianza describe "cuán concentrada quedó la respuesta", no "cuán probable es que acierte".
Motivo de más para nunca leer ese número como una promesa.

## 5. Por qué este error fue útil

El objetivo de Supply Decision Lab **no es demostrar que Laya siempre acierta**. Si así fuera, esta
corrida habría sido una mala noticia. Es al revés: el laboratorio existe para **descubrir con
experimentos**:

- qué hace bien;
- dónde falla;
- qué información necesita para responder bien;
- cuándo conviene calcular de forma determinística;
- y cuándo conviene dejarle la interpretación al modelo.

Visto así, este resultado fue productivo: descubrimos, con evidencia propia y no con teoría, un caso
donde el número devuelto no coincide con lo que un lector humano esperaría.

Ese tipo de hallazgo es el que empieza a justificar una futura capa de trabajo, algo parecido a:

```text
datos  ->  cálculos determinísticos  ->  estado enriquecido  ->  Laya  ->  decisión
```

En palabras simples: primero el software calcula lo que es aritmética pura (días de cobertura,
unidades faltantes, fechas comprometidas) y **escribe esos resultados dentro del texto** que el modelo
va a leer; después Laya interpreta y decide sobre un estado que ya viene "enriquecido" con las cuentas
hechas.

**Todavía no implementamos nada de eso.** No hay cálculos, ni reglas, ni datos en la Fase 0. Por ahora
es una hipótesis de diseño que este caso ayuda a sostener, nada más.

## 6. Qué aprendimos de ingeniería además de Laya

Construir algo real trajo, de paso, un montón de piezas de ingeniería. Ninguna fue estudiada antes:
aparecieron porque hacían falta.

- **WSL.** Es un Linux de verdad corriendo dentro de Windows. La terminal que usamos es Linux; los
  archivos viven en Windows.
- **Rutas de Linux hacia Windows.** La ruta del proyecto (`/mnt/c/Users/harry/...`) es la forma en que
  ese Linux ve la unidad `C:` de Windows. Por eso la carpeta se abre igual desde los dos lados.
- **Git y el *working tree*.** Los archivos están creados y guardados, pero **no confirmados**
  (*commit*) todavía: eso es lo que muestra `git status` con sus marcas de "modificado" y "sin
  rastrear". El *working tree* es, simplemente, el estado actual de la carpeta.
- **Dependencias.** Laya no funciona sola: necesita PyTorch, `transformers` y otras librerías. Fijar
  `laya==0.3.23` es una forma de decir "esta fase se hizo con esta versión exacta".
- **Python 3.12.** La máquina tenía Python 3.14, pero es tan nuevo que PyTorch todavía no publica
  todo lo necesario para él. Pedimos 3.12 y no se tocó el Python del sistema.
- **`uv`.** La herramienta que lee la cabecera del script, instala lo que hace falta y arma un entorno
  privado en su propia caché. Por eso el repositorio no tiene `requirements.txt` ni un `.venv`.
- **PyTorch CPU.** Esta máquina no tiene GPU, así que pedimos la variante de CPU: sin eso se
  descargarían varios GB de librerías de NVIDIA que acá no se pueden usar. Resultado verificado:
  `torch 2.14.1+cpu`, cero paquetes `nvidia-*`.
- **Checkpoints.** Son los pesos entrenados, el "modelo" propiamente dicho. Hay tres y se descargan
  la primera vez desde Hugging Face; por eso la primera corrida tarda y las siguientes no.
- **Enrutamiento por idioma.** El `Router` detectó que el texto estaba en español (`es`) y eligió el
  *checkpoint* multilingüe, sin que se lo indiquemos. Además imprimió su razón. Es una pieza de
  arquitectura que no tuvimos que construir.

## 7. Modelo mental para llevarse de esta fase

> No estamos intentando que la IA haga todo. Estamos aprendiendo qué parte conviene darle a la IA y
> qué parte debería resolver el software de forma determinística.

Una forma práctica de pensarlo: si la respuesta **se desprende de una cuenta o de una regla escrita**,
conviene calcularla con software, donde el resultado es siempre igual y se puede verificar. Si la
respuesta **depende de leer y juzgar un texto** (¿de qué se queja el cliente?, ¿esto es urgente?,
¿esta frase implica un compromiso?), conviene preguntarle al modelo.

Esa división del trabajo todavía es una hipótesis que estamos empezando a probar. Y es exactamente lo
que va a ir definiendo las próximas fases.

## 8. Preguntas para comprobar que entendí

1. ¿Qué representa `noul`?
2. ¿Por qué `0.9956` no significa "99.56% de precisión"?
3. ¿Qué diferencia hay entre `choice` y `score`?
4. ¿Qué hizo el `Router`?
5. ¿Por qué todavía no agregamos reglas de negocio?

*(Las respuestas no están acá: se pueden reconstruir con el [`README.md`](README.md) de la fase y con
la evidencia de [`learnings.md`](learnings.md).)*
