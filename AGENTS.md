# Convenciones del proyecto

Este documento reúne los acuerdos de **formato y contenido** que usamos para construir cada fase de
Supply Decision Lab. Existe por dos razones:

1. que una fase nueva se pueda escribir sin volver a discutir cómo se escribe;
2. que el conjunto se pueda copiar a otro proyecto, cambiando solo el dominio.

Vale para el código, para los documentos y para el proceso: qué se hace antes de escribir, qué se
verifica después y qué se declara siempre.

---

## 1. Idioma

| Elemento | Idioma | Ejemplo |
| --- | --- | --- |
| Documentos del proyecto (`.md`) | Español | `README.md`, `learnings.md`, `lesson.md` |
| Comentarios y *docstrings* del código | Español cuando el archivo es material de aprendizaje | `hello_laya.py` |
| Identificadores, nombres de archivo, estructura interna | Inglés | `supply_state`, `risks`, `phase_00_...` |
| Textos de ejemplo del dominio | Español | el correo del lote 4412 |
| Mensajes de *commit* | Inglés, formato Conventional Commits | `docs(phase-00): add lesson` |
| Respuesta al usuario en el chat | El idioma en el que escribe | — |

Los documentos van en **español neutro**, sin regionalismos: un artefacto tiene que poder leerlo
cualquiera, y el registro coloquial queda para la conversación.

El **texto del dominio en español no es decorativo**: es lo que ejercita el *checkpoint*
multilingüe y lo que nos dice si el sistema sirve para nuestro caso real.

---

## 2. Código y comentarios

### La regla de fondo

Un archivo de código de una fase debe poder **leerse de arriba abajo, como un recorrido**, sin
saltar a otra parte y sin adivinar nada. Si para entender la línea 40 hay que leer primero la 90,
el archivo está mal armado.

### Estructura de un archivo didáctico

1. **Docstring inicial** con cinco cosas: qué es el archivo, cómo se ejecuta, qué es la cabecera de
   configuración (si tiene), cuáles son las partes del archivo y un glosario mínimo de las palabras
   técnicas que se van a repetir.
2. **Una sección por paso del flujo**, con un título visible (`# PARTE 1 — ...`).
3. **El "por qué" antes del código**, no el "qué" obvio. Se explica por qué esa pieza existe y qué
   problema resuelve; no se comenta lo que la línea ya dice.
4. **La sintaxis del lenguaje se explica donde aparece**: si el archivo usa algo que un principiante
   no vio (f-strings, `!r`, `sorted()`, `.items()`, `\n`, concatenación implícita de texto), se
   explica ahí mismo, en una o dos frases.
5. **Las trampas se nombran como trampas**: campos de la API cuyo nombre engaña, campos que hay que
   revisar primero, decisiones que parecen arbitrarias y no lo son.

### Reglas concretas

- **No afirmar lo que no se verificó.** Si un campo existe pero su significado no está documentado
  (por ejemplo `action.act_probability`), el comentario lo dice: "existe, semántica no verificada".
- **Los `import` van juntos y sin comentarios en el medio.** La convención de Python agrupa primero
  la biblioteca estándar y después los paquetes instalados; `ruff` lo marca como error `I001`.
  La explicación de cada import va en un bloque justo debajo.
- **Proporción a favor del lector.** Es correcto y esperable que los comentarios ocupen más líneas
  que el código en un archivo didáctico (en la Fase 0: ~90 líneas de código, ~280 de archivo; en la
  Fase 1, ~130 de código, ~350 de archivo). Lo que **no** puede cambiar es el código ejecutable.
- **Se explica el código, no solo el proceso.** El comentario tiene que servirle a alguien que sabe
  poco de Python: qué es un diccionario y cómo se lee con corchetes, qué hace `raise`, por qué hay un
  `max(0.0, ...)`, qué son las anotaciones de tipo (`: float`, `-> str`), qué significa
  `if __name__ == "__main__":`, cómo se arma un formato de columna (`{x:>8}`). Explicar el flujo de
  la fase sin explicar la sintaxis deja al lector afuera: el proceso se entiende y el archivo no.
