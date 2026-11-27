"""Integridad de la estación y efectos de los ataques enemigos (`modulos/estacion.md`).

Versión de S5: integridad, destrucción, desestabilización y aturdimiento, más la
reparación (RN-46) y el blindaje (RN-47) que compra el jugador en el descanso. El
escudo acorta o alarga los efectos según lo lleno que esté, y se gasta con los
impactos que los causan; en el descanso se regenera y se expande (RN-51).
"""

from atalaya.logica.nucleo.bus import Bus
from atalaya.logica.nucleo.dominio import Mejora, TipoEnemigo
from atalaya.logica.nucleo.eventos import (
    AturdimientoIniciado,
    AturdimientoTerminado,
    DesestabilizacionIniciada,
    DesestabilizacionTerminada,
    EscudoCambiado,
    EstacionDanada,
    EstacionDestruida,
    IntegridadCambiada,
    MejoraAplicada,
    OleadaSuperada,
    PartidaIniciada,
    ProyectilImpacta,
    RegeneracionEscudoAplicada,
    ReparacionAplicada,
)
from atalaya.logica.parametros.modelo import Parametros

#: Por debajo de esta integridad, la estación se considera destruida.
_TOLERANCIA = 1e-9

#: Margen para que la suma de pasos en coma flotante no retrase un paso el fin de un efecto.
_TOLERANCIA_TIEMPO = 1e-9


