"""Pruebas del flujo: menú principal, pausa, confirmaciones, manual y resumen (Sprint 6).

Montan los módulos como en el juego real, con un teclado falso en lugar del motor.
"""

import pytest

from atalaya.arranque import Juego, montar
from atalaya.logica.flujo import (
    Confirmacion,
    OpcionConfirmacion,
    OpcionMenu,
    OpcionPausa,
    OpcionResumen,
    Pantalla,
    SeccionManual,
    SonidoMenu,
)
from atalaya.logica.nucleo import PASO
from atalaya.logica.nucleo.bus import Evento
from atalaya.logica.nucleo.eventos import (
    DisparoRealizado,
    DisparoSinEnergia,
    EnemigoDestruido,
    EstacionDestruida,
    PartidaAbandonada,
    PartidaIniciada,
    PausaCambiada,
)
from atalaya.logica.parametros import Parametros

#: Pasos de simulación en 10 s.
DIEZ_SEGUNDOS = 600


class TecladoFalso:
    def __init__(self) -> None:
        self.teclas: set[str] = set()

    def pulsadas(self, teclas: frozenset[str]) -> frozenset[str]:
        return frozenset(self.teclas) & teclas

    def tiene_foco(self) -> bool:
        return True


class Montaje:
    """Juego montado con un teclado falso y registro de los eventos de `flujo`."""

    def __init__(self, parametros: Parametros, semilla: int = 6) -> None:
        self.teclado = TecladoFalso()
        self.juego: Juego = montar(parametros, self.teclado, semilla=semilla)
        self.flujo = self.juego.flujo
        self.nucleo = self.juego.nucleo
        self.eventos: list[Evento] = []
        for tipo in (PartidaIniciada, PartidaAbandonada, PausaCambiada):
            self.nucleo.bus.suscribir(tipo, self.eventos.append)

    def avanzar(self, pasos: int = 1) -> None:
        for _ in range(pasos):
            self.nucleo.avanzar(PASO)

    def pulsar(self, *teclas: str) -> None:
        """Pulsa cada tecla durante un paso y la suelta en el siguiente.

        Las teclas que ya estaban mantenidas siguen mantenidas.
        """
        for tecla in teclas:
            self.teclado.teclas.add(tecla)
            self.avanzar()
            self.teclado.teclas.discard(tecla)
            self.avanzar()

    def jugar(self) -> None:
        """«Jugar» en el menú principal, que aparece con «Jugar» seleccionada."""
        assert self.flujo.pantalla is Pantalla.MENU_PRINCIPAL
        self.pulsar("enter")

    def superar_oleada(self) -> None:
        """Hace aparecer a todos los enemigos de la oleada y los da por destruidos."""
        oleadas = self.juego.oleadas
        while oleadas.pendientes:
            self.avanzar()
        for enemigo in self.juego.enemigos.activos:
            self.nucleo.bus.publicar(EnemigoDestruido(enemigo.id, enemigo.posicion))
        self.avanzar()

    def de_tipo(self, tipo: type[Evento]) -> list[Evento]:
        return [e for e in self.eventos if isinstance(e, tipo)]


@pytest.fixture
def montaje(parametros: Parametros) -> Montaje:
    return Montaje(parametros)


def _pausar_desde(montaje: Montaje, pantalla: Pantalla) -> None:
    """Empieza una partida, llega a `pantalla` (oleada o descanso) y pulsa Esc."""
    montaje.jugar()
    if pantalla is Pantalla.DESCANSO:
        montaje.superar_oleada()
    montaje.avanzar(30)
    assert montaje.flujo.pantalla is pantalla
    montaje.pulsar("escape")
    assert montaje.flujo.pantalla is Pantalla.PAUSA


# --- menú principal ------------------------------------------------------------------


def test_el_juego_empieza_en_el_menu_principal(montaje: Montaje) -> None:
    """RF-34: al abrir el juego se muestra el menú principal, sin partida en curso."""
    assert montaje.flujo.pantalla is Pantalla.MENU_PRINCIPAL
    assert montaje.flujo.seleccion_menu is OpcionMenu.JUGAR
    montaje.avanzar(DIEZ_SEGUNDOS)
    assert montaje.juego.enemigos.activos == ()
    assert not montaje.juego.oleadas.en_curso
    assert montaje.eventos == []