- **Sin adornos.** Nada de emojis, ni `TODO`, ni "esto imprime el resultado" cuando es evidente.

### La verificación de que solo se agregaron comentarios

Los comentarios no cambian la semántica, así que hay una forma objetiva de comprobarlo: comparar el
**AST** (el árbol que Python interpreta) del archivo antes y después, quitando el *docstring* del
módulo. Si el AST es idéntico, el programa hace exactamente lo mismo.

```bash
python - <<'PY'
import ast
def strip_docstring(t):
    for n in ast.walk(t):
        b = getattr(n, "body", None)
        if isinstance(b, list) and b and isinstance(b[0], ast.Expr) \
           and isinstance(b[0].value, ast.Constant) and isinstance(b[0].value.value, str):
            b.pop(0)
    return t
d = lambda p: ast.dump(strip_docstring(ast.parse(open(p, encoding="utf-8").read())))
print("idéntico:", d("antes.py") == d("despues.py"))
PY
```

---

## 3. Los cuatro documentos de una fase

Cada fase vive en `phases/<nombre_de_la_fase>/` y contiene **exactamente** cuatro archivos. Ni uno
más, salvo que la fase lo justifique por escrito.

| Archivo | Rol | Pregunta que responde |
| --- | --- | --- |
| `<script>.py` | El código mínimo que prueba la fase | ¿Cómo se hace, concretamente? |
| `README.md` | La especificación ejecutable de la fase | ¿Qué se probó y cómo se corre? |
| `learnings.md` | El registro técnico y la evidencia | ¿Qué pasó, de verdad? |
| `lesson.md` | La explicación didáctica | ¿Cómo lo entiende alguien que empieza? |

**Regla de no duplicación:** cada idea tiene un solo lugar. El objetivo y los límites van en el
`README.md`; los números y la evidencia, en `learnings.md`; las analogías y el "por qué importa", en
`lesson.md`. Si una idea aparece en dos documentos, uno de los dos sobra.

### 3.1 `README.md` de la fase — secciones obligatorias, en este orden

1. **Título y pregunta única** que responde la fase, en una frase.
2. **Objetivo**: qué se quiere demostrar, en pasos numerados.
3. **Hipótesis**: qué esperamos que ocurra y por qué; incluida la hipótesis secundaria si la hay.
4. **Entrada**: el estado de prueba y la tabla de preguntas (id, tipo, pregunta, forma de la respuesta).
5. **Salida esperada**: la forma real del objeto devuelto, no valores inventados. Va acompañada de la
   lectura de los campos que confunden.
6. **Cómo se ejecuta**: el comando exacto, sin pasos implícitos.
7. **Entorno**: versión de cada pieza y por qué se eligió.
8. **Límites explícitos**: la lista de lo que la fase **no** hace. Es la sección que evita discusiones
   en la fase siguiente.
9. **Criterio de cierre**: qué hay que observar para darla por terminada.
10. **Si algo falla**: los errores previsibles y qué haría cada uno.

### 3.2 `learnings.md` — secciones obligatorias, en este orden

1. **Qué probamos**: la hipótesis y el mínimo con el que se probó.
2. **Qué ocurrió**: dividido en **verificado** (antes de la corrida) y **observado** (en la corrida).
   Todo lo no observado va a una subsección **pendiente**, nunca se mezcla con lo verificado.
3. **Qué funcionó**.
4. **Qué limitaciones encontramos**: del entorno y del enfoque.
5. **Qué aprendizaje obtuvimos**: conceptos, no pasos.
6. **Qué justificaría avanzar a la fase siguiente**: condiciones numeradas y verificables.
7. **Experimentos pendientes**: registrados con su pregunta, marcados como *no ejecutados*.

Reglas de contenido:

