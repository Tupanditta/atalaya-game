"""Pruebas de las operaciones con vectores del núcleo."""

import pytest

from atalaya.logica.nucleo.dominio import Vector3
from atalaya.logica.nucleo.vectores import (
    angulo_entre,
    girar_hacia,
    limitar,
    norma,
    normalizar,
    perpendiculares,
    producto_escalar,
    producto_vectorial,
)


def test_operaciones_basicas() -> None:
    """Producto vectorial, normalización y recorte de longitud."""
    assert producto_vectorial((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)) == (0.0, 0.0, 1.0)
    assert normalizar((3.0, 0.0, 4.0)) == pytest.approx((0.6, 0.0, 0.8))
    assert limitar((3.0, 0.0, 4.0), 10) == (3.0, 0.0, 4.0)
    assert limitar((3.0, 0.0, 4.0), 1) == pytest.approx((0.6, 0.0, 0.8))
    with pytest.raises(ValueError, match="nulo"):
        normalizar((0.0, 0.0, 0.0))


@pytest.mark.parametrize(
    "d",
    [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0), normalizar((1.0, -2.0, 3.0))],
)
def test_perpendiculares(d: Vector3) -> None:
    """Los dos vectores son de longitud 1 y perpendiculares entre sí y a `d`."""
    e1, e2 = perpendiculares(d)
    assert norma(e1) == pytest.approx(1)
    assert norma(e2) == pytest.approx(1)
    for a, b in ((d, e1), (d, e2), (e1, e2)):
        assert producto_escalar(a, b) == pytest.approx(0, abs=1e-12)


def test_girar_hacia() -> None:
    """La dirección girada forma el ángulo pedido con la original."""
    d = normalizar((1.0, 2.0, -0.5))
    for azimut in (0.0, 90.0, 200.0):
        girada = girar_hacia(d, 25.0, azimut)
        assert norma(girada) == pytest.approx(1)
        assert angulo_entre(d, girada) == pytest.approx(25.0)
