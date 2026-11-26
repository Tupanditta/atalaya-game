"""Pantallas del juego y reparto de las acciones del jugador (`modulos/flujo.md`).

Versión de S5: la oleada en curso, que entrega los ejes de giro y la posición de la mira
a `vista` y el estado de la barra espaciadora a `armamento`; el descanso, con la pantalla
de mejoras (CU-11); y el resumen de fin de partida tras la derrota. La partida empieza
directamente, sin menús (CU-01). Los menús y la pausa llegan en S6.
"""

from collections.abc import Mapping
from enum import Enum
from types import MappingProxyType
from typing import Protocol

from atalaya.logica.armamento import Armamento
from atalaya.logica.mejoras import Mejoras, Motivo
from atalaya.logica.nucleo.bus import Bus
from atalaya.logica.nucleo.dominio import Accion, Mejora
from atalaya.logica.nucleo.eventos import (
    DescansoIniciado,
    DescansoTerminado,
    EstacionDestruida,
    PartidaIniciada,
    TerminarDescansoSolicitado,
)
from atalaya.logica.vista import Vista, eje_de_flechas


class Acciones(Protocol):
    """Estado de las acciones del jugador en el paso actual. Lo implementa `entrada`."""

    def mantenida(self, accion: Accion) -> bool:
        """Indica si la acción está activa en este paso."""

    def recien_pulsada(self, accion: Accion) -> bool:
        """Indica si la acción ha empezado en este paso."""

    def recien_soltada(self, accion: Accion) -> bool:
        """Indica si la acción ha terminado en este paso."""

    def puntero(self) -> tuple[float, float]:
        """Posición de la mira en la pantalla que marca el ratón."""


class Pantalla(Enum):
    """Pantallas del juego. S5 tiene la oleada en curso, el descanso y el resumen."""

    OLEADA_EN_CURSO = "oleada_en_curso"
    #: Descanso entre oleadas, con la pantalla de mejoras.
    DESCANSO = "descanso"
    RESUMEN = "resumen"


class OpcionDescanso(Enum):
    """Opciones de la pantalla de mejoras, en el orden en que se muestran (CU-11)."""

    REPARAR = "reparar"
    BLINDAJE = "blindaje"
    BATERIA = "bateria"
    GENERADOR = "generador"
    CONTINUAR = "continuar"


#: Mejora que compra cada opción de la pantalla de mejoras.
MEJORA_DE_OPCION: Mapping[OpcionDescanso, Mejora] = MappingProxyType(
    {
        OpcionDescanso.BLINDAJE: Mejora.BLINDAJE,
        OpcionDescanso.BATERIA: Mejora.BATERIA,
        OpcionDescanso.GENERADOR: Mejora.GENERADOR,
    }
)


class SonidoMenu(Enum):
    """Respuesta de un menú a una acción del jugador, que `audio` hace sonar."""

    MOVER = "mover"
    CONFIRMAR = "confirmar"
    ERROR = "error"


