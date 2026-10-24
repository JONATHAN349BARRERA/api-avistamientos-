"""Pruebas unitarias de ValidadorDeAvistamiento: la regla de negocio, sin API ni base de datos.

Los casos salen de la tabla de docs/justificacion-pruebas.md (partición de equivalencia
y valores límite). "Hoy" lo fija el stub RelojFijo en 2026-10-21.
"""
from unittest.mock import Mock

from dobles import RelojFijo
from validador import ValidadorDeAvistamiento

VALIDO = {
    "especie": "colibrí",
    "lugar": "Parque Arví",
    "fecha": "2026-03-15",
    "observador": "Ana",
}


def validar_con(**cambios):
    """Valida VALIDO con algunos campos cambiados, usando el reloj fijo."""
    validador = ValidadorDeAvistamiento(reloj=RelojFijo())
    return validador.validar({**VALIDO, **cambios})


# --- Especie: particiones [0-2] inválida, [3-50] válida, [51+] inválida ---

def test_avistamiento_con_todos_los_campos_correctos_es_valido():
    # Arrange
    validador = ValidadorDeAvistamiento(reloj=RelojFijo())
    # Act
    errores = validador.validar(VALIDO)
    # Assert
    assert errores == []


def test_especie_de_2_caracteres_es_rechazada():
    # Arrange
    especie = "ab"
    # Act
    errores = validar_con(especie=especie)
    # Assert
    assert errores == ["especie: debe tener entre 3 y 50 caracteres"]


def test_especie_de_3_caracteres_es_aceptada():
    # Arrange
    especie = "abc"
    # Act
    errores = validar_con(especie=especie)
    # Assert
    assert errores == []


def test_especie_de_50_caracteres_es_aceptada():
    # Arrange
    especie = "a" * 50
    # Act
    errores = validar_con(especie=especie)
    # Assert
    assert errores == []


def test_especie_de_51_caracteres_es_rechazada():
    # Arrange
    especie = "a" * 51
    # Act
    errores = validar_con(especie=especie)
    # Assert
    assert errores == ["especie: debe tener entre 3 y 50 caracteres"]


def test_especie_ausente_es_rechazada():
    # Arrange
    datos = {k: v for k, v in VALIDO.items() if k != "especie"}
    validador = ValidadorDeAvistamiento(reloj=RelojFijo())
    # Act
    errores = validador.validar(datos)
    # Assert
    assert errores == ["especie: debe tener entre 3 y 50 caracteres"]


# --- Fecha: particiones pasado/hoy válida, futuro inválida, formato incorrecto inválida ---

def test_fecha_igual_a_hoy_es_aceptada():
    # Arrange
    fecha = "2026-10-21"
    # Act
    errores = validar_con(fecha=fecha)
    # Assert
    assert errores == []


def test_fecha_de_manana_es_rechazada():
    # Arrange
    fecha = "2026-10-22"
    # Act
    errores = validar_con(fecha=fecha)
    # Assert
    assert errores == ["fecha: no puede ser posterior a hoy"]


def test_fecha_con_formato_dia_mes_anio_es_rechazada():
    # Arrange
    fecha = "21/10/2026"
    # Act
    errores = validar_con(fecha=fecha)
    # Assert
    assert errores == ["fecha: debe tener formato AAAA-MM-DD"]


def test_fecha_inexistente_en_el_calendario_es_rechazada():
    # Arrange
    fecha = "2026-02-30"
    # Act
    errores = validar_con(fecha=fecha)
    # Assert
    assert errores == ["fecha: debe tener formato AAAA-MM-DD"]


# --- Lugar y observador: vacío o solo espacios es inválido ---

def test_lugar_vacio_es_rechazado():
    # Arrange
    lugar = ""
    # Act
    errores = validar_con(lugar=lugar)
    # Assert
    assert errores == ["lugar: no puede estar vacío"]


def test_observador_con_solo_espacios_es_rechazado():
    # Arrange
    observador = "   "
    # Act
    errores = validar_con(observador=observador)
    # Assert
    assert errores == ["observador: no puede estar vacío"]


# --- Entrada que no es un objeto JSON ---

def test_cuerpo_que_no_es_diccionario_es_rechazado():
    # Arrange
    validador = ValidadorDeAvistamiento(reloj=RelojFijo())
    # Act
    errores = validador.validar(["no", "es", "objeto"])
    # Assert
    assert errores == ["El cuerpo debe ser un objeto JSON"]


# --- Interacción con el reloj (mock) ---

def test_validador_compara_la_fecha_contra_el_reloj_inyectado():
    # Arrange: un mock que finge que hoy es 2020-01-01
    reloj = Mock()
    reloj.hoy.return_value = RelojFijo().fecha.replace(year=2020, month=1, day=1)
    validador = ValidadorDeAvistamiento(reloj=reloj)
    # Act
    errores = validador.validar(VALIDO)  # fecha 2026-03-15, "futura" para ese reloj
    # Assert
    reloj.hoy.assert_called_once()
    assert errores == ["fecha: no puede ser posterior a hoy"]
