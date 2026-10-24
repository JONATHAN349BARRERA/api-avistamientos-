"""Regla de negocio del avistamiento, separada de la API."""
from datetime import date, datetime


class RelojDelSistema:
    """Reloj real: devuelve la fecha de hoy de la computadora."""

    def hoy(self):
        return date.today()


class ValidadorDeAvistamiento:
    def __init__(self, reloj=None):
        # Si no me dan un reloj, uso el real. En las pruebas le paso uno fijo.
        self.reloj = reloj or RelojDelSistema()

    def validar(self, datos):
        """Devuelve la lista de errores. Si está vacía, el avistamiento es válido."""
        if not isinstance(datos, dict):
            return ["El cuerpo debe ser un objeto JSON"]

        errores = []

        especie = datos.get("especie")
        if not isinstance(especie, str) or not 3 <= len(especie.strip()) <= 50:
            errores.append("especie: debe tener entre 3 y 50 caracteres")

        fecha = datos.get("fecha")
        try:
            fecha_obs = datetime.strptime(fecha, "%Y-%m-%d").date()
            if fecha_obs > self.reloj.hoy():
                errores.append("fecha: no puede ser posterior a hoy")
        except (TypeError, ValueError):
            errores.append("fecha: debe tener formato AAAA-MM-DD")

        for campo in ("lugar", "observador"):
            valor = datos.get(campo)
            if not isinstance(valor, str) or not valor.strip():
                errores.append(f"{campo}: no puede estar vacío")

        return errores
    