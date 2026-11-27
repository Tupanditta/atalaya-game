"""Paisaje 3D de cada fondo: planetas, lunas, anillos, asteroides y polvo (RN-20).

Qué hay en cada fondo lo dice `planetas.PAISAJES`; aquí se construyen los nodos. Todo
queda más lejos que el alcance del radar, así que no tapa enemigos ni proyectiles.

- **Planetas:** esferas con su textura, iluminadas por el sol del fondo, con un halo de
  atmósfera en el borde y anillos si los tienen. Los volcánicos tienen una segunda capa
  de lava que brilla también en la cara oscura. Giran despacio sobre su eje.
- **Asteroides:** un cinturón de rocas lejanas, unidas en pocas geometrías que orbitan
  despacio alrededor de la estación, y unas pocas rocas más cercanas que ruedan.
- **Polvo:** motas tenues alrededor de la estación que derivan despacio: con la cámara
  quieta, dan sensación de espacio.

Fluidez: el paisaje de un fondo se construye y se sube a la tarjeta gráfica antes de
mostrarlo (en el descanso previo al salto), y queda guardado. En cada fotograma solo se
giran unos pocos nodos.
"""

import math
import random
from dataclasses import dataclass, field

import numpy as np
from panda3d.core import (
    AmbientLight,
    CardMaker,
    ColorBlendAttrib,
    DirectionalLight,
    Geom,
    GeomNode,
    GeomPoints,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    GraphicsStateGuardianBase,
    NodePath,
    OmniBoundingVolume,
    SamplerState,
    TexGenAttrib,
    Texture,
    TextureStage,
    TransparencyAttrib,
    Vec3,
)

from atalaya.presentacion.escena.planetas import PAISAJES, Asteroides, Planeta, textura_anillos

#: Distancia de los planetas a la estación. Con el mayor radio angular (15°) y sus
#: anillos, todo cabe entre el alcance del radar y el plano lejano de la cámara.
DISTANCIA_PLANETAS = 4000.0

_LADOS_ESFERA = 64
_PARALELOS_ESFERA = 32
_LADOS_ANILLOS = 120
#: El halo de la atmósfera llega hasta este múltiplo del radio del planeta.
_ALCANCE_ATMOSFERA = 1.35
#: Luz ambiente de los planetas: la cara de noche se adivina, pero es oscura.
_AMBIENTE = (0.045, 0.045, 0.06, 1.0)

#: Grupos en que se une el cinturón lejano, y su velocidad de órbita en grados por segundo.
_GRUPOS_CINTURON = 6
_ORBITA = (0.12, 0.35)
_VARIANTES_ROCA = 5
#: Giro de las rocas cercanas, en grados por segundo.
_GIRO_ROCAS = 25.0
#: Las rocas cercanas están a esta parte de la distancia mínima del campo.
_CERCANIA_ROCAS = (0.85, 1.0)

#: Polvo: número de motas, distancias, tamaño en píxeles y giro en grados por segundo.
_MOTAS = 420
_DISTANCIA_POLVO = (60.0, 320.0)
_TAMANO_MOTA = 2.0
_GIRO_POLVO = 0.8
_OPACIDAD_POLVO = 0.35


@dataclass
class _Escenario:
    """Nodos del paisaje de un fondo y lo que se mueve en él."""

    nodo: NodePath
    giros: list[tuple[NodePath, float]] = field(default_factory=list)
    orbitas: list[tuple[NodePath, float]] = field(default_factory=list)
    rocas: list[tuple[NodePath, Vec3, Vec3]] = field(default_factory=list)
    polvo: NodePath | None = None
    tiempo: float = 0.0


