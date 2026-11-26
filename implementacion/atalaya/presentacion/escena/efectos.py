"""Efectos visuales del disparo: rayo, destello de impacto y explosión (`modulos/escena.md`).

Versión básica de S2. Cada efecto avanza con el tiempo de los fotogramas y se borra
solo al terminar.
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
