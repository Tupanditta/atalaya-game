"""Deslumbramiento del sol y destellos de lente (RN-20; `design.md`, sección 6).

En los fondos con sol (`cielo.TEMAS`), una tarjeta con shader (`sol_glsl.py`) le añade
núcleo, halo y rayos, y unos destellos tenues cruzan la pantalla desde el sol hacia el
centro cuando el sol está en el campo de visión. Si un planeta del paisaje tapa el sol,
todo se atenúa: como los planetas no se mueven respecto a la estación, eso se calcula una
vez por fondo.

Sin shaders no hay deslumbramiento ni destellos: el sol pintado en el cielo basta.
"""

import math

import numpy as np
from panda3d.core import (
    CardMaker,
    ColorBlendAttrib,
    Lens,
    NodePath,
    Point2,
    Point3,
    SamplerState,
    Texture,
    TransparencyAttrib,
    Vec3,
)

from atalaya.presentacion.escena import cielo
from atalaya.presentacion.escena.planetas import PAISAJES
from atalaya.presentacion.escena.sombreado import Sombreado

#: Distancia de la tarjeta del sol (dentro del cubo de cielo) y su radio angular, en grados.
_DISTANCIA = 9.0
_RADIO = 24.0
#: Orden de dibujo dentro del grupo `background`: tras el cubo y las estrellas.
_ORDEN = 2
#: Destellos: posición a lo largo de la recta del sol al centro (1 en el sol, 0 en el centro),
#: tamaño (en alto de pantalla), forma y tono respecto al color del sol.
_DESTELLOS: tuple[tuple[float, float, str, tuple[float, float, float]], ...] = (
    (0.55, 0.05, "disco", (1.0, 0.85, 0.6)),
    (0.2, 0.025, "disco", (0.7, 1.0, 0.75)),
    (-0.25, 0.09, "anillo", (0.75, 0.8, 1.0)),
    (-0.55, 0.04, "disco", (1.0, 0.7, 0.9)),
    (-0.95, 0.16, "anillo", (0.85, 0.75, 1.0)),
)
_INTENSIDAD_DESTELLOS = 0.16


class Deslumbramiento:
    """Deslumbramiento del sol del fondo actual y sus destellos de lente."""

    def __init__(self, espacio: NodePath, render2d: NodePath, sombreado: Sombreado | None) -> None:
        self._espacio = espacio
        programa = None if sombreado is None else sombreado.programa("sol")
        self.activo = programa is not None
        self._raiz = espacio.attach_new_node("sol")
        tarjeta = CardMaker("deslumbramiento")
        tarjeta.set_frame(-1, 1, -1, 1)
        self._tarjeta = self._raiz.attach_new_node(tarjeta.generate())
        self._tarjeta.set_scale(_DISTANCIA * math.tan(math.radians(_RADIO)))
        self._tarjeta.set_billboard_point_eye()
        self._tarjeta.set_bin("background", _ORDEN)
        self._tarjeta.set_depth_test(False)
        _aditivo(self._tarjeta)
        if programa is not None:
            self._tarjeta.set_shader(programa)
        self._tarjeta.set_shader_inputs(sol_color=Vec3(1, 1, 1), visible=1.0, tiempo=0.0)
        self._destellos = render2d.attach_new_node("destellos")
        self._destellos.set_bin("background", 0)
        self._destellos.set_depth_test(False)
        _aditivo(self._destellos)
        texturas = {"disco": _textura_destello(anillo=False), "anillo": _textura_destello(True)}
        self._piezas: list[tuple[NodePath, float, float]] = []
        for posicion, tamano, forma, tono in _DESTELLOS:
            pieza = self._destellos.attach_new_node(tarjeta.generate())
            pieza.set_texture(texturas[forma])
            pieza.set_color(*tono, 1)
            self._piezas.append((pieza, posicion, tamano))
        self._direccion: Vec3 | None = None
        self._visible = 1.0
        self._color = (1.0, 1.0, 1.0)
        self._tiempo = 0.0
        self._raiz.hide()
        self._destellos.hide()

    @property
    def mostrado(self) -> bool:
        """Indica si hay deslumbramiento en el fondo actual."""
        return self._direccion is not None

    def muestra(self) -> NodePath | None:
        """Copia diminuta del deslumbramiento delante de la cámara, para calentar su shader.

        Se ve aunque el fondo no tenga sol; `Calentamiento` la quita. Sin shaders, nada.
        """
        if not self.activo:
            return None
        copia = self._tarjeta.copy_to(self._espacio)
        copia.set_pos(0, _DISTANCIA, 0)
        copia.set_scale(0.001)
        return copia

    def mostrar(self, indice: int) -> None:
        """Pone el sol del fondo `indice`; sin sol o sin shaders, nada."""
        soles = cielo.TEMAS[indice - 1].soles
        if not soles or not self.activo:
            self._direccion = None
            self._raiz.hide()
            self._destellos.hide()
            return
        sol = soles[0]
        self._direccion = Vec3(*sol.direccion).normalized()
        self._visible = visibilidad(indice)
        self._color = sol.color
        self._tarjeta.set_pos(self._direccion * _DISTANCIA)
        self._tarjeta.set_shader_inputs(sol_color=Vec3(*sol.color), visible=self._visible)
        self._raiz.show()

    def avanzar(self, dt: float, camara: NodePath, lente: Lens, proporcion: float) -> None:
        """Coloca los destellos según dónde cae el sol en la pantalla."""
        self._tiempo += dt
        self._tarjeta.set_shader_input("tiempo", self._tiempo)
        if self._direccion is None:
            return
        hacia = camara.get_relative_vector(self._espacio, self._direccion)
        pantalla = Point2()
        if not lente.project(Point3(hacia * 1000.0), pantalla):
            self._destellos.hide()
            return
        # Más tenues cuanto más cerca del borde, y apagados con el cielo (salto, pausa).
        borde = max(abs(pantalla.x), abs(pantalla.y))
        fuerza = self._visible * _INTENSIDAD_DESTELLOS * (1 - _suave(0.6, 1.0, borde))
        escala = self._espacio.get_color_scale()
        self._destellos.set_color_scale(
            *(c * fuerza * escala[0] for c in self._color), escala[3] if escala[3] else 1.0
        )
        for pieza, posicion, tamano in self._piezas:
            pieza.set_pos(pantalla.x * posicion, 0, pantalla.y * posicion)
            pieza.set_scale(tamano / proporcion, 1, tamano)
        self._destellos.show()