class Paisaje:
    """Paisaje del fondo actual, con los de otros fondos ya preparados y ocultos."""

    def __init__(self, padre: NodePath, brillo: Texture) -> None:
        self._raiz = padre.attach_new_node("paisaje")
        self._brillo = brillo
        self._atmosfera = textura_atmosfera()
        sol = DirectionalLight("sol-paisaje")
        self._sol = self._raiz.attach_new_node(sol)
        ambiente = AmbientLight("ambiente-paisaje")
        ambiente.set_color(_AMBIENTE)
        self._raiz.set_light(self._sol)
        self._raiz.set_light(self._raiz.attach_new_node(ambiente))
        self._escenarios: dict[int, _Escenario] = {}
        self._actual: int | None = None

    @property
    def actual(self) -> int | None:
        """Fondo cuyo paisaje se ve, o `None` antes del primero."""
        return self._actual

    def preparado(self, indice: int) -> bool:
        """Indica si el paisaje del fondo `indice` ya está construido."""
        return indice in self._escenarios

    def preparar(
        self,
        indice: int,
        texturas: list[tuple[Texture, Texture | None]],
        gsg: GraphicsStateGuardianBase | None = None,
    ) -> None:
        """Construye el paisaje del fondo `indice`, oculto, y lo sube a la tarjeta gráfica."""
        if indice in self._escenarios:
            return
        escenario = self._construir(indice, texturas)
        if gsg is not None:
            escenario.nodo.prepare_scene(gsg)
        escenario.nodo.stash()
        self._escenarios[indice] = escenario

    def mostrar(self, indice: int, texturas: list[tuple[Texture, Texture | None]]) -> None:
        """Muestra el paisaje del fondo `indice` en lugar del actual."""
        if indice == self._actual:
            return
        self.preparar(indice, texturas)
        if self._actual is not None:
            self._escenarios[self._actual].nodo.stash()
        self._escenarios[indice].nodo.unstash()
        self._actual = indice
        paisaje = PAISAJES[indice - 1]
        self._sol.node().set_color((*paisaje.luz_color, 1.0))
        # La luz va del sol hacia la estación.
        self._sol.look_at(-Vec3(*paisaje.luz_direccion))

    def avanzar(self, dt: float) -> None:
        """Gira los planetas, el cinturón, las rocas cercanas y el polvo."""
        if self._actual is None:
            return
        escenario = self._escenarios[self._actual]
        escenario.tiempo += dt
        t = escenario.tiempo
        for nodo, velocidad in escenario.giros:
            nodo.set_h(velocidad * t)
        for nodo, velocidad in escenario.orbitas:
            nodo.set_h(velocidad * t)
        for roca, inicial, giro in escenario.rocas:
            roca.set_hpr(inicial + giro * t)
        if escenario.polvo is not None:
            escenario.polvo.set_h(_GIRO_POLVO * t)

    # --- construcción ----------------------------------------------------------------

    def _construir(self, indice: int, texturas: list[tuple[Texture, Texture | None]]) -> _Escenario:
        paisaje = PAISAJES[indice - 1]
        escenario = _Escenario(self._raiz.attach_new_node(f"paisaje-{indice}"))
        for planeta, (color, emisivo) in zip(paisaje.planetas, texturas, strict=True):
            self._planeta(escenario, planeta, color, emisivo, indice)
        if paisaje.asteroides is not None:
            self._asteroides(escenario, paisaje.asteroides)
        escenario.polvo = self._polvo(escenario.nodo, paisaje.polvo, indice)
        return escenario

    def _planeta(
        self,
        escenario: _Escenario,
        planeta: Planeta,
        color: Texture,
        emisivo: Texture | None,
        indice: int,
    ) -> None:
        radio = DISTANCIA_PLANETAS * math.tan(math.radians(planeta.tamano))
        nodo = escenario.nodo.attach_new_node("planeta")
        nodo.set_pos(Vec3(*planeta.direccion).normalized() * DISTANCIA_PLANETAS)
        nodo.set_scale(radio)
        eje = nodo.attach_new_node("eje")
        eje.set_hpr(*planeta.inclinacion)
        giro = eje.attach_new_node("giro")
        # Rumbo inicial distinto en cada planeta, para que no se vea siempre la misma cara.
        giro.set_h(random.Random(planeta.semilla).uniform(0, 360))
        # La esfera es una geometría compartida: cada planeta le pone su textura en un
        # nodo propio, no en ella, o todos acabarían con la misma.
        superficie = giro.attach_new_node("superficie")
        superficie.attach_new_node(_esfera())
        superficie.set_texture(color)
        if emisivo is not None:
            lava = giro.attach_new_node("lava")
            lava.attach_new_node(_esfera())
            lava.set_scale(1.002)
            lava.set_texture(emisivo)
            _aditivo(lava)
        escenario.giros.append((giro, planeta.giro))
        if planeta.atmosfera is not None:
            tarjeta = CardMaker("atmosfera")
            tarjeta.set_frame(-1, 1, -1, 1)
            halo = nodo.attach_new_node(tarjeta.generate())
            halo.set_texture(self._atmosfera)
            halo.set_scale(_ALCANCE_ATMOSFERA)
            # Desplazado un poco hacia el sol: el halo es más ancho en el lado de día.
            halo.set_pos(_hacia_el_sol(planeta, PAISAJES[indice - 1].luz_direccion) * 0.1)
            halo.set_billboard_point_eye()
            halo.set_color(*planeta.atmosfera, 0.8)
            _aditivo(halo)
        if planeta.anillos is not None:
            color_anillos, interior, exterior = planeta.anillos
            anillos = eje.attach_new_node(_anillos(interior, exterior))
            anillos.set_texture(_textura_rgba(textura_anillos(color_anillos, planeta.semilla)))
            anillos.set_transparency(TransparencyAttrib.M_alpha)
            anillos.set_two_sided(True)
            anillos.set_depth_write(False)
            anillos.set_light_off()
            luz = PAISAJES[indice - 1].luz_color
            anillos.set_color_scale(*(0.85 * c for c in luz), 1.0)

    def _asteroides(self, escenario: _Escenario, campo: Asteroides) -> None:
        azar = random.Random(campo.semilla)
        variantes = [_roca(campo.semilla * 31 + i) for i in range(_VARIANTES_ROCA)]
        centro = Vec3(*campo.centro).normalized()
        grupos = []
        for i in range(_GRUPOS_CINTURON):
            grupo = escenario.nodo.attach_new_node(f"cinturon-{i}")
            # Cada grupo orbita a su ritmo: el cinturón no se mueve como un bloque.
            velocidad = azar.uniform(*_ORBITA) * azar.choice((-1, 1))
            grupos.append(grupo)
            escenario.orbitas.append((grupo, velocidad))
        minimo, maximo = campo.distancia
        for _ in range(campo.numero):
            direccion = _cerca_de(centro, campo.extension, azar)
            roca = grupos[azar.randrange(_GRUPOS_CINTURON)].attach_new_node("roca")
            roca.attach_new_node(azar.choice(variantes))
            roca.set_pos(direccion * azar.uniform(minimo, maximo))
            roca.set_hpr(azar.uniform(0, 360), azar.uniform(0, 360), azar.uniform(0, 360))
            # Muchas rocas pequeñas y pocas grandes.
            roca.set_scale(
                campo.tamano[0] * (campo.tamano[1] / campo.tamano[0]) ** azar.random() ** 2
            )
            roca.set_color(*_variar(campo.color, azar), 1.0)
        # Unir las rocas de cada grupo deja una sola geometría que dibujar por grupo.
        for grupo in grupos:
            grupo.flatten_strong()
        for _ in range(campo.cercanos):
            direccion = _cerca_de(centro, campo.extension * 0.8, azar)
            roca = escenario.nodo.attach_new_node("roca-cercana")
            roca.attach_new_node(azar.choice(variantes))
            roca.set_pos(direccion * minimo * azar.uniform(*_CERCANIA_ROCAS))
            roca.set_scale(campo.tamano[1] * azar.uniform(1.0, 1.8))
            roca.set_color(*_variar(campo.color, azar), 1.0)
            inicial = Vec3(azar.uniform(0, 360), azar.uniform(0, 360), azar.uniform(0, 360))
            giro = Vec3(*(azar.uniform(-1, 1) * _GIRO_ROCAS for _ in range(3)))
            escenario.rocas.append((roca, inicial, giro))

    def _polvo(self, padre: NodePath, color: tuple[float, float, float], indice: int) -> NodePath:
        azar = np.random.default_rng(indice)
        direcciones = azar.normal(size=(_MOTAS, 3))
        direcciones /= np.linalg.norm(direcciones, axis=1, keepdims=True)
        distancias = azar.uniform(*_DISTANCIA_POLVO, _MOTAS)
        datos = GeomVertexData("polvo", GeomVertexFormat.get_v3(), Geom.UH_static)
        vertices = GeomVertexWriter(datos, "vertex")
        puntos = GeomPoints(Geom.UH_static)
        for i, (d, r) in enumerate(zip(direcciones, distancias, strict=True)):
            vertices.add_data3(*(d * r))
            puntos.add_vertex(i)
        geom = Geom(datos)
        geom.add_primitive(puntos)
        nodo_geom = GeomNode("polvo")
        nodo_geom.add_geom(geom)
        nodo_geom.set_bounds(OmniBoundingVolume())
        # Eje de deriva inclinado, para que el polvo no gire alrededor de la vertical.
        inclinado = padre.attach_new_node("polvo-eje")
        inclinado.set_hpr(30, 40, 0)
        polvo = inclinado.attach_new_node(nodo_geom)
        polvo.set_texture(self._brillo)
        polvo.set_tex_gen(TextureStage.get_default(), TexGenAttrib.M_point_sprite)
        polvo.set_render_mode_thickness(_TAMANO_MOTA)
        polvo.set_color(*color, _OPACIDAD_POLVO)
        _aditivo(polvo)
        return polvo


