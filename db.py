"""Acceso a la base de datos SQLite (módulo sqlite3 de la librería estándar)."""
import sqlite3

from flask import current_app, g


def get_db():
    """Devuelve la conexión de la petición actual (una por petición)."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row  # filas accesibles como diccionario
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(path):
    """Crea la tabla si no existe."""
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS avistamientos (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                especie    TEXT NOT NULL,
                lugar      TEXT NOT NULL,
                fecha      TEXT NOT NULL,
                observador TEXT NOT NULL
            )
            """
        )
