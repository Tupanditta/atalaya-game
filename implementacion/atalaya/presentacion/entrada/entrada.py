"""Traducción del teclado a acciones del jugador (`modulos/entrada.md`).

No depende del motor: lee las teclas de una `FuenteTeclado`. El adaptador de Panda3D
está en `panda.py`; las pruebas usan una fuente falsa.
"""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Protocol

from atalaya.logica.nucleo.dominio import Accion

#: Tecla de cada acción, con los nombres de botón del motor. El ratón no se usa (RES-04).
TECLAS: Mapping[Accion, str] = MappingProxyType(
    {
        Accion.IZQUIERDA: "arrow_left",
        Accion.DERECHA: "arrow_right",
        Accion.ARRIBA: "arrow_up",
        Accion.ABAJO: "arrow_down",
        Accion.DISPARO: "space",
        Accion.PAUSA: "escape",
        Accion.CONFIRMAR: "enter",
    }
)


class FuenteTeclado(Protocol):
    """Estado del teclado en el momento de la consulta."""

    def pulsadas(self, teclas: frozenset[str]) -> frozenset[str]:
        """Teclas de `teclas` que están pulsadas ahora."""

    def tiene_foco(self) -> bool:
        """Indica si la ventana del juego tiene el foco del teclado."""


class Entrada:
    """Estado de cada acción en el paso actual: mantenida, recién pulsada o recién soltada."""

    def __init__(self, fuente: FuenteTeclado) -> None:
        self._fuente = fuente
        self._teclas = frozenset(TECLAS.values())
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
            self._actuales = frozenset(a for a, tecla in TECLAS.items() if tecla in pulsadas)
        else:
            self._actuales = frozenset()

    def mantenida(self, accion: Accion) -> bool:
        """Indica si la tecla de la acción está pulsada en este paso."""
        return accion in self._actuales

    def recien_pulsada(self, accion: Accion) -> bool:
        """Indica si la tecla se ha pulsado en este paso."""
        return accion in self._actuales and accion not in self._previas

    def recien_soltada(self, accion: Accion) -> bool:
        """Indica si la tecla se ha soltado en este paso."""
        return accion in self._previas and accion not in self._actuales