# --- geometría -------------------------------------------------------------------------

_geometrias: dict[str, GeomNode] = {}


def _esfera() -> GeomNode:
    """Esfera de radio 1 con coordenadas de latitud y longitud, compartida."""
    if "esfera" in _geometrias:
        return _geometrias["esfera"]
    datos = GeomVertexData("esfera", GeomVertexFormat.get_v3n3t2(), Geom.UH_static)
    vertices = GeomVertexWriter(datos, "vertex")
    normales = GeomVertexWriter(datos, "normal")
    coordenadas = GeomVertexWriter(datos, "texcoord")
    for j in range(_PARALELOS_ESFERA + 1):
        v = j / _PARALELOS_ESFERA
        latitud = math.pi * (v - 0.5)
        for i in range(_LADOS_ESFERA + 1):
            u = i / _LADOS_ESFERA
            longitud = 2 * math.pi * u
            punto = (
                math.cos(latitud) * math.cos(longitud),
                math.cos(latitud) * math.sin(longitud),
                math.sin(latitud),
            )
            vertices.add_data3(*punto)
            normales.add_data3(*punto)
            coordenadas.add_data2(u, v)
    triangulos = GeomTriangles(Geom.UH_static)
    fila = _LADOS_ESFERA + 1
    for j in range(_PARALELOS_ESFERA):
        for i in range(_LADOS_ESFERA):
            a, b = j * fila + i, j * fila + i + 1
            c, d = a + fila, b + fila
            triangulos.add_vertices(a, b, d)
            triangulos.add_vertices(a, d, c)
    geom = Geom(datos)
    geom.add_primitive(triangulos)
    nodo = GeomNode("esfera")
    nodo.add_geom(geom)
    _geometrias["esfera"] = nodo
    return nodo


