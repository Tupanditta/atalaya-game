"""Energía, mira de precisión y disparo (`modulos/armamento.md`).

El aturdimiento llega en S4 y las mejoras de batería y generador en S5.
"""

import math
from typing import Protocol

from atalaya.logica.nucleo.azar import Azar
from atalaya.logica.nucleo.bus import Bus
from atalaya.logica.nucleo.dominio import Vector3
from atalaya.logica.nucleo.eventos import (
    ApuntadoCambiado,
    DisparoRealizado,
    DisparoSinEnergia,
    EnergiaCambiada,
    PartidaIniciada,
)
from atalaya.logica.nucleo.vectores import CERO, girar_hacia
from atalaya.logica.parametros.modelo import Parametros

#: Por debajo de esta diferencia, el progreso de apuntado se considera en su extremo.
_TOLERANCIA = 1e-9


class Mira(Protocol):
    """Lo que `armamento` consulta a `vista`: hacia dónde apunta la mira."""

    @property
    def direccion_mira(self) -> Vector3:
        """Dirección real de la mira en el mundo, de longitud 1."""


def direccion_disparo(centro: Vector3, radio: float, azar: Azar) -> Vector3:
    """Dirección al azar uniforme dentro del círculo de la mira (RN-37, `design.md` §5).

    `radio` es el radio de la mira en grados alrededor de `centro`.
    """
    angulo = radio * math.sqrt(azar.aleatorio())
    azimut = azar.uniforme(0.0, 360.0)
    return girar_hacia(centro, angulo, azimut)


class Armamento:
    """Energía del jugador, tamaño de la mira y momento del disparo."""

    def __init__(self, bus: Bus, parametros: Parametros, mira: Mira, azar: Azar) -> None:
        self._bus = bus
        self._jugador = parametros.jugador
        self._mira = mira
        self._azar = azar
        self._energia = self._jugador.energia_maxima
        self._progreso = 0.0
        self._pulsada = False
        self._pulsada_antes = False
        self._cancelado = False
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
        """Recarga la energía, resuelve el disparo al soltar y ajusta la mira."""
        self._recargar(dt)
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
        direccion = direccion_disparo(self._mira.direccion_mira, self.radio_mira, self._azar)
        self._bus.publicar(DisparoRealizado(CERO, direccion))

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

    def _al_iniciar_partida(self, evento: PartidaIniciada) -> None:
        self._energia = self._jugador.energia_maxima
        self._progreso = 0.0
        self._pulsada = False
        self._pulsada_antes = False
        self._cancelado = False
        self._bus.publicar(EnergiaCambiada(self._energia, self._jugador.energia_maxima))