def test_s6_t01_cu01_jugar_con_solo_el_nivel_1(montaje: Montaje) -> None:
    """S6-T01 CU-01, RF-34: «Jugar» empieza la partida en el nivel 1, sin elegir nivel."""
    montaje.jugar()
    assert montaje.flujo.pantalla is Pantalla.OLEADA_EN_CURSO
    assert montaje.de_tipo(PartidaIniciada) == [PartidaIniciada(nivel=1)]
    assert montaje.flujo.nivel == 1
    assert montaje.juego.oleadas.numero == 1


def test_s6_t02_cu10_manual_desde_el_menu_principal(montaje: Montaje) -> None:
    """S6-T02 CU-10, RF-39: «Manual» abre el manual; Esc vuelve al menú principal."""
    montaje.pulsar("arrow_down", "enter")
    assert montaje.flujo.pantalla is Pantalla.MANUAL
    assert montaje.flujo.seccion_manual is SeccionManual.CONTROLES
    assert montaje.flujo.pantalla_pausada is None
    montaje.pulsar("escape")
    assert montaje.flujo.pantalla is Pantalla.MENU_PRINCIPAL
    assert montaje.flujo.seleccion_menu is OpcionMenu.JUGAR
    assert montaje.eventos == []


def test_s6_t03_cu12_salir_desde_el_menu_principal(montaje: Montaje) -> None:
    """S6-T03 CU-12, RF-38: «Salir del juego» pide cerrar el juego sin confirmación."""
    montaje.pulsar("arrow_down", "arrow_down")
    assert montaje.flujo.seleccion_menu is OpcionMenu.SALIR
    assert not montaje.flujo.salir_solicitado
    montaje.pulsar("enter")
    assert montaje.flujo.salir_solicitado
    assert montaje.flujo.pantalla is Pantalla.MENU_PRINCIPAL


def test_s6_t13_navegacion_en_el_menu_principal(montaje: Montaje) -> None:
    """S6-T13: flecha abajo pasa a la siguiente opción e Intro ejecuta la seleccionada."""
    montaje.pulsar("arrow_down")
    assert montaje.flujo.seleccion_menu is OpcionMenu.MANUAL
    assert montaje.flujo.sonidos_menu(SonidoMenu.MOVER) == 1
    montaje.pulsar("arrow_up", "arrow_up")
    assert montaje.flujo.seleccion_menu is OpcionMenu.JUGAR
    # En el extremo de la lista la flecha no mueve la selección ni suena.
    assert montaje.flujo.sonidos_menu(SonidoMenu.MOVER) == 2
    montaje.pulsar("arrow_down", "enter")
    assert montaje.flujo.pantalla is Pantalla.MANUAL
    assert montaje.flujo.sonidos_menu(SonidoMenu.CONFIRMAR) == 1


def test_esc_en_el_menu_principal_no_hace_nada(montaje: Montaje) -> None:
    """En el menú principal, Esc no pausa ni cierra el juego."""
    montaje.pulsar("escape")
    assert montaje.flujo.pantalla is Pantalla.MENU_PRINCIPAL
    assert not montaje.flujo.salir_solicitado
    assert not montaje.nucleo.en_pausa


def test_en_el_menu_las_flechas_no_giran_la_vista(montaje: Montaje) -> None:
    """En el menú principal las flechas solo navegan: la vista no gira."""
    orientacion = montaje.juego.vista.orientacion
    montaje.teclado.teclas = {"arrow_right", "arrow_down"}
    montaje.avanzar(60)
    assert montaje.juego.vista.orientacion == orientacion


# --- pausa ---------------------------------------------------------------------------


def test_s6_t04_cu09_esc_durante_una_oleada(montaje: Montaje) -> None:
    """S6-T04 CU-09, RF-35: Esc abre la pausa con «Continuar» y detiene el reloj."""
    montaje.jugar()
    montaje.avanzar(30)
    montaje.teclado.teclas.add("escape")
    montaje.avanzar()
    assert montaje.flujo.pantalla is Pantalla.PAUSA
    assert montaje.flujo.seleccion_pausa is OpcionPausa.CONTINUAR
    assert montaje.flujo.pantalla_pausada is Pantalla.OLEADA_EN_CURSO
    assert montaje.de_tipo(PausaCambiada) == [PausaCambiada(activa=True)]
    assert montaje.nucleo.en_pausa
    tiempo = montaje.nucleo.tiempo_partida
    montaje.avanzar(60)
    assert montaje.nucleo.tiempo_partida == tiempo


