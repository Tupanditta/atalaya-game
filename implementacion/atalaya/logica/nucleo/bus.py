"""Bus de eventos síncrono del núcleo."""

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

#: Número máximo de eventos que se entregan en una sola llamada a `Bus.entregar`.
#: Superarlo indica un ciclo de eventos que se publican unos a otros sin fin.
MAX_EVENTOS_POR_ENTREGA = 10_000


@dataclass(frozen=True, slots=True)
class Evento:
    """Clase base de todos los eventos. Los eventos son inmutables."""


E = TypeVar("E", bound=Evento)


class Bus:
    """Canal de eventos entre módulos.

    Publicar un evento lo pone en cola. `entregar` reparte la cola en orden de
    publicación, incluidos los eventos que publiquen los suscriptores mientras
    tanto, de modo que todos llegan en el mismo paso.
    """

    def __init__(self) -> None:
        self._suscriptores: dict[type[Evento], list[Callable[[Any], None]]] = {}
        self._cola: deque[Evento] = deque()

    def suscribir(self, tipo: type[E], manejador: Callable[[E], None]) -> None:
        """Llama a `manejador` con cada evento de tipo `tipo` que se entregue."""
        self._suscriptores.setdefault(tipo, []).append(manejador)

    def publicar(self, evento: Evento) -> None:
        """Pone `evento` en la cola de entrega."""
        self._cola.append(evento)

    @property
    def pendientes(self) -> int:
        """Número de eventos publicados que aún no se han entregado."""
        return len(self._cola)

    def entregar(self) -> None:
        """Entrega todos los eventos pendientes en orden de publicación."""
        entregados = 0
        while self._cola:
            if entregados >= MAX_EVENTOS_POR_ENTREGA:
                self._cola.clear()
                raise RuntimeError(
                    f"Posible ciclo de eventos: más de {MAX_EVENTOS_POR_ENTREGA} en una entrega"
                )
            evento = self._cola.popleft()
            entregados += 1
            for manejador in tuple(self._suscriptores.get(type(evento), ())):
                manejador(evento)
