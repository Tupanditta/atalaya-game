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
    TextProperties,
    TextPropertiesManager,
    TransparencyAttrib,
)

Color = tuple[float, float, float, float]
Punto = tuple[float, float]

#: Orden de dibujo de los paneles: debajo de todo lo demás del HUD (`capa`).
ORDEN_PANEL = 0

_CARPETA_FUENTES = Path(__file__).resolve().parents[3] / "recursos" / "fuentes"

#: Fuentes candidatas, por orden de preferencia. Rajdhani es la de `interfaz.md`; si no
#: está en `recursos/fuentes/`, se usa la alternativa de las maquetas.
_FUENTES = [
    _CARPETA_FUENTES / "Rajdhani-SemiBold.ttf",
    Path("C:/Windows/Fonts/seguisb.ttf"),
    Path("C:/Windows/Fonts/segoeui.ttf"),
]

#: Fuentes para los símbolos que Rajdhani no tiene (las flechas de las ayudas de teclas).
_FUENTES_SIMBOLOS = [
    Path("C:/Windows/Fonts/seguisym.ttf"),
    Path("C:/Windows/Fonts/segoeui.ttf"),
]
#: Símbolos que se escriben con la fuente de símbolos.
_SIMBOLOS = frozenset("↑↓←→")
#: Nombre de las propiedades de texto de los símbolos en el motor.
_PROPIEDADES_SIMBOLOS = "simbolos"
_fuente_simbolos: list[TextFont] = []

