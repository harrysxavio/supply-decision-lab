# Lección de la Fase 1 — Cuando la cuenta no alcanza

Esta lección cuenta qué construimos en la Fase 1 y qué nos enseñó. En simple: hicimos que el software
**calcule**, y descubrimos que calcular no fue suficiente para cambiar el juicio del modelo. Esa es la
historia, y es más interesante de lo que parece.

El registro técnico y los números están en [`learnings.md`](learnings.md).

## 1. Qué construimos realmente

Tres piezas, en este orden:

```text
datos (3 números) -> cálculos (3 hechos) -> dos textos -> modelo -> comparación
```

- **datos**: el proveedor se retrasa 12 días, hay 500 unidades en stock, la línea consume 100 por día.
- **cálculos**: tres hechos que se obtienen con una cuenta simple — el stock alcanza para **5 días**,
  el retraso es de **12**, así que quedan **7 días sin material** y faltan **700 unidades**.
- **dos textos**: el mismo correo, en dos versiones. Una cuenta la situación tal como llega, sin hacer
  ninguna división. La otra tiene la misma narrativa y, al final, un bloque con esas tres cuentas
  resueltas.
- **el modelo**: la misma pregunta, sobre los dos textos.
- **la comparación**: ¿cambió la respuesta?

Lo que **no** construimos: ningún juicio. El software no dijo "riesgo alto", no eligió un área, no
recomendó nada. Solo hizo cuentas y las escribió en el texto. La regla de la fase fue esa, y hay un
test que la protege: si alguien agregara al cálculo un "nivel de riesgo", el test falla.

## 2. Las dos preguntas: literal contra conclusión

Le hicimos al modelo dos preguntas sobre el **mismo** texto:

| Pregunta | Qué pide | Respuesta (texto crudo) |
| --- | --- | --- |
| `retraso_mencionado` | "¿el correo menciona un retraso en la llegada del material?" | 0.9947 |
| `riesgo_parada` | "¿el correo reporta un riesgo concreto de detener la producción?" | 0.0 |

Son dos formas de preguntar por la misma situación, y la diferencia es enorme. La primera pregunta
tiene la respuesta escrita en el texto: el correo **dice** que el material llega tarde, y el modelo lo
detecta con casi total seguridad. La segunda pide algo más: que el texto **reporte** un riesgo de
detener la producción... y el texto nunca dice "la producción se va a detener". Dice que habrá que
elegir entre pagar más o avisarle al cliente.

Esa comparación fue clave, porque sin ella habríamos dicho "el modelo no entiende el texto". Falso: lo
entiende. Lo que cambia es lo que le pedimos.

## 3. El aprendizaje más importante de la fase

La hipótesis era: *si le damos las cuentas hechas, el modelo va a juzgar distinto*. Los números
dijeron que no:

```text
                          crudo      enriquecido
retraso_mencionado        0.9947  ->  0.989
riesgo_parada             0.0     ->  0.0
```

Le escribimos, con todas las letras, que hay **7 días sin cobertura** y **700 unidades faltantes**. La
respuesta no se movió ni un decimal.

Eso descarta una explicación que parecía obvia: **no le faltaba la cuenta**. La información estaba ahí
y el juicio siguió igual. Un resultado así es valioso, porque deja de hacernos perder tiempo por el
camino equivocado.

Y queda una pista fuerte juntando las dos filas: si el modelo lee bien el retraso (fila 1) y aun así
responde "no" a la pregunta de conclusión (fila 2), lo más probable es que esté contestando **literalmente**
lo que se le preguntó. El correo no *reporta* una parada; el correo permite *deducir* que puede faltar
material. Un `noul` parece responder sobre lo que el texto dice, no sobre lo que nosotros concluimos.

Ojo con no exagerar: esto es una **hipótesis** con evidencia de un caso, no una ley. Queda anotada como
experimento pendiente.

## 4. Confianza no significa estar en lo correcto

Mirá la segunda fila: `noul = 0.0` con `answer_confidence = 1.0`.

Cien por ciento de confianza en una respuesta. Y sin embargo, esa respuesta es justamente la que nos
hizo levantar la mano: un humano leería ese correo y diría "esto es grave".

Lo que `1.0` significa es que el modelo dejó **toda** la probabilidad de un lado: no dudó. No significa
"acerté seguro". Es la misma lección de la Fase 0, ahora con el número más extremo posible: alguien
puede estar absolutamente convencido y equivocado. Y el *checkpoint* que estamos usando, además, no
trae temperaturas de calibración ajustadas, así que ese 1.0 describe cuán concentrada quedó la
decisión, no cuán probable es que sea correcta.

## 5. Por qué un resultado negativo fue útil

Podría parecer que la fase falló: probamos algo y no salió. Pero en un laboratorio el resultado
negativo es información, y esta es de las caras de conseguir:

- **Cerramos una puerta**: no era falta de información. Antes de la fase, esa era la explicación más
  razonable. Ya no.
- **Apareció una pista mejor**: la redacción de la pregunta pesa más que el cálculo en el texto.
- **Cambió el plan**: la Fase 2 no va a ser "enriquecer más el estado" (hubiera sido el paso natural y
  probablemente inútil), sino probar una formulación que el texto sí sostiene.

Eso es lo que buscamos con este proyecto: no acumular funcionalidades, sino **ir achicando las
explicaciones posibles** hasta quedarnos con las que sobreviven a las pruebas.

## 6. Qué aprendimos de ingeniería además del modelo

- **Test-first, por fin de verdad.** Fue la primera fase con código determinístico, así que los tests
  se escribieron antes que la implementación. Corrieron en rojo (`enrich.py` no existía) y después en
  verde: 10 tests en 0.001 segundos. Sin modelo, sin descargas, sin esperas.
- **Importar la librería pesada solo cuando hace falta.** `laya` se importa *adentro* de la función
  que predice. Por eso los tests corren en un milisegundo: no cargan PyTorch. Es un truco chiquito con
  un efecto grande sobre la velocidad de trabajo.
- **Un test puede proteger una decisión de diseño, no solo un cálculo.** El que verifica que el
  diccionario de hechos tiene exactamente tres claves no comprueba aritmética: impide que alguien
  agregue un juicio al software sin darse cuenta.
- **Una variable por experimento.** Narrativa idéntica, un bloque agregado al final: así, si algo
  cambia, se sabe por qué. Cuesta disciplina, pero es lo que hace legible el resultado.
- **La misma pregunta, dos veces, en el mismo viaje.** Laya contesta varias preguntas en un solo paso
  interno, así que comparar dos formulaciones costó una llamada, no dos.

## 7. Modelo mental para llevarse de esta fase

> Hacer la cuenta no alcanza. Lo que el modelo responde depende de lo que le preguntamos, no solo de
> lo que le mostramos.

Y una segunda frase, que es la que va a ordenar las próximas fases:

> Antes de agregar información, conviene revisar la pregunta. Es gratis, y a veces es todo el
> problema.

## 8. Preguntas para comprobar que entendí

1. ¿Qué diferencia hay entre los estados "crudo" y "enriquecido"?
2. ¿Por qué el software calcula hechos y no veredictos?
3. ¿Qué nos dijo la comparación entre `retraso_mencionado` y `riesgo_parada`?
4. ¿Por qué `answer_confidence = 1.0` no significa "respuesta correcta"?
5. ¿Qué experimento harías ahora para seguir achicando las explicaciones posibles?

*(Las respuestas no están acá: se reconstruyen con el [`README.md`](README.md) de la fase y con la
evidencia de [`learnings.md`](learnings.md).)*
