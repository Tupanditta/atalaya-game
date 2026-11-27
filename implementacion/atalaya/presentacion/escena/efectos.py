"""Efectos visuales de la escena (`modulos/escena.md`).

Del disparo: disparo bláster que vuela del cañón al impacto con su fogonazo, destello y
chispas en el impacto, y explosión con bola de fuego, onda expansiva en anillo, chispas,
restos incandescentes y sacudida de la cámara. De los ataques enemigos: proyectiles con
estela y daño recibido (temblor de la cámara y tinte rojo en los bordes). Cada efecto
avanza con el tiempo de los fotogramas y se borra solo al terminar.
"""

import math
import random
from typing import Protocol

from panda3d.core import (
    CardMaker,
    ColorBlendAttrib,
    Geom,
    GeomNode,
    GeomPoints,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    LineSegs,
    NodePath,
    OmniBoundingVolume,
    PNMImage,
    TexGenAttrib,
    Texture,
    TextureStage,
    TransparencyAttrib,
    Vec3,
)

#: Tiempo máximo de vuelo del disparo hasta el impacto, en segundos (`design.md`, sección 6).
DURACION_RAYO = 0.1
#: Duración del destello de impacto en un enemigo.
DURACION_DESTELLO = 0.15
#: Duración de la explosión de un enemigo destruido.
DURACION_EXPLOSION = 1.2

_COLOR_RAYO = (0.55, 0.93, 1.0)
_COLOR_EXPLOSION = (1.0, 0.62, 0.35)
_COLOR_FUEGO_EXTERIOR = (0.9, 0.28, 0.08)
_COLOR_CHISPA = (1.0, 0.85, 0.6)
_COLOR_BRASA = (1.0, 0.45, 0.12)
_COLOR_RESTOS = (0x1B / 255, 0x22 / 255, 0x33 / 255, 1.0)
_PARTICULAS = 28
_RESTOS = 6

#: Velocidad del disparo bláster, en unidades por segundo, y tiempo mínimo de vuelo: el
#: haz siempre se llega a ver volar, también contra un enemigo cercano.
_VELOCIDAD_RAYO = 9000.0
_VUELO_MINIMO = 0.035
#: La cola del haz sale del cañón cuando la cabeza lleva esta parte del vuelo, y llega al
#: impacto este tiempo después que la cabeza.
_SALIDA_COLA = 0.35
_RETRASO_COLA = 0.06
#: Fogonazo del cañón: tamaño y duración.
_TAMANO_FOGONAZO = 0.2
_DURACION_FOGONAZO = 0.07
#: Chispas del impacto en un enemigo.
_CHISPAS_IMPACTO = 9
_DURACION_CHISPAS = 0.3
#: Píxeles por unidad del mundo a una unidad de distancia, con 1080 px para 70° de campo
#: de visión vertical: da el tamaño en pantalla de las chispas, que son puntos.
_PIXELES_POR_UNIDAD = 771.0
_PUNTO_MINIMO = 2.0
_PUNTO_MAXIMO = 18.0


class Efecto(Protocol):
    def avanzar(self, dt: float) -> bool:
        """Avanza el efecto `dt` segundos. Devuelve si sigue vivo."""


def textura_brillo(lado: int = 64) -> Texture:
    """Mancha de luz redonda que se apaga hacia los bordes."""
    imagen = PNMImage(lado, lado, 4)
    centro = (lado - 1) / 2
    for y in range(lado):
        for x in range(lado):
            d = math.hypot(x - centro, y - centro) / centro
            intensidad = max(0.0, 1 - d) ** 2
            imagen.set_xel_a(x, y, 1.0, 1.0, 1.0, intensidad)
    textura = Texture("brillo")
    textura.load(imagen)
    return textura


def _aditivo(nodo: NodePath) -> None:
    """Mezcla aditiva sin escribir profundidad: la luz se suma a lo que hay detrás."""
    nodo.set_attrib(
        ColorBlendAttrib.make(
            ColorBlendAttrib.M_add, ColorBlendAttrib.O_incoming_alpha, ColorBlendAttrib.O_one
        )
    )
    nodo.set_transparency(TransparencyAttrib.M_alpha)
    nodo.set_depth_write(False)
    nodo.set_light_off()
    nodo.set_bin("fixed", 10)