#: Fuentes de los títulos grandes: Rajdhani Bold (`interfaz.md`, «Tipografía»).
_FUENTES_TITULOS = [
    _CARPETA_FUENTES / "Rajdhani-Bold.ttf",
    Path("C:/Windows/Fonts/segoeuib.ttf"),
    *_FUENTES,
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


def cargar_fuente(base: ShowBase, titulos: bool = False) -> TextFont | None:
    """Primera fuente disponible de la lista, o `None` para usar la del motor.

    Con `titulos`, la de los títulos grandes.
    """
    _registrar_simbolos(base)
    return _primera(base, _FUENTES_TITULOS if titulos else _FUENTES)


def _primera(base: ShowBase, rutas: Sequence[Path]) -> TextFont | None:
    for ruta in rutas:
        if ruta.is_file():
            ruta_motor = Filename.from_os_specific(str(ruta)).get_fullpath()
            fuente: TextFont = base.loader.load_font(ruta_motor)
            if fuente is not None and fuente.is_valid():
                fuente.set_pixels_per_unit(64)
                return fuente
    return None


def _registrar_simbolos(base: ShowBase) -> None:
    """Da de alta en el motor la fuente de los símbolos, una sola vez."""
    if _fuente_simbolos:
        return
    fuente = _primera(base, _FUENTES_SIMBOLOS)
    if fuente is None:
        return
    _fuente_simbolos.append(fuente)
    propiedades = TextProperties()
    propiedades.set_font(fuente)
    TextPropertiesManager.get_global_ptr().set_properties(_PROPIEDADES_SIMBOLOS, propiedades)


def _tramos(texto: str) -> list[tuple[str, bool]]:
    """Trozos seguidos de texto normal o de símbolos, con si son símbolos."""
    tramos: list[tuple[str, bool]] = []
    for caracter in texto:
        simbolo = caracter in _SIMBOLOS
        if tramos and tramos[-1][1] == simbolo:
            tramos[-1] = (tramos[-1][0] + caracter, simbolo)
        else:
            tramos.append((caracter, simbolo))
    return tramos


def con_simbolos(texto: str) -> str:
    """`texto` con los símbolos marcados para escribirse con la fuente de símbolos.

    El motor cambia de propiedades de texto entre `\x01nombre\x01` y `\x02`.
    """
    if not _fuente_simbolos or not any(c in _SIMBOLOS for c in texto):
        return texto
    return "".join(
        f"\x01{_PROPIEDADES_SIMBOLOS}\x01{trozo}\x02" if simbolo else trozo
        for trozo, simbolo in _tramos(texto)
    )


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


def contorno_cinta(puntos: Sequence[Punto], ancho: float, cerrada: bool = False) -> list[Punto]:
    """Bordes de una cinta de `ancho` píxeles a lo largo de `puntos`.

    Devuelve los puntos alternos de un lado y del otro: (izquierda 0, derecha 0,
    izquierda 1, derecha 1…). En cada vértice el desplazamiento sigue la media de las
    normales de los dos tramos, para que la cinta no se abra ni se solape en las esquinas.
    """
    n = len(puntos)
    if n < 2:
        raise ValueError("Una cinta necesita al menos dos puntos")
    mitad = ancho / 2
    bordes: list[Punto] = []
    for i, (x, y) in enumerate(puntos):
        normales = []
        for a, b in ((i - 1, i), (i, i + 1)):
            if not cerrada and (a < 0 or b >= n):
                continue
            (ax, ay), (bx, by) = puntos[a % n], puntos[b % n]
            largo = math.hypot(bx - ax, by - ay)
            if largo > 0:
                normales.append((-(by - ay) / largo, (bx - ax) / largo))
        nx = sum(v[0] for v in normales)
        ny = sum(v[1] for v in normales)
        largo = math.hypot(nx, ny)
        if largo == 0:
            nx, ny, escala = 0.0, 0.0, 0.0
        else:
            nx, ny = nx / largo, ny / largo
            # Inglete: se alarga en las esquinas, con límite para las muy cerradas.
            coseno = max(0.5, max(nx * v[0] + ny * v[1] for v in normales))
            escala = mitad / coseno
        bordes.append((x + nx * escala, y + ny * escala))
        bordes.append((x - nx * escala, y - ny * escala))
    return bordes


def cinta(
    padre: NodePath,
    puntos: Sequence[Punto],
    ancho: float,
    relleno: Color,
    cerrada: bool = False,
) -> NodePath:
    """Trazo de `ancho` píxeles de diseño hecho con triángulos: se escala con el HUD y,
    a diferencia de `linea`, admite anchos fraccionarios y transparencia sin solapes."""
    bordes = contorno_cinta(puntos, ancho, cerrada)
    if cerrada:
        bordes += bordes[:2]
    datos = GeomVertexData("cinta", GeomVertexFormat.get_v3(), Geom.UH_static)
    vertices = GeomVertexWriter(datos, "vertex")
    for x, y in bordes:
        vertices.add_data3(x, 0, -y)
    triangulos = GeomTriangles(Geom.UH_static)
    for i in range(0, len(bordes) - 2, 2):
        triangulos.add_vertices(i, i + 1, i + 2)
        triangulos.add_vertices(i + 1, i + 3, i + 2)
    geom = Geom(datos)
    geom.add_primitive(triangulos)
    nodo = GeomNode("cinta")
    nodo.add_geom(geom)
    camino = preparar(padre.attach_new_node(nodo))
    camino.set_two_sided(True)
    camino.set_color(*relleno)
    return camino


def arco(centro: Punto, radio: float, inicio: float, fin: float, lados: int = 24) -> list[Punto]:
    """Puntos de un arco de `inicio` a `fin` grados, medidos en sentido horario desde
    arriba, como en la pantalla (la y crece hacia abajo)."""
    cx, cy = centro
    resultado = []
    for i in range(lados + 1):
        angulo = math.radians(inicio + (fin - inicio) * i / lados)
        resultado.append((cx + radio * math.sin(angulo), cy - radio * math.cos(angulo)))
    return resultado


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


def panel(
    padre: NodePath,
    x: float,
    y: float,
    ancho: float,
    alto: float,
    escala: float,
    relleno: Color | None = None,
    borde: Color | None = None,
    orden: int = ORDEN_PANEL,
) -> None:
    """Panel con dos esquinas recortadas, arriba a la izquierda y abajo a la derecha.

    Sin `relleno` ni `borde`, usa los colores fondo-panel y borde-panel de `interfaz.md`.
    `orden` es el orden de dibujo del fondo; el borde va justo encima.
    """
    recorte = 12
    puntos = [
        (x + recorte, y),
        (x + ancho, y),
        (x + ancho, y + alto - recorte),
        (x + ancho - recorte, y + alto),
        (x, y + alto),
        (x, y + recorte),
    ]
    relleno = color("#0A1220", 0.78) if relleno is None else relleno
    borde = color("#2AD4FF", 0.35) if borde is None else borde
    poligono(padre, puntos, relleno).set_bin("fixed", orden)
    contorno = linea(padre, [*puntos, puntos[0]], borde, 1, escala)
    contorno.set_bin("fixed", orden + 1)


def ancho_texto(fuente: TextFont | None, texto: str, tamano: float) -> float:
    """Ancho en píxeles de diseño de `texto` escrito con `fuente` a `tamano` píxeles."""
    nodo = TextNode("medida")
    simbolos = TextNode("medida-simbolos")
    if fuente is not None:
        nodo.set_font(fuente)
    if _fuente_simbolos:
        simbolos.set_font(_fuente_simbolos[0])
    ancho = 0.0
    for trozo, simbolo in _tramos(texto):
        medidor = simbolos if simbolo and _fuente_simbolos else nodo
        ancho += float(medidor.calc_width(trozo))
    return ancho * tamano


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
        self._tamano = tamano
        self._texto: str | None = None
        self._color: Color | None = None

    def mostrar(self, texto: str, color_texto: Color) -> None:
        if texto != self._texto:
            self._nodo.set_text(con_simbolos(texto))
            self._texto = texto
        if color_texto != self._color:
            self._nodo.set_text_color(*color_texto)
            self._color = color_texto

    def ocultar(self) -> None:
        self.mostrar("", self._color or (1.0, 1.0, 1.0, 1.0))

    def escalar(self, factor: float) -> None:
        """Agranda o reduce el texto respecto a su tamaño, para animarlo."""
        self._camino.set_scale(self._tamano * factor)
