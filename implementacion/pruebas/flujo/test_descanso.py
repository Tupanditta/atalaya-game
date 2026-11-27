"""Pruebas del flujo en el descanso: la pantalla de mejoras (Sprint 5)."""

import pytest

from atalaya.logica.armamento import Armamento
from atalaya.logica.estacion import Estacion
from atalaya.logica.flujo import Flujo, OpcionDescanso, Pantalla, SonidoMenu
from atalaya.logica.mejoras import Mejoras
from atalaya.logica.nucleo import PASO, Etapa, Nucleo
from atalaya.logica.nucleo.dominio import Accion, Mejora, TipoEnemigo
from atalaya.logica.nucleo.eventos import (
    DescansoIniciado,
    DescansoTerminado,
    DisparoRealizado,
    DisparoSinEnergia,
    OleadaSuperada,
    ProyectilImpacta,
    TerminarDescansoSolicitado,
)
from atalaya.logica.parametros import Parametros
from atalaya.logica.vista import Vista


class AccionesFalsas:
    """Acciones mantenidas que fija la prueba; cada pulsación dura un solo paso."""

    def __init__(self) -> None:
        self.mantenidas: set[Accion] = set()
        self.pulsadas: set[Accion] = set()

    def mantenida(self, accion: Accion) -> bool:
        return accion in self.mantenidas

    def recien_pulsada(self, accion: Accion) -> bool:
        return accion in self.pulsadas

    def recien_soltada(self, accion: Accion) -> bool:
        return False

    def puntero(self) -> tuple[float, float]:
        return (0.0, 0.0)


class Montaje:
    """Flujo con vista, armamento, estación y mejoras en un núcleo."""

    def __init__(self, parametros: Parametros) -> None:
        self.parametros = parametros
        self.nucleo = Nucleo(semilla=5)
        bus = self.nucleo.bus
        self.acciones = AccionesFalsas()
        self.vista = Vista(bus, parametros)
        self.armamento = Armamento(bus, parametros, self.vista)
        self.estacion = Estacion(bus, parametros)
        self.mejoras = Mejoras(bus, parametros)
        self.flujo = Flujo(
            bus, self.acciones, self.vista, self.armamento, self.mejoras, self.nucleo
        )
        self.nucleo.registrar(Etapa.FLUJO, self.flujo)
        self.nucleo.registrar(Etapa.VISTA, self.vista)
        self.nucleo.registrar(Etapa.ARMAMENTO, self.armamento)
        self.nucleo.registrar(Etapa.ESTACION, self.estacion)
        self.solicitudes: list[TerminarDescansoSolicitado] = []
        bus.suscribir(TerminarDescansoSolicitado, self.solicitudes.append)
        self.flujo.iniciar_partida()
        self.avanzar()

    def avanzar(self, pasos: int = 1) -> None:
        for _ in range(pasos):
            self.nucleo.avanzar(PASO)

    def pulsar(self, *acciones: Accion) -> None:
        """Pulsa las acciones durante un paso y las suelta en el siguiente."""
        for accion in acciones:
            self.acciones.pulsadas = {accion}
            self.avanzar()
            self.acciones.pulsadas = set()
            self.avanzar()

    def abrir_descanso(self, puntos_de_oleadas: int = 0) -> None:
        """Da los puntos de `puntos_de_oleadas` oleadas rápidas y abre el descanso."""
        bus = self.nucleo.bus
        for numero in range(1, puntos_de_oleadas + 1):
            bus.publicar(OleadaSuperada(numero, 1.0, 3))
        bus.publicar(DescansoIniciado(self.parametros.duracion_descanso(1), 2))
        self.avanzar()


@pytest.fixture
def montaje(parametros: Parametros) -> Montaje:
    return Montaje(parametros)


def test_s5_t16_continuar_termina_el_descanso(montaje: Montaje) -> None:
    """S5-T16: DescansoIniciado abre el descanso; Continuar pide terminarlo."""
    assert montaje.flujo.pantalla is Pantalla.OLEADA_EN_CURSO
    montaje.abrir_descanso()
    assert montaje.flujo.pantalla is Pantalla.DESCANSO
    assert montaje.flujo.seleccion_descanso is OpcionDescanso.REPARAR
    montaje.pulsar(*[Accion.ABAJO] * 4)
    assert montaje.flujo.seleccion_descanso is OpcionDescanso.CONTINUAR
    montaje.pulsar(Accion.CONFIRMAR)
    assert montaje.solicitudes == [TerminarDescansoSolicitado()]
    # Pulsar otra vez antes de que se cierre no pide terminarlo dos veces.
    montaje.pulsar(Accion.CONFIRMAR)
    assert len(montaje.solicitudes) == 1
    montaje.nucleo.bus.publicar(DescansoTerminado())
    montaje.avanzar()
    assert montaje.flujo.pantalla is Pantalla.OLEADA_EN_CURSO


def test_s5_t17_flechas_en_la_pantalla_de_mejoras(montaje: Montaje) -> None:
    """S5-T17: las flechas mueven la selección y no giran la vista."""
    montaje.abrir_descanso()
    orientacion = montaje.vista.orientacion
    montaje.pulsar(Accion.ABAJO, Accion.ABAJO)
    assert montaje.flujo.seleccion_descanso is OpcionDescanso.BATERIA
    montaje.pulsar(Accion.ARRIBA)
    assert montaje.flujo.seleccion_descanso is OpcionDescanso.BLINDAJE
    montaje.acciones.mantenidas = {Accion.DERECHA, Accion.ARRIBA}
    montaje.avanzar(60)
    montaje.acciones.mantenidas = set()
    assert montaje.vista.orientacion == orientacion
    assert montaje.flujo.seleccion_descanso is OpcionDescanso.BLINDAJE