def brillo(padre: NodePath, textura: Texture, color: tuple[float, float, float]) -> NodePath:
    """Mancha de luz aditiva que siempre mira a la cámara."""
    return _tarjeta(padre, textura, color)


def _tarjeta(padre: NodePath, textura: Texture, color: tuple[float, float, float]) -> NodePath:
    tarjeta = CardMaker("brillo")
    tarjeta.set_frame(-1, 1, -1, 1)
    nodo = padre.attach_new_node(tarjeta.generate())
    nodo.set_texture(textura)
    nodo.set_color(*color, 1.0)
    nodo.set_billboard_point_eye()
    _aditivo(nodo)
    return nodo


class Rayo:
    """Disparo bláster: un haz brillante que sale del cañón y vuela hasta el impacto.

    Con núcleo blanco y halo del color del disparo. La cabeza llega al impacto en
    `duracion_vuelo`, como mucho 0,1 s. La cola sale del cañón un poco después y alcanza
    el impacto en `_RETRASO_COLA` más, mientras el haz se apaga. Como el disparo va casi
    en la línea de visión, un haz corto se vería como un punto: así se ve la traza
    entera, del cañón al blanco, y su movimiento. En el cañón deja un fogonazo.
    """

    def __init__(self, padre: NodePath, textura: Texture, inicio: Vec3, fin: Vec3) -> None:
        recorrido = fin - inicio
        self._distancia = max(recorrido.length(), 1e-3)
        self._direccion = recorrido / self._distancia
        self._inicio = Vec3(inicio)
        self.duracion_vuelo = min(
            DURACION_RAYO, max(_VUELO_MINIMO, self._distancia / _VELOCIDAD_RAYO)
        )
        self._nodo = padre.attach_new_node("rayo")
        for grosor, color, alfa in (
            (14.0, _COLOR_RAYO, 0.28),
            (6.0, _COLOR_RAYO, 0.85),
            (2.5, (1.0, 1.0, 1.0), 1.0),
        ):
            linea = LineSegs("rayo")
            linea.set_thickness(grosor)
            # Cola tenue y cabeza brillante: se ve hacia dónde va.
            linea.set_color(*color, alfa * 0.25)
            linea.move_to(0, 0, 0)
            linea.set_color(*color, alfa)
            linea.draw_to(0, 1, 0)
            self._nodo.attach_new_node(linea.create())
        _aditivo(self._nodo)
        self._nodo.look_at(fin)
        self._fogonazo = _tarjeta(padre, textura, _COLOR_RAYO)
        self._fogonazo.set_pos(inicio)
        self._tiempo = 0.0
        self.avanzar(0.0)

    def avanzar(self, dt: float) -> bool:
        self._tiempo += dt
        fogonazo = 1 - self._tiempo / _DURACION_FOGONAZO
        if fogonazo > 0:
            self._fogonazo.set_scale(_TAMANO_FOGONAZO * (1.4 - 0.6 * fogonazo))
            self._fogonazo.set_alpha_scale(fogonazo)
        else:
            self._fogonazo.hide()
        vuelo = self.duracion_vuelo
        cola_t = (self._tiempo - vuelo * _SALIDA_COLA) / (
            vuelo * (1 - _SALIDA_COLA) + _RETRASO_COLA
        )
        if cola_t >= 1:
            self._nodo.remove_node()
            self._fogonazo.remove_node()
            return False
        cabeza = self._distancia * min(1.0, self._tiempo / vuelo)
        cola = self._distancia * max(0.0, cola_t)
        self._nodo.set_pos(self._inicio + self._direccion * cola)
        self._nodo.set_scale(1, max(1e-3, cabeza - cola), 1)
        # Se apaga mientras la cola recorre el camino.
        self._nodo.set_alpha_scale(1 - max(0.0, cola_t) ** 2)
        return True


