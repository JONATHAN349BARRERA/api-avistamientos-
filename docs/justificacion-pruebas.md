# Justificación de las pruebas: API de avistamientos de aves

Ingeniería de Software 2 (ISW-2), Sesión 22. Jonathan Barrera.
Repositorio: https://github.com/JONATHAN349BARRERA/api-avistamientos-

Suite final: **28 pruebas** (14 unitarias en `tests/test_validador.py` y 14 de integración en `tests/test_api.py`), todas en verde. Cobertura de líneas y ramas: **96 %**.

---

## 1. Qué cambió en el código

| Cambio | Antes | Después | Por qué mejora la testeabilidad |
|---|---|---|---|
| **Validación extraída** | La función `validar()` vivía dentro de `app.py`, junto a las rutas. | Clase `ValidadorDeAvistamiento` en `validador.py`, sin imports de Flask ni de la base de datos. | La regla de negocio se prueba llamando a un método común y corriente, sin levantar la API ni crear una base de datos. Las pruebas unitarias corren en milisegundos y, si fallan, el error solo puede estar en la regla. |
| **Regla de negocio nueva** | Solo revisaba que los campos no estuvieran vacíos y que la fecha tuviera formato. | La especie debe tener entre 3 y 50 caracteres y la fecha no puede ser posterior a hoy. Cada error dice qué campo falló (`"especie: ..."`). | Da lógica con fronteras reales que vale la pena probar con valores límite. |
| **Reloj inyectable** | No existía: la fecha de hoy habría salido de `date.today()` dentro del validador. | El validador recibe un objeto `reloj` con un método `hoy()`. En producción se usa `RelojDelSistema`; en las pruebas, el stub `RelojFijo`. `create_app(database, reloj)` también lo acepta. | El resultado de "¿la fecha es futura?" deja de depender del día en que se corren las pruebas. Sin esto, la prueba de "mañana" pasa hoy y falla dentro de un mes. |
| **Base de datos configurable** | Ya existía `create_app(database=...)`. | Se mantiene: cada prueba de integración recibe su propio archivo SQLite temporal. | Pruebas independientes, sin datos compartidos entre ellas. |
| **Detalle corregido gracias a las pruebas** | `init_db` usaba `with sqlite3.connect(...)`, que hace commit pero **no cierra** la conexión. | Ahora usa `contextlib.closing(...)`. | Pytest mostraba avisos `ResourceWarning: unclosed database`. Las pruebas destaparon una fuga de conexiones. |

Las pruebas quedaron en la carpeta `tests/`. El doble de prueba compartido está en `tests/dobles.py`.

---

## 2. Tabla de casos (Parte A)

Para todas las pruebas, **hoy = 2026-10-21**, fijado por el stub `RelojFijo`.

### Especie: válida si tiene entre 3 y 50 caracteres

Particiones de equivalencia según la longitud: **[0–2] inválida**, **[3–50] válida**, **[51, ∞) inválida**, más la clase "campo ausente o que no es texto".

| # | Valor | Largo | Tipo de caso | Esperado | Por qué este valor |
|---|---|---|---|---|---|
| 1 | `"colibrí"` | 7 | Representativo de [3–50] | Válido | Un nombre real, lejos de los bordes. Representa a toda la clase válida. |
| 2 | `"ab"` | 2 | Límite inferior, lado inválido | Error en especie | Es el último valor de la clase [0–2]. Si el código usara `>= 2` en vez de `>= 3`, solo este caso lo detectaría. |
| 3 | `"abc"` | 3 | Límite inferior, lado válido | Válido | El primer valor aceptado. Detecta un `>` que debía ser `>=`. |
| 4 | `"a" * 50` | 50 | Límite superior, lado válido | Válido | El último valor aceptado. Detecta un `< 50` que debía ser `<= 50`. |
| 5 | `"a" * 51` | 51 | Límite superior, lado inválido | Error en especie | El primer valor de la clase [51, ∞). |
| 6 | *(campo ausente)* | — | Inválido (clase "no es texto") | Error en especie | Cubre la rama `not isinstance(especie, str)`. Un cliente puede olvidar el campo. |

No se probó una especie de 0 caracteres aparte: pertenece a la misma partición que la de 2 caracteres, y la frontera relevante (2 frente a 3) ya está cubierta. Un valor intermedio como 25 tampoco aporta nada que no aporte "colibrí".

### Fecha: formato AAAA-MM-DD y no posterior a hoy

