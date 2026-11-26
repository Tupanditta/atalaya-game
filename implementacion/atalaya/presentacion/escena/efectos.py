"""Efectos visuales de la escena (`modulos/escena.md`).

Del disparo (S2): rayo, destello de impacto y explosión. Cada uno avanza con el tiempo
de los fotogramas y se borra solo al terminar. De los ataques enemigos (S3): proyectiles
con estela y daño recibido (temblor de la cámara y tinte rojo en los bordes).
"""

import math
import random
from typing import Protocol

from panda3d.core import (
    CardMaker,
    ColorBlendAttrib,
    LineSegs,
    NodePath,
    PNMImage,
    Texture,
    TransparencyAttrib,
    Vec3,
)

#: Duración del rayo del disparo, en segundos (`design.md`, sección 6).
DURACION_RAYO = 0.1
#: Duración del destello de impacto en un enemigo.
DURACION_DESTELLO = 0.15
#: Duración de la explosión de un enemigo destruido.
DURACION_EXPLOSION = 0.9

_COLOR_RAYO = (0.55, 0.93, 1.0)
_COLOR_EXPLOSION = (1.0, 0.62, 0.35)
_PARTICULAS = 28


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
    """Línea luminosa de la estación al punto de impacto que se desvanece en 0,1 s."""

    def __init__(self, padre: NodePath, inicio: Vec3, fin: Vec3) -> None:
        self._nodo = padre.attach_new_node("rayo")
        for grosor, alfa in ((9.0, 0.25), (3.0, 1.0)):
            linea = LineSegs("rayo")
            linea.set_thickness(grosor)
            linea.set_color(*_COLOR_RAYO, alfa)
            linea.move_to(inicio)
            linea.draw_to(fin)
            self._nodo.attach_new_node(linea.create())
        _aditivo(self._nodo)
        self._tiempo = 0.0

    def avanzar(self, dt: float) -> bool:
        self._tiempo += dt
        if self._tiempo >= DURACION_RAYO:
            self._nodo.remove_node()
            return False
        self._nodo.set_alpha_scale(1 - self._tiempo / DURACION_RAYO)
        return True


class Destello:
    """Destello breve en el punto de impacto sobre un enemigo."""

    def __init__(self, padre: NodePath, textura: Texture, punto: Vec3, tamano: float) -> None:
        self._nodo = _tarjeta(padre, textura, _COLOR_RAYO)
        self._nodo.set_pos(punto)
        self._tamano = tamano
        self._tiempo = 0.0
        self.avanzar(0.0)

    def avanzar(self, dt: float) -> bool:
        self._tiempo += dt
        t = self._tiempo / DURACION_DESTELLO
        if t >= 1:
            self._nodo.remove_node()
            return False
        self._nodo.set_scale(self._tamano * (0.6 + 0.8 * t))
        self._nodo.set_alpha_scale(1 - t)
        return True


class Explosion:
    """Destello de luz y chispas que salen despedidas desde el enemigo destruido."""

    def __init__(self, padre: NodePath, textura: Texture, punto: Vec3, tamano: float) -> None:
        # Azar solo visual: no forma parte de la simulación.
        azar = random.Random()
        self._nodo = padre.attach_new_node("explosion")
        self._nodo.set_pos(punto)
        self._tamano = tamano
        self._luz = _tarjeta(self._nodo, textura, _COLOR_EXPLOSION)
        self._chispas: list[tuple[NodePath, Vec3]] = []
        for _ in range(_PARTICULAS):
            chispa = _tarjeta(self._nodo, textura, (1.0, 0.85, 0.6))
            direccion = Vec3(azar.gauss(0, 1), azar.gauss(0, 1), azar.gauss(0, 1)).normalized()
            velocidad = direccion * tamano * azar.uniform(2.0, 6.0)
            chispa.set_scale(tamano * azar.uniform(0.12, 0.3))
            self._chispas.append((chispa, velocidad))
        self._tiempo = 0.0
        self.avanzar(0.0)

    def avanzar(self, dt: float) -> bool:
        self._tiempo += dt
        t = self._tiempo / DURACION_EXPLOSION
        if t >= 1:
            self._nodo.remove_node()
            return False
        # La luz crece deprisa y se apaga en el primer tercio.
        luz = min(1.0, t * 3)
        self._luz.set_scale(self._tamano * (1 + 3 * luz))
        self._luz.set_alpha_scale(max(0.0, 1 - luz))
        frenado = 1 - t * 0.6
        for chispa, velocidad in self._chispas:
            chispa.set_pos(chispa.get_pos() + velocidad * dt * frenado)
        for chispa, _ in self._chispas:
            chispa.set_alpha_scale(1 - t)
        return True


# --- ataques enemigos (S3) -----------------------------------------------------------

#: Daño recibido: temblor de la cámara y tinte rojo en los bordes (`interfaz.md`, «Avisos»).
DURACION_DANO = 0.3
#: Giro máximo de la cámara durante el temblor, en grados. Solo es visual.
_TEMBLOR_MAXIMO = 0.8
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
    """Esfera luminosa del color del tipo con una estela corta detrás."""

    def __init__(
        self, padre: NodePath, textura: Texture, color_tipo: tuple[float, float, float]
    ) -> None:
        self.nodo = padre.attach_new_node("proyectil")
        self._brillo = _tarjeta(self.nodo, textura, color_tipo)
        self._nucleo = _tarjeta(self.nodo, textura, (1.0, 1.0, 1.0))
        estela = LineSegs("estela")
        estela.set_thickness(3.0)
        estela.set_color(*color_tipo, 0.9)
        estela.move_to(0, 0, 0)
        estela.set_color(*color_tipo, 0.0)
        estela.draw_to(0, -_LARGO_ESTELA, 0)
        self._estela = self.nodo.attach_new_node(estela.create())
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


class DanoRecibido:
    """Temblor breve de la cámara y tinte rojo en los bordes al recibir daño (RF-14).

    El temblor es solo visual: gira la cámara de la escena, no la orientación de `vista`.
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
        self._tiempo = 0.0

    def recibir(self) -> None:
        """Empieza (o renueva) el temblor y el tinte."""
        self._restante = DURACION_DANO

    def avanzar(self, dt: float, camara: NodePath) -> None:
        """Aplica el temblor a `camara`, ya orientada en este fotograma, y apaga el tinte."""
        self._tiempo += dt
        if self._restante <= 0:
            return
        self._restante = max(0.0, self._restante - dt)
        fuerza = self._restante / DURACION_DANO
        if fuerza == 0:
            self._tinte.hide()
            return
        self._tinte.show()
        self._tinte.set_alpha_scale(_OPACIDAD_TINTE * fuerza)
        # Ruido suave: suma de senos de frecuencias no múltiplos entre sí.
        t = self._tiempo
        amplitud = _TEMBLOR_MAXIMO * fuerza
        rumbo = amplitud * (math.sin(t * 61.0) * 0.6 + math.sin(t * 37.0 + 1.3) * 0.4)
        cabeceo = amplitud * (math.sin(t * 53.0 + 0.7) * 0.6 + math.sin(t * 29.0 + 2.1) * 0.4)
        camara.set_hpr(camara, rumbo, cabeceo, 0)
