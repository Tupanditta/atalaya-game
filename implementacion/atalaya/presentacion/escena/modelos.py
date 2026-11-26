"""Modelos de los enemigos, generados por código (`design.md`, sección 6; RES-03).

Pocos polígonos: un cuerpo oscuro y aristas luminosas del color de su tipo, como en
`interfaz/03-oleada.svg`. Cada tipo tiene su forma y el tamaño del modelo coincide con
la zona de impacto de su tamaño.
"""

import math

from panda3d.core import (
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    LineSegs,
    NodePath,
    Vec3,
)

from atalaya.logica.nucleo.dominio import TipoEnemigo

#: Colores de `interfaz/interfaz.md`, sección 3, en RGB de 0 a 1.
COLOR_TIPO: dict[TipoEnemigo, tuple[float, float, float]] = {
    TipoEnemigo.SIN_EFECTO: (1.0, 0x4D / 255, 0x5E / 255),
    TipoEnemigo.DESESTABILIZADOR: (1.0, 0xD2 / 255, 0x3F / 255),
    TipoEnemigo.ATURDIDOR: (0xB3 / 255, 0x6B / 255, 1.0),
}

#: Color del cuerpo de los enemigos.
_COLOR_CUERPO = (0x1B / 255, 0x22 / 255, 0x33 / 255, 1.0)

#: Vértices, caras y aristas luminosas de un modelo.
_Forma = tuple[list[tuple[float, float, float]], list[tuple[int, int, int]], list[tuple[int, int]]]

# Ejes del modelo: x a la derecha, y hacia delante (sentido de la marcha), z arriba.
# Vista de frente, cada forma recuerda al símbolo de su tipo en el radar
# (`interfaz.md`, «Radar»), para distinguirlos por forma y no solo por color.

#: Sin efecto especial: bipirámide alargada en horizontal, el rombo de la maqueta.
_SIN_EFECTO: _Forma = (
    [
        (1.0, 0.0, 0.0),
        (-1.0, 0.0, 0.0),
        (0.0, 0.0, 0.72),
        (0.0, 0.0, -0.72),
        (0.0, 0.9, 0.0),
        (0.0, -0.55, 0.0),
    ],
    [(4, 0, 2), (4, 2, 1), (4, 1, 3), (4, 3, 0), (5, 2, 0), (5, 1, 2), (5, 3, 1), (5, 0, 3)],
    [(0, 2), (2, 1), (1, 3), (3, 0), (4, 0), (4, 1), (4, 2), (4, 3), (5, 0), (5, 1)],
)

#: Desestabilizador: bipirámide de base triangular, con un vértice arriba: el triángulo.
_DESESTABILIZADOR: _Forma = (
    [(0.0, 0.0, 1.0), (0.95, 0.0, -0.6), (-0.95, 0.0, -0.6), (0.0, 1.0, 0.0), (0.0, -0.7, 0.0)],
    [(3, 0, 1), (3, 1, 2), (3, 2, 0), (4, 1, 0), (4, 2, 1), (4, 0, 2)],
    [(0, 1), (1, 2), (2, 0), (3, 0), (3, 1), (3, 2), (4, 0), (4, 1), (4, 2)],
)

#: Aturdidor: octaedro regular, un rombo igual de alto que de ancho, con un anillo.
_ATURDIDOR: _Forma = (
    [
        (0.85, 0.0, 0.0),
        (-0.85, 0.0, 0.0),
        (0.0, 0.0, 0.85),
        (0.0, 0.0, -0.85),
        (0.0, 0.85, 0.0),
        (0.0, -0.85, 0.0),
    ],
    [(4, 0, 2), (4, 2, 1), (4, 1, 3), (4, 3, 0), (5, 2, 0), (5, 1, 2), (5, 3, 1), (5, 0, 3)],
    [
        (0, 2),
        (2, 1),
        (1, 3),
        (3, 0),
        (4, 0),
        (4, 1),
        (4, 2),
        (4, 3),
        (5, 0),
        (5, 1),
        (5, 2),
        (5, 3),
    ],
)

_FORMAS: dict[TipoEnemigo, _Forma] = {
    TipoEnemigo.SIN_EFECTO: _SIN_EFECTO,
    TipoEnemigo.DESESTABILIZADOR: _DESESTABILIZADOR,
    TipoEnemigo.ATURDIDOR: _ATURDIDOR,
}

#: Radio del anillo del aturdidor, en radios del modelo, y sus lados.
_RADIO_ANILLO = 1.0
_LADOS_ANILLO = 32


def modelo_enemigo(tipo: TipoEnemigo, radio: float) -> NodePath:
    """Modelo de un enemigo de `tipo` cuyo tamaño exterior es `radio`.

    La forma y el color de las aristas dependen del tipo; la escala, del tamaño.
    """
    vertices, caras, aristas_forma = _FORMAS[tipo]
    raiz = NodePath(f"enemigo-{tipo.value}")
    cuerpo = raiz.attach_new_node(_cuerpo(vertices, caras))
    cuerpo.set_color(*_COLOR_CUERPO)
    aristas = LineSegs("aristas")
    aristas.set_thickness(2.0)
    aristas.set_color(*COLOR_TIPO[tipo], 1.0)
    for a, b in aristas_forma:
        aristas.move_to(*vertices[a])
        aristas.draw_to(*vertices[b])
    if tipo is TipoEnemigo.ATURDIDOR:
        # Anillo alrededor del cuerpo, perpendicular a la marcha.
        for i in range(_LADOS_ANILLO + 1):
            angulo = 2 * math.pi * i / _LADOS_ANILLO
            punto = (_RADIO_ANILLO * math.cos(angulo), 0.0, _RADIO_ANILLO * math.sin(angulo))
            if i == 0:
                aristas.move_to(*punto)
            else:
                aristas.draw_to(*punto)
    lineas = raiz.attach_new_node(aristas.create())
    lineas.set_light_off()
    # Las aristas se dibujan un poco por fuera para que el cuerpo no las tape.
    lineas.set_scale(1.01)
    raiz.set_scale(radio)
    return raiz


def _cuerpo(
    puntos: list[tuple[float, float, float]], caras: list[tuple[int, int, int]]
) -> GeomNode:
    """Caras del modelo, con una normal por cara para un sombreado plano."""
    datos = GeomVertexData("cuerpo", GeomVertexFormat.get_v3n3(), Geom.UH_static)
    vertices = GeomVertexWriter(datos, "vertex")
    normales = GeomVertexWriter(datos, "normal")
    triangulos = GeomTriangles(Geom.UH_static)
    for i, cara in enumerate(caras):
        a, b, c = (Vec3(*puntos[v]) for v in cara)
        normal = (b - a).cross(c - a).normalized()
        # Las caras se orientan hacia fuera, sea cual sea el orden en la tabla.
        if normal.dot(a + b + c) < 0:
            b, c = c, b
            normal = -normal
        for punto in (a, b, c):
            vertices.add_data3(punto)
            normales.add_data3(normal)
        triangulos.add_vertices(3 * i, 3 * i + 1, 3 * i + 2)
    geom = Geom(datos)
    geom.add_primitive(triangulos)
    nodo = GeomNode("cuerpo")
    nodo.add_geom(geom)
    return nodo