def test_s6_t06_rn50_pausa_durante_el_descanso(montaje: Montaje) -> None:
    """S6-T06 RN-50: 10 s de pausa en el descanso no cambian la cuenta atrás."""
    _pausar_desde(montaje, Pantalla.DESCANSO)
    assert montaje.flujo.pantalla_pausada is Pantalla.DESCANSO
    restante = montaje.juego.oleadas.tiempo_descanso
    montaje.avanzar(DIEZ_SEGUNDOS)
    assert montaje.juego.oleadas.tiempo_descanso == restante
    assert montaje.juego.oleadas.en_descanso


@pytest.mark.parametrize("pantalla", [Pantalla.OLEADA_EN_CURSO, Pantalla.DESCANSO])
@pytest.mark.parametrize("tecla", ["enter", "escape"], ids=["continuar", "esc"])
def test_s6_t07_rf36_reanudar(montaje: Montaje, pantalla: Pantalla, tecla: str) -> None:
    """S6-T07 RF-36: «Continuar» o Esc vuelven a la pantalla anterior y el reloj sigue."""
    _pausar_desde(montaje, pantalla)
    montaje.avanzar(60)
    tiempo = montaje.nucleo.tiempo_partida
    montaje.pulsar(tecla)
    assert montaje.flujo.pantalla is pantalla
    assert montaje.flujo.pantalla_pausada is None
    assert montaje.de_tipo(PausaCambiada)[-1] == PausaCambiada(activa=False)
    assert not montaje.nucleo.en_pausa
    assert montaje.nucleo.tiempo_partida == pytest.approx(tiempo + 2 * PASO)


def test_s6_t08_rn38_pausar_apuntando(montaje: Montaje) -> None:
    """S6-T08 RN-38, CU-09 A1: pausar con la barra pulsada cancela el apuntado; al
    reanudar y soltar no se dispara."""
    disparos: list[Evento] = []
    montaje.nucleo.bus.suscribir(DisparoRealizado, disparos.append)
    montaje.nucleo.bus.suscribir(DisparoSinEnergia, disparos.append)
    montaje.jugar()
    armamento = montaje.juego.armamento
    montaje.teclado.teclas.add("space")
    montaje.avanzar(30)
    apuntado = armamento.progreso_apuntado
    assert apuntado > 0
    montaje.pulsar("escape")
    montaje.avanzar(60)
    montaje.pulsar("escape")
    assert montaje.flujo.pantalla is Pantalla.OLEADA_EN_CURSO
    # Con la barra aún pulsada, la mira vuelve a su tamaño normal en vez de reducirse.
    assert armamento.progreso_apuntado < apuntado
    montaje.avanzar(30)
    assert armamento.progreso_apuntado == 0
    montaje.teclado.teclas.discard("space")
    montaje.avanzar(5)
    assert disparos == []
    # Una pulsación nueva sí apunta y dispara.
    montaje.teclado.teclas.add("space")
    montaje.avanzar(30)
    montaje.teclado.teclas.discard("space")
    montaje.avanzar()
    assert len(disparos) == 1


def test_s6_t09_en_pausa_las_flechas_no_giran(montaje: Montaje) -> None:
    """S6-T09: con la partida en pausa, las flechas no cambian la orientación."""
    montaje.jugar()
    montaje.pulsar("escape")
    orientacion = montaje.juego.vista.orientacion
    montaje.teclado.teclas = {"arrow_left", "arrow_up"}
    montaje.avanzar(60)
    assert montaje.juego.vista.orientacion == orientacion


def test_s6_t10_manual_desde_la_pausa(montaje: Montaje) -> None:
    """S6-T10: «Manual» en la pausa abre el manual con la partida detenida; Esc vuelve."""
    montaje.jugar()
    montaje.pulsar("escape", "arrow_down", "enter")
    assert montaje.flujo.pantalla is Pantalla.MANUAL
    assert montaje.flujo.pantalla_pausada is Pantalla.OLEADA_EN_CURSO
    tiempo = montaje.nucleo.tiempo_partida
    montaje.pulsar("arrow_right")
    montaje.avanzar(60)
    assert montaje.nucleo.en_pausa
    assert montaje.nucleo.tiempo_partida == tiempo
    montaje.pulsar("escape")
    assert montaje.flujo.pantalla is Pantalla.PAUSA
    assert montaje.flujo.seleccion_pausa is OpcionPausa.CONTINUAR
    assert montaje.nucleo.en_pausa


