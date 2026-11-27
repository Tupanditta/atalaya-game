"""Entorno: fondo espacial de la partida (`modulos/entorno.md`).

Versión mínima: el fondo actual, de 1 a 5, que cambia al terminar cada salto
hiperespacial (RN-20). La niebla y los destellos (RN-44) llegan en un sprint posterior.
"""

from atalaya.logica.nucleo.bus import Bus
from atalaya.logica.nucleo.eventos import (
    EstacionDestruida,
    FondoCambiado,
    PartidaAbandonada,
    PartidaIniciada,
    SaltoIniciado,
    SaltoTerminado,
)
from atalaya.logica.parametros.modelo import Parametros

#: Fondo con el que empieza toda partida.
FONDO_INICIAL = 1


class EntornoEspacial:
    """Decide qué fondo espacial se ve en cada momento de la partida."""

    def __init__(self, bus: Bus, parametros: Parametros) -> None:
        self._bus = bus
        self._parametros = parametros
        self._fondo = FONDO_INICIAL
        self._destino: int | None = None
        bus.suscribir(PartidaIniciada, self._al_iniciar_partida)
        bus.suscribir(SaltoIniciado, self._al_iniciar_salto)
        bus.suscribir(SaltoTerminado, self._al_terminar_salto)
        bus.suscribir(PartidaAbandonada, self._al_detener)
        bus.suscribir(EstacionDestruida, self._al_detener)

    def actualizar(self, dt: float) -> None:
        """Una vez por paso. Sin niebla ni destellos todavía, no hay nada que avanzar."""

    # --- consultas -------------------------------------------------------------------

    @property
    def fondo(self) -> int:
        """Índice del fondo actual, de 1 a 5."""
        return self._fondo

    @property
    def fondo_destino(self) -> int | None:
        """Fondo al que lleva el salto en curso, o `None` si no hay salto."""
        return self._destino

    # --- eventos ---------------------------------------------------------------------

    def _cambiar(self, fondo: int) -> None:
        if fondo != self._fondo:
            self._fondo = fondo
            self._bus.publicar(FondoCambiado(fondo))

    def _al_iniciar_partida(self, evento: PartidaIniciada) -> None:
        """Toda partida empieza en el fondo 1."""
        self._destino = None
        self._cambiar(FONDO_INICIAL)

    def _al_iniciar_salto(self, evento: SaltoIniciado) -> None:
        self._destino = evento.fondo

    def _al_terminar_salto(self, evento: SaltoTerminado) -> None:
        """Al llegar, el fondo de destino pasa a ser el actual (RN-20)."""
        if self._destino is not None:
            self._cambiar(self._destino)
        self._destino = None

    def _al_detener(self, evento: object) -> None:
        """Un salto interrumpido por el fin de la partida no cambia el fondo."""
        self._destino = None