Particiones: **pasado o hoy (válida)**, **futuro (inválida)**, **formato incorrecto (inválida)** y **formato correcto pero fecha inexistente (inválida)**.

| # | Valor | Tipo de caso | Esperado | Por qué este valor |
|---|---|---|---|---|
| 7 | `"2026-03-15"` | Representativo del pasado | Válido | Es la fecha de los datos válidos base (prueba 1). |
| 8 | `"2026-10-21"` | Límite, lado válido | Válido | Es exactamente hoy. La regla dice "no posterior", así que hoy debe aceptarse. Detecta un `>=` que debía ser `>`. |
| 9 | `"2026-10-22"` | Límite, lado inválido | Error en fecha | Mañana, el primer día futuro. Solo es estable gracias al stub del reloj. |
| 10 | `"21/10/2026"` | Inválido (formato) | Error de formato | El formato que más usaría un usuario hispanohablante por error. |
| 11 | `"2026-02-30"` | Inválido (fecha inexistente) | Error de formato | Cumple el patrón AAAA-MM-DD pero el día no existe. Comprueba que se valida la fecha real y no solo la forma del texto. |

### Lugar y observador: no vacíos

| # | Valor | Tipo de caso | Esperado | Por qué este valor |
|---|---|---|---|---|
| 12 | lugar = `""` | Inválido (vacío) | Error en lugar | El caso obvio de campo vacío. |
| 13 | observador = `"   "` | Inválido (solo espacios) | Error en observador | Un `if valor:` simple lo daría por bueno. Comprueba que se usa `.strip()`. |
| 14 | cuerpo = `["no","es","objeto"]` | Inválido (tipo) | "El cuerpo debe ser un objeto JSON" | JSON válido pero que no es un objeto. Cubre la primera rama del validador. |

Cada fila corresponde a una prueba en `tests/test_validador.py`. Los nombres siguen el estilo de especificación, por ejemplo `test_especie_de_51_caracteres_es_rechazada`, y cada prueba muestra la estructura **Arrange / Act / Assert** con comentarios.

---

## 3. Por qué cada nivel

**`test_especie_de_51_caracteres_es_rechazada` es unitaria.** Lo que se verifica es una regla pura: una entrada produce una salida. No hay HTTP, base de datos ni Flask involucrados. Probarla por integración sería más lento y, si fallara, no sabríamos si el problema está en la regla, en la ruta o en la serialización JSON. Los valores límite se prueban en el nivel unitario porque ahí cada caso es barato y el error queda aislado.

**`test_crear_valido_devuelve_201_con_el_recurso_y_queda_guardado` es de integración.** Lo que importa aquí es que las piezas funcionen **juntas**: la ruta `POST /avistamientos`, la lectura del JSON, el validador, el `INSERT` en SQLite, el código 201, la cabecera `Location` y que un `GET` posterior devuelva el mismo recurso. La prueba unitaria del validador no puede detectar, por ejemplo:
- que la ruta responda 200 en vez de 201,
- que se olvide el `db.commit()` y el avistamiento no se guarde de verdad,
- que el orden de las columnas del `INSERT` esté cruzado (lugar guardado como especie),
- que la API no use el validador en absoluto.

**`test_crear_con_especie_corta_devuelve_400_indicando_el_campo_y_no_guarda` es de integración aunque repite un caso unitario.** No vuelve a probar la regla, porque eso ya lo hace la prueba unitaria del caso 2. Prueba la **frontera** entre la API y el validador: que el resultado del validador se traduce en un 400 con el mensaje en JSON y que **no se guarda nada**. Por eso solo hay un caso inválido por endpoint en integración, y no se repiten todos los valores límite.

---

## 4. Los dobles de prueba

| Doble | Tipo | Dónde | Por qué ese tipo |
|---|---|---|---|
| `RelojFijo` (`tests/dobles.py`) | **Stub** | Pruebas unitarias del validador y todas las de integración (`create_app(..., reloj=RelojFijo())`) | Solo hace falta que **responda** una fecha fija. No interesa verificar cómo se llama, así que un stub, lo más simple, es suficiente. |
| `Mock()` de `unittest.mock` | **Mock** | `test_validador_compara_la_fecha_contra_el_reloj_inyectado` | Aquí sí se verifica la **interacción**: `reloj.hoy.assert_called_once()` comprueba que el validador consulta el reloj inyectado en lugar de llamar a `date.today()` por su cuenta. Un stub no puede comprobar eso. |

