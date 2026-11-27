"""Puntos de mejora, reparación y mejoras de la estación (`modulos/mejoras.md`).

Al superar una oleada da puntos según lo rápido que se ha superado (RN-45). Durante el
descanso, y solo entonces (RN-48), el jugador los gasta en reparar (RN-46), en regenerar
el escudo (RN-51) o en subir un nivel el blindaje, el escudo, la batería o el generador
(RN-47). `mejoras` no cambia la integridad, el escudo ni la energía: publica
ReparacionAplicada, RegeneracionEscudoAplicada y MejoraAplicada, y `estacion` y
`armamento` aplican el efecto. Los puntos y las mejoras solo duran la partida (RN-49).
"""

from dataclasses import dataclass
from enum import Enum

from atalaya.logica.nucleo.bus import Bus
from atalaya.logica.nucleo.dominio import Mejora
from atalaya.logica.nucleo.eventos import (
    DescansoIniciado,
    DescansoTerminado,
    EscudoCambiado,
    IntegridadCambiada,
    MejoraAplicada,
    OleadaSuperada,
    PartidaIniciada,
    PuntosObtenidos,
    RegeneracionEscudoAplicada,
    ReparacionAplicada,
)
from atalaya.logica.parametros.modelo import Parametros

#: Margen para comparar tiempos y cantidades acumulados en coma flotante.
_TOLERANCIA = 1e-9


class Motivo(Enum):
    """Por qué no se puede comprar una opción de la pantalla de mejoras."""

    SIN_PUNTOS = "sin_puntos"
    INTEGRIDAD_MAXIMA = "integridad_maxima"
    ESCUDO_MAXIMO = "escudo_maximo"
    NIVEL_MAXIMO = "nivel_maximo"
    FUERA_DEL_DESCANSO = "fuera_del_descanso"


@dataclass(frozen=True, slots=True)
class ResultadoOleada:
    """Resultado de la última oleada superada (RF-43)."""

    numero: int
    #: Segundos que ha durado la oleada.
    tiempo: float
    tiempo_referencia: float
    puntos: int


def tiempo_referencia(parametros: Parametros, enemigos: int) -> float:
    """Tiempo de referencia de una oleada con `enemigos` enemigos (RN-45)."""
    m = parametros.mejoras
    return m.tiempo_referencia_base + m.tiempo_referencia_por_enemigo * enemigos


def puntos_oleada(parametros: Parametros, tiempo: float, enemigos: int) -> int:
    """Puntos por superar en `tiempo` segundos una oleada de `enemigos` enemigos (RN-45).

    Cuanto más rápido, más puntos; siempre al menos los de una oleada lenta.
    """
    m = parametros.mejoras
    referencia = tiempo_referencia(parametros, enemigos)
    if tiempo <= referencia + _TOLERANCIA:
        return m.puntos_rapido
    if tiempo <= referencia * m.factor_tiempo_medio + _TOLERANCIA:
        return m.puntos_medio
    return m.puntos_lento


