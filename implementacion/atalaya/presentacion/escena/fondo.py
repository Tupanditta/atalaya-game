"""Fondos espaciales como cubos de cielo generados por código (`design.md`, sección 6).

Cada fondo es un mapa cúbico de seis caras con estrellas. Se genera con una semilla
fija por índice, de modo que el mismo fondo se ve siempre igual.
"""

import math
import random

from panda3d.core import (
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexArrayFormat,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    InternalName,
    NodePath,
    PNMImage,
    SamplerState,
    Texture,
)

#: Lado de cada cara en píxeles. Con 1024 px por cada 90° y 1080 px de alto para 70° de
#: campo de visión, la textura casi nunca se reduce en pantalla y las estrellas no parpadean.
LADO_CARA = 1024

#: Estrellas por cara.
_ESTRELLAS = 1800

#: Color del espacio vacío.
_COLOR_FONDO = (0.004, 0.006, 0.016)

# Tonos de estrella, de rojizo a azulado.
_TONOS = [(1.0, 0.82, 0.70), (1.0, 0.93, 0.85), (1.0, 1.0, 1.0), (0.85, 0.90, 1.0)]


def textura_fondo(indice: int, lado: int = LADO_CARA) -> Texture:
    """Mapa cúbico de estrellas del fondo `indice`."""
    azar = random.Random(f"fondo-{indice}")
    textura = Texture(f"fondo-{indice}")
    textura.setup_cube_map(lado, Texture.T_unsigned_byte, Texture.F_rgb)
    for cara, imagen in enumerate(_caras(azar, lado)):
        textura.load(imagen, cara, 0)
    textura.set_minfilter(SamplerState.FT_linear)
    textura.set_magfilter(SamplerState.FT_linear)
    textura.set_wrap_u(SamplerState.WM_clamp)
    textura.set_wrap_v(SamplerState.WM_clamp)
    return textura


def _caras(azar: random.Random, lado: int) -> list[PNMImage]:
    """Las seis caras, con estrellas repartidas por igual en todas las direcciones.

    En las esquinas de una cara cada píxel abarca menos ángulo que en el centro. Para que
    las estrellas se vean igual de densas y de grandes en todo el cielo, se eligen
    direcciones uniformes en la esfera y el radio en píxeles crece hacia las esquinas.
    """
    caras = [PNMImage(lado, lado, 3) for _ in range(6)]
    for imagen in caras:
        imagen.fill(*_COLOR_FONDO)
    for _ in range(_ESTRELLAS * 6):
        cara, s, t = _proyectar(_direccion_al_azar(azar))
        x = (s + 1) / 2 * lado
        y = (t + 1) / 2 * lado
        # Muchas estrellas débiles y pocas brillantes.
        brillo = 0.25 + 0.75 * azar.random() ** 3
        tono = azar.choice(_TONOS)
        radio = (1.6 if brillo > 0.7 else 1.0) * (1 + s * s + t * t) ** 0.75
        _estrella(caras[cara], x, y, brillo, tono, radio)
    return caras


def _direccion_al_azar(azar: random.Random) -> tuple[float, float, float]:
    z = azar.uniform(-1, 1)
    angulo = azar.uniform(0, 2 * math.pi)
    r = math.sqrt(1 - z * z)
    return (r * math.cos(angulo), r * math.sin(angulo), z)


def _proyectar(d: tuple[float, float, float]) -> tuple[int, float, float]:
    """Cara (0 a 5: +x, −x, +y, −y, +z, −z) y coordenadas (s, t) en [−1, 1] de `d`."""
    x, y, z = d
    ax, ay, az = abs(x), abs(y), abs(z)
    if ax >= ay and ax >= az:
        return (0, -z / ax, -y / ax) if x > 0 else (1, z / ax, -y / ax)
    if ay >= az:
        return (2, x / ay, z / ay) if y > 0 else (3, x / ay, -z / ay)
    return (4, x / az, -y / az) if z > 0 else (5, -x / az, -y / az)


def _estrella(
    imagen: PNMImage,
    x: float,
    y: float,
    brillo: float,
    tono: tuple[float, float, float],
    radio: float,
) -> None:
    """Dibuja una estrella suave sumando luz a los píxeles de alrededor."""
    alcance = math.ceil(radio)
    for py in range(int(y) - alcance, int(y) + alcance + 1):
        for px in range(int(x) - alcance, int(x) + alcance + 1):
            if not (0 <= px < imagen.get_x_size() and 0 <= py < imagen.get_y_size()):
                continue
            distancia = math.hypot(px + 0.5 - x, py + 0.5 - y)
            intensidad = brillo * max(0.0, 1 - distancia / (radio + 0.5)) ** 2
            if intensidad <= 0:
                continue
            actual = imagen.get_xel(px, py)
            imagen.set_xel(
                px,
                py,
                min(1.0, actual[0] + intensidad * tono[0]),
                min(1.0, actual[1] + intensidad * tono[1]),
                min(1.0, actual[2] + intensidad * tono[2]),
            )


def cubo_de_cielo(textura: Texture) -> NodePath:
    """Cubo centrado en el origen con `textura` como mapa cúbico.

    Se dibuja el primero, sin prueba ni escritura de profundidad, así que siempre queda
    detrás de todo lo demás, como si estuviera a distancia infinita.
    """
    columnas = GeomVertexArrayFormat()
    columnas.add_column(InternalName.get_vertex(), 3, Geom.NT_float32, Geom.C_point)
    # Coordenadas de textura en 3D: la dirección desde el centro del cubo.
    columnas.add_column(InternalName.get_texcoord(), 3, Geom.NT_float32, Geom.C_texcoord)
    formato = GeomVertexFormat.register_format(GeomVertexFormat(columnas))
    datos = GeomVertexData("fondo", formato, Geom.UH_static)
    vertices = GeomVertexWriter(datos, "vertex")
    coordenadas = GeomVertexWriter(datos, "texcoord")
    esquinas = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    for esquina in esquinas:
        vertices.add_data3(*esquina)
        coordenadas.add_data3(*esquina)
    triangulos = GeomTriangles(Geom.UH_static)
    # Cada cara del cubo: cuatro esquinas que comparten una coordenada.
    for eje in range(3):
        for signo in (-1, 1):
            cara = [i for i, e in enumerate(esquinas) if e[eje] == signo]
            a, b, c, d = cara
            triangulos.add_vertices(a, b, d)
            triangulos.add_vertices(a, d, c)
    geom = Geom(datos)
    geom.add_primitive(triangulos)
    nodo = GeomNode("fondo")
    nodo.add_geom(geom)
    cubo = NodePath(nodo)
    cubo.set_texture(textura)
    cubo.set_two_sided(True)
    cubo.set_light_off()
    cubo.set_bin("background", 0)
    cubo.set_depth_test(False)
    cubo.set_depth_write(False)
    cubo.set_scale(10)
    return cubo
