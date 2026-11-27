"""Capa de estrellas brillantes que centellean, delante del cubo de cielo (RN-20).

Las estrellas más brillantes de cada cielo (`cielo.brillantes`) no están pintadas en el
cubo: aquí se dibujan como una sola geometría de puntos, con una textura de brillo. Con
shaders (`estrellas_glsl.py`) cada una centellea con su propio ritmo, muy poco; sin ellos,
son puntos fijos.

Están a distancia fija alrededor de la cámara, en el mismo grupo de dibujo que el cubo y
sin profundidad: siempre quedan detrás de todo, como el cielo.
"""

import numpy as np
from panda3d.core import (
    ColorBlendAttrib,
    Geom,
    GeomNode,
    GeomPoints,
    GeomVertexArrayFormat,
    GeomVertexData,
    GeomVertexFormat,
    InternalName,
    NodePath,
    OmniBoundingVolume,
    TexGenAttrib,
    Texture,
    TextureStage,
    TransparencyAttrib,
)

from atalaya.presentacion.escena import cielo
from atalaya.presentacion.escena.sombreado import Sombreado

#: Estrellas de la capa en cada cielo.
NUMERO = 1500
#: Distancia de los puntos a la cámara (dentro del cubo de cielo, de lado 20).
_DISTANCIA = 9.0
#: Lado de cada punto en píxeles; el brillo de la estrella decide cuánto se llena.
_TAMANO = 6.0
#: Orden de dibujo dentro del grupo `background`: justo después del cubo (0).
_ORDEN = 1


class CapaEstrellas:
    """Estrellas brillantes del fondo actual; las de otros fondos se crean al pedirlas."""

    def __init__(self, padre: NodePath, brillo: Texture, sombreado: Sombreado | None) -> None:
        self._raiz = padre.attach_new_node("estrellas")
        self._raiz.set_bin("background", _ORDEN)
        self._raiz.set_depth_test(False)
        self._raiz.set_depth_write(False)
        self._raiz.set_light_off()
        self._raiz.set_texture(brillo)
        self._raiz.set_tex_gen(TextureStage.get_default(), TexGenAttrib.M_point_sprite)
        self._raiz.set_render_mode_thickness(_TAMANO)
        self._raiz.set_attrib(
            ColorBlendAttrib.make(
                ColorBlendAttrib.M_add, ColorBlendAttrib.O_incoming_alpha, ColorBlendAttrib.O_one
            )
        )
        self._raiz.set_transparency(TransparencyAttrib.M_alpha)
        programa = None if sombreado is None else sombreado.programa("estrellas")
        if programa is not None:
            self._raiz.set_shader(programa)
        self._raiz.set_shader_input("tiempo", 0.0)
        self._capas: dict[int, NodePath] = {}
        self._actual: int | None = None
        self._tiempo = 0.0

    @property
    def actual(self) -> int | None:
        return self._actual

    def mostrar(self, indice: int) -> None:
        """Muestra las estrellas del cielo `indice` en lugar de las del actual."""
        if indice == self._actual:
            return
        if indice not in self._capas:
            self._capas[indice] = self._raiz.attach_new_node(_puntos(indice))
        if self._actual is not None:
            self._capas[self._actual].stash()
        self._capas[indice].unstash()
        self._actual = indice

    def avanzar(self, dt: float) -> None:
        """Hace avanzar el centelleo."""
        self._tiempo += dt
        self._raiz.set_shader_input("tiempo", self._tiempo)


def _puntos(indice: int) -> GeomNode:
    """Una geometría de puntos con las estrellas brillantes del cielo `indice`.

    Cada punto lleva su color ya multiplicado por su brillo y, en la columna `fase`, el
    momento y el ritmo de su centelleo.
    """
    direcciones, colores, brillo = cielo.brillantes(indice, NUMERO)
    azar = np.random.default_rng(indice)
    fase = np.stack([azar.uniform(0, 2 * np.pi, NUMERO), azar.uniform(0.6, 2.2, NUMERO)], -1)
    filas = np.concatenate(
        [
            direcciones * _DISTANCIA,
            colores * brillo[:, None],
            np.ones((NUMERO, 1)),
            fase,
        ],
        axis=1,
    ).astype(np.float32)
    datos = GeomVertexData("estrellas", _formato(), Geom.UH_static)
    datos.unclean_set_num_rows(NUMERO)
    memoryview(datos.modify_array(0)).cast("B")[:] = filas.tobytes()
    puntos = GeomPoints(Geom.UH_static)
    puntos.add_consecutive_vertices(0, NUMERO)
    geom = Geom(datos)
    geom.add_primitive(puntos)
    nodo = GeomNode(f"estrellas-{indice}")
    nodo.add_geom(geom)
    nodo.set_bounds(OmniBoundingVolume())
    nodo.set_final(True)
    return nodo


_formatos: dict[str, GeomVertexFormat] = {}


def _formato() -> GeomVertexFormat:
    """Posición, color RGBA y fase del centelleo (momento y ritmo), en float32."""
    if "estrellas" not in _formatos:
        columnas = GeomVertexArrayFormat()
        columnas.add_column(InternalName.get_vertex(), 3, Geom.NT_float32, Geom.C_point)
        columnas.add_column(InternalName.get_color(), 4, Geom.NT_float32, Geom.C_color)
        columnas.add_column(InternalName.make("fase"), 2, Geom.NT_float32, Geom.C_other)
        _formatos["estrellas"] = GeomVertexFormat.register_format(GeomVertexFormat(columnas))
    return _formatos["estrellas"]