class Destello:
    """Destello breve en el punto de impacto sobre un enemigo.

    Con `retraso`, espera a que llegue el disparo antes de encenderse.
    """

    def __init__(
        self, padre: NodePath, textura: Texture, punto: Vec3, tamano: float, retraso: float = 0.0
    ) -> None:
        self._nodo = _tarjeta(padre, textura, _COLOR_RAYO)
        self._nodo.set_pos(punto)
        self._tamano = tamano
        self._tiempo = -retraso
        self.avanzar(0.0)

    def avanzar(self, dt: float) -> bool:
        self._tiempo += dt
        if self._tiempo < 0:
            self._nodo.hide()
            return True
        self._nodo.show()
        t = self._tiempo / DURACION_DESTELLO
        if t >= 1:
            self._nodo.remove_node()
            return False
        self._nodo.set_scale(self._tamano * (0.6 + 0.8 * t))
        self._nodo.set_alpha_scale(1 - t)
        return True


def _direcciones(azar: random.Random, numero: int) -> list[Vec3]:
    return [
        Vec3(azar.gauss(0, 1), azar.gauss(0, 1), azar.gauss(0, 1)).normalized()
        for _ in range(numero)
    ]


def _puntos(
    padre: NodePath,
    textura: Texture,
    velocidades: list[Vec3],
    color: tuple[float, float, float],
    diametro: float,
    distancia: float,
) -> NodePath:
    """Chispas como una sola geometría de puntos con textura: un único dibujo.

    Cada punto está en su velocidad, así que escalar el nodo por el camino recorrido
    mueve todas las chispas a la vez. El tamaño en pantalla se fija según la distancia.
    """
    datos = GeomVertexData("chispas", GeomVertexFormat.get_v3(), Geom.UH_static)
    vertices = GeomVertexWriter(datos, "vertex")
    puntos = GeomPoints(Geom.UH_static)
    for i, velocidad in enumerate(velocidades):
        vertices.add_data3(velocidad)
        puntos.add_vertex(i)
    geom = Geom(datos)
    geom.add_primitive(puntos)
    geom_nodo = GeomNode("chispas")
    geom_nodo.add_geom(geom)
    # La escala del nodo cambia en cada fotograma: un volumen infinito evita recalcularlo.
    geom_nodo.set_bounds(OmniBoundingVolume())
    geom_nodo.set_final(True)
    nodo = padre.attach_new_node(geom_nodo)
    nodo.set_texture(textura)
    nodo.set_tex_gen(TextureStage.get_default(), TexGenAttrib.M_point_sprite)
    pixeles = _PIXELES_POR_UNIDAD * diametro / max(distancia, 1.0)
    nodo.set_render_mode_thickness(min(_PUNTO_MAXIMO, max(_PUNTO_MINIMO, pixeles)))
    nodo.set_color(*color, 1.0)
    _aditivo(nodo)
    return nodo


class Chispas:
    """Chispas que saltan desde un punto y se apagan; con `retraso`, esperan al disparo."""

    def __init__(
        self,
        padre: NodePath,
        textura: Texture,
        punto: Vec3,
        tamano: float,
        color: tuple[float, float, float] = _COLOR_CHISPA,
        numero: int = _CHISPAS_IMPACTO,
        retraso: float = 0.0,
    ) -> None:
        # Azar solo visual: no forma parte de la simulación.
        azar = random.Random()
        velocidades = [d * tamano * azar.uniform(3.0, 7.0) for d in _direcciones(azar, numero)]
        self._nodo = _puntos(padre, textura, velocidades, color, tamano * 0.15, punto.length())
        self._nodo.set_pos(punto)
        self._recorrido = 0.0
        self._tiempo = -retraso
        self.avanzar(0.0)

    def avanzar(self, dt: float) -> bool:
        self._tiempo += dt
        if self._tiempo < 0:
            self._nodo.hide()
            return True
        self._nodo.show()
        t = self._tiempo / _DURACION_CHISPAS
        if t >= 1:
            self._nodo.remove_node()
            return False
        self._recorrido += dt * (1 - t)
        self._nodo.set_scale(max(1e-4, self._recorrido))
        self._nodo.set_alpha_scale((1 - t) ** 1.5)
        return True