- **No se anota nada que no se haya observado.** Sin "probablemente", sin "debería dar".
- **Evidencia reproducible**: el comando que se corrió o `archivo:línea` del código fuente citado.
- **Observación ≠ conclusión.** Una sola corrida produce una observación con hipótesis posibles. Una
  afirmación sobre la capacidad del sistema necesita más de una prueba.
- **Los números se citan completos**, con la unidad o el significado al lado (`noul = 0.0044` es
  P(verdadero), no "un 0.44% de riesgo").

### 3.3 `lesson.md` — secciones obligatorias, en este orden

1. **Qué construimos realmente**, con el flujo en un diagrama de texto y un párrafo sobre lo que
   *todavía no* se construyó.
2. **Las formas de preguntar**, cada una con un ejemplo y una analogía cotidiana; sin dar por sabido
   nada de *machine learning*.
3. **El aprendizaje más importante de la fase**, explicado con el caso real: qué significa el número,
   qué **no** significa y qué diferencia deja ver.
4. **Confianza ≠ estar en lo correcto**, con una analogía humana.
5. **Por qué el resultado fue útil**, aunque parezca un error.
6. **Qué aprendimos de ingeniería además del modelo**, en viñetas cortas.
7. **Modelo mental** para llevarse, en dos o tres frases.
8. **Preguntas de autoevaluación**: cinco, cortas, **sin respuestas**.

Reglas de contenido:

- La lección explica, no demuestra: no repite tablas de evidencia ni comandos.
- Nada de jerga sin traducir; si aparece un término técnico, se define en la misma frase.
- No se afirma nada más fuerte de lo que el registro técnico sostiene.

---

## 4. Honestidad técnica

Estas reglas son las que hacen que el proyecto enseñe algo. Aplican a documentos, comentarios y
respuestas.

- **No asumir una API: leerla.** Antes de usar un campo, se lee el código de la versión que está
  instalada (o la publicada) y, si se pudo, se confirma que son idénticas (`diff`). La documentación
  puede estar atrasada; el código no.
- **Imprimir solo lo que el objeto devuelve.** Nada de campos "que deberían estar". Si un campo no
  aparece, se dice que no aparece.
- **No llamar "calibrado" a lo que no está calibrado.** Si un número es la cantidad sobre la que se
  ajusta la calibración, se dice exactamente eso; si el *checkpoint* no trae temperaturas ajustadas,
  se declara y se explica cómo se lee el número en consecuencia.
- **Nombrar el límite de lo verificado.** Un campo sin semántica documentada se marca como tal; una
  cifra no medida se declara "no medida".
- **Propagar la corrección.** Cuando un documento demuestra que otro afirmaba de más, se corrigen
  **todos** los que lo repetían en el mismo turno, y se avisa.
- **Declarar los desvíos.** Si se toca algo fuera de lo autorizado (aunque sea para evitar una
  contradicción), se dice explícitamente y se ofrece revertirlo.

---

## 5. Alcance y proceso

Orden de trabajo para cualquier pedido:

1. **Inspeccionar** el repositorio y decir qué existe, antes de proponer nada.
2. **Proponer** la estructura mínima y explicar **por qué cada archivo**, sin escribir todavía.
3. **Esperar autorización** con el alcance enumerado.
4. **Implementar solo eso**, con verificación.
5. **Reportar** qué se hizo, qué se verificó, qué quedó fuera y qué falta.

Reglas de alcance:

- **Una fase = un incremento.** No se agrega arquitectura, ni métricas de negocio, ni reglas
  determinísticas, ni recuperación de documentos, ni entrenamiento propio, ni interfaz gráfica, ni
  capas, sin un pedido explícito.
- **Estructura mínima primero.** Un script y tres documentos alcanzan; el *packaging*, la
  configuración externa y los tests se agregan cuando exista algo que los justifique.
- **Sin *commit* sin pedido.** El *working tree* queda para revisión; `git status` es el reporte.
- **Verificación obligatoria antes de decir "listo"**: sintaxis del intérprete fijado, linter
  (`ruff`) y, cuando se tocaron comentarios, equivalencia de AST.
