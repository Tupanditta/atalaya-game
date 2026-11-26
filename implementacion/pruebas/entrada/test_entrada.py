"""Pruebas del módulo entrada con una fuente de teclado falsa (Sprint 1)."""

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
    assert len(set(TECLAS.values())) == len(TECLAS)


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
    teclado.teclas = {"arrow_up", "arrow_right", "a"}
    entrada.actualizar(PASO)
    mantenidas = {a for a in Accion if entrada.mantenida(a)}
    assert mantenidas == {Accion.ARRIBA, Accion.DERECHA}
    assert teclado.consultas[-1] == frozenset(TECLAS.values())


def test_s1_t13_perdida_de_foco() -> None:
    """S1-T13 entrada, foco: si la ventana pierde el foco, todas las acciones quedan sueltas."""
    teclado = TecladoFalso()
    entrada = Entrada(teclado)
    teclado.teclas = set(TECLAS.values())
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