def test_s6_t11_rf37_abandonar(montaje: Montaje) -> None:
    """S6-T11 RF-37, CU-09 A4 y A5: abandonar pide confirmación; «No» y Esc vuelven a la
    pausa; «Sí» vuelve al menú principal sin enemigos y con las oleadas detenidas."""
    montaje.jugar()
    montaje.avanzar(5 * 60)
    assert montaje.juego.enemigos.activos
    flujo = montaje.flujo
    montaje.pulsar("escape", "arrow_down", "arrow_down")
    assert flujo.seleccion_pausa is OpcionPausa.ABANDONAR
    montaje.pulsar("enter")
    assert flujo.pantalla is Pantalla.CONFIRMACION
    assert flujo.confirmacion is Confirmacion.ABANDONAR
    assert flujo.seleccion_confirmacion is OpcionConfirmacion.NO
    montaje.pulsar("enter")
    assert flujo.pantalla is Pantalla.PAUSA
    montaje.pulsar("arrow_down", "arrow_down", "enter")
    assert flujo.pantalla is Pantalla.CONFIRMACION
    montaje.pulsar("escape")
    assert flujo.pantalla is Pantalla.PAUSA
    assert montaje.nucleo.en_pausa
    montaje.pulsar("arrow_down", "arrow_down", "enter", "arrow_right")
    assert flujo.seleccion_confirmacion is OpcionConfirmacion.SI
    assert montaje.de_tipo(PartidaAbandonada) == []
    montaje.pulsar("enter")
    assert flujo.pantalla is Pantalla.MENU_PRINCIPAL
    assert flujo.seleccion_menu is OpcionMenu.JUGAR
    assert montaje.de_tipo(PartidaAbandonada) == [PartidaAbandonada()]
    assert montaje.de_tipo(PausaCambiada)[-1] == PausaCambiada(activa=False)
    assert not montaje.nucleo.en_pausa
    assert not flujo.salir_solicitado
    assert montaje.juego.enemigos.activos == ()
    assert montaje.juego.enemigos.proyectiles == ()
    oleadas = montaje.juego.oleadas
    assert not oleadas.en_curso
    assert oleadas.pendientes == 0
    montaje.avanzar(DIEZ_SEGUNDOS)
    assert montaje.juego.enemigos.activos == ()


def test_abandonar_desde_el_descanso(montaje: Montaje, parametros: Parametros) -> None:
    """Abandonar durante el descanso detiene la cuenta atrás: no empieza otra oleada."""
    _pausar_desde(montaje, Pantalla.DESCANSO)
    montaje.pulsar("arrow_down", "arrow_down", "enter", "arrow_right", "enter")
    assert montaje.flujo.pantalla is Pantalla.MENU_PRINCIPAL
    assert not montaje.juego.oleadas.en_descanso
    montaje.avanzar(round(2 * parametros.duracion_descanso(1) / PASO))
    assert montaje.juego.oleadas.numero == 1
    assert not montaje.juego.oleadas.en_curso
    assert montaje.flujo.pantalla is Pantalla.MENU_PRINCIPAL


def test_s6_t12_cu12_salir_desde_la_pausa(montaje: Montaje) -> None:
    """S6-T12 CU-12 A1: «Salir del juego» en la pausa pide confirmación; «Sí» cierra."""
    montaje.jugar()
    montaje.pulsar("escape", "arrow_down", "arrow_down", "arrow_down", "enter")
    assert montaje.flujo.pantalla is Pantalla.CONFIRMACION
    assert montaje.flujo.confirmacion is Confirmacion.SALIR
    assert not montaje.flujo.salir_solicitado
    # «No» y «Sí» también se recorren con ↑↓.
    montaje.pulsar("arrow_down")
    assert montaje.flujo.seleccion_confirmacion is OpcionConfirmacion.SI
    montaje.pulsar("enter")
    assert montaje.flujo.salir_solicitado


