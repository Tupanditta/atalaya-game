"""Animación del salto hiperespacial entre dos fondos (RN-20; `modulos/escena.md`).

La misma en los cuatro cambios de fondo. Dura lo que el salto de `oleadas` y tiene cinco
fases, en fracciones de esa duración:

1. Carga: las estrellas se estiran poco a poco.
2. Arranque: las estrellas se vuelven estelas que pasan junto a la cámara y hay un
   destello blanco.
3. Túnel: un túnel azul envuelve la cámara y tiembla un poco. El cielo queda oculto y,
   a mitad del túnel, se cambia por el del fondo de destino.
4. Salida: las estelas se frenan y se recogen, con otro destello, y aparece el cielo
   nuevo.
5. Asentamiento: lo que queda de las estelas se apaga.

Fluidez: toda la geometría se crea una vez al arrancar. En cada fotograma solo se
escriben con numpy las posiciones y los colores de las estelas en su búfer de vértices,
y se mueve la textura del túnel.
"""

import math
from collections.abc import Callable

import numpy as np
from panda3d.core import (
    CardMaker,
    ColorBlendAttrib,
    Geom,
    GeomLines,
    GeomNode,
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
    Texture,
    TextureStage,
    TransparencyAttrib,
)

# --- fases, en fracciones de la duración del salto -----------------------------------

_FIN_CARGA = 0.2
_FIN_ARRANQUE = 0.3
_FIN_TUNEL = 0.75
_FIN_SALIDA = 0.9
#: Momento en que se cambia el cielo, oculto por el túnel.
_CAMBIO_CIELO = 0.5

# --- estelas -------------------------------------------------------------------------

#: Número de estelas.
_ESTELAS = 480
#: Distancia lateral de las estelas al eje de la marcha, en unidades de la cámara.
_RADIO_MINIMO = 2.5
_RADIO_MAXIMO = 70.0
#: Profundidad a la que nacen y mueren las estelas delante de la cámara.
_CERCA = 1.0
_LEJOS = 420.0
#: Velocidad de crucero, en unidades por segundo, y largo de la estela por unidad de
#: velocidad.
_VELOCIDAD_CRUCERO = 2600.0
_LARGO_POR_VELOCIDAD = 0.07
_LARGO_MAXIMO = 260.0
_GROSOR_ESTELA = 2.0

# --- túnel ---------------------------------------------------------------------------

_RADIO_TUNEL = 9.0
_LARGO_TUNEL = 700.0
_LADOS_TUNEL = 28
#: Repeticiones de la textura a lo largo y alrededor del túnel.
_REPETICION_LARGO = 6.0
_REPETICION_VUELTA = 2.0
#: Velocidad a la que corre la textura del túnel, en repeticiones por segundo.
_VELOCIDAD_TUNEL = 2.2
_GIRO_TUNEL = 0.05

# --- cámara --------------------------------------------------------------------------

#: Grados que se abre el campo de visión al arrancar: sensación de velocidad.
_APERTURA_ARRANQUE = 14.0
_APERTURA_TUNEL = 9.0
#: Temblor de la cámara dentro del túnel, en grados.
_TEMBLOR_TUNEL = 0.18

_COLOR_ESTELA = np.array([0.85, 0.92, 1.0], dtype=np.float32)
_COLOR_ESTELA_TUNEL = np.array([0.55, 0.78, 1.0], dtype=np.float32)

#: Orden de dibujo del destello en `render2d`: encima de la escena y debajo del HUD.
_ORDEN_DESTELLO = -8


