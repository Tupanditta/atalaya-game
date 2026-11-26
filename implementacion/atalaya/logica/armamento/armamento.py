"""Energía, mira de precisión y disparo (`modulos/armamento.md`).

El disparo sale justo hacia el centro de la mira, sin dispersión (RN-37). Incluye el
bloqueo del disparo por aturdimiento (RN-13, RN-38). Las mejoras de batería y generador
llegan en S5.
"""

from typing import Protocol

from atalaya.logica.nucleo.bus import Bus
from atalaya.logica.nucleo.dominio import Vector3
from atalaya.logica.nucleo.eventos import (
    ApuntadoCambiado,
    AturdimientoIniciado,
    AturdimientoTerminado,
    DisparoRealizado,
    DisparoSinEnergia,
    EnergiaCambiada,
    PartidaIniciada,
)
from atalaya.logica.nucleo.vectores import CERO
from atalaya.logica.parametros.modelo import Parametros

#: Por debajo de esta diferencia, el progreso de apuntado se considera en su extremo.
_TOLERANCIA = 1e-9


class Mira(Protocol):
    """Lo que `armamento` consulta a `vista`: hacia dónde apunta la mira."""

    @property
    def direccion_mira(self) -> Vector3:
        """Dirección real de la mira en el mundo, de longitud 1."""


class Armamento:
    """Energía del jugador, tamaño de la mira y momento del disparo."""

    def __init__(self, bus: Bus, parametros: Parametros, mira: Mira) -> None:
        self._bus = bus
        self._jugador = parametros.jugador
        self._mira = mira
        self._energia = self._jugador.energia_maxima
        self._progreso = 0.0
        self._pulsada = False
        self._pulsada_antes = False
        self._cancelado = False
        self._aturdido = False
        bus.suscribir(AturdimientoIniciado, self._al_aturdir)
        bus.suscribir(AturdimientoTerminado, self._al_terminar_aturdimiento)
        bus.suscribir(PartidaIniciada, self._al_iniciar_partida)

    # --- operaciones -----------------------------------------------------------------

    def recibir_disparo(self, pulsada: bool) -> None:
        """Estado de la barra espaciadora en este paso. Lo entrega `flujo`."""
        self._pulsada = pulsada

    def cancelar_apuntado(self) -> None:
        """Devuelve la mira a su tamaño normal. Al soltar la barra no se dispara (RN-38)."""
        if self._pulsada:
            self._cancelado = True

    def actualizar(self, dt: float) -> None:
        """Recarga la energía, resuelve el disparo al soltar y ajusta la mira.

        Aturdido, la barra pulsada no apunta: el apuntado queda cancelado hasta que se
        suelte, también si se pulsó durante el aturdimiento (RN-13, RN-38).
        """
        self._recargar(dt)
        if self._aturdido:
            self.cancelar_apuntado()
        if self._pulsada_antes and not self._pulsada:
            # La mira con la que se dispara es la del momento de soltar.
            if not self._cancelado:
                self._disparar()
            self._cancelado = False
        self._pulsada_antes = self._pulsada
        self._ajustar_mira(dt)

    # --- consultas -------------------------------------------------------------------

    @property
    def energia(self) -> float:
        """Energía actual."""
        return self._energia

    @property
    def energia_maxima(self) -> float:
        """Energía máxima."""
        return self._jugador.energia_maxima

    @property
    def progreso_apuntado(self) -> float:
        """Progreso de apuntado: 0 con la mira normal, 1 con la mira mínima."""
        return self._progreso

    @property
    def radio_mira(self) -> float:
        """Radio de dispersión de la mira, en grados (RN-37, RN-38)."""
        j = self._jugador
        return j.mira_normal + (j.mira_minima - j.mira_normal) * self._progreso

    @property
    def aturdido(self) -> bool:
        """Indica si el disparo está bloqueado por aturdimiento (RN-13)."""
        return self._aturdido

    # --- internos --------------------------------------------------------------------

    def _recargar(self, dt: float) -> None:
        maxima = self._jugador.energia_maxima
        if self._energia >= maxima:
            return
        self._cambiar_energia(min(maxima, self._energia + self._jugador.recarga_energia * dt))

    def _disparar(self) -> None:
        coste = self._jugador.coste_disparo
        if self._energia < coste - _TOLERANCIA:
            self._bus.publicar(DisparoSinEnergia())
            return
        self._cambiar_energia(max(0.0, self._energia - coste))
        # Justo hacia el centro de la mira, con el desvío por desestabilización (RN-12, RN-37).
        self._bus.publicar(DisparoRealizado(CERO, self._mira.direccion_mira))

    def _ajustar_mira(self, dt: float) -> None:
        j = self._jugador
        if self._pulsada and not self._cancelado:
            progreso = self._progreso + dt / j.tiempo_apuntado
        else:
            progreso = self._progreso - dt / j.tiempo_vuelta_mira
        if progreso > 1 - _TOLERANCIA:
            progreso = 1.0
        elif progreso < _TOLERANCIA:
            progreso = 0.0
        if progreso != self._progreso:
            self._progreso = progreso
            self._bus.publicar(ApuntadoCambiado(progreso))

    def _cambiar_energia(self, energia: float) -> None:
        if energia != self._energia:
            self._energia = energia
            self._bus.publicar(EnergiaCambiada(energia, self._jugador.energia_maxima))

    def _al_aturdir(self, evento: AturdimientoIniciado) -> None:
        """La mira vuelve a su tamaño normal y no se dispara al soltar (RN-13, RN-38)."""
        self._aturdido = True
        self.cancelar_apuntado()

    def _al_terminar_aturdimiento(self, evento: AturdimientoTerminado) -> None:
        self._aturdido = False

    def _al_iniciar_partida(self, evento: PartidaIniciada) -> None:
        self._aturdido = False
        self._energia = self._jugador.energia_maxima
        self._progreso = 0.0
        self._pulsada = False
        self._pulsada_antes = False
        self._cancelado = False
        self._bus.publicar(EnergiaCambiada(self._energia, self._jugador.energia_maxima))
