"""Pruebas del flujo mínimo: la oleada en curso entrega el giro a vista y la barra a armamento."""

import pytest

from atalaya.logica.armamento import Armamento
from atalaya.logica.flujo import Flujo, Pantalla
from atalaya.logica.nucleo import PASO, Etapa, Nucleo
from atalaya.logica.nucleo.dominio import Accion, Vector3
from atalaya.logica.nucleo.eventos import PartidaIniciada
from atalaya.logica.parametros import Parametros
from atalaya.logica.vista import ADELANTE, Vista


class AccionesFalsas:
    """Acciones mantenidas que fija la prueba; las pulsaciones se dan en un solo paso."""

    def __init__(self) -> None:
        self.mantenidas: set[Accion] = set()
        self.pulsadas: set[Accion] = set()

    def mantenida(self, accion: Accion) -> bool:
        return accion in self.mantenidas

    def recien_pulsada(self, accion: Accion) -> bool:
        return accion in self.pulsadas

    def recien_soltada(self, accion: Accion) -> bool:
        return False


def _flujo(nucleo: Nucleo, parametros: Parametros, acciones: AccionesFalsas, vista: Vista) -> Flujo:
    armamento = Armamento(nucleo.bus, parametros, vista, nucleo.azar)
    return Flujo(nucleo.bus, acciones, vista, armamento)


def _montar(parametros: Parametros) -> tuple[Nucleo, Flujo, Vista, AccionesFalsas]:
    nucleo = Nucleo(semilla=1)
    acciones = AccionesFalsas()
    vista = Vista(nucleo.bus, parametros)
    flujo = _flujo(nucleo, parametros, acciones, vista)
    nucleo.registrar(Etapa.FLUJO, flujo)
    nucleo.registrar(Etapa.VISTA, vista)
    flujo.iniciar_partida()
    return nucleo, flujo, vista, acciones


def _pasos(nucleo: Nucleo, n: int) -> None:
    for _ in range(n):
        nucleo.avanzar(PASO)


def _cerca(a: Vector3, b: Vector3) -> bool:
    return all(abs(x - y) < 1e-9 for x, y in zip(a, b, strict=True))


def test_iniciar_partida(parametros: Parametros) -> None:
    """Iniciar la partida pasa a la oleada en curso y publica PartidaIniciada con el nivel."""
    nucleo = Nucleo(semilla=1)
    recibidos: list[PartidaIniciada] = []
    nucleo.bus.suscribir(PartidaIniciada, recibidos.append)
    flujo = _flujo(nucleo, parametros, AccionesFalsas(), Vista(nucleo.bus, parametros))
    assert flujo.pantalla is None
    flujo.iniciar_partida(nivel=3)
    nucleo.bus.entregar()
    assert flujo.pantalla is Pantalla.OLEADA_EN_CURSO
    assert flujo.nivel == 3
    assert recibidos == [PartidaIniciada(nivel=3)]


def test_antes_de_la_partida_no_gira(parametros: Parametros) -> None:
    """Sin pantalla de oleada, las flechas no giran la vista."""
    nucleo = Nucleo(semilla=1)
    acciones = AccionesFalsas()
    vista = Vista(nucleo.bus, parametros)
    nucleo.registrar(Etapa.FLUJO, _flujo(nucleo, parametros, acciones, vista))
    nucleo.registrar(Etapa.VISTA, vista)
    acciones.mantenidas = {Accion.DERECHA}
    _pasos(nucleo, 10)
    assert _cerca(vista.adelante, ADELANTE)


def test_flechas_giran_la_vista(parametros: Parametros) -> None:
    """RF-02: durante la oleada, flecha derecha gira la vista a la derecha."""
    nucleo, _, vista, acciones = _montar(parametros)
    derecha = vista.derecha
    acciones.mantenidas = {Accion.DERECHA}
    _pasos(nucleo, 60)
    assert _cerca(vista.adelante, derecha)


@pytest.mark.parametrize(
    ("mantenidas", "gira_arriba"),
    [
        ({Accion.IZQUIERDA, Accion.DERECHA}, False),
        ({Accion.ARRIBA, Accion.IZQUIERDA, Accion.DERECHA}, True),
        ({Accion.ARRIBA, Accion.ABAJO, Accion.IZQUIERDA, Accion.DERECHA}, False),
    ],
    ids=["izquierda-derecha", "arriba-izquierda-derecha", "cuatro-flechas"],
)
def test_s1_t03_rn26_flechas_opuestas(
    parametros: Parametros, mantenidas: set[Accion], gira_arriba: bool
) -> None:
    """S1-T03 RN-26: las flechas opuestas de un eje se anulan; el otro eje no se ve afectado."""
    nucleo, _, vista, acciones = _montar(parametros)
    arriba = vista.arriba
    acciones.mantenidas = mantenidas
    _pasos(nucleo, 60)
    if gira_arriba:
        assert _cerca(vista.adelante, arriba)
    else:
        assert _cerca(vista.adelante, ADELANTE)


def test_esc_pide_salir(parametros: Parametros) -> None:
    """Provisional hasta S6: Esc durante la oleada pide cerrar el juego."""
    nucleo, flujo, _, acciones = _montar(parametros)
    _pasos(nucleo, 1)
    assert not flujo.salir_solicitado
    acciones.pulsadas = {Accion.PAUSA}
    _pasos(nucleo, 1)
    assert flujo.salir_solicitado


def test_barra_espaciadora_llega_a_armamento(parametros: Parametros) -> None:
    """Durante la oleada, mantener la barra espaciadora hace apuntar a armamento (RN-38)."""
    nucleo = Nucleo(semilla=1)
    acciones = AccionesFalsas()
    vista = Vista(nucleo.bus, parametros)
    armamento = Armamento(nucleo.bus, parametros, vista, nucleo.azar)
    flujo = Flujo(nucleo.bus, acciones, vista, armamento)
    nucleo.registrar(Etapa.FLUJO, flujo)
    nucleo.registrar(Etapa.ARMAMENTO, armamento)
    flujo.iniciar_partida()
    acciones.mantenidas = {Accion.DISPARO}
    _pasos(nucleo, 30)
    assert armamento.progreso_apuntado > 0
