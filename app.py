"""API REST para el registro de avistamientos de aves."""
from datetime import datetime
import os

from flask import Flask, jsonify, request

from db import close_db, get_db, init_db

CAMPOS = ("especie", "lugar", "fecha", "observador")


def validar(datos):
    """Devuelve una lista de errores; vacía si los datos son válidos."""
    if not isinstance(datos, dict):
        return ["El cuerpo debe ser un objeto JSON"]

    errores = []
    for campo in CAMPOS:
        valor = datos.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            errores.append(f"Falta el campo '{campo}' o está vacío")

    fecha = datos.get("fecha")
    if isinstance(fecha, str) and fecha.strip():
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            errores.append("El campo 'fecha' debe tener formato AAAA-MM-DD")
    return errores


def a_dict(fila):
    return dict(fila)


def create_app(database=None):
    app = Flask(__name__)
    app.json.ensure_ascii = False  # para que "colibrí" salga con tilde
    app.config["DATABASE"] = database or os.environ.get(
        "DATABASE", "avistamientos.db"
    )
    init_db(app.config["DATABASE"])
    app.teardown_appcontext(close_db)

    @app.get("/avistamientos")
    def listar():
        filas = get_db().execute("SELECT * FROM avistamientos ORDER BY id").fetchall()
        return jsonify([a_dict(f) for f in filas]), 200

    # Bonus. Va antes de /<id> por claridad; además <int:id> no acepta "resumen".
    @app.get("/avistamientos/resumen")
    def resumen():
        filas = get_db().execute(
            "SELECT especie, COUNT(*) AS cantidad FROM avistamientos "
            "GROUP BY especie ORDER BY cantidad DESC, especie"
        ).fetchall()
        return jsonify([a_dict(f) for f in filas]), 200

    @app.get("/avistamientos/<int:id>")
    def ver(id):
        fila = get_db().execute(
            "SELECT * FROM avistamientos WHERE id = ?", (id,)
        ).fetchone()
        if fila is None:
            return jsonify(error="Avistamiento no encontrado"), 404
        return jsonify(a_dict(fila)), 200

    @app.post("/avistamientos")
    def crear():
        datos = request.get_json(silent=True)
        errores = validar(datos)
        if errores:
            return jsonify(errores=errores), 400

        db = get_db()
        cursor = db.execute(
            "INSERT INTO avistamientos (especie, lugar, fecha, observador) "
            "VALUES (?, ?, ?, ?)",
            tuple(datos[c].strip() for c in CAMPOS),
        )
        db.commit()
        fila = db.execute(
            "SELECT * FROM avistamientos WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        respuesta = jsonify(a_dict(fila))
        respuesta.headers["Location"] = f"/avistamientos/{cursor.lastrowid}"
        return respuesta, 201

    @app.put("/avistamientos/<int:id>")
    def actualizar(id):
        db = get_db()
        if db.execute("SELECT 1 FROM avistamientos WHERE id = ?", (id,)).fetchone() is None:
            return jsonify(error="Avistamiento no encontrado"), 404

        datos = request.get_json(silent=True)
        errores = validar(datos)
        if errores:
            return jsonify(errores=errores), 400

        db.execute(
            "UPDATE avistamientos SET especie = ?, lugar = ?, fecha = ?, observador = ? "
            "WHERE id = ?",
            (*(datos[c].strip() for c in CAMPOS), id),
        )
        db.commit()
        fila = db.execute("SELECT * FROM avistamientos WHERE id = ?", (id,)).fetchone()
        return jsonify(a_dict(fila)), 200

    @app.delete("/avistamientos/<int:id>")
    def eliminar(id):
        db = get_db()
        cursor = db.execute("DELETE FROM avistamientos WHERE id = ?", (id,))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify(error="Avistamiento no encontrado"), 404
        return "", 204

    # Errores genéricos también en JSON (ej. rutas inexistentes).
    @app.errorhandler(404)
    def no_encontrado(_e):
        return jsonify(error="Recurso no encontrado"), 404

    @app.errorhandler(405)
    def metodo_no_permitido(_e):
        return jsonify(error="Método no permitido"), 405

    return app


if __name__ == "__main__":
    create_app().run(port=int(os.environ.get("PORT", 5000)), debug=True)
