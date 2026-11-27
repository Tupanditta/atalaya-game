"""Paisaje 3D de cada fondo: planetas, lunas, anillos, asteroides y polvo (RN-20).

Qué hay en cada fondo lo dice `planetas.PAISAJES`; aquí se construyen los nodos. Todo
queda más lejos que el alcance del radar, así que no tapa enemigos ni proyectiles.

- **Planetas:** esferas con su textura, iluminadas por el sol del fondo, con atmósfera y
  anillos si los tienen. Giran despacio sobre su eje. Con shaders (`planetas_glsl.py`),
  la luz se calcula por píxel: relieve, nubes con sombra, brillo del hielo, lava que se ve
  más de noche, una atmósfera que dispersa la luz del sol y sombras entre el planeta y sus
  anillos. Sin shaders, luz del motor, un halo plano y una segunda esfera de lava.
- **Asteroides:** un cinturón de rocas lejanas, unidas en pocas geometrías que orbitan
  despacio alrededor de la estación, y unas pocas rocas más cercanas, con más detalle, que
  ruedan. Cada roca es una malla deformada con ruido, de normales suaves y con las
  hendiduras oscurecidas; con shaders (`asteroides_glsl.py`), la luz es por píxel.
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
from numpy.typing import NDArray
from panda3d.core import (
    AmbientLight,
    CardMaker,
    ColorBlendAttrib,
    DirectionalLight,
    Geom,
    GeomNode,
    GeomPoints,
    GeomTriangles,
    GeomVertexArrayFormat,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    GraphicsStateGuardianBase,
    InternalName,
    NodePath,
    OmniBoundingVolume,
    SamplerState,
    Shader,
    TexGenAttrib,
    Texture,
    TextureStage,
    TransparencyAttrib,
    Vec3,
    Vec4,
)

from atalaya.presentacion.escena.planetas import (
    PAISAJES,
    Asteroides,
    Planeta,
    Superficie,
    textura_anillos,
)
from atalaya.presentacion.escena.ruido import fractal
from atalaya.presentacion.escena.sombreado import Sombreado

#: Texturas de un planeta en el motor: color (con la altura), luz propia y nubes.
TexturasMotor = tuple[Texture, Texture | None, Texture | None]

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
#: Con shaders: radio de la cáscara de la atmósfera, en radios del planeta.
_CASCARA_ATMOSFERA = 1.045
#: Altura del relieve, en radios del planeta (exagerada para que se vea desde lejos).
_RELIEVE = 0.03
#: Opacidad de las nubes.
_OPACIDAD_NUBES = 0.92

#: Grupos en que se une el cinturón lejano, y su velocidad de órbita en grados por segundo.
_GRUPOS_CINTURON = 6
_ORBITA = (0.12, 0.35)
_VARIANTES_ROCA = 8
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

    def __init__(
        self, padre: NodePath, brillo: Texture, sombreado: Sombreado | None = None
    ) -> None:
        self._raiz = padre.attach_new_node("paisaje")
        self._brillo = brillo
        self._sombreado = sombreado
        self._atmosfera = textura_atmosfera()
        self._vacia = _textura_rgba(np.zeros((1, 1, 4), dtype=np.uint8))
        # Valores por defecto de las entradas de los shaders: cada planeta pone los suyos.
        self._raiz.set_shader_inputs(
            tex_emisivo=self._vacia,
            tex_nubes=self._vacia,
            tex_anillos=self._vacia,
            emisivo=0.0,
            hielo=0.0,
            relieve=0.0,
            tiempo=0.0,
            nubes=Vec4(0, 0, 0, 0),
            atmosfera=Vec4(0, 0, 0, 0),
            anillos=Vec3(0, 0, 0),
            alcance=_CASCARA_ATMOSFERA,
            luz_dir=Vec3(0, 0, 1),
            luz_color=Vec3(1, 1, 1),
        )
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
        texturas: list[TexturasMotor],
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

    def mostrar(self, indice: int, texturas: list[TexturasMotor]) -> None:
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
        escenario.nodo.set_shader_input("tiempo", t)
        for nodo, velocidad in escenario.giros:
            nodo.set_h(velocidad * t)
        for nodo, velocidad in escenario.orbitas:
            nodo.set_h(velocidad * t)
        for roca, inicial, giro in escenario.rocas:
            roca.set_hpr(inicial + giro * t)
        if escenario.polvo is not None:
            escenario.polvo.set_h(_GIRO_POLVO * t)

    # --- construcción ----------------------------------------------------------------

    def _construir(self, indice: int, texturas: list[TexturasMotor]) -> _Escenario:
        paisaje = PAISAJES[indice - 1]
        escenario = _Escenario(self._raiz.attach_new_node(f"paisaje-{indice}"))
        escenario.nodo.set_shader_inputs(
            luz_dir=Vec3(*paisaje.luz_direccion).normalized(), luz_color=Vec3(*paisaje.luz_color)
        )
        for planeta, texturas_planeta in zip(paisaje.planetas, texturas, strict=True):
            self._planeta(escenario, planeta, texturas_planeta, indice)
        if paisaje.asteroides is not None:
            self._asteroides(escenario, paisaje.asteroides)
        escenario.polvo = self._polvo(escenario.nodo, paisaje.polvo, indice)
        return escenario

    def _planeta(
        self, escenario: _Escenario, planeta: Planeta, texturas: TexturasMotor, indice: int
    ) -> None:
        color, emisivo, nubes = texturas
        programa = self._programa("planeta")
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
        bandas = (
            None
            if planeta.anillos is None
            else _textura_rgba(textura_anillos(planeta.anillos[0], planeta.semilla))
        )
        if planeta.anillos is not None and bandas is not None:
            nodo.set_shader_inputs(
                anillos=Vec3(planeta.anillos[1], planeta.anillos[2], 1), tex_anillos=bandas
            )
        if planeta.atmosfera is not None:
            # En un gigante gaseoso, una atmósfera fuerte taparía sus bandas.
            fuerza = 0.45 if planeta.superficie is Superficie.GASEOSO else 1.0
            nodo.set_shader_input("atmosfera", Vec4(*planeta.atmosfera, fuerza))
        if programa is not None:
            superficie.set_shader(programa)
            superficie.set_shader_inputs(
                tex_color=color,
                relieve=_RELIEVE * color.get_x_size() / (4 * math.pi),
                hielo=1.0 if planeta.superficie is Superficie.HELADO else 0.0,
            )
            if emisivo is not None:
                superficie.set_shader_inputs(tex_emisivo=emisivo, emisivo=1.0)
            if nubes is not None:
                superficie.set_shader_inputs(
                    tex_nubes=nubes, nubes=Vec4(*planeta.color_nubes, _OPACIDAD_NUBES)
                )
        elif emisivo is not None:
            lava = giro.attach_new_node("lava")
            lava.attach_new_node(_esfera())
            lava.set_scale(1.002)
            lava.set_texture(emisivo)
            _aditivo(lava)
        escenario.giros.append((giro, planeta.giro))
        atmosfera = self._programa("atmosfera")
        if planeta.atmosfera is not None and atmosfera is not None:
            cascara = nodo.attach_new_node("atmosfera")
            cascara.attach_new_node(_esfera())
            cascara.set_scale(_CASCARA_ATMOSFERA)
            cascara.set_shader(atmosfera)
            _aditivo(cascara)
        elif planeta.atmosfera is not None:
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
        if planeta.anillos is not None and bandas is not None:
            _, interior, exterior = planeta.anillos
            anillos = eje.attach_new_node(_anillos(interior, exterior))
            anillos.set_texture(bandas)
            anillos.set_transparency(TransparencyAttrib.M_alpha)
            anillos.set_two_sided(True)
            anillos.set_depth_write(False)
            anillos.set_light_off()
            programa_anillos = self._programa("anillos")
            if programa_anillos is not None:
                anillos.set_shader(programa_anillos)
            else:
                luz = PAISAJES[indice - 1].luz_color
                anillos.set_color_scale(*(0.85 * c for c in luz), 1.0)

    def muestras(self, punto: Vec3) -> list[NodePath]:
        """Una pieza diminuta con cada shader del paisaje, en `punto`, para calentarlos.

        Planeta, atmósfera, anillos y roca, con los valores por defecto de las entradas.
        `Calentamiento` las dibuja en el menú y las quita: así el primer dibujo de cada
        programa no da un tirón en partida. Sin shaders, ninguna.
        """
        if self._sombreado is None or not self._sombreado.activo:
            return []
        grupo = self._raiz.attach_new_node("calentamiento")
        grupo.set_pos(punto)
        grupo.set_scale(0.01)
        piezas = {
            "planeta": _esfera(),
            "atmosfera": _esfera(),
            "anillos": _anillos(1.2, 2.0),
            "roca": _roca(0, 2),
        }
        for nombre, geometria in piezas.items():
            programa = self._programa(nombre)
            if programa is None:
                continue
            pieza = grupo.attach_new_node(f"muestra-{nombre}")
            pieza.attach_new_node(geometria)
            pieza.set_shader(programa)
            pieza.set_shader_input("tex_color", self._vacia)
            if nombre == "atmosfera":
                _aditivo(pieza)
            elif nombre == "anillos":
                pieza.set_transparency(TransparencyAttrib.M_alpha)
                pieza.set_depth_write(False)
        return [grupo]

    def _programa(self, nombre: str) -> Shader | None:
        return None if self._sombreado is None else self._sombreado.programa(nombre)

    def _asteroides(self, escenario: _Escenario, campo: Asteroides) -> None:
        azar = random.Random(campo.semilla)
        # Las lejanas ocupan pocos píxeles: con menos detalle basta.
        variantes = [_roca(campo.semilla * 31 + i, 2) for i in range(_VARIANTES_ROCA)]
        detalladas = [_roca(campo.semilla * 31 + i, 3) for i in range(_VARIANTES_ROCA)]
        centro = Vec3(*campo.centro).normalized()
        asteroides = escenario.nodo.attach_new_node("asteroides")
        programa = self._programa("roca")
        if programa is not None:
            asteroides.set_shader(programa)
        grupos = []
        for i in range(_GRUPOS_CINTURON):
            grupo = asteroides.attach_new_node(f"cinturon-{i}")
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
            # Escala de color, no color: así se conservan las vetas y sombras de la roca.
            roca.set_color_scale(*_variar(campo.color, azar), 1.0)
        # Unir las rocas de cada grupo deja una sola geometría que dibujar por grupo.
        for grupo in grupos:
            grupo.flatten_strong()
        for _ in range(campo.cercanos):
            direccion = _cerca_de(centro, campo.extension * 0.8, azar)
            roca = asteroides.attach_new_node("roca-cercana")
            roca.attach_new_node(azar.choice(detalladas))
            roca.set_pos(direccion * minimo * azar.uniform(*_CERCANIA_ROCAS))
            roca.set_scale(campo.tamano[1] * azar.uniform(1.0, 1.8))
            roca.set_color_scale(*_variar(campo.color, azar), 1.0)
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


@dataclass(frozen=True)
class FormaRoca:
    """Malla de una roca: vértices, normales suaves, color por vértice y triángulos."""

    puntos: NDArray[np.float32]
    normales: NDArray[np.float32]
    colores: NDArray[np.float32]
    triangulos: NDArray[np.int64]


def forma_roca(semilla: int, subdivisiones: int) -> FormaRoca:
    """Roca irregular: icosaedro subdividido y desplazado con ruido.

    Bultos grandes y detalle fino de `ruido.fractal`, unos cuantos cráteres hundidos y una
    forma alargada. Las normales son suaves (la media de las caras de alrededor) y el color
    de cada vértice oscurece las hendiduras, como una oclusión de la luz ambiente, y añade
    vetas claras y oscuras.
    """
    azar = np.random.default_rng(semilla)
    d, caras = _icosfera(subdivisiones)
    s = semilla * 13
    radio = (
        1.0
        + 1.0 * (fractal(d * 1.4, s, 3) - 0.5)
        + 0.4 * (fractal(d * 4.5, s + 1, 3) - 0.5)
        + 0.15 * (fractal(d * 11.0, s + 3, 2) - 0.5)
    )
    for _ in range(int(azar.integers(2, 6))):
        centro = azar.normal(size=3)
        centro /= np.linalg.norm(centro)
        ancho = azar.uniform(0.25, 0.6)
        distancia = np.arccos(np.clip(d @ centro, -1, 1)) / ancho
        hundido = np.clip(1 - distancia**2, 0, None) * azar.uniform(0.08, 0.18)
        borde = np.exp(-(((distancia - 1.0) / 0.25) ** 2)) * 0.04
        radio = radio - hundido + borde
    estirado = np.asarray(
        (azar.uniform(0.85, 1.35), azar.uniform(0.7, 1.0), azar.uniform(0.6, 0.9)), np.float32
    )
    puntos = (d * radio[:, None] * estirado).astype(np.float32)
    # Normales suaves: suma de las normales de las caras de cada vértice, pesadas por área.
    a, b, c = (puntos[caras[:, k]] for k in range(3))
    de_cara = np.cross(b - a, c - a)
    normales = np.zeros_like(puntos)
    for k in range(3):
        np.add.at(normales, caras[:, k], de_cara)
    normales /= np.linalg.norm(normales, axis=1, keepdims=True)
    # Hendiduras: vértices por debajo de la media de sus vecinos.
    vecinos = np.zeros(len(d), np.float32)
    cuenta = np.zeros(len(d), np.float32)
    for k in range(3):
        for m in (1, 2):
            np.add.at(vecinos, caras[:, k], radio[caras[:, (k + m) % 3]])
            np.add.at(cuenta, caras[:, k], 1.0)
    oclusion = np.clip(1.0 + 6.0 * (radio - vecinos / cuenta), 0.45, 1.15)
    vetas = 0.78 + 0.44 * fractal(d * 3.0 + np.float32(9.1), s + 2, 3)
    gris = (oclusion * vetas).astype(np.float32)
    colores = np.stack([gris, gris * 0.98, gris * 0.95, np.ones_like(gris)], axis=1)
    return FormaRoca(puntos, normales.astype(np.float32), colores.astype(np.float32), caras)


def _roca(semilla: int, subdivisiones: int) -> GeomNode:
    """Geometría del motor de `forma_roca`, escrita de una vez desde numpy."""
    forma = forma_roca(semilla, subdivisiones)
    filas = np.concatenate([forma.puntos, forma.normales, forma.colores], axis=1)
    datos = GeomVertexData("roca", _formato_roca(), Geom.UH_static)
    datos.unclean_set_num_rows(len(filas))
    memoryview(datos.modify_array(0)).cast("B")[:] = filas.astype(np.float32).tobytes()
    triangulos = GeomTriangles(Geom.UH_static)
    triangulos.set_index_type(Geom.NT_uint16)
    indices = triangulos.modify_vertices()
    indices.unclean_set_num_rows(forma.triangulos.size)
    memoryview(indices).cast("B")[:] = forma.triangulos.astype(np.uint16).tobytes()
    geom = Geom(datos)
    geom.add_primitive(triangulos)
    nodo = GeomNode("roca")
    nodo.add_geom(geom)
    return nodo


def _medio(
    puntos: list[NDArray[np.float64]], medios: dict[tuple[int, int], int], a: int, b: int
) -> int:
    """Índice del punto medio entre los puntos `a` y `b`, sobre la esfera; lo crea si falta."""
    clave = (min(a, b), max(a, b))
    if clave not in medios:
        p = puntos[a] + puntos[b]
        puntos.append(p / np.linalg.norm(p))
        medios[clave] = len(puntos) - 1
    return medios[clave]


def _formato_roca() -> GeomVertexFormat:
    """Posición, normal y color RGBA, todo en float32 y en una sola tabla."""
    if "formato-roca" not in _formatos:
        columnas = GeomVertexArrayFormat()
        columnas.add_column(InternalName.get_vertex(), 3, Geom.NT_float32, Geom.C_point)
        columnas.add_column(InternalName.get_normal(), 3, Geom.NT_float32, Geom.C_normal)
        columnas.add_column(InternalName.get_color(), 4, Geom.NT_float32, Geom.C_color)
        _formatos["formato-roca"] = GeomVertexFormat.register_format(GeomVertexFormat(columnas))
    return _formatos["formato-roca"]


_formatos: dict[str, GeomVertexFormat] = {}


def _icosfera(subdivisiones: int) -> tuple[NDArray[np.float32], NDArray[np.int64]]:
    """Esfera de radio 1: icosaedro con cada triángulo partido en 4 `subdivisiones` veces.

    Los triángulos van en sentido antihorario vistos desde fuera.
    """
    t = (1 + math.sqrt(5)) / 2
    puntos = [
        np.asarray(v, np.float64) / math.sqrt(1 + t * t)
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
    for _ in range(subdivisiones):
        medios: dict[tuple[int, int], int] = {}
        nuevas = []
        for a, b, c in caras:
            ab, bc, ca = (_medio(puntos, medios, x, y) for x, y in ((a, b), (b, c), (c, a)))
            nuevas += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        caras = nuevas
    d = np.asarray(puntos, np.float32)
    indices = np.asarray(caras, np.int64)
    # Antihorario visto desde fuera: la normal de la cara apunta hacia fuera.
    pa, pb, pc = (d[indices[:, k]] for k in range(3))
    hacia_dentro = np.einsum("ij,ij->i", np.cross(pb - pa, pc - pa), pa + pb + pc) < 0
    indices[hacia_dentro] = indices[hacia_dentro][:, [0, 2, 1]]
    return d, indices


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