class Mejoras:
    """Puntos disponibles, nivel de cada mejora y compras durante el descanso."""

    def __init__(self, bus: Bus, parametros: Parametros) -> None:
        self._bus = bus
        self._parametros = parametros
        self._datos = parametros.mejoras
        self._puntos = 0
        self._niveles = dict.fromkeys(Mejora, 0)
        self._en_descanso = False
        self._resultado: ResultadoOleada | None = None
        self._integridad = parametros.jugador.integridad_maxima
        self._integridad_maxima = parametros.jugador.integridad_maxima
        self._escudo = parametros.jugador.escudo_maximo
        self._escudo_maximo = parametros.jugador.escudo_maximo
        bus.suscribir(OleadaSuperada, self._al_superar_oleada)
        bus.suscribir(DescansoIniciado, self._al_iniciar_descanso)
        bus.suscribir(DescansoTerminado, self._al_terminar_descanso)
        bus.suscribir(IntegridadCambiada, self._al_cambiar_integridad)
        bus.suscribir(EscudoCambiado, self._al_cambiar_escudo)
        bus.suscribir(PartidaIniciada, self._al_iniciar_partida)

    # --- operaciones -----------------------------------------------------------------

    def reparar(self) -> Motivo | None:
        """Gasta el coste de una reparación y publica ReparacionAplicada (RN-46).

        Devuelve el motivo si no se puede reparar, sin gastar nada, o `None` si repara.
        """
        motivo = self.motivo_reparar()
        if motivo is not None:
            return motivo
        cantidad = self._datos.cantidad_reparacion
        self._puntos -= self._datos.coste_reparacion
        # La integridad que confirma `estacion` llega con IntegridadCambiada en la siguiente
        # entrega; se anticipa para que otra reparación en el mismo paso la tenga en cuenta.
        self._integridad = min(self._integridad_maxima, self._integridad + cantidad)
        self._bus.publicar(ReparacionAplicada(cantidad))
        return None

    def regenerar_escudo(self) -> Motivo | None:
        """Gasta el coste de una regeneración y publica RegeneracionEscudoAplicada (RN-51).

        Devuelve el motivo si no se puede regenerar, sin gastar nada, o `None` si regenera.
        """
        motivo = self.motivo_regenerar_escudo()
        if motivo is not None:
            return motivo
        cantidad = self._datos.cantidad_regeneracion
        self._puntos -= self._datos.coste_regeneracion
        # Igual que en `reparar`: se anticipa lo que confirmará `estacion`.
        self._escudo = min(self._escudo_maximo, self._escudo + cantidad)
        self._bus.publicar(RegeneracionEscudoAplicada(cantidad))
        return None

    def mejorar(self, mejora: Mejora) -> Motivo | None:
        """Gasta el coste de `mejora`, sube su nivel y publica MejoraAplicada (RN-47).

        Devuelve el motivo si no se puede mejorar, sin gastar nada, o `None` si mejora.
        """
        motivo = self.motivo_mejorar(mejora)
        if motivo is not None:
            return motivo
        datos = self._datos.de(mejora)
        self._puntos -= datos.coste
        self._niveles[mejora] += 1
        if mejora is Mejora.BLINDAJE:
            # Igual que en `reparar`: se anticipa lo que confirmará `estacion`.
            self._integridad_maxima += datos.efecto
            self._integridad += datos.efecto
        elif mejora is Mejora.ESCUDO:
            self._escudo_maximo += datos.efecto
            self._escudo += datos.efecto
        self._bus.publicar(MejoraAplicada(mejora, self._niveles[mejora]))
        return None

    # --- consultas -------------------------------------------------------------------

    @property
    def puntos(self) -> int:
        """Puntos de mejora disponibles."""
        return self._puntos

    @property
    def en_descanso(self) -> bool:
        """Indica si está abierto el descanso, el único momento de comprar (RN-48)."""
        return self._en_descanso

    @property
    def resultado(self) -> ResultadoOleada | None:
        """Resultado de la última oleada superada, o `None` si aún no se ha superado ninguna."""
        return self._resultado

    @property
    def coste_reparacion(self) -> int:
        """Puntos que cuesta una reparación."""
        return self._datos.coste_reparacion

    @property
    def cantidad_reparacion(self) -> float:
        """Integridad que devuelve una reparación."""
        return self._datos.cantidad_reparacion

    @property
    def coste_regeneracion(self) -> int:
        """Puntos que cuesta una regeneración del escudo."""
        return self._datos.coste_regeneracion

    @property
    def cantidad_regeneracion(self) -> float:
        """Escudo que devuelve una regeneración."""
        return self._datos.cantidad_regeneracion

    def nivel(self, mejora: Mejora) -> int:
        """Nivel actual de `mejora`, de 0 al máximo."""
        return self._niveles[mejora]

    def nivel_maximo(self, mejora: Mejora) -> int:
        """Nivel máximo de `mejora`."""
        return self._datos.de(mejora).niveles_maximos

    def coste(self, mejora: Mejora) -> int:
        """Puntos que cuesta subir un nivel `mejora`."""
        return self._datos.de(mejora).coste

    def efecto(self, mejora: Mejora) -> float:
        """Lo que sube la característica con cada nivel de `mejora`."""
        return self._datos.de(mejora).efecto

    def motivo_reparar(self) -> Motivo | None:
        """Por qué no se puede reparar ahora, o `None` si se puede."""
        if not self._en_descanso:
            return Motivo.FUERA_DEL_DESCANSO
        if self._integridad >= self._integridad_maxima - _TOLERANCIA:
            return Motivo.INTEGRIDAD_MAXIMA
        if self._puntos < self._datos.coste_reparacion:
            return Motivo.SIN_PUNTOS
        return None

    def motivo_regenerar_escudo(self) -> Motivo | None:
        """Por qué no se puede regenerar el escudo ahora, o `None` si se puede."""
        if not self._en_descanso:
            return Motivo.FUERA_DEL_DESCANSO
        if self._escudo >= self._escudo_maximo - _TOLERANCIA:
            return Motivo.ESCUDO_MAXIMO
        if self._puntos < self._datos.coste_regeneracion:
            return Motivo.SIN_PUNTOS
        return None

    def motivo_mejorar(self, mejora: Mejora) -> Motivo | None:
        """Por qué no se puede subir `mejora` ahora, o `None` si se puede."""
        if not self._en_descanso:
            return Motivo.FUERA_DEL_DESCANSO
        if self._niveles[mejora] >= self.nivel_maximo(mejora):
            return Motivo.NIVEL_MAXIMO
        if self._puntos < self.coste(mejora):
            return Motivo.SIN_PUNTOS
        return None

    # --- eventos ---------------------------------------------------------------------

    def _al_superar_oleada(self, evento: OleadaSuperada) -> None:
        """Da los puntos de la oleada y los suma a los disponibles (RN-45)."""
        referencia = tiempo_referencia(self._parametros, evento.enemigos)
        puntos = puntos_oleada(self._parametros, evento.tiempo, evento.enemigos)
        self._puntos += puntos
        self._resultado = ResultadoOleada(evento.numero, evento.tiempo, referencia, puntos)
        self._bus.publicar(PuntosObtenidos(puntos, self._puntos, evento.tiempo, referencia))

    def _al_iniciar_descanso(self, evento: DescansoIniciado) -> None:
        self._en_descanso = True

    def _al_terminar_descanso(self, evento: DescansoTerminado) -> None:
        self._en_descanso = False

    def _al_cambiar_integridad(self, evento: IntegridadCambiada) -> None:
        self._integridad = evento.actual
        self._integridad_maxima = evento.maxima

    def _al_cambiar_escudo(self, evento: EscudoCambiado) -> None:
        self._escudo = evento.actual
        self._escudo_maximo = evento.maxima

    def _al_iniciar_partida(self, evento: PartidaIniciada) -> None:
        """Sin puntos ni mejoras al empezar (RN-49)."""
        self._puntos = 0
        self._niveles = dict.fromkeys(Mejora, 0)
        self._en_descanso = False
        self._resultado = None
        self._integridad = self._parametros.jugador.integridad_maxima
        self._integridad_maxima = self._parametros.jugador.integridad_maxima
        self._escudo = self._parametros.jugador.escudo_maximo
        self._escudo_maximo = self._parametros.jugador.escudo_maximo