class Estacion:
    """Integridad de la estación, su destrucción y los efectos sobre el jugador."""

    def __init__(self, bus: Bus, parametros: Parametros) -> None:
        self._bus = bus
        self._parametros = parametros
        self._maxima = parametros.jugador.integridad_maxima
        self._integridad = self._maxima
        self._destruida = False
        self._oleadas_superadas = 0
        self._aturdimiento = 0.0
        self._desestabilizacion = 0.0
        self._escudo_maximo = parametros.jugador.escudo_maximo
        self._escudo = self._escudo_maximo
        bus.suscribir(ProyectilImpacta, self._al_impactar)
        bus.suscribir(OleadaSuperada, self._al_superar_oleada)
        bus.suscribir(ReparacionAplicada, self._al_reparar)
        bus.suscribir(RegeneracionEscudoAplicada, self._al_regenerar_escudo)
        bus.suscribir(MejoraAplicada, self._al_mejorar)
        bus.suscribir(PartidaIniciada, self._al_iniciar_partida)

    # --- operaciones -----------------------------------------------------------------

    def actualizar(self, dt: float) -> None:
        """Descuenta la duración de los efectos y publica su fin al llegar a cero."""
        if self._desestabilizacion > 0:
            self._desestabilizacion -= dt
            if self._desestabilizacion <= _TOLERANCIA_TIEMPO:
                self._desestabilizacion = 0.0
                self._bus.publicar(DesestabilizacionTerminada())
        if self._aturdimiento > 0:
            self._aturdimiento -= dt
            if self._aturdimiento <= _TOLERANCIA_TIEMPO:
                self._aturdimiento = 0.0
                self._bus.publicar(AturdimientoTerminado())

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

    @property
    def escudo(self) -> float:
        """Escudo actual, entre 0 y el máximo."""
        return self._escudo

    @property
    def escudo_maximo(self) -> float:
        """Escudo máximo."""
        return self._escudo_maximo

    @property
    def aturdido(self) -> bool:
        """Indica si el jugador está aturdido (RN-13)."""
        return self._aturdimiento > 0

    @property
    def tiempo_aturdimiento(self) -> float:
        """Segundos que le quedan al aturdimiento; 0 si no está aturdido."""
        return self._aturdimiento

    @property
    def desestabilizado(self) -> bool:
        """Indica si la estación está desestabilizada (RN-12)."""
        return self._desestabilizacion > 0

    @property
    def tiempo_desestabilizacion(self) -> float:
        """Segundos que le quedan a la desestabilización; 0 si no está desestabilizada."""
        return self._desestabilizacion

    # --- eventos ---------------------------------------------------------------------

    def _al_impactar(self, evento: ProyectilImpacta) -> None:
        """Resta el daño del tipo sin bajar de cero y aplica su efecto (RN-10 a RN-13).

        A cero, la estación cae una sola vez y deja de recibir impactos (RN-17). El
        impacto que la destruye no empieza ningún efecto: la partida ya ha terminado.
        """
        if self._destruida:
            return
        datos = self._parametros.tipos.de(evento.tipo_enemigo)
        anterior = self._integridad
        self._integridad = max(0.0, anterior - datos.dano)
        if self._integridad <= _TOLERANCIA:
            self._integridad = 0.0
        if self._integridad > 0:
            # La duración sale del escudo de antes del impacto; después se gasta (RN-51).
            fraccion = self._escudo / self._escudo_maximo
            duracion = self._parametros.duracion_efecto(evento.tipo_enemigo, fraccion)
            self._aplicar_efecto(evento.tipo_enemigo, duracion)
            self._gastar_escudo(datos.desgaste_escudo)
        self._bus.publicar(
            EstacionDanada(anterior - self._integridad, self._integridad, self._maxima)
        )
        self._bus.publicar(IntegridadCambiada(self._integridad, self._maxima))
        if self._integridad == 0:
            self._destruida = True
            self._bus.publicar(EstacionDestruida(self._oleadas_superadas))

    def _aplicar_efecto(self, tipo: TipoEnemigo, duracion: float) -> None:
        """Empieza o renueva el efecto del tipo con su duración completa (RN-12, RN-13)."""
        if tipo is TipoEnemigo.DESESTABILIZADOR:
            self._desestabilizacion = duracion
            self._bus.publicar(DesestabilizacionIniciada(duracion))
        elif tipo is TipoEnemigo.ATURDIDOR:
            self._aturdimiento = duracion
            self._bus.publicar(AturdimientoIniciado(duracion))

    def _gastar_escudo(self, desgaste: float) -> None:
        """Resta `desgaste` al escudo sin bajar de cero (RN-51)."""
        if desgaste <= 0 or self._escudo <= 0:
            return
        self._escudo = max(0.0, self._escudo - desgaste)
        if self._escudo <= _TOLERANCIA:
            self._escudo = 0.0
        self._bus.publicar(EscudoCambiado(self._escudo, self._escudo_maximo))

    def _al_regenerar_escudo(self, evento: RegeneracionEscudoAplicada) -> None:
        """Suma la regeneración sin superar el escudo máximo (RN-51)."""
        if self._destruida:
            return
        self._escudo = min(self._escudo_maximo, self._escudo + evento.cantidad)
        self._bus.publicar(EscudoCambiado(self._escudo, self._escudo_maximo))

    def _al_reparar(self, evento: ReparacionAplicada) -> None:
        """Suma la reparación sin superar la integridad máxima (RN-46)."""
        if self._destruida:
            return
        self._integridad = min(self._maxima, self._integridad + evento.cantidad)
        self._bus.publicar(IntegridadCambiada(self._integridad, self._maxima))

    def _al_mejorar(self, evento: MejoraAplicada) -> None:
        """El blindaje sube la integridad máxima y la actual con cada nivel (RN-47); el
        escudo, el escudo máximo y el actual (RN-51)."""
        if self._destruida:
            return
        if evento.mejora is Mejora.BLINDAJE:
            efecto = self._parametros.mejoras.blindaje.efecto
            maxima = self._parametros.jugador.integridad_maxima + efecto * evento.nivel
            self._integridad += maxima - self._maxima
            self._maxima = maxima
            self._bus.publicar(IntegridadCambiada(self._integridad, self._maxima))
        elif evento.mejora is Mejora.ESCUDO:
            efecto = self._parametros.mejoras.escudo.efecto
            maxima = self._parametros.jugador.escudo_maximo + efecto * evento.nivel
            self._escudo += maxima - self._escudo_maximo
            self._escudo_maximo = maxima
            self._bus.publicar(EscudoCambiado(self._escudo, self._escudo_maximo))

    def _al_superar_oleada(self, evento: OleadaSuperada) -> None:
        self._oleadas_superadas = evento.numero

    def _al_iniciar_partida(self, evento: PartidaIniciada) -> None:
        """Todo vuelve a sus valores iniciales; los efectos activos terminan sin evento.

        `vista` y `armamento` también se restablecen con PartidaIniciada.
        """
        self._maxima = self._parametros.jugador.integridad_maxima
        self._integridad = self._maxima
        self._destruida = False
        self._oleadas_superadas = 0
        self._aturdimiento = 0.0
        self._desestabilizacion = 0.0
        self._escudo_maximo = self._parametros.jugador.escudo_maximo
        self._escudo = self._escudo_maximo
        self._bus.publicar(IntegridadCambiada(self._integridad, self._maxima))
        self._bus.publicar(EscudoCambiado(self._escudo, self._escudo_maximo))