def textura_anillo(lado: int = 128) -> Texture:
    """Anillo de luz de borde suave, para la onda expansiva de las explosiones."""
    imagen = PNMImage(lado, lado, 4)
    centro = (lado - 1) / 2
    for y in range(lado):
        for x in range(lado):
            d = math.hypot(x - centro, y - centro) / centro
            borde = math.exp(-(((d - 0.8) / 0.09) ** 2))
            relleno = 0.12 * max(0.0, 1 - abs(d - 0.55) / 0.3) if d < 0.8 else 0.0
            imagen.set_xel_a(x, y, 1.0, 1.0, 1.0, min(1.0, borde + relleno))
    textura = Texture("anillo")
    textura.load(imagen)
    textura.set_wrap_u(Texture.WM_clamp)
    textura.set_wrap_v(Texture.WM_clamp)
    return textura


_geometria_restos: GeomNode | None = None


def _resto() -> GeomNode:
    """Tetraedro pequeño, compartido por todos los restos de las explosiones."""
    global _geometria_restos
    if _geometria_restos is None:
        puntos = [Vec3(1, 1, 1), Vec3(-1, -1, 1), Vec3(-1, 1, -1), Vec3(1, -1, -1)]
        datos = GeomVertexData("resto", GeomVertexFormat.get_v3n3(), Geom.UH_static)
        vertices = GeomVertexWriter(datos, "vertex")
        normales = GeomVertexWriter(datos, "normal")
        triangulos = GeomTriangles(Geom.UH_static)
        for i, (a, b, c) in enumerate(((0, 1, 2), (0, 3, 1), (0, 2, 3), (1, 3, 2))):
            pa, pb, pc = puntos[a], puntos[b], puntos[c]
            normal = (pb - pa).cross(pc - pa).normalized()
            if normal.dot(pa + pb + pc) < 0:
                pb, pc, normal = pc, pb, -normal
            for punto in (pa, pb, pc):
                vertices.add_data3(punto)
                normales.add_data3(normal)
            triangulos.add_vertices(3 * i, 3 * i + 1, 3 * i + 2)
        geom = Geom(datos)
        geom.add_primitive(triangulos)
        _geometria_restos = GeomNode("resto")
        _geometria_restos.add_geom(geom)
    return _geometria_restos


