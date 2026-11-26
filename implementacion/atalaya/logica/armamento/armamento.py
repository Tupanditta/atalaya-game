"""Energía, mira de precisión y disparo (`modulos/armamento.md`).

El disparo sale justo hacia el centro de la mira, sin dispersión (RN-37). Incluye el
bloqueo del disparo por aturdimiento (RN-13, RN-38) y las mejoras de batería y
generador que compra el jugador en el descanso (RN-47).
"""

from typing import Protocol

from atalaya.logica.nucleo.bus import Bus
from atalaya.logica.nucleo.dominio import Mejora, Vector3
from atalaya.logica.nucleo.eventos import (
    ApuntadoCambiado,
    AturdimientoIniciado,
    AturdimientoTerminado,
    DisparoRealizado,
    DisparoSinEnergia,
    EnergiaCambiada,
    MejoraAplicada,
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
        self._mejoras = parametros.mejoras
        self._mira = mira
        self._energia_maxima = self._jugador.energia_maxima
        self._recarga = self._jugador.recarga_energia
        self._energia = self._energia_maxima
        self._progreso = 0.0
        self._pulsada = False
        self._pulsada_antes = False
        self._cancelado = False
        self._aturdido = False
        bus.suscribir(AturdimientoIniciado, self._al_aturdir)
        bus.suscribir(AturdimientoTerminado, self._al_terminar_aturdimiento)
        bus.suscribir(MejoraAplicada, self._al_mejorar)
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
        """Energía máxima, con la mejora de batería."""
        return self._energia_maxima

    @property
    def recarga_energia(self) -> float:
        """Energía recargada por segundo, con la mejora de generador."""
        return self._recarga

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
        maxima = self._energia_maxima
        if self._energia >= maxima:
            return
        self._cambiar_energia(min(maxima, self._energia + self._recarga * dt))

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
            self._bus.publicar(EnergiaCambiada(energia, self._energia_maxima))

    def _al_aturdir(self, evento: AturdimientoIniciado) -> None:
        """La mira vuelve a su tamaño normal y no se dispara al soltar (RN-13, RN-38)."""
        self._aturdido = True
        self.cancelar_apuntado()

    def _al_terminar_aturdimiento(self, evento: AturdimientoTerminado) -> None:
        self._aturdido = False

    def _al_mejorar(self, evento: MejoraAplicada) -> None:
        """La batería sube la energía máxima y el generador la recarga (RN-47).

        La energía actual no cambia: la recarga la lleva hasta la nueva máxima.
        """
        if evento.mejora is Mejora.BATERIA:
            efecto = self._mejoras.bateria.efecto
            self._energia_maxima = self._jugador.energia_maxima + efecto * evento.nivel
            self._bus.publicar(EnergiaCambiada(self._energia, self._energia_maxima))
        elif evento.mejora is Mejora.GENERADOR:
            efecto = self._mejoras.generador.efecto
            self._recarga = self._jugador.recarga_energia + efecto * evento.nivel

    def _al_iniciar_partida(self, evento: PartidaIniciada) -> None:
        """Energía al máximo base y sin mejoras (RN-02, RN-49)."""
        self._aturdido = False
        self._energia_maxima = self._jugador.energia_maxima
        self._recarga = self._jugador.recarga_energia
        self._energia = self._energia_maxima
        self._progreso = 0.0
        self._pulsada = False
        self._pulsada_antes = False
        self._cancelado = False
        self._bus.publicar(EnergiaCambiada(self._energia, self._energia_maxima))
