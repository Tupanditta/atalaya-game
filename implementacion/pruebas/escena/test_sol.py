"""Pruebas del deslumbramiento del sol y de los destellos de lente (`sol.py`)."""

import pytest
from panda3d.core import NodePath, PerspectiveLens, Shader, Vec3

from atalaya.presentacion.escena import cielo, sol
from atalaya.presentacion.escena.sol import Deslumbramiento
from atalaya.presentacion.escena.sombreado import PROGRAMAS, Sombreado


class _SombreadoFalso(Sombreado):
    def __init__(self) -> None:
        super().__init__(None)

    def programa(self, nombre: str) -> Shader | None:
        return Shader.make(Shader.SL_GLSL, *PROGRAMAS[nombre])


@pytest.fixture
def escena() -> tuple[NodePath, NodePath, NodePath, PerspectiveLens]:
    render = NodePath("render")
    espacio = render.attach_new_node("espacio")
    camara = render.attach_new_node("camara")
    lente = PerspectiveLens()
    lente.set_fov(100, 70)
    return espacio, NodePath("render2d"), camara, lente


def test_solo_en_los_fondos_con_sol(
    escena: tuple[NodePath, NodePath, NodePath, PerspectiveLens],
) -> None:
    """Los fondos 2 y 5 no tienen sol: no hay deslumbramiento."""
    espacio, render2d, _, _ = escena
    deslumbramiento = Deslumbramiento(espacio, render2d, _SombreadoFalso())
    for indice in range(1, 6):
        deslumbramiento.mostrar(indice)
        assert deslumbramiento.mostrado == bool(cielo.TEMAS[indice - 1].soles)
    assert not cielo.TEMAS[1].soles
    assert not cielo.TEMAS[4].soles


def test_sin_shaders_no_hay_deslumbramiento(
    escena: tuple[NodePath, NodePath, NodePath, PerspectiveLens],
) -> None:
    espacio, render2d, camara, lente = escena
    deslumbramiento = Deslumbramiento(espacio, render2d, Sombreado(None))
    deslumbramiento.mostrar(1)
    deslumbramiento.avanzar(0.1, camara, lente, 16 / 9)
    assert not deslumbramiento.mostrado
    assert espacio.find("sol").is_hidden()
    assert render2d.find("destellos").is_hidden()


def test_destellos_solo_con_el_sol_en_pantalla(
    escena: tuple[NodePath, NodePath, NodePath, PerspectiveLens],
) -> None:
    espacio, render2d, camara, lente = escena
    deslumbramiento = Deslumbramiento(espacio, render2d, _SombreadoFalso())
    deslumbramiento.mostrar(1)
    direccion = Vec3(*cielo.TEMAS[0].soles[0].direccion)
    camara.look_at(direccion)
    deslumbramiento.avanzar(0.1, camara, lente, 16 / 9)
    assert not render2d.find("destellos").is_hidden()
    camara.look_at(-direccion)
    deslumbramiento.avanzar(0.1, camara, lente, 16 / 9)
    assert render2d.find("destellos").is_hidden()


def test_planeta_delante_del_sol() -> None:
    """La visibilidad baja a 0 si un planeta tapa el sol; sin planetas delante, es 1."""
    for indice in (1, 3, 4):
        assert 0.0 <= sol.visibilidad(indice) <= 1.0
    assert sol.visibilidad(2) == 0.0
    assert sol.visibilidad(1) == pytest.approx(1.0)


def test_muestra_para_calentar(
    escena: tuple[NodePath, NodePath, NodePath, PerspectiveLens],
) -> None:
    """La muestra lleva el shader del sol y se ve aunque el fondo no tenga sol."""
    espacio, render2d, _, _ = escena
    assert Deslumbramiento(espacio, render2d, Sombreado(None)).muestra() is None
    deslumbramiento = Deslumbramiento(espacio, render2d, _SombreadoFalso())
    deslumbramiento.mostrar(2)
    muestra = deslumbramiento.muestra()
    assert muestra is not None
    assert muestra.get_shader() is not None
    assert not muestra.is_hidden()