class Explosion:
    """Explosión de un enemigo destruido.

    - Fogonazo blanco y bola de fuego que crece y se apaga.
    - Onda expansiva: un anillo del color del tipo, en un plano al azar, que se ensancha.
    - Chispas que salen despedidas y restos oscuros que giran con una brasa encendida.
    """

    def __init__(
        self,
        padre: NodePath,
        textura: Texture,
        anillo: Texture,
        punto: Vec3,
        tamano: float,
        color_tipo: tuple[float, float, float] = _COLOR_EXPLOSION,
    ) -> None:
        # Azar solo visual: no forma parte de la simulación.
        azar = random.Random()
        self._nodo = padre.attach_new_node("explosion")
        self._nodo.set_pos(punto)
        self._tamano = tamano
        self._fogonazo = _tarjeta(self._nodo, textura, (1.0, 1.0, 1.0))
        self._fuego_exterior = _tarjeta(self._nodo, textura, _COLOR_FUEGO_EXTERIOR)
        self._fuego = _tarjeta(self._nodo, textura, _COLOR_EXPLOSION)
        tarjeta = CardMaker("onda")
        tarjeta.set_frame(-1, 1, -1, 1)
        self._onda = self._nodo.attach_new_node(tarjeta.generate())
        self._onda.set_texture(anillo)
        mezcla = tuple(0.55 * c + 0.45 for c in color_tipo)
        self._onda.set_color(*mezcla, 1.0)
        self._onda.set_hpr(azar.uniform(0, 360), azar.uniform(-60, 60), azar.uniform(0, 360))
        self._onda.set_two_sided(True)
        _aditivo(self._onda)
        distancia = punto.length()
        velocidades = [d * tamano * azar.uniform(2.5, 7.0) for d in _direcciones(azar, _PARTICULAS)]
        self._chispas = _puntos(
            self._nodo, textura, velocidades, _COLOR_CHISPA, tamano * 0.35, distancia
        )
        self._recorrido = 0.0
        # Restos: tetraedros que giran, cada uno con una brasa encendida en su sitio.
        self._grupo_restos = self._nodo.attach_new_node("restos")
        self._grupo_restos.set_transparency(TransparencyAttrib.M_alpha)
        self._restos: list[tuple[NodePath, Vec3, Vec3, Vec3]] = []
        velocidades_restos = []
        for direccion in _direcciones(azar, _RESTOS):
            # Un nodo propio por resto: la geometría compartida cuelga de cada uno.
            resto = self._grupo_restos.attach_new_node("resto")
            resto.attach_new_node(_resto())
            resto.set_color(*_COLOR_RESTOS)
            resto.set_scale(tamano * azar.uniform(0.04, 0.08))
            inicial = Vec3(azar.uniform(0, 360), azar.uniform(0, 360), azar.uniform(0, 360))
            velocidad = direccion * tamano * azar.uniform(0.8, 2.2)
            giro = Vec3(azar.uniform(-400, 400), azar.uniform(-400, 400), azar.uniform(-400, 400))
            self._restos.append((resto, velocidad, inicial, giro))
            velocidades_restos.append(velocidad)
        self._brasas = _puntos(
            self._nodo, textura, velocidades_restos, _COLOR_BRASA, tamano * 0.4, distancia
        )
        self._tiempo = 0.0
        self.avanzar(0.0)

    def avanzar(self, dt: float) -> bool:
        self._tiempo += dt
        t = self._tiempo / DURACION_EXPLOSION
        if t >= 1:
            self._nodo.remove_node()
            return False
        r = self._tamano
        # Fogonazo: muy rápido, en el primer 15 %.
        fogonazo = min(1.0, t / 0.15)
        self._fogonazo.set_scale(r * (1.2 + 2.5 * fogonazo))
        self._fogonazo.set_alpha_scale(max(0.0, 1 - fogonazo) ** 2)
        # Bola de fuego: crece deprisa y se apaga hacia la mitad.
        fuego = min(1.0, t / 0.5)
        crecimiento = 1 - (1 - min(1.0, t / 0.3)) ** 3
        self._fuego.set_scale(r * (0.6 + 2.6 * crecimiento))
        self._fuego.set_alpha_scale(max(0.0, 1 - fuego) ** 1.5)
        self._fuego_exterior.set_scale(r * (0.8 + 3.4 * crecimiento))
        self._fuego_exterior.set_alpha_scale(0.8 * max(0.0, 1 - fuego) ** 1.2)
        # Onda expansiva: se ensancha frenando y se desvanece.
        onda = min(1.0, t / 0.6)
        self._onda.set_scale(r * (0.5 + 4.5 * (1 - (1 - onda) ** 2.5)))
        self._onda.set_alpha_scale(0.7 * (1 - onda) ** 2)
        apagado = 1 - t
        self._recorrido += dt * (1 - t * 0.6)
        self._chispas.set_scale(max(1e-4, self._recorrido))
        self._chispas.set_alpha_scale(apagado)
        # Los restos no frenan: su posición es su velocidad por el tiempo.
        for resto, velocidad, inicial, giro in self._restos:
            resto.set_pos(velocidad * self._tiempo)
            resto.set_hpr(inicial + giro * self._tiempo)
        self._grupo_restos.set_alpha_scale(min(1.0, 3 * apagado))
        self._brasas.set_scale(max(1e-4, self._tiempo))
        self._brasas.set_alpha_scale(apagado**2)
        return True


