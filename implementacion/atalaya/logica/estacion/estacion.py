"""Integridad y destrucción de la estación (`modulos/estacion.md`).

Versión de S3: integridad y destrucción. El aturdimiento y la desestabilización llegan
en S4; la reparación y el blindaje, en S5.
"""

from atalaya.logica.nucleo.bus import Bus
from atalaya.logica.nucleo.eventos import (
    EstacionDanada,
    EstacionDestruida,
    IntegridadCambiada,
    OleadaSuperada,
    PartidaIniciada,
    ProyectilImpacta,
)
from atalaya.logica.parametros.modelo import Parametros

#: Por debajo de esta integridad, la estación se considera destruida.
_TOLERANCIA = 1e-9


class Estacion:
    """Integridad de la estación y su destrucción (RN-10, RN-17)."""

    def __init__(self, bus: Bus, parametros: Parametros) -> None:
        self._bus = bus
        self._parametros = parametros
        self._maxima = parametros.jugador.integridad_maxima
        self._integridad = self._maxima
        self._destruida = False
        self._oleadas_superadas = 0
        bus.suscribir(ProyectilImpacta, self._al_impactar)
        bus.suscribir(OleadaSuperada, self._al_superar_oleada)
        bus.suscribir(PartidaIniciada, self._al_iniciar_partida)

    # --- consultas -------------------------------------------------------------------

    @property
    def integridad(self) -> float:
        """Integridad actual, entre 0 y la máxima."""
        return self._integridad

    @property
    def integridad_maxima(self) -> float:
        """Integridad máxima."""
        return self._maxima

    @property
    def destruida(self) -> bool:
        """Indica si la integridad ha llegado a cero en esta partida."""
        return self._destruida

    # --- eventos ---------------------------------------------------------------------

    def _al_impactar(self, evento: ProyectilImpacta) -> None:
        """Resta el daño del tipo sin bajar de cero; a cero, la estación cae una vez."""
        if self._destruida:
            return
        dano = self._parametros.tipos.de(evento.tipo_enemigo).dano
        anterior = self._integridad
        self._integridad = max(0.0, anterior - dano)
        if self._integridad <= _TOLERANCIA:
            self._integridad = 0.0
        self._bus.publicar(
            EstacionDanada(anterior - self._integridad, self._integridad, self._maxima)
        )
        self._bus.publicar(IntegridadCambiada(self._integridad, self._maxima))
        if self._integridad == 0:
            self._destruida = True
            self._bus.publicar(EstacionDestruida(self._oleadas_superadas))

    def _al_superar_oleada(self, evento: OleadaSuperada) -> None:
        self._oleadas_superadas = evento.numero

    def _al_iniciar_partida(self, evento: PartidaIniciada) -> None:
        self._maxima = self._parametros.jugador.integridad_maxima
        self._integridad = self._maxima
        self._destruida = False
        self._oleadas_superadas = 0
        self._bus.publicar(IntegridadCambiada(self._integridad, self._maxima))