def _anillos(interior: float, exterior: float) -> GeomNode:
    """Corona plana en el ecuador del planeta; u va de dentro (0) a fuera (1)."""
    datos = GeomVertexData("anillos", GeomVertexFormat.get_v3t2(), Geom.UH_static)
    vertices = GeomVertexWriter(datos, "vertex")
    coordenadas = GeomVertexWriter(datos, "texcoord")
    for i in range(_LADOS_ANILLOS + 1):
        angulo = 2 * math.pi * i / _LADOS_ANILLOS
        c, s = math.cos(angulo), math.sin(angulo)
        for radio, u in ((interior, 0.0), (exterior, 1.0)):
            vertices.add_data3(radio * c, radio * s, 0)
            coordenadas.add_data2(u, 0.5)
    triangulos = GeomTriangles(Geom.UH_static)
    for i in range(_LADOS_ANILLOS):
        a, b, c, d = 2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3
        triangulos.add_vertices(a, c, b)
        triangulos.add_vertices(b, c, d)
    geom = Geom(datos)
    geom.add_primitive(triangulos)
    nodo = GeomNode("anillos")
    nodo.add_geom(geom)
    return nodo


def _roca(semilla: int) -> GeomNode:
    """Roca irregular: icosaedro subdividido con los vértices desplazados, de caras planas."""
    azar = random.Random(semilla)
    t = (1 + math.sqrt(5)) / 2
    puntos = [
        Vec3(*v).normalized()
        for v in [
            (-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0),
            (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
            (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1),
        ]
    ]  # fmt: skip
    caras = [
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
    ]  # fmt: skip
    medios: dict[tuple[int, int], int] = {}

    def medio(a: int, b: int) -> int:
        clave = (min(a, b), max(a, b))
        if clave not in medios:
            puntos.append((puntos[a] + puntos[b]).normalized())
            medios[clave] = len(puntos) - 1
        return medios[clave]

    subdivididas = []
    for a, b, c in caras:
        ab, bc, ca = medio(a, b), medio(b, c), medio(c, a)
        subdivididas += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
    # Forma alargada e irregular: cada vértice a su propia distancia del centro.
    estirado = Vec3(azar.uniform(0.8, 1.3), azar.uniform(0.7, 1.0), azar.uniform(0.6, 0.9))
    deformados = [
        Vec3(p.x * estirado.x, p.y * estirado.y, p.z * estirado.z) * azar.uniform(0.75, 1.1)
        for p in puntos
    ]
    datos = GeomVertexData("roca", GeomVertexFormat.get_v3n3(), Geom.UH_static)
    vertices = GeomVertexWriter(datos, "vertex")
    normales = GeomVertexWriter(datos, "normal")
    triangulos = GeomTriangles(Geom.UH_static)
    for i, (a, b, c) in enumerate(subdivididas):
        pa, pb, pc = deformados[a], deformados[b], deformados[c]
        normal = (pb - pa).cross(pc - pa).normalized()
        if normal.dot(pa + pb + pc) < 0:
            pb, pc, normal = pc, pb, -normal
        for punto in (pa, pb, pc):
            vertices.add_data3(punto)
            normales.add_data3(normal)
        triangulos.add_vertices(3 * i, 3 * i + 1, 3 * i + 2)
    geom = Geom(datos)
    geom.add_primitive(triangulos)
    nodo = GeomNode("roca")
    nodo.add_geom(geom)
    return nodo


# --- texturas y ayudas -----------------------------------------------------------------


def textura_atmosfera(lado: int = 128) -> Texture:
    """Halo de la atmósfera: un aro de luz justo en el borde del planeta, hacia fuera."""
    centro = (lado - 1) / 2
    y, x = np.mgrid[0:lado, 0:lado].astype(np.float32)
    d = np.hypot(x - centro, y - centro) / centro
    borde = 1 / _ALCANCE_ATMOSFERA
    fuera = np.exp(-(((d - borde) / 0.11) ** 2))
    dentro = np.exp(-(((d - borde) / 0.03) ** 2))
    alfa = np.where(d >= borde, fuera, dentro) * (d < 1)
    imagen = np.ones((lado, lado, 4), dtype=np.float32)
    imagen[..., 3] = alfa
    return _textura_rgba((imagen * 255 + 0.5).astype(np.uint8), repetir=False)


def _textura_rgba(imagen: np.ndarray, repetir: bool = False) -> Texture:
    """Textura del motor con una imagen RGBA de numpy (fila 0 abajo)."""
    datos = np.ascontiguousarray(imagen[..., [2, 1, 0, 3]])
    textura = Texture("rgba")
    textura.setup_2d_texture(
        datos.shape[1], datos.shape[0], Texture.T_unsigned_byte, Texture.F_rgba
    )
    textura.set_ram_image(datos.data)
    modo = SamplerState.WM_repeat if repetir else SamplerState.WM_clamp
    textura.set_wrap_u(modo)
    textura.set_wrap_v(modo)
    textura.set_minfilter(SamplerState.FT_linear)
    textura.set_magfilter(SamplerState.FT_linear)
    return textura


def _aditivo(nodo: NodePath) -> None:
    """Luz que se suma a lo que hay detrás, sin luces ni escritura de profundidad."""
    nodo.set_attrib(
        ColorBlendAttrib.make(
            ColorBlendAttrib.M_add, ColorBlendAttrib.O_incoming_alpha, ColorBlendAttrib.O_one
        )
    )
    nodo.set_transparency(TransparencyAttrib.M_alpha)
    nodo.set_depth_write(False)
    nodo.set_light_off()


def _hacia_el_sol(planeta: Planeta, sol: tuple[float, float, float]) -> Vec3:
    """Dirección del sol vista sobre el disco del planeta, desde la estación."""
    hacia_camara = -Vec3(*planeta.direccion).normalized()
    luz = Vec3(*sol).normalized()
    lateral = luz - hacia_camara * luz.dot(hacia_camara)
    return lateral.normalized() if lateral.length() > 1e-6 else Vec3(0, 0, 0)


def _cerca_de(centro: Vec3, extension: float, azar: random.Random) -> Vec3:
    """Dirección al azar a unos `extension` grados de `centro`, más densa en el medio."""
    auxiliar = Vec3(0, 0, 1) if abs(centro.z) < 0.9 else Vec3(1, 0, 0)
    u = centro.cross(auxiliar).normalized()
    v = centro.cross(u).normalized()
    angulo = math.radians(extension) * min(1.0, abs(azar.gauss(0, 0.5)))
    rumbo = azar.uniform(0, 2 * math.pi)
    lateral = u * math.cos(rumbo) + v * math.sin(rumbo)
    return (centro * math.cos(angulo) + lateral * math.sin(angulo)).normalized()


def _variar(color: tuple[float, float, float], azar: random.Random) -> tuple[float, float, float]:
    """El color del campo con un poco de variación, para que cada roca sea distinta."""
    k = azar.uniform(0.75, 1.15)
    return (min(1.0, color[0] * k), min(1.0, color[1] * k), min(1.0, color[2] * k))
