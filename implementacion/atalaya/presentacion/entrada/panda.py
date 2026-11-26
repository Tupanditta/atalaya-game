"""Fuentes de teclado y de ratón de Panda3D para `Entrada`."""

from direct.showbase.ShowBase import ShowBase
from panda3d.core import ButtonHandle, ButtonRegistry


class FuenteTecladoPanda:
    """Lee el estado de las teclas del observador de botones de la ventana."""

    def __init__(self, base: ShowBase) -> None:
        self._base = base
        self._botones: dict[str, ButtonHandle] = {}

    def pulsadas(self, teclas: frozenset[str]) -> frozenset[str]:
        observador = self._base.mouseWatcherNode
        return frozenset(t for t in teclas if observador.is_button_down(self._boton(t)))

    def tiene_foco(self) -> bool:
        ventana = self._base.win
        return ventana is not None and bool(ventana.get_properties().get_foreground())

    def _boton(self, tecla: str) -> ButtonHandle:
        if tecla not in self._botones:
            boton = ButtonRegistry.ptr().find_button(tecla)
            if boton == ButtonHandle.none():
                raise ValueError(f"El motor no conoce la tecla '{tecla}'")
            self._botones[tecla] = boton
        return self._botones[tecla]


class FuenteRatonPanda:
    """Lee la posición del ratón del observador de la ventana."""

    def __init__(self, base: ShowBase) -> None:
        self._base = base

    def posicion(self) -> tuple[float, float] | None:
        observador = self._base.mouseWatcherNode
        if not observador.has_mouse():
            return None
        # El motor da x e y de −1 a 1 de borde a borde; x se pasa a medias alturas.
        raton = observador.get_mouse()
        return raton.x * self._base.get_aspect_ratio(), raton.y
