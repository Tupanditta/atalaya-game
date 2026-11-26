"""Ventana y escena 3D (`modulos/escena.md`).

Versión mínima de S1: ventana a pantalla completa, cámara orientada según `vista` y
fondo 1. Enemigos, efectos y cambios de fondo llegan en sprints posteriores.
"""

import math

from direct.showbase.ShowBase import ShowBase
from panda3d.core import Quat, WindowProperties, load_prc_file_data

from atalaya.logica.vista import Vista, interpolar
from atalaya.presentacion.escena.fondo import cubo_de_cielo, textura_fondo

#: Resolución si el sistema no informa de la de la pantalla (`design.md`, sección 6).
ANCHO = 1920
ALTO = 1080

#: Distancia del plano cercano de la cámara.
_PLANO_CERCANO = 0.5
#: Distancia del plano lejano: más allá del alcance del radar.
_PLANO_LEJANO = 5000.0


def crear_ventana() -> ShowBase:
    """Abre la ventana del juego a pantalla completa con la resolución nativa de la pantalla.

    Sin ratón (RES-04). La cámara adapta el campo de visión horizontal a la proporción
    de la pantalla, así que cualquier resolución se ve sin deformar.
    """
    load_prc_file_data(
        "atalaya",
        """
        window-title Atalaya
        sync-video true
        cursor-hidden true
        show-frame-rate-meter false
        """,
    )
    base = ShowBase(windowType="none")
    base.makeDefaultPipe()
    ancho, alto = base.pipe.get_display_width(), base.pipe.get_display_height()
    if ancho <= 0 or alto <= 0:
        ancho, alto = ANCHO, ALTO
    propiedades = WindowProperties.get_default()
    propiedades.set_size(ancho, alto)
    propiedades.set_fullscreen(True)
    base.openDefaultWindow(props=propiedades)
    base.disable_mouse()
    base.set_background_color(0, 0, 0, 1)
    return base


class Escena:
    """Dibuja el mundo desde la cámara del jugador."""

    def __init__(self, base: ShowBase, vista: Vista) -> None:
        self._base = base
        self._vista = vista
        base.camLens.set_near_far(_PLANO_CERCANO, _PLANO_LEJANO)
        self._fondo = cubo_de_cielo(textura_fondo(1))
        self._fondo.reparent_to(base.render)

    def dibujar(self, fraccion: float) -> None:
        """Coloca la cámara interpolando entre los dos últimos pasos de simulación.

        `fraccion` es la parte del paso siguiente ya transcurrida, entre 0 y 1.
        """
        v = self._vista
        q = interpolar(v.orientacion_anterior, v.orientacion, fraccion)
        # Panda3D usa la misma convención de ejes que la lógica (x derecha, y delante,
        # z arriba), así que el cuaternión se pasa tal cual.
        self._base.camera.set_quat(Quat(q.w, q.x, q.y, q.z))
        self._ajustar_lente(v.campo_vision)

    def _ajustar_lente(self, vertical: float) -> None:
        """Campo de visión vertical en grados; el horizontal sale de la proporción."""
        proporcion = self._base.get_aspect_ratio()
        horizontal = math.degrees(2 * math.atan(math.tan(math.radians(vertical) / 2) * proporcion))
        self._base.camLens.set_fov(horizontal, vertical)
