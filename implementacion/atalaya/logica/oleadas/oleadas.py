"""Oleadas: aparición de los enemigos de la oleada en curso (`modulos/oleadas.md`).

Versión de S2: solo la aparición, con su ritmo y el máximo de enemigos activos (RN-43).
Todos los enemigos son medianos y sin efecto especial; la mezcla de tipos y tamaños
llega en S4. El fin de oleada y el cronómetro llegan en S3; el descanso, en S5.
"""

from dataclasses import dataclass

from atalaya.logica.nucleo.bus import Bus
from atalaya.logica.nucleo.dominio import Tamano, TipoEnemigo
from atalaya.logica.nucleo.eventos import (
    EnemigoDestruido,
    EstacionDestruida,
    OleadaIniciada,
    PartidaAbandonada,
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
    """Decide qué enemigos aparecen y cuándo."""

    def __init__(self, bus: Bus, parametros: Parametros) -> None:
        self._bus = bus
        self._parametros = parametros
        self._nivel = 1
        self._numero = 0
        self._en_curso = False
        self._pendientes: list[EnemigoPendiente] = []
        self._activos = 0
        self._desde_aparicion = 0.0
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
        self._pendientes = [
            EnemigoPendiente(TipoEnemigo.SIN_EFECTO, Tamano.MEDIANO, vida)
            for _ in range(composicion.numero_enemigos)
        ]
        self._activos = 0
        # El primer enemigo aparece en el primer paso de la oleada.
        self._desde_aparicion = self._parametros.ataques.intervalo_aparicion
        self._bus.publicar(OleadaIniciada(numero, self._parametros.entorno_oleada(numero)))

    def actualizar(self, dt: float) -> None:
        """Pide una aparición cada intervalo mientras haya hueco y pendientes (RN-43)."""
        if not self._en_curso:
            return
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

    # --- eventos ---------------------------------------------------------------------

    def _al_iniciar_partida(self, evento: PartidaIniciada) -> None:
        self._nivel = evento.nivel
        self.iniciar_oleada(1)

    def _al_destruir_enemigo(self, evento: EnemigoDestruido) -> None:
        if self._en_curso and self._activos > 0:
            self._activos -= 1

    def _al_detener(self, evento: object) -> None:
        self._en_curso = False
        self._pendientes = []
        self._activos = 0
