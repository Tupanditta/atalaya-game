"""Primitivas 2D del HUD en coordenadas de diseño (`interfaz/interfaz.md`, sección 2).

Las coordenadas son las de las maquetas: píxeles de una pantalla de 1920 × 1080, con el
origen arriba a la izquierda y la y hacia abajo. El nodo raíz del HUD las escala a la
pantalla real. Los grosores de línea se dan en píxeles de diseño.
"""

import math
from collections.abc import Sequence
from pathlib import Path

from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    Filename,
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    LineSegs,
    NodePath,
    TextFont,
    TextNode,
    TransparencyAttrib,
)

Color = tuple[float, float, float, float]
Punto = tuple[float, float]

#: Orden de dibujo de los paneles: debajo de todo lo demás del HUD (`capa`).
ORDEN_PANEL = 0

#: Fuentes candidatas, por orden de preferencia. Rajdhani es la de `interfaz.md`; si no
#: está en `recursos/fuentes/`, se usa la alternativa de las maquetas.
_FUENTES = [
    Path(__file__).resolve().parents[3] / "recursos" / "fuentes" / "Rajdhani-SemiBold.ttf",
    Path("C:/Windows/Fonts/seguisb.ttf"),
    Path("C:/Windows/Fonts/segoeui.ttf"),
]


def color(hexadecimal: str, alfa: float = 1.0) -> Color:
    """Color de `interfaz.md` (`#RRGGBB`) con su opacidad."""
    valor = int(hexadecimal.lstrip("#"), 16)
    return ((valor >> 16) / 255, ((valor >> 8) & 0xFF) / 255, (valor & 0xFF) / 255, alfa)


def mezclar(a: Color, b: Color, t: float) -> Color:
    """Color a medio camino entre `a` (t = 0) y `b` (t = 1)."""
    return (
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t,
        a[3] + (b[3] - a[3]) * t,
    )


def cargar_fuente(base: ShowBase) -> TextFont | None:
    """Primera fuente disponible de la lista, o `None` para usar la del motor."""
    for ruta in _FUENTES:
        if ruta.is_file():
            ruta_motor = Filename.from_os_specific(str(ruta)).get_fullpath()
            fuente: TextFont = base.loader.load_font(ruta_motor)
            if fuente is not None and fuente.is_valid():
                fuente.set_pixels_per_unit(64)
                return fuente
    return None


def capa(padre: NodePath, nombre: str, orden: int) -> NodePath:
    """Nodo cuyo contenido se dibuja en el orden `orden`: los mayores, encima.

    Todo el HUD está a la misma profundidad, así que el orden de dibujo se fija aquí y no
    depende de cómo ordene el motor los objetos transparentes.
    """
    nodo = padre.attach_new_node(nombre)
    nodo.set_bin("fixed", orden)
    return nodo


def preparar(nodo: NodePath) -> NodePath:
    """Ajustes comunes de todo lo que se dibuja en el HUD."""
    nodo.set_transparency(TransparencyAttrib.M_alpha)
    nodo.set_depth_test(False)
    nodo.set_depth_write(False)
    return nodo


def poligono(padre: NodePath, puntos: Sequence[Punto], relleno: Color) -> NodePath:
    """Polígono convexo relleno."""
    datos = GeomVertexData("poligono", GeomVertexFormat.get_v3(), Geom.UH_static)
    vertices = GeomVertexWriter(datos, "vertex")
    for x, y in puntos:
        vertices.add_data3(x, 0, -y)
    triangulos = GeomTriangles(Geom.UH_static)
    for i in range(1, len(puntos) - 1):
        triangulos.add_vertices(0, i + 1, i)
    geom = Geom(datos)
    geom.add_primitive(triangulos)
    nodo = GeomNode("poligono")
    nodo.add_geom(geom)
    camino = preparar(padre.attach_new_node(nodo))
    camino.set_two_sided(True)
    camino.set_color(*relleno)
    return camino


def rectangulo(
    padre: NodePath, x: float, y: float, ancho: float, alto: float, relleno: Color
) -> NodePath:
    """Rectángulo relleno con la esquina superior izquierda en (x, y)."""
    return poligono(padre, [(x, y), (x + ancho, y), (x + ancho, y + alto), (x, y + alto)], relleno)


def linea(
    padre: NodePath, puntos: Sequence[Punto], color_linea: Color, grosor: float, escala: float
) -> NodePath:
    """Línea poligonal de `grosor` píxeles de diseño."""
    segmentos = LineSegs("linea")
    segmentos.set_thickness(max(1.0, grosor * escala))
    segmentos.set_color(*color_linea)
    segmentos.move_to(puntos[0][0], 0, -puntos[0][1])
    for x, y in puntos[1:]:
        segmentos.draw_to(x, 0, -y)
    return preparar(padre.attach_new_node(segmentos.create()))


def circulo(centro: Punto, radio: float, lados: int = 64) -> list[Punto]:
    """Puntos de una circunferencia cerrada."""
    cx, cy = centro
    return [
        (
            cx + radio * math.cos(2 * math.pi * i / lados),
            cy + radio * math.sin(2 * math.pi * i / lados),
        )
        for i in range(lados + 1)
    ]


def panel(padre: NodePath, x: float, y: float, ancho: float, alto: float, escala: float) -> None:
    """Panel con dos esquinas recortadas, arriba a la izquierda y abajo a la derecha."""
    recorte = 12
    puntos = [
        (x + recorte, y),
        (x + ancho, y),
        (x + ancho, y + alto - recorte),
        (x + ancho - recorte, y + alto),
        (x, y + alto),
        (x, y + recorte),
    ]
    poligono(padre, puntos, color("#0A1220", 0.78)).set_bin("fixed", ORDEN_PANEL)
    borde = linea(padre, [*puntos, puntos[0]], color("#2AD4FF", 0.35), 1, escala)
    borde.set_bin("fixed", ORDEN_PANEL + 1)


class Texto:
    """Texto del HUD que solo se reconstruye cuando cambia."""

    def __init__(
        self,
        padre: NodePath,
        fuente: TextFont | None,
        x: float,
        y: float,
        tamano: float,
        alineacion: int = TextNode.A_left,
        orden: int = 50,
    ) -> None:
        self._nodo = TextNode("texto")
        if fuente is not None:
            self._nodo.set_font(fuente)
        self._nodo.set_align(alineacion)
        self._camino = preparar(padre.attach_new_node(self._nodo))
        self._camino.set_bin("fixed", orden)
        # La línea base del texto queda en la y indicada, como en las maquetas SVG.
        self._camino.set_pos(x, 0, -y)
        self._camino.set_scale(tamano)
        self._texto: str | None = None
        self._color: Color | None = None

    def mostrar(self, texto: str, color_texto: Color) -> None:
        if texto != self._texto:
            self._nodo.set_text(texto)
            self._texto = texto
        if color_texto != self._color:
            self._nodo.set_text_color(*color_texto)
            self._color = color_texto

    def ocultar(self) -> None:
        self.mostrar("", self._color or (1.0, 1.0, 1.0, 1.0))