def test_la_seleccion_no_sale_de_la_lista(montaje: Montaje) -> None:
    """En los extremos de la lista, la flecha no mueve la selección ni suena."""
    montaje.abrir_descanso()
    montaje.pulsar(Accion.ARRIBA)
    assert montaje.flujo.seleccion_descanso is OpcionDescanso.REPARAR
    assert montaje.flujo.sonidos_menu(SonidoMenu.MOVER) == 0
    montaje.pulsar(*[Accion.ABAJO] * 6)
    assert montaje.flujo.seleccion_descanso is OpcionDescanso.CONTINUAR
    assert montaje.flujo.sonidos_menu(SonidoMenu.MOVER) == 4


def test_cu11_intro_repara(montaje: Montaje, parametros: Parametros) -> None:
    """CU-11: Intro sobre «Reparar» gasta un punto y devuelve integridad."""
    for _ in range(10):
        montaje.nucleo.bus.publicar(ProyectilImpacta(TipoEnemigo.SIN_EFECTO))
    montaje.abrir_descanso(puntos_de_oleadas=1)
    assert montaje.estacion.integridad == 70
    montaje.pulsar(Accion.CONFIRMAR)
    assert montaje.estacion.integridad == 70 + parametros.mejoras.cantidad_reparacion
    assert montaje.mejoras.puntos == 2
    assert montaje.flujo.sonidos_menu(SonidoMenu.CONFIRMAR) == 1
    assert montaje.flujo.sonidos_menu(SonidoMenu.ERROR) == 0


def test_cu11_intro_mejora(montaje: Montaje) -> None:
    """CU-11 A1: Intro sobre «Generador» sube su nivel."""
    montaje.abrir_descanso(puntos_de_oleadas=1)
    montaje.pulsar(Accion.ABAJO, Accion.ABAJO, Accion.ABAJO, Accion.CONFIRMAR)
    assert montaje.mejoras.nivel(Mejora.GENERADOR) == 1
    assert montaje.armamento.recarga_energia == 9
    assert montaje.mejoras.puntos == 1


def test_cu11_a2_opcion_no_disponible_suena_error(montaje: Montaje) -> None:
    """CU-11 A2, A3: una opción que no se puede comprar no aplica nada y suena el error."""
    montaje.abrir_descanso()
    # Integridad al máximo y sin puntos: ni reparar ni mejorar.
    montaje.pulsar(Accion.CONFIRMAR, Accion.ABAJO, Accion.CONFIRMAR)
    assert montaje.flujo.sonidos_menu(SonidoMenu.ERROR) == 2
    assert montaje.flujo.sonidos_menu(SonidoMenu.CONFIRMAR) == 0
    assert montaje.mejoras.nivel(Mejora.BLINDAJE) == 0
    assert montaje.estacion.integridad_maxima == 100


def test_la_barra_pulsada_al_acabar_la_oleada_no_dispara(montaje: Montaje) -> None:
    """Soltar en el descanso la barra que se pulsó en la oleada no dispara ni apunta."""
    disparos: list[object] = []
    montaje.nucleo.bus.suscribir(DisparoRealizado, disparos.append)
    montaje.nucleo.bus.suscribir(DisparoSinEnergia, disparos.append)
    montaje.acciones.mantenidas = {Accion.DISPARO}
    montaje.avanzar(30)
    assert montaje.armamento.progreso_apuntado > 0
    montaje.abrir_descanso()
    montaje.avanzar(30)
    assert montaje.armamento.progreso_apuntado == 0
    montaje.acciones.mantenidas = set()
    montaje.avanzar(5)
    assert disparos == []


def test_el_descanso_vuelve_a_empezar_en_reparar(montaje: Montaje) -> None:
    """Cada descanso abre la pantalla de mejoras con «Reparar» seleccionada."""
    montaje.abrir_descanso()
    montaje.pulsar(Accion.ABAJO, Accion.ABAJO)
    montaje.nucleo.bus.publicar(DescansoTerminado())
    montaje.avanzar()
    montaje.abrir_descanso()
    assert montaje.flujo.seleccion_descanso is OpcionDescanso.REPARAR
    # Continuar se puede volver a pedir en el nuevo descanso.
    montaje.pulsar(*[Accion.ABAJO] * 4, Accion.CONFIRMAR)
    assert len(montaje.solicitudes) == 1


def test_descanso_fuera_de_la_oleada_no_cambia_de_pantalla(montaje: Montaje) -> None:
    """Un DescansoIniciado en el resumen o un DescansoTerminado en la oleada no hacen nada."""
    montaje.nucleo.bus.publicar(DescansoTerminado())
    montaje.avanzar()
    assert montaje.flujo.pantalla is Pantalla.OLEADA_EN_CURSO
    for _ in range(40):
        montaje.nucleo.bus.publicar(ProyectilImpacta(TipoEnemigo.SIN_EFECTO))
    montaje.avanzar()
    assert montaje.flujo.pantalla is Pantalla.RESUMEN
    montaje.abrir_descanso()
    assert montaje.flujo.pantalla is Pantalla.RESUMEN
