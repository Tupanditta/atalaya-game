"""Pantallas del juego y reparto de las acciones del jugador (`modulos/flujo.md`).

Versión de S6: el juego empieza en el menú principal (CU-01, RF-34). Durante la oleada,
`flujo` entrega los ejes de giro y la posición de la mira a `vista` y el estado de la
barra espaciadora a `armamento`. Esc pausa la partida durante la oleada o el descanso
(CU-09); desde la pausa se consulta el manual (CU-10), se abandona la partida o se sale
del juego (CU-12), con confirmación. Tras la derrota se muestra el resumen con «Volver a
jugar» y «Menú principal». La selección de nivel y la victoria llegan en S7: hasta
entonces solo existe el nivel 1 y «Jugar» empieza la partida directamente (CU-01, A1).
Durante el salto hiperespacial entre dos fondos (RN-20) la vista gira, pero la barra
espaciadora no apunta ni dispara.
"""

from collections.abc import Mapping
from enum import Enum
from types import MappingProxyType
from typing import Protocol, TypeVar

from atalaya.logica.armamento import Armamento
from atalaya.logica.mejoras import Mejoras, Motivo
from atalaya.logica.nucleo.bus import Bus
from atalaya.logica.nucleo.dominio import Accion, Mejora
from atalaya.logica.nucleo.eventos import (
    DescansoIniciado,
    DescansoTerminado,
    EstacionDestruida,
    PartidaAbandonada,
    PartidaIniciada,
    PausaCambiada,
    SaltoIniciado,
    SaltoTerminado,
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


class Reloj(Protocol):
    """Reloj pausable de la partida. Lo implementa `nucleo` (RN-50)."""

    def pausar(self) -> None:
        """Detiene el tiempo de la partida."""

    def reanudar(self) -> None:
        """Reanuda el tiempo de la partida donde se detuvo."""


class Pantalla(Enum):
    """Pantallas del juego. La selección de nivel llega en S7."""

    MENU_PRINCIPAL = "menu_principal"
    OLEADA_EN_CURSO = "oleada_en_curso"
    #: Descanso entre oleadas, con la pantalla de mejoras.
    DESCANSO = "descanso"
    PAUSA = "pausa"
    MANUAL = "manual"
    #: Confirmación de abandonar la partida o de salir del juego, encima de la pausa.
    CONFIRMACION = "confirmacion"
    RESUMEN = "resumen"


class OpcionMenu(Enum):
    """Opciones del menú principal, en el orden en que se muestran (RF-34)."""

    JUGAR = "jugar"
    MANUAL = "manual"
    SALIR = "salir"


class OpcionDescanso(Enum):
    """Opciones de la pantalla de mejoras, en el orden en que se muestran (CU-11)."""

    REPARAR = "reparar"
    BLINDAJE = "blindaje"
    BATERIA = "bateria"
    GENERADOR = "generador"
    CONTINUAR = "continuar"


class OpcionPausa(Enum):
    """Opciones del menú de pausa, en el orden en que se muestran (CU-09)."""

    CONTINUAR = "continuar"
    MANUAL = "manual"
    ABANDONAR = "abandonar"
    SALIR = "salir"


class Confirmacion(Enum):
    """Lo que se pide confirmar desde la pausa."""

    ABANDONAR = "abandonar"
    SALIR = "salir"


class OpcionConfirmacion(Enum):
    """Opciones de una confirmación, de izquierda a derecha. «No» es la primera."""

    NO = "no"
    SI = "si"


class OpcionResumen(Enum):
    """Opciones del resumen de fin de partida. «Subir nivel» llega en S7 (CU-08)."""

    VOLVER_A_JUGAR = "volver_a_jugar"
    MENU_PRINCIPAL = "menu_principal"


class SeccionManual(Enum):
    """Secciones del manual, en el orden en que se muestran (CU-10)."""

    CONTROLES = "controles"
    ENEMIGOS = "enemigos"
    TAMANOS = "tamanos"
    ENTORNOS = "entornos"
    MEJORAS = "mejoras"


#: Mejora que compra cada opción de la pantalla de mejoras.
MEJORA_DE_OPCION: Mapping[OpcionDescanso, Mejora] = MappingProxyType(
    {
        OpcionDescanso.BLINDAJE: Mejora.BLINDAJE,
        OpcionDescanso.BATERIA: Mejora.BATERIA,
        OpcionDescanso.GENERADOR: Mejora.GENERADOR,
    }
)

#: Opciones de cada pantalla con menú, en el orden en que se muestran. En el manual, las
#: «opciones» son sus secciones.
_OPCIONES: Mapping[Pantalla, tuple[Enum, ...]] = MappingProxyType(
    {
        Pantalla.MENU_PRINCIPAL: tuple(OpcionMenu),
        Pantalla.DESCANSO: tuple(OpcionDescanso),
        Pantalla.PAUSA: tuple(OpcionPausa),
        Pantalla.CONFIRMACION: tuple(OpcionConfirmacion),
        Pantalla.RESUMEN: tuple(OpcionResumen),
        Pantalla.MANUAL: tuple(SeccionManual),
    }
)

#: Pantallas de la partida en curso, desde las que Esc pausa (RF-35).
_PANTALLAS_PAUSABLES = (Pantalla.OLEADA_EN_CURSO, Pantalla.DESCANSO)

#: Nivel de dificultad con el que se juega mientras no hay selección de nivel (hasta S7).
_NIVEL_INICIAL = 1

_E = TypeVar("_E", bound=Enum)


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
        reloj: Reloj,
    ) -> None:
        self._bus = bus
        self._acciones = acciones
        self._vista = vista
        self._armamento = armamento
        self._mejoras = mejoras
        self._reloj = reloj
        self._pantalla = Pantalla.MENU_PRINCIPAL
        #: Pantalla de la partida a la que vuelve la pausa.
        self._pausada = Pantalla.OLEADA_EN_CURSO
        #: Pantalla a la que vuelve el manual: el menú principal o la pausa.
        self._origen_manual = Pantalla.MENU_PRINCIPAL
        self._confirmacion = Confirmacion.ABANDONAR
        self._nivel = _NIVEL_INICIAL
        self._oleadas_superadas = 0
        self._salir = False
        self._seleccion = dict.fromkeys(_OPCIONES, 0)
        self._continuar_pedido = False
        self._sonidos = dict.fromkeys(SonidoMenu, 0)
        self._en_salto = False
        bus.suscribir(EstacionDestruida, self._al_destruir_estacion)
        bus.suscribir(DescansoIniciado, self._al_iniciar_descanso)
        bus.suscribir(DescansoTerminado, self._al_terminar_descanso)
        bus.suscribir(SaltoIniciado, self._al_iniciar_salto)
        bus.suscribir(SaltoTerminado, self._al_terminar_salto)

    # --- consultas -------------------------------------------------------------------

    @property
    def pantalla(self) -> Pantalla:
        """Pantalla actual."""
        return self._pantalla

    @property
    def pantalla_pausada(self) -> Pantalla | None:
        """Pantalla de la partida detenida (oleada o descanso), o `None` si no hay pausa.

        Durante la pausa, el manual abierto desde ella o una confirmación.
        """
        if self._pantalla is Pantalla.PAUSA or self._pantalla is Pantalla.CONFIRMACION:
            return self._pausada
        if self._pantalla is Pantalla.MANUAL and self._origen_manual is Pantalla.PAUSA:
            return self._pausada
        return None

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
    def opciones_menu(self) -> tuple[OpcionMenu, ...]:
        """Opciones del menú principal, en el orden en que se muestran."""
        return tuple(OpcionMenu)

    @property
    def seleccion_menu(self) -> OpcionMenu:
        """Opción seleccionada en el menú principal."""
        return self._seleccionada(Pantalla.MENU_PRINCIPAL, OpcionMenu)

    @property
    def opciones_descanso(self) -> tuple[OpcionDescanso, ...]:
        """Opciones de la pantalla de mejoras, en el orden en que se muestran."""
        return tuple(OpcionDescanso)

    @property
    def seleccion_descanso(self) -> OpcionDescanso:
        """Opción seleccionada en la pantalla de mejoras."""
        return self._seleccionada(Pantalla.DESCANSO, OpcionDescanso)

    @property
    def opciones_pausa(self) -> tuple[OpcionPausa, ...]:
        """Opciones del menú de pausa, en el orden en que se muestran."""
        return tuple(OpcionPausa)

    @property
    def seleccion_pausa(self) -> OpcionPausa:
        """Opción seleccionada en el menú de pausa."""
        return self._seleccionada(Pantalla.PAUSA, OpcionPausa)

    @property
    def confirmacion(self) -> Confirmacion:
        """Lo que pide confirmar la última confirmación abierta."""
        return self._confirmacion

    @property
    def seleccion_confirmacion(self) -> OpcionConfirmacion:
        """Opción seleccionada en la confirmación."""
        return self._seleccionada(Pantalla.CONFIRMACION, OpcionConfirmacion)

    @property
    def opciones_resumen(self) -> tuple[OpcionResumen, ...]:
        """Opciones del resumen de fin de partida, en el orden en que se muestran."""
        return tuple(OpcionResumen)

    @property
    def seleccion_resumen(self) -> OpcionResumen:
        """Opción seleccionada en el resumen de fin de partida."""
        return self._seleccionada(Pantalla.RESUMEN, OpcionResumen)

    @property
    def secciones_manual(self) -> tuple[SeccionManual, ...]:
        """Secciones del manual, en el orden en que se muestran."""
        return tuple(SeccionManual)

    @property
    def seccion_manual(self) -> SeccionManual:
        """Sección del manual que se está mostrando."""
        return self._seleccionada(Pantalla.MANUAL, SeccionManual)

    @property
    def nivel_manual(self) -> int:
        """Nivel cuya vida de los enemigos muestra el manual (CU-10, A1).

        Abierto desde la pausa, el de la partida en curso; desde el menú principal, el 1.
        """
        return self._nivel if self._origen_manual is Pantalla.PAUSA else _NIVEL_INICIAL

    def sonidos_menu(self, sonido: SonidoMenu) -> int:
        """Veces que ha tocado `sonido` desde el arranque; `audio` lo hace sonar cuando sube."""
        return self._sonidos[sonido]

    # --- operaciones -----------------------------------------------------------------

    def iniciar_partida(self, nivel: int = _NIVEL_INICIAL) -> None:
        """Empieza una partida en `nivel` y pasa a la oleada en curso."""
        self._nivel = nivel
        self._oleadas_superadas = 0
        self._en_salto = False
        self._pantalla = Pantalla.OLEADA_EN_CURSO
        self._bus.publicar(PartidaIniciada(nivel))

    def actualizar(self, dt: float) -> None:
        """Reparte las acciones del paso según la pantalla actual."""
        pantalla = self._pantalla
        if pantalla is Pantalla.OLEADA_EN_CURSO:
            self._actualizar_oleada()
        elif pantalla is Pantalla.DESCANSO:
            self._actualizar_descanso()
        elif pantalla is Pantalla.MENU_PRINCIPAL:
            self._actualizar_menu()
        elif pantalla is Pantalla.PAUSA:
            self._actualizar_pausa()
        elif pantalla is Pantalla.CONFIRMACION:
            self._actualizar_confirmacion()
        elif pantalla is Pantalla.MANUAL:
            self._actualizar_manual()
        else:
            self._actualizar_resumen()

    # --- partida ---------------------------------------------------------------------

    def _actualizar_oleada(self) -> None:
        if self._acciones.recien_pulsada(Accion.PAUSA):
            self._pausar()
            return
        self._entregar_controles()

    def _entregar_controles(self) -> None:
        """Ejes de giro y mira a `vista`; barra espaciadora a `armamento`."""
        a = self._acciones
        self._vista.recibir_ejes(
            eje_de_flechas(a.mantenida(Accion.IZQUIERDA), a.mantenida(Accion.DERECHA)),
            eje_de_flechas(a.mantenida(Accion.ABAJO), a.mantenida(Accion.ARRIBA)),
        )
        self._vista.recibir_puntero(*a.puntero())
        # Durante el salto no se dispara: no hay enemigos y la estación está en tránsito.
        self._armamento.recibir_disparo(not self._en_salto and a.mantenida(Accion.DISPARO))

    def _actualizar_descanso(self) -> None:
        """Pantalla de mejoras: las flechas mueven la selección e Intro la elige (CU-11).

        Las flechas no giran la vista: en el descanso no se entregan ejes a `vista`.
        """
        if self._acciones.recien_pulsada(Accion.PAUSA):
            self._pausar()
            return
        self._navegar_vertical()
        if self._acciones.recien_pulsada(Accion.CONFIRMAR):
            self._elegir_descanso(self.seleccion_descanso)

    def _elegir_descanso(self, opcion: OpcionDescanso) -> None:
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

    # --- menú principal --------------------------------------------------------------

    def _actualizar_menu(self) -> None:
        """Jugar, Manual o Salir del juego; Esc no hace nada (RF-34)."""
        self._navegar_vertical()
        if not self._acciones.recien_pulsada(Accion.CONFIRMAR):
            return
        opcion = self.seleccion_menu
        self._sonar(SonidoMenu.CONFIRMAR)
        if opcion is OpcionMenu.JUGAR:
            # Hasta S7 solo existe el nivel 1: no se pide elegir nivel (CU-01, A1).
            self.iniciar_partida(_NIVEL_INICIAL)
        elif opcion is OpcionMenu.MANUAL:
            self._abrir_manual(Pantalla.MENU_PRINCIPAL)
        else:
            # Desde el menú principal se sale sin confirmación (CU-12).
            self._salir = True

    # --- pausa -----------------------------------------------------------------------

    def _pausar(self) -> None:
        """Detiene el tiempo de la partida y abre el menú de pausa (CU-09, RN-50).

        Si la barra estaba pulsada, el apuntado se cancela: al soltarla no se dispara
        (CU-09, A1; RN-38).
        """
        self._pausada = self._pantalla
        self._soltar_disparo()
        self._reloj.pausar()
        self._abrir(Pantalla.PAUSA)
        self._bus.publicar(PausaCambiada(activa=True))

    def _reanudar(self) -> None:
        """Vuelve a la pantalla detenida y reanuda el tiempo donde se detuvo (RF-36).

        En la oleada, los controles de este paso llegan ya a `vista` y `armamento`: el
        paso de partida que se ejecuta ahora es el mismo que se habría ejecutado sin pausa.
        """
        self._pantalla = self._pausada
        self._reloj.reanudar()
        self._bus.publicar(PausaCambiada(activa=False))
        if self._pantalla is Pantalla.OLEADA_EN_CURSO:
            self._entregar_controles()

    def _actualizar_pausa(self) -> None:
        """Continuar (o Esc), Manual, Abandonar partida o Salir del juego (CU-09)."""
        a = self._acciones
        if a.recien_pulsada(Accion.PAUSA):
            self._reanudar()
            return
        self._navegar_vertical()
        if not a.recien_pulsada(Accion.CONFIRMAR):
            return
        opcion = self.seleccion_pausa
        self._sonar(SonidoMenu.CONFIRMAR)
        if opcion is OpcionPausa.CONTINUAR:
            self._reanudar()
        elif opcion is OpcionPausa.MANUAL:
            self._abrir_manual(Pantalla.PAUSA)
        elif opcion is OpcionPausa.ABANDONAR:
            self._abrir_confirmacion(Confirmacion.ABANDONAR)
        else:
            self._abrir_confirmacion(Confirmacion.SALIR)

    def _abrir_confirmacion(self, confirmacion: Confirmacion) -> None:
        """Pide confirmación con «No» seleccionada (CU-09 A4, CU-12 A1)."""
        self._confirmacion = confirmacion
        self._abrir(Pantalla.CONFIRMACION)

    def _actualizar_confirmacion(self) -> None:
        """«No» o Esc vuelven a la pausa; «Sí» abandona la partida o cierra el juego."""
        a = self._acciones
        if a.recien_pulsada(Accion.PAUSA):
            self._abrir(Pantalla.PAUSA)
            return
        # «No» y «Sí» están en una fila: se cambia con ←→ o con ↑↓ (`interfaz.md`).
        self._navegar(Accion.IZQUIERDA, Accion.DERECHA)
        self._navegar_vertical()
        if not a.recien_pulsada(Accion.CONFIRMAR):
            return
        self._sonar(SonidoMenu.CONFIRMAR)
        if self.seleccion_confirmacion is OpcionConfirmacion.NO:
            self._abrir(Pantalla.PAUSA)
        elif self._confirmacion is Confirmacion.ABANDONAR:
            self._abandonar()
        else:
            # La partida en curso se pierde con el juego (CU-12, A1).
            self._salir = True

    def _abandonar(self) -> None:
        """Descarta la partida y vuelve al menú principal (RF-37, CU-09 A4).

        No cambia el nivel desbloqueado. `enemigos` y `oleadas` se limpian con
        PartidaAbandonada; el reloj vuelve a correr para el menú.
        """
        self._reloj.reanudar()
        self._bus.publicar(PausaCambiada(activa=False))
        self._bus.publicar(PartidaAbandonada())
        self._abrir(Pantalla.MENU_PRINCIPAL)

    # --- manual ----------------------------------------------------------------------

    def _abrir_manual(self, origen: Pantalla) -> None:
        """Abre el manual por su primera sección (CU-10)."""
        self._origen_manual = origen
        self._abrir(Pantalla.MANUAL)

    def _actualizar_manual(self) -> None:
        """←→ cambian de sección; Esc vuelve a la pantalla desde la que se abrió (CU-10).

        Abierto desde la pausa, la partida sigue detenida: el reloj no se toca.
        """
        if self._acciones.recien_pulsada(Accion.PAUSA):
            self._abrir(self._origen_manual)
            return
        self._navegar(Accion.IZQUIERDA, Accion.DERECHA)

    # --- resumen ---------------------------------------------------------------------

    def _actualizar_resumen(self) -> None:
        """Volver a jugar con el mismo nivel o ir al menú principal (RF-19, RF-20)."""
        self._navegar_vertical()
        if not self._acciones.recien_pulsada(Accion.CONFIRMAR):
            return
        self._sonar(SonidoMenu.CONFIRMAR)
        if self.seleccion_resumen is OpcionResumen.VOLVER_A_JUGAR:
            # Solo se conserva el nivel de la partida anterior (CU-01, A2).
            self.iniciar_partida(self._nivel)
        else:
            self._abrir(Pantalla.MENU_PRINCIPAL)

    # --- menús -----------------------------------------------------------------------

    def _abrir(self, pantalla: Pantalla) -> None:
        """Muestra `pantalla` con su primera opción seleccionada."""
        self._pantalla = pantalla
        self._seleccion[pantalla] = 0

    def _seleccionada(self, pantalla: Pantalla, tipo: type[_E]) -> _E:
        return list(tipo)[self._seleccion[pantalla]]

    def _navegar_vertical(self) -> None:
        self._navegar(Accion.ARRIBA, Accion.ABAJO)

    def _navegar(self, anterior: Accion, siguiente: Accion) -> None:
        """Mueve la selección de la pantalla actual con las flechas `anterior` y `siguiente`."""
        a = self._acciones
        if a.recien_pulsada(anterior):
            self._mover_seleccion(-1)
        if a.recien_pulsada(siguiente):
            self._mover_seleccion(1)

    def _mover_seleccion(self, desplazamiento: int) -> None:
        """Mueve la selección sin salir de la lista; en los extremos no hace nada."""
        pantalla = self._pantalla
        actual = self._seleccion[pantalla]
        seleccion = max(0, min(len(_OPCIONES[pantalla]) - 1, actual + desplazamiento))
        if seleccion != actual:
            self._seleccion[pantalla] = seleccion
            self._sonar(SonidoMenu.MOVER)

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
        self._abrir(Pantalla.RESUMEN)
        # Soltar la barra después de la derrota no debe disparar.
        self._soltar_disparo()

    def _al_iniciar_descanso(self, evento: DescansoIniciado) -> None:
        """Se abre la pantalla de mejoras con «Reparar» seleccionada (CU-11)."""
        if self._pantalla is not Pantalla.OLEADA_EN_CURSO:
            return
        self._abrir(Pantalla.DESCANSO)
        self._continuar_pedido = False
        # La barra pulsada al acabar la oleada no apunta ni dispara durante el descanso.
        self._soltar_disparo()

    def _al_iniciar_salto(self, evento: SaltoIniciado) -> None:
        """Empieza el salto: la barra pulsada no apunta ni dispara hasta llegar (RN-20)."""
        self._en_salto = True
        self._soltar_disparo()

    def _al_terminar_salto(self, evento: SaltoTerminado) -> None:
        self._en_salto = False

    def _al_terminar_descanso(self, evento: DescansoTerminado) -> None:
        """Se cierra la pantalla de mejoras y sigue la oleada (CU-11, A5 y A6)."""
        if self._pantalla is Pantalla.DESCANSO:
            self._pantalla = Pantalla.OLEADA_EN_CURSO
        elif self.pantalla_pausada is Pantalla.DESCANSO:
            # Al reanudar se vuelve a la oleada, no a un descanso que ya ha terminado.
            self._pausada = Pantalla.OLEADA_EN_CURSO