class Calentamiento:
    """Efectos que se dibujan solo en los primeros fotogramas, lejos y diminutos.

    La primera vez que se dibuja cada combinación de estados, el controlador gráfico la
    prepara y ese fotograma tarda más. Así ocurre en el menú, sin que se note, y no con la
    primera explosión de la partida.
    """

    _FOTOGRAMAS = 2

    def __init__(self, efectos: list[Efecto], quitar: list[NodePath]) -> None:
        self._efectos = efectos
        self._quitar = quitar
        self._restantes = self._FOTOGRAMAS

    def avanzar(self, dt: float) -> bool:
        self._restantes -= 1
        # Con un tiempo infinito (la escena se limpia) termina en el acto.
        if self._restantes > 0 and dt < math.inf:
            return True
        for efecto in self._efectos:
            efecto.avanzar(math.inf)
        for nodo in self._quitar:
            nodo.remove_node()
        return False


class Sacudida:
    """Sacudida breve de la cámara por una explosión cercana. Solo visual."""

    #: Rapidez con que se apaga, por segundo.
    _AMORTIGUACION = 8.0

    def __init__(self) -> None:
        self._fuerza = 0.0
        self._tiempo = 0.0

    def sacudir(self, amplitud: float) -> None:
        """Empieza una sacudida de `amplitud` grados, o refuerza la que hay."""
        self._fuerza = max(self._fuerza, amplitud)

    def avanzar(self, dt: float, camara: NodePath) -> None:
        self._tiempo += dt
        self._fuerza *= math.exp(-self._AMORTIGUACION * dt)
        if self._fuerza < 1e-3:
            self._fuerza = 0.0
            return
        t, a = self._tiempo, self._fuerza
        camara.set_hpr(
            camara,
            a * (math.sin(t * 71.0) * 0.6 + math.sin(t * 43.0 + 0.9) * 0.4),
            a * (math.sin(t * 59.0 + 0.4) * 0.6 + math.sin(t * 31.0 + 1.7) * 0.4),
            0,
        )


# --- ataques enemigos (S3) -----------------------------------------------------------

#: Daño recibido: tinte rojo en los bordes (`interfaz.md`, «Avisos») y turbulencia, una
#: sacudida breve y fuerte de la cámara que también mueve la mira.
DURACION_DANO = 0.3
DURACION_TURBULENCIA = 0.2
#: Giro máximo de la cámara durante la turbulencia, en grados. Solo es visual.
TURBULENCIA_MAXIMA = 1.3
#: Opacidad del tinte rojo de los bordes al recibir daño.
_OPACIDAD_TINTE = 0.4
#: Color «peligro» de `interfaz.md`.
_COLOR_PELIGRO = (1.0, 0x4D / 255, 0x5E / 255)

#: Tamaño mínimo del brillo de un proyectil, como fracción de su distancia a la cámara:
#: así se ve durante todo el recorrido, también desde lejos (CU-06).
_TAMANO_ANGULAR_PROYECTIL = 0.02
_TAMANO_PROYECTIL = 3.0
#: Largo de la estela de un proyectil, en unidades del mundo.
_LARGO_ESTELA = 45.0


def textura_vineta(lado: int = 128) -> Texture:
    """Viñeta: transparente en el centro y opaca hacia los bordes de la pantalla."""
    imagen = PNMImage(lado, lado, 4)
    centro = (lado - 1) / 2
    for y in range(lado):
        for x in range(lado):
            # Distancia al centro con forma de rectángulo redondeado.
            dx, dy = abs(x - centro) / centro, abs(y - centro) / centro
            d = (dx**4 + dy**4) ** 0.25
            intensidad = min(1.0, max(0.0, (d - 0.55) / 0.45)) ** 1.6
            imagen.set_xel_a(x, y, 1.0, 1.0, 1.0, intensidad)
    textura = Texture("vineta")
    textura.load(imagen)
    textura.set_wrap_u(Texture.WM_clamp)
    textura.set_wrap_v(Texture.WM_clamp)
    return textura


