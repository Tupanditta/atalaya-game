"""Pruebas de los cuaterniones de orientación (Sprint 1)."""

import math

import pytest

from atalaya.logica.vista import ADELANTE, ARRIBA, Cuaternion, angulo_entre, interpolar


def test_rotacion_de_un_vector() -> None:
    """Una rotación de 90° sobre z lleva el eje y al eje −x."""
    q = Cuaternion.rotacion(ARRIBA, 90)
    assert q.rotar(ADELANTE) == pytest.approx((-1.0, 0.0, 0.0), abs=1e-12)


def test_producto_aplica_primero_el_de_la_derecha() -> None:
    """`a * b` aplica `b` y después `a`."""
    a = Cuaternion.rotacion(ARRIBA, 90)
    b = Cuaternion.rotacion((1.0, 0.0, 0.0), 90)
    # b lleva y a z; a deja z como está.
    assert (a * b).rotar(ADELANTE) == pytest.approx((0.0, 0.0, 1.0), abs=1e-12)


def test_s1_t14_interpolacion_a_medio_camino() -> None:
    """S1-T14 interpolación: con factor 0,5 el resultado está a medio camino y tiene norma 1."""
    a = Cuaternion.rotacion(ARRIBA, 10)
    b = Cuaternion.rotacion((1 / math.sqrt(2), 0.0, 1 / math.sqrt(2)), 80)
    medio = interpolar(a, b, 0.5)
    total = angulo_entre(a, b)
    assert medio.norma() == pytest.approx(1.0, abs=1e-12)
    assert angulo_entre(a, medio) == pytest.approx(total / 2, abs=1e-9)
    assert angulo_entre(medio, b) == pytest.approx(total / 2, abs=1e-9)


def test_interpolacion_extremos() -> None:
    """Con factor 0 da el origen y con factor 1 da el destino."""
    a = Cuaternion.rotacion(ARRIBA, 0)
    b = Cuaternion.rotacion(ARRIBA, 120)
    assert angulo_entre(interpolar(a, b, 0.0), a) == pytest.approx(0.0, abs=1e-6)
    assert angulo_entre(interpolar(a, b, 1.0), b) == pytest.approx(0.0, abs=1e-6)


def test_interpolacion_por_el_camino_corto() -> None:
    """Si los cuaterniones tienen signos opuestos, se interpola por el camino más corto."""
    a = Cuaternion.rotacion(ARRIBA, 10)
    b = Cuaternion.rotacion(ARRIBA, 30)
    b_opuesto = Cuaternion(-b.w, -b.x, -b.y, -b.z)
    medio = interpolar(a, b_opuesto, 0.5)
    assert angulo_entre(medio, Cuaternion.rotacion(ARRIBA, 20)) == pytest.approx(0.0, abs=1e-6)


def test_interpolacion_entre_orientaciones_casi_iguales() -> None:
    """Entre orientaciones casi iguales el resultado sigue teniendo norma 1."""
    a = Cuaternion.rotacion(ARRIBA, 1.0)
    b = Cuaternion.rotacion(ARRIBA, 1.5)
    medio = interpolar(a, b, 0.5)
    assert medio.norma() == pytest.approx(1.0, abs=1e-12)
    assert angulo_entre(a, medio) == pytest.approx(0.25, abs=1e-6)
