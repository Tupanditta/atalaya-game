"""Pruebas de integración del arranque sin ventana (Sprint 1).

Montan los módulos como en el juego real, con un teclado falso en lugar del motor.
"""

import pytest

from atalaya.arranque import montar
from atalaya.logica.flujo import Pantalla
from atalaya.logica.nucleo import PASO
from atalaya.logica.parametros import Parametros


class TecladoFalso:
    def __init__(self) -> None:
        self.teclas: set[str] = set()

    def pulsadas(self, teclas: frozenset[str]) -> frozenset[str]:
        return frozenset(self.teclas) & teclas

    def tiene_foco(self) -> bool:
        return True


def test_flecha_derecha_gira_la_vista(parametros: Parametros) -> None:
    """RF-02: con los módulos montados, mantener la flecha derecha 1 s gira 90°."""
    teclado = TecladoFalso()
    juego = montar(parametros, teclado, semilla=1)
    juego.flujo.iniciar_partida()
    derecha = juego.vista.derecha
    teclado.teclas = {"arrow_right"}
    for _ in range(60):
        juego.nucleo.avanzar(PASO)
    assert juego.flujo.pantalla is Pantalla.OLEADA_EN_CURSO
    assert juego.vista.adelante == pytest.approx(derecha, abs=1e-9)


def test_rnf02_respuesta_en_el_mismo_paso(parametros: Parametros) -> None:
    """RNF-02: la vista empieza a girar en el mismo paso en que se pulsa y para al soltar."""
    teclado = TecladoFalso()
    juego = montar(parametros, teclado, semilla=1)
    juego.flujo.iniciar_partida()
    juego.nucleo.avanzar(PASO)
    inicial = juego.vista.orientacion
    teclado.teclas = {"arrow_up"}
    juego.nucleo.avanzar(PASO)
    girada = juego.vista.orientacion
    assert girada != inicial
    teclado.teclas = set()
    juego.nucleo.avanzar(PASO)
    assert juego.vista.orientacion == girada


def test_esc_cierra_el_juego(parametros: Parametros) -> None:
    """Provisional hasta S6: Esc pide cerrar el juego."""
    teclado = TecladoFalso()
    juego = montar(parametros, teclado, semilla=1)
    juego.flujo.iniciar_partida()
    teclado.teclas = {"escape"}
    juego.nucleo.avanzar(PASO)
    assert juego.flujo.salir_solicitado