class Proyectil:
    """Esfera luminosa del color del tipo con una estela de dardo bláster detrás."""

    def __init__(
        self, padre: NodePath, textura: Texture, color_tipo: tuple[float, float, float]
    ) -> None:
        self.nodo = padre.attach_new_node("proyectil")
        self._brillo = _tarjeta(self.nodo, textura, color_tipo)
        self._nucleo = _tarjeta(self.nodo, textura, (1.0, 1.0, 1.0))
        # Estela de dardo bláster: halo del color del tipo y núcleo blanco más corto.
        self._estela = self.nodo.attach_new_node("estela")
        for grosor, color, largo in (
            (5.0, color_tipo, _LARGO_ESTELA),
            (1.8, (1.0, 1.0, 1.0), _LARGO_ESTELA * 0.5),
        ):
            estela = LineSegs("estela")
            estela.set_thickness(grosor)
            estela.set_color(*color, 0.95)
            estela.move_to(0, 0, 0)
            estela.set_color(*color, 0.0)
            estela.draw_to(0, -largo, 0)
            self._estela.attach_new_node(estela.create())
        _aditivo(self._estela)

    def colocar(self, posicion: Vec3, velocidad: Vec3) -> None:
        """Pone el proyectil en `posicion`, con la estela en sentido contrario a la marcha."""
        self.nodo.set_pos(posicion)
        if velocidad.length() > 1e-6:
            self.nodo.look_at(posicion + velocidad)
        tamano = max(_TAMANO_PROYECTIL, posicion.length() * _TAMANO_ANGULAR_PROYECTIL)
        self._brillo.set_scale(tamano)
        self._nucleo.set_scale(tamano * 0.45)

    def quitar(self) -> None:
        self.nodo.remove_node()


def turbulencia(tiempo: float, fuerza: float, fase: float = 0.0) -> tuple[float, float]:
    """Desvío de la turbulencia en el instante `tiempo`, en grados (rumbo, cabeceo).

    Ruido suave: suma de senos de frecuencias que no son múltiplos entre sí. `fuerza` va
    de 0 a 1; con otra `fase` sale otro temblor del mismo carácter.
    """
    t = tiempo + fase
    amplitud = TURBULENCIA_MAXIMA * fuerza
    rumbo = amplitud * (math.sin(t * 61.0) * 0.6 + math.sin(t * 37.0 + 1.3) * 0.4)
    cabeceo = amplitud * (math.sin(t * 53.0 + 0.7) * 0.6 + math.sin(t * 29.0 + 2.1) * 0.4)
    return rumbo, cabeceo


class DanoRecibido:
    """Turbulencia de la cámara y tinte rojo en los bordes al recibir daño (RF-14).

    La turbulencia dura 0,2 s y es solo visual: gira la cámara de la escena, no la
    orientación de `vista`. La mira tiembla a la vez desde el HUD.
    """

    def __init__(self, render2d: NodePath) -> None:
        tarjeta = CardMaker("tinte-dano")
        tarjeta.set_frame(-1, 1, -1, 1)
        self._tinte = render2d.attach_new_node(tarjeta.generate())
        self._tinte.set_texture(textura_vineta())
        self._tinte.set_color(*_COLOR_PELIGRO, 1.0)
        self._tinte.set_transparency(TransparencyAttrib.M_alpha)
        self._tinte.set_depth_test(False)
        self._tinte.set_depth_write(False)
        # Por debajo del HUD, que también cuelga de `render2d`.
        self._tinte.set_bin("fixed", -10)
        self._tinte.hide()
        self._restante = 0.0
        self._turbulencia = 0.0
        self._tiempo = 0.0

    def recibir(self) -> None:
        """Empieza (o renueva) la turbulencia y el tinte."""
        self._restante = DURACION_DANO
        self._turbulencia = DURACION_TURBULENCIA

    def avanzar(self, dt: float, camara: NodePath) -> None:
        """Aplica el temblor a `camara`, ya orientada en este fotograma, y apaga el tinte."""
        self._tiempo += dt
        if self._restante <= 0:
            return
        self._restante = max(0.0, self._restante - dt)
        self._turbulencia = max(0.0, self._turbulencia - dt)
        fuerza = self._restante / DURACION_DANO
        if fuerza == 0:
            self._tinte.hide()
            return
        self._tinte.show()
        self._tinte.set_alpha_scale(_OPACIDAD_TINTE * fuerza)
        if self._turbulencia > 0:
            rumbo, cabeceo = turbulencia(self._tiempo, self._turbulencia / DURACION_TURBULENCIA)
            camara.set_hpr(camara, rumbo, cabeceo, 0)
