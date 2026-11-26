"""Oleadas: aparición, cronómetro y fin de cada oleada (`modulos/oleadas.md`).

Versión de S3: aparición con su ritmo y el máximo de enemigos activos (RN-43),
cronómetro y fin de oleada (RN-15). Al superar una oleada empieza directamente la
siguiente; el descanso llega en S5. Todos los enemigos son medianos y sin efecto
especial; la mezcla de tipos y tamaños llega en S4.
"""

from dataclasses import dataclass

from atalaya.logica.nucleo.bus import Bus
from atalaya.logica.nucleo.dominio import Tamano, TipoEnemigo
from atalaya.logica.nucleo.eventos import (
    EnemigoDestruido,
    EstacionDestruida,
    OleadaIniciada,
    OleadaSuperada,
    PartidaAbandonada,
    PartidaGanada,
    PartidaIniciada,
    SolicitudAparicion,
)
from atalaya.logica.parametros.modelo import Parametros


@dataclass(frozen=True, slots=True)
class EnemigoPendiente:
    """Enemigo de la oleada que aún no ha aparecido."""

    tipo: TipoEnemigo
    tamano: Tamano
    vida: float


class Oleadas:
    """Decide qué enemigos aparecen y cuándo, y cuándo termina cada oleada."""

    def __init__(self, bus: Bus, parametros: Parametros) -> None:
        self._bus = bus
        self._parametros = parametros
        self._nivel = 1
        self._numero = 0
        self._en_curso = False
        self._pendientes: list[EnemigoPendiente] = []
        self._enemigos = 0
        self._activos = 0
        self._desde_aparicion = 0.0
        self._cronometro = 0.0
        self._cronometro_en_marcha = False
        bus.suscribir(PartidaIniciada, self._al_iniciar_partida)
        bus.suscribir(EnemigoDestruido, self._al_destruir_enemigo)
        bus.suscribir(PartidaAbandonada, self._al_detener)
        bus.suscribir(EstacionDestruida, self._al_detener)

    # --- operaciones -----------------------------------------------------------------

    def iniciar_oleada(self, numero: int) -> None:
        """Empieza la oleada `numero` con el nivel de la partida en curso."""
        composicion = self._parametros.composicion_oleada(numero)
        vida = self._parametros.vida_enemigo(Tamano.MEDIANO, self._nivel)
        self._numero = numero
        self._en_curso = True
        self._enemigos = composicion.numero_enemigos
        self._pendientes = [
            EnemigoPendiente(TipoEnemigo.SIN_EFECTO, Tamano.MEDIANO, vida)
            for _ in range(composicion.numero_enemigos)
        ]
        self._activos = 0
        self._cronometro = 0.0
        self._cronometro_en_marcha = False
        # El primer enemigo aparece en el primer paso de la oleada.
        self._desde_aparicion = self._parametros.ataques.intervalo_aparicion
        self._bus.publicar(OleadaIniciada(numero, self._parametros.entorno_oleada(numero)))

    def actualizar(self, dt: float) -> None:
        """Avanza el cronómetro y pide una aparición cada intervalo si hay hueco (RN-43)."""
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
        # Hasta S5 no hay descanso: la siguiente oleada empieza en el acto.
        self.iniciar_oleada(self._numero + 1)

    def _al_detener(self, evento: object) -> None:
        self._en_curso = False
        self._cronometro_en_marcha = False
        self._pendientes = []
        self._activos = 0
