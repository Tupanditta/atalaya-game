"""Pruebas de las estrellas: color por temperatura y capa de las que centellean (RN-20)."""

import numpy as np
from panda3d.core import NodePath, Shader

from atalaya.presentacion.escena import cielo
from atalaya.presentacion.escena.efectos import textura_brillo
from atalaya.presentacion.escena.estrellas import NUMERO, CapaEstrellas
from atalaya.presentacion.escena.sombreado import PROGRAMAS, Sombreado


class _SombreadoFalso(Sombreado):
    def __init__(self) -> None:
        super().__init__(None)

    def programa(self, nombre: str) -> Shader | None:
        return Shader.make(Shader.SL_GLSL, *PROGRAMAS[nombre])


def test_color_por_temperatura() -> None:
    """Las frías, rojizas; las calientes, azuladas; el Sol, casi blanco."""
    fria, sol, caliente = cielo.color_temperatura(np.array([3000.0, 5800.0, 20000.0]))
    assert fria[0] > fria[2] + 0.2
    assert caliente[2] > caliente[0] + 0.1
    assert sol.min() > 0.85
    for color in (fria, sol, caliente):
        assert color.max() == 1.0


def test_cielos_con_estrellas_de_varios_colores() -> None:
    """En un cielo cálido hay de todo, con más anaranjadas que azuladas."""
    colores = cielo.colores_estrellas(np.random.default_rng(1), 5200.0, 5000)
    rojizas = (colores[:, 0] - colores[:, 2] > 0.15).mean()
    azuladas = (colores[:, 2] - colores[:, 0] > 0.05).mean()
    assert rojizas > azuladas > 0.02


def test_brillantes_siempre_iguales() -> None:
    for indice in range(1, 6):
        d1, c1, b1 = cielo.brillantes(indice, 200)
        d2, c2, b2 = cielo.brillantes(indice, 200)
        assert np.array_equal(d1, d2)
        assert np.array_equal(c1, c2)
        assert np.array_equal(b1, b2)
        assert np.allclose(np.linalg.norm(d1, axis=1), 1.0, atol=1e-5)
        assert 0.5 <= b1.min() <= b1.max() <= 1.0
    assert not np.array_equal(cielo.brillantes(1, 200)[0], cielo.brillantes(2, 200)[0])


def test_capa_sin_shaders_con_todas_las_estrellas() -> None:
    """Sin GLSL las estrellas brillantes se ven igual, como puntos fijos."""
    raiz = NodePath("espacio")
    capa = CapaEstrellas(raiz, textura_brillo(8), Sombreado(None))
    capa.mostrar(1)
    nodo = raiz.find("**/estrellas-1")
    assert nodo.node().get_geom(0).get_vertex_data().get_num_rows() == NUMERO
    assert raiz.find("estrellas").get_shader() is None
    assert raiz.find("estrellas").get_bin_name() == "background"


def test_capa_cambia_con_el_fondo() -> None:
    raiz = NodePath("espacio")
    capa = CapaEstrellas(raiz, textura_brillo(8), _SombreadoFalso())
    assert raiz.find("estrellas").get_shader() is not None
    capa.mostrar(2)
    capa.mostrar(4)
    assert capa.actual == 4
    assert raiz.find("**/estrellas-2").is_empty()
    assert not raiz.find("**/estrellas-4").is_empty()
    capa.avanzar(0.5)
    assert raiz.find("estrellas").get_shader_input("tiempo").get_vector()[0] == 0.5
