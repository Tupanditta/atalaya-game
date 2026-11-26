"""Bucle a paso fijo y reloj pausable del núcleo."""

from enum import IntEnum
from typing import Protocol

from atalaya.logica.nucleo.azar import Azar, semilla_nueva
from atalaya.logica.nucleo.bus import Bus

#: Duración de un paso de simulación, en segundos.
PASO = 1 / 60

#: Pasos de simulación que se ejecutan como máximo en una llamada a `Nucleo.avanzar`.
MAX_PASOS = 5

# Tolerancia para que la suma de duraciones en coma flotante no pierda pasos.
_TOLERANCIA = 1e-9


class Etapa(IntEnum):
    """Etapas de un paso de simulación, en el orden de actualización de `modulos/README.md`."""

    ENTRADA = 1
    FLUJO = 2
    VISTA = 3
    ARMAMENTO = 4
    ENEMIGOS = 5
    OLEADAS = 6
    ESTACION = 7
    ENTORNO = 8

    @property
    def de_partida(self) -> bool:
        """Indica si la etapa se detiene con la partida en pausa (etapas 3 a 8)."""
        return self >= Etapa.VISTA


class Actualizable(Protocol):
    """Módulo que el núcleo actualiza en cada paso."""

    def actualizar(self, dt: float) -> None:
        """Avanza el estado del módulo `dt` segundos."""


class Nucleo:
    """Da a todos los módulos un tiempo común, un bus de eventos y una fuente de azar."""

    def __init__(self, semilla: int | None = None) -> None:
        self.bus = Bus()
        self.azar = Azar(semilla_nueva() if semilla is None else semilla)
        self._modulos: dict[Etapa, Actualizable] = {}
        self._acumulado = 0.0
        self._en_pausa = False
        self._pasos_partida = 0

    def registrar(self, etapa: Etapa, modulo: Actualizable) -> None:
        """Asigna `modulo` a `etapa`. Cada etapa admite un solo módulo."""
        if etapa in self._modulos:
            raise ValueError(f"La etapa {etapa.name} ya tiene un módulo registrado")
        self._modulos[etapa] = modulo

    def reiniciar_azar(self, semilla: int | None = None) -> None:
        """Reinicia el azar con `semilla`, o con una semilla nueva si no se indica."""
        self.azar.reiniciar(semilla_nueva() if semilla is None else semilla)

    @property
    def en_pausa(self) -> bool:
        """Indica si el reloj de la partida está en pausa."""
        return self._en_pausa

    def pausar(self) -> None:
        """Detiene el reloj de la partida (RN-50). Los menús siguen respondiendo."""
        self._en_pausa = True

    def reanudar(self) -> None:
        """Reanuda el reloj de la partida."""
        self._en_pausa = False

    @property
    def tiempo_partida(self) -> float:
        """Tiempo de partida acumulado, en segundos. No avanza durante la pausa."""
        return self._pasos_partida * PASO

    @property
    def fraccion_paso(self) -> float:
        """Parte del siguiente paso ya acumulada, entre 0 y 1.

        Sirve para interpolar entre los dos últimos pasos al dibujar (`design.md`, sección 4).
        """
        return min(1.0, self._acumulado / PASO)

    def avanzar(self, transcurrido: float) -> int:
        """Ejecuta los pasos de simulación que caben en `transcurrido` segundos reales.

        Ejecuta como máximo `MAX_PASOS` pasos; el tiempo que sobra se descarta.
        Devuelve el número de pasos de partida ejecutados (los que no estaban en pausa).
        """
        if transcurrido < 0:
            raise ValueError("El tiempo transcurrido no puede ser negativo")
        self._acumulado += transcurrido
        pasos = 0
        pasos_partida = 0
        while self._acumulado >= PASO - _TOLERANCIA:
            if pasos == MAX_PASOS:
                self._acumulado = 0.0
                break
            self._acumulado = max(0.0, self._acumulado - PASO)
            pasos += 1
            if self._paso():
                pasos_partida += 1
        return pasos_partida

    def _paso(self) -> bool:
        """Ejecuta un paso. Devuelve si se han ejecutado las etapas de partida."""
        self.bus.entregar()
        etapas = sorted(self._modulos)
        for etapa in (e for e in etapas if not e.de_partida):
            self._actualizar(etapa)
        # La pausa se comprueba después de `flujo`, que es quien la activa o la quita.
        if self._en_pausa:
            return False
        for etapa in (e for e in etapas if e.de_partida):
            self._actualizar(etapa)
        self._pasos_partida += 1
        return True

    def _actualizar(self, etapa: Etapa) -> None:
        self._modulos[etapa].actualizar(PASO)
        self.bus.entregar()
