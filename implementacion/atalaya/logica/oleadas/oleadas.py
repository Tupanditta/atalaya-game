"""Oleadas: aparición, cronómetro y fin de cada oleada (`modulos/oleadas.md`).

Versión de S5: composición completa de cada oleada, con tamaños y tipos mezclados
(RN-06, RN-16), aparición con su ritmo y el máximo de enemigos activos (RN-43),
cronómetro y fin de oleada (RN-15), y descanso entre oleadas con su cuenta atrás y su
fin anticipado (RN-18, RF-44). Tras el descanso de las oleadas 10, 20, 30 y 40 hay un
salto hiperespacial al fondo siguiente antes de empezar la oleada (RN-20).
"""

from dataclasses import dataclass

from atalaya.logica.nucleo.azar import Azar
from atalaya.logica.nucleo.bus import Bus
from atalaya.logica.nucleo.dominio import Tamano, TipoEnemigo
from atalaya.logica.nucleo.eventos import (
    DescansoIniciado,
    DescansoTerminado,
    EnemigoDestruido,
    EstacionDestruida,
    OleadaIniciada,
    OleadaSuperada,
    PartidaAbandonada,
    PartidaGanada,
    PartidaIniciada,
    SaltoIniciado,
    SaltoTerminado,
    SolicitudAparicion,
    TerminarDescansoSolicitado,
)
from atalaya.logica.parametros.modelo import Parametros

#: Margen para que la suma de pasos en coma flotante no retrase un paso el fin del descanso
#: o del salto.
_TOLERANCIA_TIEMPO = 1e-9


@dataclass(frozen=True, slots=True)
class EnemigoPendiente:
    """Enemigo de la oleada que aún no ha aparecido."""

    tipo: TipoEnemigo
    tamano: Tamano
    vida: float


def componer_oleada(
    parametros: Parametros, numero: int, nivel: int, azar: Azar
) -> list[EnemigoPendiente]:
    """Enemigos de la oleada `numero` en el nivel `nivel`, en su orden de aparición.

    - Cada enemigo tiene un tamaño al azar entre los tres (RN-06).
    - Desde que se permiten tipos con efecto, la oleada lleva el máximo de enemigos con
      efecto que admite (un tercio), cada uno de un tipo con efecto permitido al azar. Así
      la dificultad nunca baja de una oleada a la siguiente (RN-16).
    - El orden de aparición se baraja.
    """
    composicion = parametros.composicion_oleada(numero)
    con_efecto = sorted(
        (t for t in composicion.tipos_permitidos if t is not TipoEnemigo.SIN_EFECTO),
        key=lambda t: t.value,
    )
    tipos = [TipoEnemigo.SIN_EFECTO] * composicion.numero_enemigos
    if con_efecto:
        for i in range(composicion.maximo_con_efecto):
            tipos[i] = azar.elegir(con_efecto)
    tamanos = list(Tamano)
    pendientes = []
    for tipo in tipos:
        tamano = azar.elegir(tamanos)
        pendientes.append(EnemigoPendiente(tipo, tamano, parametros.vida_enemigo(tamano, nivel)))
    azar.barajar(pendientes)
    return pendientes