def test_no_confirmar_la_salida(montaje: Montaje) -> None:
    """CU-12 A2: «No» en la confirmación de salida vuelve a la pausa sin cerrar."""
    montaje.jugar()
    montaje.pulsar("escape", "arrow_down", "arrow_down", "arrow_down", "enter")
    montaje.pulsar("arrow_right", "arrow_left", "enter")
    assert montaje.flujo.pantalla is Pantalla.PAUSA
    assert not montaje.flujo.salir_solicitado


# --- manual --------------------------------------------------------------------------


def test_cu10_secciones_del_manual(montaje: Montaje) -> None:
    """CU-10: ←→ cambian de sección sin salir de la lista; ↑↓ no hacen nada."""
    montaje.pulsar("arrow_down", "enter")
    flujo = montaje.flujo
    assert flujo.secciones_manual == tuple(SeccionManual)
    montaje.pulsar("arrow_left")
    assert flujo.seccion_manual is SeccionManual.CONTROLES
    montaje.pulsar("arrow_right")
    assert flujo.seccion_manual is SeccionManual.ENEMIGOS
    montaje.pulsar("arrow_down", "arrow_up")
    assert flujo.seccion_manual is SeccionManual.ENEMIGOS
    montaje.pulsar(*["arrow_right"] * 6)
    assert flujo.seccion_manual is SeccionManual.MEJORAS
    # Al volver a abrirlo, empieza otra vez por la primera sección.
    montaje.pulsar("escape", "arrow_down", "enter")
    assert flujo.pantalla is Pantalla.MANUAL
    assert flujo.seccion_manual is SeccionManual.CONTROLES


def test_cu10_a1_nivel_del_manual(parametros: Parametros) -> None:
    """CU-10 A1: desde la pausa, el manual usa el nivel de la partida; desde el menú, el 1."""
    montaje = Montaje(parametros)
    montaje.flujo.iniciar_partida(nivel=3)
    montaje.pulsar("escape", "arrow_down", "enter")
    assert montaje.flujo.pantalla is Pantalla.MANUAL
    assert montaje.flujo.nivel_manual == 3
    # Abandonar y abrir el manual desde el menú principal.
    montaje.pulsar("escape", "arrow_down", "arrow_down", "enter", "arrow_right", "enter")
    assert montaje.flujo.pantalla is Pantalla.MENU_PRINCIPAL
    montaje.pulsar("arrow_down", "enter")
    assert montaje.flujo.pantalla is Pantalla.MANUAL
    assert montaje.flujo.nivel_manual == 1


# --- resumen de fin de partida -------------------------------------------------------


def _perder(montaje: Montaje, nivel: int) -> None:
    montaje.flujo.iniciar_partida(nivel=nivel)
    montaje.avanzar(30)
    montaje.nucleo.bus.publicar(EstacionDestruida(oleadas_superadas=0))
    montaje.avanzar()
    assert montaje.flujo.pantalla is Pantalla.RESUMEN


def test_s6_t14_rf20_volver_a_jugar(montaje: Montaje) -> None:
    """S6-T14 RF-19, RF-20: tras la derrota, «Volver a jugar» repite el mismo nivel."""
    _perder(montaje, nivel=2)
    assert montaje.flujo.opciones_resumen == tuple(OpcionResumen)
    assert montaje.flujo.seleccion_resumen is OpcionResumen.VOLVER_A_JUGAR
    montaje.pulsar("enter")
    assert montaje.flujo.pantalla is Pantalla.OLEADA_EN_CURSO
    assert montaje.de_tipo(PartidaIniciada) == [PartidaIniciada(nivel=2)] * 2


def test_s6_t15_resumen_al_menu_principal(montaje: Montaje) -> None:
    """S6-T15: tras la derrota, «Menú principal» vuelve al menú principal."""
    _perder(montaje, nivel=1)
    montaje.pulsar("arrow_down")
    assert montaje.flujo.seleccion_resumen is OpcionResumen.MENU_PRINCIPAL
    montaje.pulsar("enter")
    assert montaje.flujo.pantalla is Pantalla.MENU_PRINCIPAL
    assert montaje.flujo.seleccion_menu is OpcionMenu.JUGAR
    assert not montaje.nucleo.en_pausa
    # Desde el menú se puede volver a jugar.
    montaje.jugar()
    assert montaje.flujo.pantalla is Pantalla.OLEADA_EN_CURSO
