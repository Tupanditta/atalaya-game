"""Capa holográfica sobre toda la interfaz (`interfaz.md`, «Estilo»).

Líneas de barrido horizontales muy tenues, una cada pocos píxeles de pantalla, y una
franja de luz del color de acento que recorre la pantalla de arriba abajo cada pocos
segundos. Da a los paneles el aire de una proyección holográfica sin restar legibilidad.

Fluidez: son dos tarjetas a pantalla completa con texturas diminutas que se repiten; en
cada fotograma solo se mueve la franja.
"""

import numpy as np
from panda3d.core import (
    CardMaker,
    ColorBlendAttrib,
    NodePath,
    SamplerState,
    Texture,
    TextureStage,
    TransparencyAttrib,
)

from atalaya.presentacion.hud.estilo import ACENTO

#: Separación entre líneas de barrido, en píxeles de pantalla, y su opacidad.
SEPARACION_LINEAS = 3
OPACIDAD_LINEAS = 0.07
#: Franja de luz: alto en fracción de la pantalla, opacidad, duración del recorrido y
#: tiempo entre una pasada y la siguiente, en segundos.
ALTO_FRANJA = 0.12
OPACIDAD_FRANJA = 0.06
RECORRIDO_FRANJA = 2.2
PERIODO_FRANJA = 7.0

#: Orden de dibujo en `render2d`: encima de todo, también de los menús.
_ORDEN = 95


class Holograma:
    """Líneas de barrido y franja de luz a pantalla completa."""

    def __init__(self, render2d: NodePath) -> None:
        tarjeta = CardMaker("lineas-barrido")
        tarjeta.set_frame(-1, 1, -1, 1)
        self._lineas = render2d.attach_new_node(tarjeta.generate())
        self._lineas.set_texture(_textura_lineas())
        self._lineas.set_transparency(TransparencyAttrib.M_alpha)
        self._lineas.set_color(0, 0, 0, OPACIDAD_LINEAS)
        _preparar(self._lineas)
        franja = CardMaker("franja")
        franja.set_frame(-1, 1, -ALTO_FRANJA, ALTO_FRANJA)
        self._franja = render2d.attach_new_node(franja.generate())
        self._franja.set_texture(_textura_franja())
        self._franja.set_color(ACENTO[0], ACENTO[1], ACENTO[2], OPACIDAD_FRANJA)
        self._franja.set_attrib(
            ColorBlendAttrib.make(
                ColorBlendAttrib.M_add, ColorBlendAttrib.O_incoming_alpha, ColorBlendAttrib.O_one
            )
        )
        _preparar(self._franja)
        self._alto_ventana = 0
        self._tiempo = 0.0

    def dibujar(self, dt: float, alto_ventana: int) -> None:
        """Ajusta las líneas al alto de la ventana y mueve la franja."""
        if alto_ventana != self._alto_ventana and alto_ventana > 0:
            self._alto_ventana = alto_ventana
            # Una línea cada `SEPARACION_LINEAS` píxeles, sea cual sea la resolución.
            self._lineas.set_tex_scale(
                TextureStage.get_default(), 1, alto_ventana / SEPARACION_LINEAS
            )
        self._tiempo = (self._tiempo + dt) % PERIODO_FRANJA
        avance = self._tiempo / RECORRIDO_FRANJA
        if avance >= 1:
            self._franja.hide()
            return
        self._franja.show()
        # De arriba abajo, entrando y saliendo por completo de la pantalla.
        self._franja.set_z(1 + ALTO_FRANJA - avance * 2 * (1 + ALTO_FRANJA))


def _preparar(nodo: NodePath) -> None:
    nodo.set_depth_test(False)
    nodo.set_depth_write(False)
    nodo.set_bin("fixed", _ORDEN)


def _textura_lineas() -> Texture:
    """Una línea opaca y el resto transparente: se repite a lo alto de la pantalla."""
    alfa = np.zeros((SEPARACION_LINEAS, 1), dtype=np.uint8)
    alfa[0] = 255
    return _textura(alfa, "lineas", SamplerState.FT_nearest)


def _textura_franja(alto: int = 64) -> Texture:
    """Degradado suave, más intenso en el centro de la franja."""
    v = np.linspace(-1, 1, alto)
    alfa = (np.exp(-(v**2) * 4) * 255).astype(np.uint8)[:, None]
    return _textura(alfa, "franja", SamplerState.FT_linear)


def _textura(alfa: np.ndarray, nombre: str, filtro: int) -> Texture:
    """Textura blanca con la opacidad de `alfa` (filas de abajo arriba)."""
    imagen = np.full((*alfa.shape, 4), 255, dtype=np.uint8)
    imagen[..., 3] = alfa
    textura = Texture(nombre)
    textura.setup_2d_texture(alfa.shape[1], alfa.shape[0], Texture.T_unsigned_byte, Texture.F_rgba)
    textura.set_ram_image(np.ascontiguousarray(imagen).data)
    textura.set_minfilter(filtro)
    textura.set_magfilter(filtro)
    textura.set_wrap_u(SamplerState.WM_repeat)
    textura.set_wrap_v(SamplerState.WM_repeat)
    return textura