def _suave(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def _entre(u: float, a: float, b: float) -> float:
    """0 antes de `a`, 1 después de `b` y una subida suave entre ambos."""
    return _suave((u - a) / (b - a))


def _aditivo(nodo: NodePath, orden: int) -> None:
    nodo.set_attrib(
        ColorBlendAttrib.make(
            ColorBlendAttrib.M_add, ColorBlendAttrib.O_incoming_alpha, ColorBlendAttrib.O_one
        )
    )
    nodo.set_transparency(TransparencyAttrib.M_alpha)
    nodo.set_depth_write(False)
    nodo.set_depth_test(False)
    nodo.set_light_off()
    nodo.set_bin("fixed", orden)


def textura_tunel(alto: int = 256, ancho: int = 64, semilla: int = 3) -> Texture:
    """Franjas de luz a lo largo del túnel: azul con hebras blancas."""
    azar = np.random.default_rng(semilla)
    v = np.arange(alto, dtype=np.float32)[:, None] / alto
    columnas = np.arange(ancho, dtype=np.float32)[None, :] / ancho
    intensidad = np.zeros((alto, ancho), dtype=np.float32)
    for _ in range(14):
        centro = azar.random()
        anchura = azar.uniform(0.01, 0.05)
        # Distancia alrededor del túnel, que da la vuelta.
        d = np.abs((columnas - centro + 0.5) % 1.0 - 0.5)
        hebra = np.exp(-((d / anchura) ** 2))
        # A lo largo, la hebra se enciende y se apaga varias veces.
        ciclos = int(azar.integers(1, 4))
        fase = azar.random() * 2 * math.pi
        a_lo_largo = 0.5 + 0.5 * np.sin(2 * math.pi * ciclos * v + fase)
        intensidad += hebra * a_lo_largo**2 * azar.uniform(0.4, 1.0)
    intensidad = np.clip(intensidad, 0.0, 1.0)
    rojo = 0.35 + 0.65 * intensidad**2
    verde = 0.6 + 0.4 * intensidad
    azul = np.ones_like(intensidad)
    alfa = 0.25 + 0.75 * intensidad
    imagen = np.stack([azul, verde, rojo, alfa], axis=-1)  # BGRA, el orden del motor.
    datos = np.ascontiguousarray((imagen * 255).astype(np.uint8))
    textura = Texture("tunel")
    textura.setup_2d_texture(ancho, alto, Texture.T_unsigned_byte, Texture.F_rgba)
    textura.set_ram_image(datos.data)
    textura.set_wrap_u(SamplerState.WM_repeat)
    textura.set_wrap_v(SamplerState.WM_repeat)
    textura.set_minfilter(SamplerState.FT_linear_mipmap_linear)
    textura.set_magfilter(SamplerState.FT_linear)
    return textura


class SaltoHiperespacial:
    """Animación del salto, colgada de la cámara para que siempre quede delante."""

    def __init__(
        self, camara: NodePath, render2d: NodePath, espacio: NodePath, brillo: Texture
    ) -> None:
        # Cielo y paisaje: se apagan juntos durante el túnel.
        self._espacio = espacio
        self._raiz = camara.attach_new_node("salto")
        self._raiz.hide()
        # Azar solo visual: no forma parte de la simulación.
        self._azar = np.random.default_rng()
        self._datos, estelas = self._crear_estelas()
        self._estelas = self._raiz.attach_new_node(estelas)
        _aditivo(self._estelas, 21)
        self._estelas.set_render_mode_thickness(_GROSOR_ESTELA)
        self._tunel = self._raiz.attach_new_node(self._crear_tunel())
        self._tunel.set_texture(textura_tunel())
        self._tunel.set_two_sided(True)
        _aditivo(self._tunel, 20)
        # Luz al fondo del túnel: tapa su boca y marca hacia dónde se viaja.
        tarjeta = CardMaker("fondo-tunel")
        tarjeta.set_frame(-1, 1, -1, 1)
        # Cuelga de la raíz, no del túnel: así no hereda el movimiento de su textura.
        self._luz_fondo = self._raiz.attach_new_node(tarjeta.generate())
        self._luz_fondo.set_texture(brillo)
        self._luz_fondo.set_pos(0, _LARGO_TUNEL * 0.9, 0)
        self._luz_fondo.set_scale(_RADIO_TUNEL * _LARGO_TUNEL * 0.9 / 25.0)
        self._luz_fondo.set_color(0.75, 0.88, 1.0, 1)
        _aditivo(self._luz_fondo, 22)
        self._destello = self._crear_destello(render2d)
        angulo = self._azar.uniform(0, 2 * math.pi, _ESTELAS)
        # Más estelas cerca del eje: el centro de la pantalla se llena de luz.
        radio = _RADIO_MINIMO + (_RADIO_MAXIMO - _RADIO_MINIMO) * self._azar.random(_ESTELAS) ** 1.6
        self._x = (radio * np.cos(angulo)).astype(np.float32)
        self._z = (radio * np.sin(angulo)).astype(np.float32)
        self._y = self._azar.uniform(_CERCA, _LEJOS, _ESTELAS).astype(np.float32)
        self._brillo = (0.4 + 0.6 * self._azar.random(_ESTELAS)).astype(np.float32)
        self._activo = False
        self._tiempo = 0.0
        self._duracion = 1.0
        self._cambiar_cielo: Callable[[], None] | None = None
        self._apertura = 0.0
        self._temblor = 0.0

    # --- consultas -------------------------------------------------------------------

    @property
    def activo(self) -> bool:
        """Indica si la animación está en marcha."""
        return self._activo

    @property
    def apertura(self) -> float:
        """Grados que hay que sumar al campo de visión en este fotograma."""
        return self._apertura

    @property
    def progreso(self) -> float:
        """Parte del salto ya transcurrida, de 0 a 1."""
        return min(1.0, self._tiempo / self._duracion) if self._activo else 0.0

    # --- operaciones -----------------------------------------------------------------

    def preparar(self, gsg: GraphicsStateGuardianBase) -> None:
        """Sube a la tarjeta gráfica la geometría y la textura del túnel y de las estelas."""
        self._raiz.prepare_scene(gsg)

    def iniciar(self, duracion: float, cambiar_cielo: Callable[[], None]) -> None:
        """Empieza la animación; `cambiar_cielo` pone el cielo de destino, ya oculto."""
        self._activo = True
        self._tiempo = 0.0
        self._duracion = max(duracion, 1e-3)
        self._cambiar_cielo = cambiar_cielo
        self._y[:] = self._azar.uniform(_CERCA, _LEJOS, _ESTELAS)
        self._raiz.show()
        self.avanzar(0.0, None)

    def cancelar(self) -> None:
        """Detiene la animación y deja la escena como estaba, sin destello ni túnel."""
        self._activo = False
        self._cambiar_cielo = None
        self._raiz.hide()
        self._destello.hide()
        self._espacio.clear_color_scale()
        self._apertura = 0.0

    def avanzar(self, dt: float, camara: NodePath | None) -> None:
        """Avanza la animación `dt` segundos y aplica el temblor a `camara`."""
        if not self._activo:
            return
        self._tiempo += dt
        u = self._tiempo / self._duracion
        if self._cambiar_cielo is not None and u >= _CAMBIO_CIELO:
            self._cambiar_cielo()
            self._cambiar_cielo = None
        if u >= 1.0:
            # El cielo de destino queda puesto aunque el fotograma de su cambio no llegara.
            self.cancelar()
            return
        velocidad = self._velocidad(u)
        self._mover_estelas(u, velocidad, dt)
        tunel = _entre(u, _FIN_CARGA + 0.06, _FIN_ARRANQUE + 0.04) * (
            1 - _entre(u, _FIN_TUNEL - 0.06, _FIN_TUNEL + 0.03)
        )
        self._tunel.set_alpha_scale(0.85 * tunel)
        self._luz_fondo.set_alpha_scale(tunel)
        self._tunel.set_tex_offset(
            TextureStage.get_default(),
            self._tiempo * _GIRO_TUNEL,
            -self._tiempo * _VELOCIDAD_TUNEL,
        )
        # El cielo se apaga al arrancar y vuelve, ya el nuevo, al salir del túnel.
        cielo = 1 - _entre(u, _FIN_CARGA, _FIN_ARRANQUE)
        cielo = max(cielo, _entre(u, _FIN_TUNEL - 0.02, _FIN_SALIDA))
        self._espacio.set_color_scale(cielo, cielo, cielo, 1)
        destello = max(
            math.exp(-(((u - _FIN_ARRANQUE) / 0.025) ** 2)),
            0.75 * math.exp(-(((u - _FIN_TUNEL) / 0.03) ** 2)),
        )
        if destello > 0.01:
            self._destello.show()
            self._destello.set_alpha_scale(destello)
        else:
            self._destello.hide()
        self._apertura = (
            -2.0 * _entre(u, 0.0, _FIN_CARGA) * (1 - _entre(u, _FIN_CARGA, _FIN_ARRANQUE))
            + _APERTURA_ARRANQUE
            * _entre(u, _FIN_CARGA, _FIN_ARRANQUE)
            * (1 - _entre(u, _FIN_ARRANQUE, _FIN_ARRANQUE + 0.1))
            + _APERTURA_TUNEL
            * _entre(u, _FIN_ARRANQUE, _FIN_ARRANQUE + 0.1)
            * (1 - _entre(u, _FIN_TUNEL - 0.05, _FIN_SALIDA))
        )
        if camara is not None and tunel > 0:
            t = self._tiempo
            amplitud = _TEMBLOR_TUNEL * tunel
            camara.set_hpr(
                camara,
                amplitud * math.sin(t * 47.0) * math.sin(t * 3.1),
                amplitud * math.sin(t * 39.0 + 1.1) * math.sin(t * 2.3 + 0.4),
                0,
            )

    # --- interno ---------------------------------------------------------------------

    @staticmethod
    def _velocidad(u: float) -> float:
        """Velocidad de las estelas en cada momento del salto."""
        if u < _FIN_CARGA:
            return 40.0 * _entre(u, 0.0, _FIN_CARGA)
        if u < _FIN_ARRANQUE:
            # Subida exponencial: el tirón del arranque.
            k = (u - _FIN_CARGA) / (_FIN_ARRANQUE - _FIN_CARGA)
            return 40.0 * math.pow(_VELOCIDAD_CRUCERO / 40.0, k)
        if u < _FIN_TUNEL:
            return _VELOCIDAD_CRUCERO
        k = _entre(u, _FIN_TUNEL, _FIN_SALIDA)
        return _VELOCIDAD_CRUCERO * (1 - k) ** 3

    def _mover_estelas(self, u: float, velocidad: float, dt: float) -> None:
        y = self._y
        y -= np.float32(velocidad * dt)
        # Las que pasan junto a la cámara vuelven a nacer al fondo.
        atras = y < _CERCA
        y[atras] += np.float32(_LEJOS - _CERCA)
        largo = np.float32(min(_LARGO_MAXIMO, 0.3 + velocidad * _LARGO_POR_VELOCIDAD))
        posiciones = np.frombuffer(
            memoryview(self._datos.modify_array(0)), dtype=np.float32
        ).reshape(_ESTELAS, 2, 3)
        posiciones[:, 0, 0] = self._x
        posiciones[:, 0, 1] = y
        posiciones[:, 0, 2] = self._z
        posiciones[:, 1, 0] = self._x
        posiciones[:, 1, 1] = y + largo
        posiciones[:, 1, 2] = self._z
        # Las estelas aparecen en la carga y se apagan en el asentamiento.
        visible = _entre(u, 0.0, _FIN_CARGA * 0.6) * (1 - _entre(u, _FIN_SALIDA, 1.0))
        # Más tenues dentro del túnel, donde manda su luz.
        visible *= 1 - 0.45 * _entre(u, _FIN_ARRANQUE, _FIN_ARRANQUE + 0.08) * (
            1 - _entre(u, _FIN_TUNEL - 0.05, _FIN_TUNEL)
        )
        mezcla = _entre(u, _FIN_CARGA, _FIN_ARRANQUE) * (1 - _entre(u, _FIN_TUNEL, _FIN_SALIDA))
        tono = _COLOR_ESTELA * (1 - mezcla) + _COLOR_ESTELA_TUNEL * mezcla
        # Las lejanas, más tenues: dan profundidad.
        cercania = np.clip(1.15 - y / _LEJOS, 0.0, 1.0)
        alfa = self._brillo * cercania * np.float32(visible)
        colores = np.frombuffer(memoryview(self._datos.modify_array(1)), dtype=np.float32).reshape(
            _ESTELAS, 2, 4
        )
        colores[:, :, :3] = tono
        # La cabeza, cerca de la cámara, brilla; la cola se apaga.
        colores[:, 0, 3] = alfa
        colores[:, 1, 3] = 0.0

    def _crear_estelas(self) -> tuple[GeomVertexData, GeomNode]:
        posicion = GeomVertexArrayFormat()
        posicion.add_column(InternalName.get_vertex(), 3, Geom.NT_float32, Geom.C_point)
        color = GeomVertexArrayFormat()
        color.add_column(InternalName.get_color(), 4, Geom.NT_float32, Geom.C_color)
        formato = GeomVertexFormat()
        formato.add_array(posicion)
        formato.add_array(color)
        datos = GeomVertexData(
            "estelas", GeomVertexFormat.register_format(formato), Geom.UH_dynamic
        )
        datos.unclean_set_num_rows(2 * _ESTELAS)
        lineas = GeomLines(Geom.UH_static)
        for i in range(_ESTELAS):
            lineas.add_vertices(2 * i, 2 * i + 1)
        geom = Geom(datos)
        geom.add_primitive(lineas)
        nodo = GeomNode("estelas")
        nodo.add_geom(geom)
        # Las posiciones cambian en cada fotograma: un volumen infinito evita recalcular la
        # caja y que el motor recorte estelas que sí se ven.
        nodo.set_bounds(OmniBoundingVolume())
        nodo.set_final(True)
        return datos, nodo

    @staticmethod
    def _crear_tunel() -> GeomNode:
        datos = GeomVertexData("tunel", GeomVertexFormat.get_v3t2(), Geom.UH_static)
        vertices = GeomVertexWriter(datos, "vertex")
        coordenadas = GeomVertexWriter(datos, "texcoord")
        for i in range(_LADOS_TUNEL + 1):
            angulo = 2 * math.pi * i / _LADOS_TUNEL
            x, z = _RADIO_TUNEL * math.cos(angulo), _RADIO_TUNEL * math.sin(angulo)
            u = _REPETICION_VUELTA * i / _LADOS_TUNEL
            for y, v in ((_CERCA, 0.0), (_LARGO_TUNEL, _REPETICION_LARGO)):
                vertices.add_data3(x, y, z)
                coordenadas.add_data2(u, v)
        triangulos = GeomTriangles(Geom.UH_static)
        for i in range(_LADOS_TUNEL):
            a, b, c, d = 2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3
            triangulos.add_vertices(a, c, b)
            triangulos.add_vertices(b, c, d)
        geom = Geom(datos)
        geom.add_primitive(triangulos)
        nodo = GeomNode("tunel")
        nodo.add_geom(geom)
        return nodo

    @staticmethod
    def _crear_destello(render2d: NodePath) -> NodePath:
        tarjeta = CardMaker("destello-salto")
        tarjeta.set_frame(-1, 1, -1, 1)
        destello = render2d.attach_new_node(tarjeta.generate())
        destello.set_color(0.9, 0.95, 1.0, 1)
        destello.set_transparency(TransparencyAttrib.M_alpha)
        destello.set_depth_test(False)
        destello.set_depth_write(False)
        destello.set_bin("fixed", _ORDEN_DESTELLO)
        destello.hide()
        return destello
