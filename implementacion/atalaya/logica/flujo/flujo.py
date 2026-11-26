"""Pantallas del juego y reparto de las acciones del jugador (`modulos/flujo.md`).

Versión mínima: una sola pantalla, la oleada en curso, que entrega los ejes de giro a
`vista` y el estado de la barra espaciadora a `armamento`. Los menús, la pausa y el
descanso llegan en sprints posteriores.
"""

from enum import Enum
from typing import Protocol

from atalaya.logica.armamento import Armamento
from atalaya.logica.nucleo.bus import Bus
from atalaya.logica.nucleo.dominio import Accion
from atalaya.logica.nucleo.eventos import PartidaIniciada
from atalaya.logica.vista import Vista, eje_de_flechas


class Acciones(Protocol):
    """Estado de las acciones del jugador en el paso actual. Lo implementa `entrada`."""

    def mantenida(self, accion: Accion) -> bool:
        """Indica si la acción está activa en este paso."""

    def recien_pulsada(self, accion: Accion) -> bool:
        """Indica si la acción ha empezado en este paso."""

    def recien_soltada(self, accion: Accion) -> bool:
        """Indica si la acción ha terminado en este paso."""


class Pantalla(Enum):
    """Pantallas del juego. S1 solo tiene la oleada en curso."""

    OLEADA_EN_CURSO = "oleada_en_curso"


class Flujo:
    """Sabe en qué pantalla está el juego y decide qué hace cada acción en ella."""

    def __init__(self, bus: Bus, acciones: Acciones, vista: Vista, armamento: Armamento) -> None:
        self._bus = bus
        self._acciones = acciones
        self._vista = vista
        self._armamento = armamento
        self._pantalla: Pantalla | None = None
        self._nivel = 1
        self._salir = False

    @property
    def pantalla(self) -> Pantalla | None:
        """Pantalla actual, o `None` antes de empezar."""
        return self._pantalla

    @property
    def nivel(self) -> int:
        """Nivel de la partida en curso."""
        return self._nivel

    @property
    def salir_solicitado(self) -> bool:
        """Indica si el jugador ha pedido cerrar el juego."""
        return self._salir

    def iniciar_partida(self, nivel: int = 1) -> None:
        """Empieza una partida en `nivel` y pasa a la oleada en curso."""
        self._nivel = nivel
        self._pantalla = Pantalla.OLEADA_EN_CURSO
        self._bus.publicar(PartidaIniciada(nivel))

    def actualizar(self, dt: float) -> None:
        """Reparte las acciones del paso según la pantalla actual."""
        if self._pantalla is Pantalla.OLEADA_EN_CURSO:
            self._actualizar_oleada()

    def _actualizar_oleada(self) -> None:
        a = self._acciones
        # Provisional hasta S6: sin pantalla de pausa, Esc cierra el juego.
        if a.recien_pulsada(Accion.PAUSA):
            self._salir = True
            return
        self._vista.recibir_ejes(
            eje_de_flechas(a.mantenida(Accion.IZQUIERDA), a.mantenida(Accion.DERECHA)),
            eje_de_flechas(a.mantenida(Accion.ABAJO), a.mantenida(Accion.ARRIBA)),
        )
        self._armamento.recibir_disparo(a.mantenida(Accion.DISPARO))
