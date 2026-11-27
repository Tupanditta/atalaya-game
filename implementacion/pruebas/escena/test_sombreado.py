"""Pruebas de los shaders del paisaje y de su respaldo sin GLSL (`sombreado.py`).

Las que compilan de verdad abren una ventana fuera de pantalla; si el equipo no tiene
GLSL (sin controlador, escritorio remoto), se omiten.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from panda3d.core import GraphicsStateGuardianBase, Vec3, load_prc_file_data

from atalaya.presentacion.escena import fondo, planetas
from atalaya.presentacion.escena.efectos import textura_brillo
from atalaya.presentacion.escena.estrellas import CapaEstrellas
from atalaya.presentacion.escena.paisaje import Paisaje
from atalaya.presentacion.escena.sol import Deslumbramiento
from atalaya.presentacion.escena.sombreado import PROGRAMAS, Sombreado

_VERTICE = """
#version 130
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
void main() { gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex; }
"""
_FRAGMENTO = """
#version 130
out vec4 color;
void main() { color = vec4(1.0); }
"""


@pytest.fixture(scope="module")
def base() -> Iterator[Any]:
    load_prc_file_data("pruebas-sombreado", "window-type offscreen\nwin-size 32 32")
    from direct.showbase.ShowBase import ShowBase

    try:
        base = ShowBase()
    except Exception:
        pytest.skip("no se puede abrir una ventana fuera de pantalla")
    if base.win is None or not base.win.get_gsg().get_supports_glsl():
        base.destroy()
        pytest.skip("el equipo no tiene GLSL")
    yield base
    base.destroy()


@pytest.fixture(scope="module")
def gsg(base: Any) -> GraphicsStateGuardianBase:
    return base.win.get_gsg()


def test_sin_tarjeta_grafica_ningun_programa() -> None:
    """Sin GSG (pruebas, servidores) todo se dibuja como antes de los shaders."""
    sombreado = Sombreado(None)
    assert not sombreado.activo
    for nombre in PROGRAMAS:
        assert sombreado.programa(nombre) is None
    assert sombreado.programa("no-existe") is None


def test_un_programa_roto_no_se_usa(gsg: GraphicsStateGuardianBase) -> None:
    """Un error de compilación no cierra el juego: ese programa queda sin usar."""
    roto = _FRAGMENTO.replace("vec4(1.0)", "vec4(no_declarada)")
    sombreado = Sombreado(gsg, {"bueno": (_VERTICE, _FRAGMENTO), "roto": (_VERTICE, roto)})
    assert sombreado.activo
    assert sombreado.programa("bueno") is not None
    assert sombreado.programa("roto") is None


def test_los_programas_del_juego_compilan(gsg: GraphicsStateGuardianBase) -> None:
    sombreado = Sombreado(gsg)
    for nombre in PROGRAMAS:
        assert sombreado.programa(nombre) is not None, nombre


def test_se_dibuja_todo_con_los_shaders(base: Any) -> None:
    """Los cinco paisajes, las estrellas, el sol y las muestras se dibujan sin errores.

    A un shader al que le falta una entrada, el motor le responde con una excepción al
    dibujar: esta prueba la detecta antes que el jugador.
    """
    sombreado = Sombreado(base.win.get_gsg())
    espacio = base.render.attach_new_node("espacio")
    brillo = textura_brillo(8)
    paisaje = Paisaje(espacio, brillo, sombreado)
    estrellas = CapaEstrellas(espacio, brillo, sombreado)
    deslumbramiento = Deslumbramiento(espacio, base.render2d, sombreado)
    assert paisaje.muestras(Vec3(0, 50, 0))
    muestra_sol = deslumbramiento.muestra()
    assert muestra_sol is not None
    try:
        # Las muestras están delante, como en el menú al calentar.
        base.camera.look_at(Vec3(0, 1, 0))
        base.graphicsEngine.render_frame()
        for indice in range(1, 6):
            texturas = [fondo.texturas_motor(t) for t in planetas.generar_texturas(indice, 16)]
            paisaje.mostrar(indice, texturas)
            estrellas.mostrar(indice)
            deslumbramiento.mostrar(indice)
            for planeta in planetas.PAISAJES[indice - 1].planetas:
                base.camera.look_at(Vec3(*planeta.direccion))
                paisaje.avanzar(0.1)
                estrellas.avanzar(0.1)
                deslumbramiento.avanzar(0.1, base.camera, base.camLens, 1.0)
                base.graphicsEngine.render_frame()
    finally:
        espacio.remove_node()
        base.render2d.find("destellos").remove_node()
