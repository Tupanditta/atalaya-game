"""Traducción del teclado y del ratón a acciones del jugador (`modulos/entrada.md`).

No depende del motor: lee las teclas de una `FuenteTeclado` y la posición del ratón de
una `FuenteRaton`. Los adaptadores de Panda3D están en `panda.py`; las pruebas usan
fuentes falsas.
"""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Protocol

from atalaya.logica.nucleo.dominio import Accion

#: Teclas de cada acción, con los nombres de botón del motor. Cualquiera de ellas activa
#: la acción: W, A, S y D equivalen a las flechas, y el botón izquierdo del ratón
#: («mouse1») a la barra espaciadora.
TECLAS: Mapping[Accion, tuple[str, ...]] = MappingProxyType(
    {
        Accion.IZQUIERDA: ("arrow_left", "a"),
        Accion.DERECHA: ("arrow_right", "d"),
        Accion.ARRIBA: ("arrow_up", "w"),
        Accion.ABAJO: ("arrow_down", "s"),
        Accion.DISPARO: ("space", "mouse1"),
        Accion.PAUSA: ("escape",),
        Accion.CONFIRMAR: ("enter",),
    }
)


class FuenteTeclado(Protocol):
    """Estado del teclado en el momento de la consulta."""

    def pulsadas(self, teclas: frozenset[str]) -> frozenset[str]:
        """Teclas de `teclas` que están pulsadas ahora."""

    def tiene_foco(self) -> bool:
        """Indica si la ventana del juego tiene el foco del teclado."""


class FuenteRaton(Protocol):
    """Posición del ratón en el momento de la consulta."""

    def posicion(self) -> tuple[float, float] | None:
        """Posición en medias alturas de ventana desde su centro (`y` hacia arriba, de
        −1 a 1; `x` hacia la derecha), o `None` si el ratón está fuera de la ventana."""


class Entrada:
    """Estado de cada acción en el paso actual y posición de la mira que marca el ratón."""

    def __init__(self, fuente: FuenteTeclado, raton: FuenteRaton | None = None) -> None:
        self._fuente = fuente
        self._raton = raton
        self._puntero = (0.0, 0.0)
        self._teclas = frozenset(t for teclas in TECLAS.values() for t in teclas)
        self._actuales: frozenset[Accion] = frozenset()
        self._previas: frozenset[Accion] = frozenset()

    def actualizar(self, dt: float) -> None:
        """Toma el estado del teclado. Se llama al principio de cada paso de simulación.

        Sin foco, todas las acciones se informan como sueltas, para que no quede un giro
        o un apuntado atascado.
        """
        self._previas = self._actuales
        if self._fuente.tiene_foco():
            pulsadas = self._fuente.pulsadas(self._teclas)
            self._actuales = frozenset(
                a for a, teclas in TECLAS.items() if any(t in pulsadas for t in teclas)
            )
        else:
            self._actuales = frozenset()
        # Fuera de la ventana, la mira se queda donde estaba.
        posicion = self._raton.posicion() if self._raton is not None else None
        if posicion is not None:
            self._puntero = posicion

    def mantenida(self, accion: Accion) -> bool:
        """Indica si la tecla de la acción está pulsada en este paso."""
        return accion in self._actuales

    def recien_pulsada(self, accion: Accion) -> bool:
        """Indica si la tecla se ha pulsado en este paso."""
        return accion in self._actuales and accion not in self._previas

    def puntero(self) -> tuple[float, float]:
        """Posición de la mira en la pantalla según el ratón; el centro sin ratón."""
        return self._puntero

    def recien_soltada(self, accion: Accion) -> bool:
        """Indica si la tecla se ha soltado en este paso."""
        return accion in self._previas and accion not in self._actuales
