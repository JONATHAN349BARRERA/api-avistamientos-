"""Pruebas de integración: cada test usa una base de datos SQLite temporal."""
import pytest

from app import create_app

EJEMPLO = {
    "especie": "colibrí",
    "lugar": "Parque Arví",
    "fecha": "2026-09-29",
    "observador": "Ana",
}


@pytest.fixture
def client(tmp_path):
    app = create_app(str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    return app.test_client()


def crear(client, datos=EJEMPLO):
    return client.post("/avistamientos", json=datos)


def test_listar_vacio(client):
    r = client.get("/avistamientos")
    assert r.status_code == 200
    assert r.get_json() == []


def test_crear_devuelve_201_con_id(client):
    r = crear(client)
    assert r.status_code == 201
    cuerpo = r.get_json()
    assert cuerpo["id"] == 1
    assert cuerpo["especie"] == "colibrí"
    assert r.headers["Location"] == "/avistamientos/1"


def test_crear_sin_datos_devuelve_400(client):
    r = client.post("/avistamientos", json={"especie": "colibrí"})
    assert r.status_code == 400
    assert len(r.get_json()["errores"]) == 3


def test_crear_sin_json_devuelve_400(client):
    r = client.post("/avistamientos", data="no es json")
    assert r.status_code == 400


def test_crear_fecha_invalida_devuelve_400(client):
    r = crear(client, {**EJEMPLO, "fecha": "29/09/2026"})
    assert r.status_code == 400


def test_ver_existente_y_listar(client):
    crear(client)
    r = client.get("/avistamientos/1")
    assert r.status_code == 200
    assert r.get_json()["lugar"] == "Parque Arví"
    assert len(client.get("/avistamientos").get_json()) == 1


def test_ver_inexistente_devuelve_404(client):
    assert client.get("/avistamientos/99").status_code == 404


def test_actualizar(client):
    crear(client)
    r = client.put("/avistamientos/1", json={**EJEMPLO, "especie": "tucán"})
    assert r.status_code == 200
    assert r.get_json()["especie"] == "tucán"
    assert client.get("/avistamientos/1").get_json()["especie"] == "tucán"


def test_actualizar_inexistente_devuelve_404(client):
    assert client.put("/avistamientos/99", json=EJEMPLO).status_code == 404


def test_actualizar_datos_incompletos_devuelve_400(client):
    crear(client)
    assert client.put("/avistamientos/1", json={"especie": "tucán"}).status_code == 400


def test_eliminar(client):
    crear(client)
    assert client.delete("/avistamientos/1").status_code == 204
    assert client.get("/avistamientos/1").status_code == 404


def test_eliminar_inexistente_devuelve_404(client):
    assert client.delete("/avistamientos/99").status_code == 404


def test_resumen_por_especie(client):
    crear(client)
    crear(client)
    crear(client, {**EJEMPLO, "especie": "tucán"})
    r = client.get("/avistamientos/resumen")
    assert r.status_code == 200
    assert r.get_json() == [
        {"especie": "colibrí", "cantidad": 2},
        {"especie": "tucán", "cantidad": 1},
    ]