class Flujo:
    """Sabe en qué pantalla está el juego y decide qué hace cada acción en ella."""

    def __init__(
        self,
        bus: Bus,
        acciones: Acciones,
        vista: Vista,
        armamento: Armamento,
        mejoras: Mejoras,
    ) -> None:
        self._bus = bus
        self._acciones = acciones
        self._vista = vista
        self._armamento = armamento
        self._mejoras = mejoras
        self._pantalla: Pantalla | None = None
        self._nivel = 1
        self._oleadas_superadas = 0
        self._salir = False
        self._opciones = tuple(OpcionDescanso)
        self._seleccion = 0
        self._continuar_pedido = False
        self._sonidos = dict.fromkeys(SonidoMenu, 0)
        bus.suscribir(EstacionDestruida, self._al_destruir_estacion)
        bus.suscribir(DescansoIniciado, self._al_iniciar_descanso)
        bus.suscribir(DescansoTerminado, self._al_terminar_descanso)

    # --- consultas -------------------------------------------------------------------

    @property
    def pantalla(self) -> Pantalla | None:
        """Pantalla actual, o `None` antes de empezar."""
        return self._pantalla

    @property
    def nivel(self) -> int:
        """Nivel de la partida en curso."""
        return self._nivel

    @property
    def oleadas_superadas(self) -> int:
        """Oleadas superadas en la partida terminada, para el resumen."""
        return self._oleadas_superadas

    @property
    def salir_solicitado(self) -> bool:
        """Indica si el jugador ha pedido cerrar el juego."""
        return self._salir

    @property
    def opciones_descanso(self) -> tuple[OpcionDescanso, ...]:
        """Opciones de la pantalla de mejoras, en el orden en que se muestran."""
        return self._opciones

    @property
    def seleccion_descanso(self) -> OpcionDescanso:
        """Opción seleccionada en la pantalla de mejoras."""
        return self._opciones[self._seleccion]

    def sonidos_menu(self, sonido: SonidoMenu) -> int:
        """Veces que ha tocado `sonido` desde el arranque; `audio` lo hace sonar cuando sube."""
        return self._sonidos[sonido]

    # --- operaciones -----------------------------------------------------------------

    def iniciar_partida(self, nivel: int = 1) -> None:
        """Empieza una partida en `nivel` y pasa a la oleada en curso."""
        self._nivel = nivel
        self._oleadas_superadas = 0
        self._pantalla = Pantalla.OLEADA_EN_CURSO
        self._bus.publicar(PartidaIniciada(nivel))

    def actualizar(self, dt: float) -> None:
        """Reparte las acciones del paso según la pantalla actual."""
        if self._pantalla is Pantalla.OLEADA_EN_CURSO:
            self._actualizar_oleada()
        elif self._pantalla is Pantalla.DESCANSO:
            self._actualizar_descanso()
        elif self._pantalla is Pantalla.RESUMEN:
            self._actualizar_resumen()

    # --- pantallas -------------------------------------------------------------------

    def _actualizar_oleada(self) -> None:
        a = self._acciones
        # Provisional hasta S6: sin pantalla de pausa, Esc cierra el juego.
        if a.recien_pulsada(Accion.PAUSA):
            self._salir = True
            return
        self._vista.recibir_ejes(
            eje_de_flechas(a.mantenida(Accion.IZQUIERDA), a.mantenida(Accion.DERECHA)),
            eje_de_flechas(a.mantenida(Accion.ABAJO), a.mantenida(Accion.ARRIBA)),
        )
        self._vista.recibir_puntero(*a.puntero())
        self._armamento.recibir_disparo(a.mantenida(Accion.DISPARO))

    def _actualizar_descanso(self) -> None:
        """Pantalla de mejoras: las flechas mueven la selección e Intro la elige (CU-11).

        Las flechas no giran la vista: en el descanso no se entregan ejes a `vista`.
        """
        a = self._acciones
        # Provisional hasta S6, igual que en la oleada: sin pausa, Esc cierra el juego.
        if a.recien_pulsada(Accion.PAUSA):
            self._salir = True
            return
        if a.recien_pulsada(Accion.ARRIBA):
            self._mover_seleccion(-1)
        if a.recien_pulsada(Accion.ABAJO):
            self._mover_seleccion(1)
        if a.recien_pulsada(Accion.CONFIRMAR):
            self._elegir(self.seleccion_descanso)

    def _mover_seleccion(self, desplazamiento: int) -> None:
        """Mueve la selección sin salir de la lista; en los extremos no hace nada."""
        seleccion = max(0, min(len(self._opciones) - 1, self._seleccion + desplazamiento))
        if seleccion != self._seleccion:
            self._seleccion = seleccion
            self._sonar(SonidoMenu.MOVER)

    def _elegir(self, opcion: OpcionDescanso) -> None:
        """Compra la opción en `mejoras` o termina el descanso (CU-11, A1 a A5).

        Si la compra no es posible, no se aplica nada y suena el error (A2 a A4).
        """
        if opcion is OpcionDescanso.CONTINUAR:
            if not self._continuar_pedido:
                self._continuar_pedido = True
                self._sonar(SonidoMenu.CONFIRMAR)
                self._bus.publicar(TerminarDescansoSolicitado())
            return
        motivo: Motivo | None
        if opcion is OpcionDescanso.REPARAR:
            motivo = self._mejoras.reparar()
        else:
            motivo = self._mejoras.mejorar(MEJORA_DE_OPCION[opcion])
        self._sonar(SonidoMenu.CONFIRMAR if motivo is None else SonidoMenu.ERROR)

    def _actualizar_resumen(self) -> None:
        """Resumen mínimo de derrota: Intro vuelve a jugar y Esc cierra el juego."""
        a = self._acciones
        if a.recien_pulsada(Accion.CONFIRMAR):
            self.iniciar_partida(self._nivel)
        elif a.recien_pulsada(Accion.PAUSA):
            self._salir = True

    # --- internos --------------------------------------------------------------------

    def _sonar(self, sonido: SonidoMenu) -> None:
        self._sonidos[sonido] += 1

    def _soltar_disparo(self) -> None:
        """Cancela el apuntado y da la barra por suelta, sin disparar."""
        self._armamento.cancelar_apuntado()
        self._armamento.recibir_disparo(False)

    # --- eventos ---------------------------------------------------------------------

    def _al_destruir_estacion(self, evento: EstacionDestruida) -> None:
        """La partida termina: se muestra el resumen y se deja de apuntar (CU-06, A3)."""
        self._oleadas_superadas = evento.oleadas_superadas
        self._pantalla = Pantalla.RESUMEN
        # Soltar la barra después de la derrota no debe disparar.
        self._soltar_disparo()

    def _al_iniciar_descanso(self, evento: DescansoIniciado) -> None:
        """Se abre la pantalla de mejoras con «Reparar» seleccionada (CU-11)."""
        if self._pantalla is not Pantalla.OLEADA_EN_CURSO:
            return
        self._pantalla = Pantalla.DESCANSO
        self._seleccion = 0
        self._continuar_pedido = False
        # La barra pulsada al acabar la oleada no apunta ni dispara durante el descanso.
        self._soltar_disparo()

    def _al_terminar_descanso(self, evento: DescansoTerminado) -> None:
        """Se cierra la pantalla de mejoras y sigue la oleada (CU-11, A5 y A6)."""
        if self._pantalla is Pantalla.DESCANSO:
            self._pantalla = Pantalla.OLEADA_EN_CURSO