class Oleadas:
    """Decide qué enemigos aparecen y cuándo, y cuándo termina cada oleada."""

    def __init__(self, bus: Bus, parametros: Parametros, azar: Azar) -> None:
        self._bus = bus
        self._parametros = parametros
        self._azar = azar
        self._nivel = 1
        self._numero = 0
        self._en_curso = False
        self._pendientes: list[EnemigoPendiente] = []
        self._enemigos = 0
        self._activos = 0
        self._desde_aparicion = 0.0
        self._cronometro = 0.0
        self._cronometro_en_marcha = False
        self._en_descanso = False
        self._descanso = 0.0
        self._en_salto = False
        self._salto = 0.0
        bus.suscribir(PartidaIniciada, self._al_iniciar_partida)
        bus.suscribir(EnemigoDestruido, self._al_destruir_enemigo)
        bus.suscribir(TerminarDescansoSolicitado, self._al_pedir_fin_descanso)
        bus.suscribir(PartidaAbandonada, self._al_detener)
        bus.suscribir(EstacionDestruida, self._al_detener)

    # --- operaciones -----------------------------------------------------------------

    def iniciar_oleada(self, numero: int) -> None:
        """Empieza la oleada `numero` con el nivel de la partida en curso."""
        self._pendientes = componer_oleada(self._parametros, numero, self._nivel, self._azar)
        self._numero = numero
        self._en_curso = True
        self._en_descanso = False
        self._descanso = 0.0
        self._en_salto = False
        self._salto = 0.0
        self._enemigos = len(self._pendientes)
        self._activos = 0
        self._cronometro = 0.0
        self._cronometro_en_marcha = False
        # El primer enemigo aparece en el primer paso de la oleada.
        self._desde_aparicion = self._parametros.ataques.intervalo_aparicion
        self._bus.publicar(OleadaIniciada(numero, self._parametros.entorno_oleada(numero)))

    def actualizar(self, dt: float) -> None:
        """Avanza el cronómetro y pide una aparición cada intervalo si hay hueco (RN-43).

        Durante el descanso solo descuenta su tiempo; al llegar a cero, empieza la
        siguiente oleada (RN-18) o, si cambia el fondo, el salto. Durante el salto también
        descuenta su tiempo y, al llegar a cero, empieza la oleada (RN-20).
        """
        if self._en_descanso:
            self._descanso -= dt
            if self._descanso <= _TOLERANCIA_TIEMPO:
                self._terminar_descanso()
            return
        if self._en_salto:
            self._salto -= dt
            if self._salto <= _TOLERANCIA_TIEMPO:
                self._terminar_salto()
            return
        if not self._en_curso:
            return
        if self._cronometro_en_marcha:
            self._cronometro += dt
        ataques = self._parametros.ataques
        self._desde_aparicion += dt
        if (
            self._pendientes
            and self._activos < ataques.enemigos_activos_maximos
            and self._desde_aparicion >= ataques.intervalo_aparicion - 1e-9
        ):
            siguiente = self._pendientes.pop(0)
            self._activos += 1
            self._desde_aparicion = 0.0
            # El cronómetro corre desde que aparece el primer enemigo.
            self._cronometro_en_marcha = True
            self._bus.publicar(SolicitudAparicion(siguiente.tipo, siguiente.tamano, siguiente.vida))

    # --- consultas -------------------------------------------------------------------

    @property
    def numero(self) -> int:
        """Número de la oleada actual, o 0 antes de empezar."""
        return self._numero

    @property
    def nivel(self) -> int:
        """Nivel de dificultad de la partida."""
        return self._nivel

    @property
    def en_curso(self) -> bool:
        """Indica si hay una oleada en curso."""
        return self._en_curso

    @property
    def activos(self) -> int:
        """Enemigos de la oleada que han aparecido y siguen sin destruir."""
        return self._activos

    @property
    def pendientes(self) -> int:
        """Enemigos de la oleada que aún no han aparecido."""
        return len(self._pendientes)

    @property
    def restantes(self) -> int:
        """Enemigos de la oleada que faltan por destruir."""
        return self._activos + len(self._pendientes)

    @property
    def en_descanso(self) -> bool:
        """Indica si la partida está en el descanso entre dos oleadas (RN-18)."""
        return self._en_descanso

    @property
    def tiempo_descanso(self) -> float:
        """Segundos que le quedan al descanso; 0 fuera del descanso."""
        return self._descanso

    @property
    def en_salto(self) -> bool:
        """Indica si la partida está en el salto hiperespacial a otro fondo (RN-20)."""
        return self._en_salto

    @property
    def tiempo_salto(self) -> float:
        """Segundos que le quedan al salto; 0 fuera del salto."""
        return self._salto

    @property
    def cronometro(self) -> float:
        """Segundos desde que apareció el primer enemigo de la oleada actual."""
        return self._cronometro

    # --- eventos ---------------------------------------------------------------------

    def _al_iniciar_partida(self, evento: PartidaIniciada) -> None:
        self._nivel = evento.nivel
        self.iniciar_oleada(1)

    def _al_destruir_enemigo(self, evento: EnemigoDestruido) -> None:
        if not self._en_curso or self._activos == 0:
            return
        self._activos -= 1
        if self.restantes == 0:
            self._superar_oleada()

    def _superar_oleada(self) -> None:
        """Sin enemigos activos ni pendientes, la oleada está superada (RN-15, RN-19)."""
        self._en_curso = False
        self._cronometro_en_marcha = False
        if self._numero == self._parametros.oleadas.numero_oleadas:
            self._bus.publicar(PartidaGanada(self._nivel))
            return
        self._bus.publicar(OleadaSuperada(self._numero, self._cronometro, self._enemigos))
        self._en_descanso = True
        self._descanso = self._parametros.duracion_descanso(self._nivel)
        self._bus.publicar(DescansoIniciado(self._descanso, self._numero + 1))

    def _terminar_descanso(self) -> None:
        """Cierra el descanso y empieza la siguiente oleada (RN-18, CU-07 paso 7).

        Si la siguiente oleada es de otro fondo, antes empieza el salto (RN-20).
        """
        self._en_descanso = False
        self._descanso = 0.0
        self._bus.publicar(DescansoTerminado())
        if self._parametros.hay_salto_tras(self._numero):
            self._en_salto = True
            self._salto = self._parametros.oleadas.duracion_salto
            fondo = self._parametros.fondo_oleada(self._numero + 1)
            self._bus.publicar(SaltoIniciado(fondo, self._salto))
            return
        self.iniciar_oleada(self._numero + 1)

    def _terminar_salto(self) -> None:
        """Cierra el salto y empieza la siguiente oleada en el fondo nuevo (RN-20)."""
        self._en_salto = False
        self._salto = 0.0
        self._bus.publicar(SaltoTerminado())
        self.iniciar_oleada(self._numero + 1)

    def _al_pedir_fin_descanso(self, evento: TerminarDescansoSolicitado) -> None:
        """El jugador termina el descanso antes de tiempo (RF-44)."""
        if self._en_descanso:
            self._terminar_descanso()

    def _al_detener(self, evento: object) -> None:
        self._en_curso = False
        self._en_descanso = False
        self._descanso = 0.0
        self._en_salto = False
        self._salto = 0.0
        self._cronometro_en_marcha = False
        self._pendientes = []
        self._activos = 0
