"""Pruebas de integración: la API completa por HTTP (test_client de Flask) con SQLite real.

Cada prueba recibe una base de datos nueva en una carpeta temporal (fixture tmp_path),
así que ninguna depende de otra ni del orden en que se ejecuten.
"""
import pytest

from app import create_app
from dobles import RelojFijo

EJEMPLO = {
    "especie": "colibrí",
    "lugar": "Parque Arví",
    "fecha": "2026-09-29",
    "observador": "Ana",
}


@pytest.fixture
def client(tmp_path):
    app = create_app(str(tmp_path / "test.db"), reloj=RelojFijo())
    app.config["TESTING"] = True
    return app.test_client()


def crear(client, datos=EJEMPLO):
    return client.post("/avistamientos", json=datos)


# --- GET /avistamientos ---

def test_listar_sin_avistamientos_devuelve_200_y_lista_vacia(client):
    # Act
    r = client.get("/avistamientos")
    # Assert
    assert r.status_code == 200
    assert r.get_json() == []


def test_listar_devuelve_los_avistamientos_registrados(client):
    # Arrange
    crear(client)
    crear(client, {**EJEMPLO, "especie": "tucán"})
    # Act
    r = client.get("/avistamientos")
    # Assert
    assert r.status_code == 200
    assert [a["especie"] for a in r.get_json()] == ["colibrí", "tucán"]


# --- POST /avistamientos ---

def test_crear_valido_devuelve_201_con_el_recurso_y_queda_guardado(client):
    # Act
    r = crear(client)
    # Assert: respuesta completa
    assert r.status_code == 201
    assert r.get_json() == {"id": 1, **EJEMPLO}
    assert r.headers["Location"] == "/avistamientos/1"
    # Assert: efecto, el nuevo id se puede consultar
    assert client.get("/avistamientos/1").get_json() == {"id": 1, **EJEMPLO}


def test_crear_con_especie_corta_devuelve_400_indicando_el_campo_y_no_guarda(client):
    # Act
    r = crear(client, {**EJEMPLO, "especie": "ab"})
    # Assert
    assert r.status_code == 400
    assert r.get_json() == {"errores": ["especie: debe tener entre 3 y 50 caracteres"]}
    assert client.get("/avistamientos").get_json() == []


def test_crear_con_fecha_futura_devuelve_400(client):
    # Act
    r = crear(client, {**EJEMPLO, "fecha": "2026-10-22"})
    # Assert
    assert r.status_code == 400
    assert r.get_json() == {"errores": ["fecha: no puede ser posterior a hoy"]}


def test_crear_sin_cuerpo_json_devuelve_400(client):
    # Act
    r = client.post("/avistamientos", data="no es json")
    # Assert
    assert r.status_code == 400
    assert r.get_json() == {"errores": ["El cuerpo debe ser un objeto JSON"]}


# --- GET /avistamientos/{id} ---

def test_ver_existente_devuelve_200_con_sus_datos(client):
    # Arrange
    crear(client)
    # Act
    r = client.get("/avistamientos/1")
    # Assert
    assert r.status_code == 200
    assert r.get_json() == {"id": 1, **EJEMPLO}


def test_ver_inexistente_devuelve_404_con_mensaje(client):
    # Act
    r = client.get("/avistamientos/99")
    # Assert
    assert r.status_code == 404
    assert r.get_json() == {"error": "Avistamiento no encontrado"}


# --- PUT /avistamientos/{id} ---

def test_actualizar_existente_devuelve_200_y_persiste_el_cambio(client):
    # Arrange
    crear(client)
    cambios = {**EJEMPLO, "especie": "tucán", "lugar": "Jardín Botánico"}
    # Act
    r = client.put("/avistamientos/1", json=cambios)
    # Assert
    assert r.status_code == 200
    assert r.get_json() == {"id": 1, **cambios}
    assert client.get("/avistamientos/1").get_json()["especie"] == "tucán"


def test_actualizar_inexistente_devuelve_404(client):
    # Act
    r = client.put("/avistamientos/99", json=EJEMPLO)
    # Assert
    assert r.status_code == 404
    assert r.get_json() == {"error": "Avistamiento no encontrado"}


def test_actualizar_con_datos_invalidos_devuelve_400_y_no_modifica(client):
    # Arrange
    crear(client)
    # Act
    r = client.put("/avistamientos/1", json={**EJEMPLO, "observador": ""})
    # Assert
    assert r.status_code == 400
    assert r.get_json() == {"errores": ["observador: no puede estar vacío"]}
    assert client.get("/avistamientos/1").get_json()["observador"] == "Ana"


# --- DELETE /avistamientos/{id} ---

def test_eliminar_existente_devuelve_204_y_despues_get_da_404(client):
    # Arrange
    crear(client)
    # Act
    r = client.delete("/avistamientos/1")
    # Assert
    assert r.status_code == 204
    assert client.get("/avistamientos/1").status_code == 404


def test_eliminar_inexistente_devuelve_404(client):
    # Act
    r = client.delete("/avistamientos/99")
    # Assert
    assert r.status_code == 404
    assert r.get_json() == {"error": "Avistamiento no encontrado"}


# --- GET /avistamientos/resumen (bonus) ---

def test_resumen_cuenta_avistamientos_por_especie(client):
    # Arrange
    crear(client)
    crear(client)
    crear(client, {**EJEMPLO, "especie": "tucán"})
    # Act
    r = client.get("/avistamientos/resumen")
    # Assert
    assert r.status_code == 200
    assert r.get_json() == [
        {"especie": "colibrí", "cantidad": 2},
        {"especie": "tucán", "cantidad": 1},
    ]