- **Lo que no se pudo verificar se dice.** Un verificador que no corrió no es un verificador aprobado.

---

## 6. Checklist: abrir una fase nueva

- [ ] Existe una pregunta única que la fase responde, en una frase.
- [ ] La carpeta `phases/<nombre>/` tiene nombre con prefijo numérico (`phase_01_...`) y en inglés.
- [ ] El script declara intérprete y dependencias **dentro del archivo** (PEP 723) o en un archivo
      de proyecto, y la versión de la librería está fijada.
- [ ] Los cuatro documentos existen, con sus secciones en el orden de arriba.
- [ ] Los límites de la fase están escritos en el `README.md` antes de escribir código.
- [ ] El criterio de cierre es observable (no es "que funcione").

## 7. Checklist: cerrar una fase

- [ ] La corrida se hizo y su salida está citada en `learnings.md`.
- [ ] Cada criterio de cierre tiene estado: cumplido, parcial o pendiente.
- [ ] Las secciones "pendiente" del registro siguen diciendo *pendiente* si nadie las midió.
- [ ] La lección no contradice al registro técnico ni al `README.md`.
- [ ] Lo que la fase aprendió está resumido en una frase que se podría explicar sin abrir el código.

---

## 8. Cómo replicarlo en otro proyecto

1. Copiar este archivo al proyecto nuevo (idealmente como `AGENTS.md` en la raíz, que es como los
   agentes lo leen automáticamente).
2. Cambiar solo tres cosas: el nombre de la carpeta de fases, el dominio de los ejemplos y el
   *checkpoint* o motor con el que se trabaja.
3. Mantener intacto el resto: los cuatro documentos, el orden de sus secciones y las reglas de
   honestidad. Son las que hacen que un proyecto se pueda retomar meses después.
4. La primera fase de cualquier proyecto nuevo debería ser siempre del mismo tipo: **el caso más
   pequeño que demuestre que el motor funciona**, sin dominio, sin métricas y sin capas.

---

## 9. Decisiones registradas y su porqué

Las decisiones de la Fase 0, con la razón que las sostiene. Si en otro proyecto la razón no aplica,
la decisión puede cambiar; la razón es lo que se copia, no la decisión.

| Decisión | Por qué | Cuándo deja de aplicar |
| --- | --- | --- |
| `uv` en lugar de `pip`/`venv` | El Python del sistema no trae `pip` ni `ensurepip`, y `uv` resuelve eso sin permisos de administrador | Si el entorno ya tiene `pip` y un gestor de proyectos |
| Python 3.12 fijo | PyTorch no publica todo lo necesario para versiones muy nuevas de Python | Si las dependencias ya soportan la versión del sistema |
| Dependencias dentro del script (PEP 723) | Un archivo, un comando, cero configuración en el repositorio | Cuando haya varios módulos y dependa de un árbol de paquetes |
| Índice de PyTorch CPU | La máquina no tiene GPU; sin eso se descargan varios GB inútiles | En una máquina con GPU y necesidad real de usarla |
| Versión de la librería fijada | Reproducibilidad: la fase se hizo con esa versión exacta | Nunca: fijar versión siempre |
| Sin tests automatizados en la fase 0 | Un test solo podría afirmar la salida de un modelo que hay que descargar; frágil y lento | Cuando exista código determinístico propio |
| Sin *commit* automático | El humano revisa antes; el *working tree* es el reporte | No aplica: el *commit* sigue siendo decisión humana |
| Cuatro documentos por fase | Separar especificación, evidencia, enseñanza y código evita que uno contamine al otro | Nunca, si se mantiene la disciplina de no duplicar |

---

*Este documento se actualiza cuando un acuerdo nuevo demuestra ser reutilizable. Si una regla no
sobrevivió al contacto con un caso real, se borra: estas convenciones existen para trabajar mejor,
no para acumularse.*