def visibilidad(indice: int) -> float:
    """Parte del sol del fondo `indice` que no tapa ningún planeta, de 0 a 1."""
    soles = cielo.TEMAS[indice - 1].soles
    if not soles:
        return 0.0
    sol = Vec3(*soles[0].direccion).normalized()
    visible = 1.0
    for planeta in PAISAJES[indice - 1].planetas:
        centro = Vec3(*planeta.direccion).normalized()
        separacion = math.degrees(math.acos(max(-1.0, min(1.0, sol.dot(centro)))))
        # Tapado del todo si el disco del sol queda dentro del planeta, con un margen.
        visible *= _suave(planeta.tamano - 1.0, planeta.tamano + 2.0, separacion)
    return visible


def _suave(a: float, b: float, x: float) -> float:
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def _textura_destello(anillo: bool, lado: int = 64) -> Texture:
    """Disco tenue de borde suave o anillo fino, en blanco, con la forma en el alfa."""
    centro = (lado - 1) / 2
    y, x = np.mgrid[0:lado, 0:lado].astype(np.float32)
    r = np.hypot(x - centro, y - centro) / centro
    if anillo:
        alfa = np.exp(-(((r - 0.85) / 0.06) ** 2)) * 0.8 + 0.15 * np.clip(1 - r, 0, 1)
    else:
        alfa = np.clip(1 - r, 0, 1) ** 0.6 * 0.7 + np.exp(-(((r - 0.92) / 0.05) ** 2)) * 0.3
    imagen = np.ones((lado, lado, 4), dtype=np.float32)
    imagen[..., 3] = alfa * (r < 1)
    datos = np.ascontiguousarray((imagen * 255 + 0.5).astype(np.uint8)[..., [2, 1, 0, 3]])
    textura = Texture("destello")
    textura.setup_2d_texture(lado, lado, Texture.T_unsigned_byte, Texture.F_rgba)
    textura.set_ram_image(datos.data)
    textura.set_minfilter(SamplerState.FT_linear)
    textura.set_magfilter(SamplerState.FT_linear)
    return textura


def _aditivo(nodo: NodePath) -> None:
    nodo.set_attrib(
        ColorBlendAttrib.make(
            ColorBlendAttrib.M_add, ColorBlendAttrib.O_incoming_alpha, ColorBlendAttrib.O_one
        )
    )
    nodo.set_transparency(TransparencyAttrib.M_alpha)
    nodo.set_depth_write(False)
    nodo.set_light_off()
