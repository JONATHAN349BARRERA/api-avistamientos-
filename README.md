# API REST: Registro de avistamientos de aves

Trabajo en clase, Ingeniería de Software 2 (ISW-2), sesión 17.

API REST para registrar avistamientos de aves. Hecha con **Python 3 + Flask**, y los datos se guardan en **SQLite** (módulo `sqlite3`, que ya viene con Python). Recibe y responde JSON.

## Modelo: avistamiento

| Campo        | Tipo    | Descripción                          |
|--------------|---------|--------------------------------------|
| `id`         | entero  | Lo asigna el sistema                 |
| `especie`    | texto   | Nombre de la especie (ej. "colibrí") |
| `lugar`      | texto   | Dónde se observó                     |
| `fecha`      | texto   | Formato `AAAA-MM-DD`                 |
| `observador` | texto   | Quién lo registró                    |

**Regla de negocio** (en `validador.py`, clase `ValidadorDeAvistamiento`). Un avistamiento es válido si:

- la `especie` tiene entre 3 y 50 caracteres,
- la `fecha` tiene formato `AAAA-MM-DD` y no es posterior a hoy,
- el `lugar` y el `observador` no están vacíos.

Si no es válido, `POST` y `PUT` responden `400` con la lista de errores, cada uno indicando el campo que falló.

## Requisitos

- Python 3.9 o superior
- Git

## Instalación y ejecución

git clone https://github.com/JONATHAN349BARRERA/api-avistamientos-.git
cd api-avistamientos-

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

La API queda en `http://localhost:5000`. La base de datos `avistamientos.db` se crea sola la primera vez.
Variables opcionales: `PORT` (puerto, por defecto 5000) y `DATABASE` (ruta del archivo SQLite).

## Endpoints

| Método | Ruta                       | Respuesta                                         |
|--------|----------------------------|---------------------------------------------------|
| GET    | `/avistamientos`           | `200` con la lista                                |
| GET    | `/avistamientos/{id}`      | `200` con el avistamiento, `404` si no existe     |
| POST   | `/avistamientos`           | `201` con el avistamiento creado, `400` si faltan datos |
| PUT    | `/avistamientos/{id}`      | `200` con el avistamiento, `404` si no existe, `400` si faltan datos |
| DELETE | `/avistamientos/{id}`      | `204` sin contenido, `404` si no existe           |
| GET    | `/avistamientos/resumen`   | `200` con la cantidad de avistamientos por especie (bonus) |

### Ejemplos con curl

> En Windows usen `curl.exe` en PowerShell, o Git Bash para copiar los comandos tal cual.

**Registrar un avistamiento** → `201`

```bash
curl -i -X POST http://localhost:5000/avistamientos \
  -H "Content-Type: application/json" \
  -d '{"especie":"colibrí","lugar":"Parque Arví","fecha":"2026-09-29","observador":"Ana"}'
```

```json
{"especie":"colibrí","fecha":"2026-09-29","id":1,"lugar":"Parque Arví","observador":"Ana"}
```

**Registrar con datos faltantes** → `400`

```bash
curl -i -X POST http://localhost:5000/avistamientos \
  -H "Content-Type: application/json" \
  -d '{"especie":"colibrí"}'
```

```json
{"errores":["fecha: debe tener formato AAAA-MM-DD","lugar: no puede estar vacío","observador: no puede estar vacío"]}
```

**Listar todos** → `200`

```bash
curl -i http://localhost:5000/avistamientos
```

**Ver uno** → `200` (o `404` si no existe)

```bash
curl -i http://localhost:5000/avistamientos/1
```

**Actualizar** → `200` (o `404` si no existe)

```bash
curl -i -X PUT http://localhost:5000/avistamientos/1 \
  -H "Content-Type: application/json" \
  -d '{"especie":"tucán","lugar":"Jardín Botánico","fecha":"2026-09-30","observador":"Ana"}'
```

**Eliminar** → `204` (o `404` si no existe)

```bash
curl -i -X DELETE http://localhost:5000/avistamientos/1
```

**Resumen por especie (bonus)** → `200`

```bash
curl -i http://localhost:5000/avistamientos/resumen
```

```json
[{"cantidad":2,"especie":"colibrí"},{"cantidad":1,"especie":"tucán"}]
```

## Pruebas

28 pruebas con `pytest`, en la carpeta `tests/`:

- `tests/test_validador.py`: **pruebas unitarias** de la regla de negocio (partición de equivalencia y valores límite), con el stub `RelojFijo` para fijar "hoy".
- `tests/test_api.py`: **pruebas de integración** de los endpoints por HTTP (`test_client` de Flask) con una base SQLite temporal y nueva para cada prueba.
- `tests/dobles.py`: dobles de prueba (`RelojFijo`).

Con el entorno virtual activado:

**Correr las pruebas**

```bash
python -m pytest -v
```

**Generar la cobertura** (líneas y ramas)

```bash
python -m pytest --cov=app --cov=db --cov=validador --cov-branch --cov-report=term-missing
```

Para un reporte HTML navegable, agreguen `--cov-report=html` y abran `htmlcov/index.html`.

La justificación de las pruebas está en [docs/justificacion-pruebas.md](docs/justificacion-pruebas.md).

## Estructura

```
app.py                       # Rutas de la API
validador.py                 # Regla de negocio (ValidadorDeAvistamiento) y reloj del sistema
db.py                        # Conexión y creación de la tabla en SQLite
tests/test_validador.py      # Pruebas unitarias
tests/test_api.py            # Pruebas de integración
tests/dobles.py              # Dobles de prueba
docs/justificacion-pruebas.md  # Documento de justificación
docs/cobertura.txt           # Último reporte de cobertura
pruebas.http                 # Peticiones de ejemplo para REST Client (VS Code)
requirements.txt             # Dependencias (Flask, pytest, pytest-cov)
```

## Uso de IA y créditos

- Se usó **Claude** (Anthropic), modelo **Claude Opus 5.5**, como apoyo para escribir el código, las pruebas, este README y el documento de justificación. Revisé y entiendo todo el código publicado.
- Librerías: [Flask](https://flask.palletsprojects.com/) y [pytest](https://docs.pytest.org/).