**¿Qué habría pasado sin el doble?** Las pruebas `test_fecha_igual_a_hoy_es_aceptada` y `test_fecha_de_manana_es_rechazada` usan fechas fijas (2026-10-21 y 2026-10-22). Con el reloj real:
- desde el 22 de octubre de 2026, "mañana" (2026-10-22) ya no es futura y la prueba fallaría aunque el código esté bien;
- la alternativa de calcular la fecha con `date.today() + timedelta(1)` dentro de la prueba repite la misma lógica que se quiere probar.

La prueba sería **no determinista**: su resultado dependería del día y no del código.

No se usó un fake de repositorio porque la API no tiene una capa de servicio separada: las consultas SQL están en las rutas. Para las rutas, SQLite en un archivo temporal ya es rápido y aislado. Reemplazarlo por un fake no habría aportado velocidad y sí habría escondido errores reales de SQL.

---

## 5. Lo que decidimos no probar

1. **Los manejadores genéricos de 404 y 405** (`no_encontrado` y `metodo_no_permitido` en `app.py`). Solo convierten en JSON los errores que Flask ya produce, para rutas que no existen como `/pajaros` o métodos no soportados como `PATCH`. No forman parte de los cinco endpoints que pide el enunciado ni de la regla de negocio, y su lógica es una sola línea sin decisiones.
2. **Cada valor límite repetido a través de HTTP.** Los límites 2/3/50/51 y hoy/mañana ya están cubiertos en el nivel unitario. Repetirlos en integración agregaría 6 pruebas más lentas que fallarían por la misma causa que las unitarias, sin detectar ningún defecto nuevo.
3. **Concurrencia (dos POST al mismo tiempo) y rendimiento.** Es una API de un solo proceso para uso local, y SQLite serializa las escrituras. Esto sería tema de pruebas de carga, no de pruebas unitarias o de integración.
4. **`RelojDelSistema.hoy()`.** Es una línea que delega en `date.today()` de la librería estándar. Probarla sería probar Python, no nuestro código.

---

## 6. Lectura de la cobertura

Comando:

```bash
python -m pytest --cov=app --cov=db --cov=validador --cov-branch --cov-report=term-missing
```

Se usó cobertura de **líneas y de ramas** (`--cov-branch`). El criterio de ramas es más exigente: cuenta si cada `if` se probó por su lado verdadero y por su lado falso.

```
Name           Stmts   Miss Branch BrPart  Cover   Missing
----------------------------------------------------------
app.py            71      3     12      1    95%   103, 107, 113
db.py             15      0      4      1    95%   10->13
validador.py      26      1     10      0    97%   9
----------------------------------------------------------
TOTAL            112      4     26      2    96%
```

(También guardado en `docs/cobertura.txt`.)

**Qué quedó sin cubrir y qué decidimos:**

| Sin cubrir | Qué es | ¿Hace falta prueba? |
|---|---|---|
| `app.py` 103 y 107 | Los manejadores genéricos de 404 y 405 | **No**, por lo explicado en la sección 5. |
| `app.py` 113 | `if __name__ == "__main__": create_app().run(...)` | **No.** Solo se ejecuta al lanzar el servidor a mano. Las pruebas usan `create_app` directamente. |
| `db.py` rama `10->13` | En `get_db()`, el caso en que la conexión **ya existe** en `g` y se reutiliza | **No vale la pena ahora.** Ningún endpoint llama a `get_db()` dos veces en la misma petición. Si en el futuro un endpoint lo hiciera, la rama se cubriría sola con su prueba de integración. |
| `validador.py` 9 | `RelojDelSistema.hoy()` | **No.** Es consecuencia directa de usar el stub en todas las pruebas: el reloj real nunca se ejecuta. Es la señal de que el doble está aislando lo que debe aislar. |

**Conclusión.** Las líneas sin cubrir son infraestructura (arranque del servidor, manejadores de una línea, reloj real) y no lógica de negocio. El validador, donde vive la regla, tiene el **100 % de sus ramas** cubiertas. El 96 % no es un objetivo en sí mismo: ninguna prueba se escribió para subir el número, y todas tienen un `assert` sobre el comportamiento.

---

## Uso de IA

Se usó **Claude** (Anthropic), modelo **Claude Opus 5.5**, como apoyo para escribir el código, las pruebas y este documento. Revisé el código y las decisiones aquí descritas.
