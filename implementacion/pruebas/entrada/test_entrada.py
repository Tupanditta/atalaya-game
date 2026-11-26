"""Pruebas del módulo entrada con una fuente de teclado falsa (Sprint 1)."""

import pytest

from atalaya.logica.nucleo import PASO
from atalaya.logica.nucleo.dominio import Accion
from atalaya.presentacion.entrada import TECLAS, Entrada


class TecladoFalso:
    """Teclado que controla la prueba."""

    def __init__(self) -> None:
        self.teclas: set[str] = set()
        self.foco = True
        self.consultas: list[frozenset[str]] = []

    def pulsadas(self, teclas: frozenset[str]) -> frozenset[str]:
        self.consultas.append(teclas)
        return frozenset(self.teclas) & teclas

    def tiene_foco(self) -> bool:
        return self.foco


def _estado(entrada: Entrada, accion: Accion) -> tuple[bool, bool, bool]:
    return (
        entrada.recien_pulsada(accion),
        entrada.mantenida(accion),
        entrada.recien_soltada(accion),
    )


def test_todas_las_acciones_tienen_tecla() -> None:
    """Cada acción tiene una tecla y no hay dos acciones con la misma."""
    assert set(TECLAS) == set(Accion)
    todas = [t for teclas in TECLAS.values() for t in teclas]
    assert all(TECLAS.values())
    assert len(set(todas)) == len(todas)


def test_s1_t12_pulsar_mantener_soltar() -> None:
    """S1-T12 entrada: recién pulsada, mantenida y recién soltada en los pasos correctos."""
    teclado = TecladoFalso()
    entrada = Entrada(teclado)
    entrada.actualizar(PASO)
    assert _estado(entrada, Accion.DISPARO) == (False, False, False)

    teclado.teclas = {"space"}
    entrada.actualizar(PASO)
    assert _estado(entrada, Accion.DISPARO) == (True, True, False)

    entrada.actualizar(PASO)
    assert _estado(entrada, Accion.DISPARO) == (False, True, False)

    teclado.teclas = set()
    entrada.actualizar(PASO)
    assert _estado(entrada, Accion.DISPARO) == (False, False, True)

    entrada.actualizar(PASO)
    assert _estado(entrada, Accion.DISPARO) == (False, False, False)


def test_el_estado_solo_cambia_al_actualizar() -> None:
    """El teclado se lee al principio del paso; los cambios posteriores esperan al siguiente."""
    teclado = TecladoFalso()
    entrada = Entrada(teclado)
    entrada.actualizar(PASO)
    teclado.teclas = {"arrow_left"}
    assert not entrada.mantenida(Accion.IZQUIERDA)
    entrada.actualizar(PASO)
    assert entrada.mantenida(Accion.IZQUIERDA)


def test_varias_teclas_a_la_vez() -> None:
    """Cada acción se informa por separado."""
    teclado = TecladoFalso()
    entrada = Entrada(teclado)
    teclado.teclas = {"arrow_up", "arrow_right", "q"}
    entrada.actualizar(PASO)
    mantenidas = {a for a in Accion if entrada.mantenida(a)}
    assert mantenidas == {Accion.ARRIBA, Accion.DERECHA}
    assert teclado.consultas[-1] == frozenset(t for teclas in TECLAS.values() for t in teclas)


def test_s1_t13_perdida_de_foco() -> None:
    """S1-T13 entrada, foco: si la ventana pierde el foco, todas las acciones quedan sueltas."""
    teclado = TecladoFalso()
    entrada = Entrada(teclado)
    teclado.teclas = {t for teclas in TECLAS.values() for t in teclas}
    entrada.actualizar(PASO)
    assert all(entrada.mantenida(a) for a in Accion)

    teclado.foco = False
    entrada.actualizar(PASO)
    assert not any(entrada.mantenida(a) for a in Accion)
    assert all(entrada.recien_soltada(a) for a in Accion)

    entrada.actualizar(PASO)
    assert not any(entrada.mantenida(a) or entrada.recien_soltada(a) for a in Accion)

    teclado.foco = True
    entrada.actualizar(PASO)
    assert all(entrada.recien_pulsada(a) for a in Accion)


class RatonFalso:
    def __init__(self) -> None:
        self.posicion_actual: tuple[float, float] | None = None

    def posicion(self) -> tuple[float, float] | None:
        return self.posicion_actual


def test_sin_raton_la_mira_queda_en_el_centro() -> None:
    """Sin fuente de ratón, la mira está en el centro de la pantalla."""
    entrada = Entrada(TecladoFalso())
    entrada.actualizar(PASO)
    assert entrada.puntero() == (0.0, 0.0)


def test_raton_mueve_la_mira() -> None:
    """La mira sigue al ratón y se queda donde estaba si el ratón sale de la ventana."""
    raton = RatonFalso()
    entrada = Entrada(TecladoFalso(), raton)
    raton.posicion_actual = (0.8, -0.3)
    entrada.actualizar(PASO)
    assert entrada.puntero() == (0.8, -0.3)
    raton.posicion_actual = None
    entrada.actualizar(PASO)
    assert entrada.puntero() == (0.8, -0.3)


@pytest.mark.parametrize(
    ("tecla", "accion"),
    [
        ("a", Accion.IZQUIERDA),
        ("d", Accion.DERECHA),
        ("w", Accion.ARRIBA),
        ("s", Accion.ABAJO),
        ("mouse1", Accion.DISPARO),
    ],
)
def test_teclas_alternativas(tecla: str, accion: Accion) -> None:
    """W, A, S y D equivalen a las flechas, y el clic izquierdo a la barra espaciadora."""
    teclado = TecladoFalso()
    entrada = Entrada(teclado)
    teclado.teclas = {tecla}
    entrada.actualizar(PASO)
    assert _estado(entrada, accion) == (True, True, False)
    teclado.teclas = set()
    entrada.actualizar(PASO)
    assert _estado(entrada, accion) == (False, False, True)


def test_dos_teclas_de_la_misma_accion() -> None:
    """Con la flecha y su letra a la vez, soltar una de las dos no suelta la acción."""
    teclado = TecladoFalso()
    entrada = Entrada(teclado)
    teclado.teclas = {"arrow_right", "d"}
    entrada.actualizar(PASO)
    teclado.teclas = {"d"}
    entrada.actualizar(PASO)
    assert _estado(entrada, Accion.DERECHA) == (False, True, False)
