"""Dobles de prueba compartidos por las pruebas unitarias y de integración."""
from datetime import date

HOY = date(2026, 10, 21)


class RelojFijo:
    """Stub del reloj: siempre responde la misma fecha, sin importar el día real."""

    def __init__(self, fecha=HOY):
        self.fecha = fecha

    def hoy(self):
        return self.fecha
