"""Pruebas del bucle a paso fijo y del reloj pausable (Sprint 0)."""

import pytest

from atalaya.logica.nucleo import MAX_PASOS, PASO, Etapa, Nucleo


class ModuloFalso:
    """Módulo que anota cada llamada en un registro compartido."""

    def __init__(self, nombre: str, registro: list[str]) -> None:
        self.nombre = nombre
        self.registro = registro

    def actualizar(self, dt: float) -> None:
        assert dt == PASO
        self.registro.append(self.nombre)


def test_s0_t01_un_paso_por_sesenta_avo_de_segundo() -> None:
    """S0-T01 nucleo, paso fijo: avanzar 1/60 s ejecuta 1 paso."""
    nucleo = Nucleo(semilla=1)
    assert nucleo.avanzar(1 / 60) == 1


def test_s0_t02_acumulador() -> None:
    """S0-T02 nucleo, acumulador: 0,05 s da 3 pasos; después 0,01 s dos veces da 0 y 1."""
    nucleo = Nucleo(semilla=1)
    assert nucleo.avanzar(0.05) == 3
    assert nucleo.avanzar(0.01) == 0
    assert nucleo.avanzar(0.01) == 1


def test_s0_t03_limite_de_pasos() -> None:
    """S0-T03 nucleo, límite de pasos: 1 s da 5 pasos y el resto se descarta."""
    nucleo = Nucleo(semilla=1)
    assert nucleo.avanzar(1.0) == MAX_PASOS == 5
    assert nucleo.avanzar(0.0) == 0


def test_s0_t04_rn50_reloj_en_pausa() -> None:
    """S0-T04 RN-50: con el reloj en pausa no hay pasos de partida ni avanza el tiempo."""
    nucleo = Nucleo(semilla=1)
    nucleo.avanzar(0.1)
    tiempo = nucleo.tiempo_partida
    nucleo.pausar()
    assert nucleo.en_pausa
    assert nucleo.avanzar(1.0) == 0
    assert nucleo.tiempo_partida == tiempo
    nucleo.reanudar()
    assert not nucleo.en_pausa
    assert nucleo.avanzar(1 / 60) == 1
    assert nucleo.tiempo_partida == pytest.approx(tiempo + PASO)


def test_s0_t05_orden_de_actualizacion() -> None:
    """S0-T05 orden de actualización: los módulos se llaman en el orden de modulos/README.md."""
    registro: list[str] = []
    nucleo = Nucleo(semilla=1)
    for etapa in reversed(Etapa):
        nucleo.registrar(etapa, ModuloFalso(etapa.name, registro))
    nucleo.avanzar(PASO)
    assert registro == [
        "ENTRADA",
        "FLUJO",
        "VISTA",
        "ARMAMENTO",
        "ENEMIGOS",
        "OLEADAS",
        "ESTACION",
        "ENTORNO",
    ]


def test_s0_t05_pausa_solo_actualiza_entrada_y_flujo() -> None:
    """S0-T05, RN-50: con la partida en pausa no se ejecutan las etapas 3 a 8."""
    registro: list[str] = []
    nucleo = Nucleo(semilla=1)
    for etapa in Etapa:
        nucleo.registrar(etapa, ModuloFalso(etapa.name, registro))
    nucleo.pausar()
    nucleo.avanzar(PASO)
    assert registro == ["ENTRADA", "FLUJO"]


def test_pausa_desde_flujo_detiene_el_mismo_paso() -> None:
    """RN-50: si flujo pausa durante un paso, las etapas de partida de ese paso no se ejecutan."""
    registro: list[str] = []
    nucleo = Nucleo(semilla=1)

    class FlujoQuePausa:
        def actualizar(self, dt: float) -> None:
            registro.append("FLUJO")
            nucleo.pausar()

    nucleo.registrar(Etapa.FLUJO, FlujoQuePausa())
    nucleo.registrar(Etapa.VISTA, ModuloFalso("VISTA", registro))
    assert nucleo.avanzar(PASO) == 0
    assert registro == ["FLUJO"]


def test_etapa_registrada_dos_veces() -> None:
    """Cada etapa admite un solo módulo."""
    nucleo = Nucleo(semilla=1)
    nucleo.registrar(Etapa.VISTA, ModuloFalso("a", []))
    with pytest.raises(ValueError, match="VISTA"):
        nucleo.registrar(Etapa.VISTA, ModuloFalso("b", []))


def test_tiempo_negativo() -> None:
    """El tiempo transcurrido no puede ser negativo."""
    with pytest.raises(ValueError, match="negativo"):
        Nucleo(semilla=1).avanzar(-0.1)


def test_eventos_se_entregan_tras_cada_modulo() -> None:
    """Un evento publicado por un módulo llega antes de que se actualice el siguiente."""
    from atalaya.logica.nucleo.eventos import PartidaIniciada

    registro: list[str] = []
    nucleo = Nucleo(semilla=1)

    class Publicador:
        def actualizar(self, dt: float) -> None:
            nucleo.bus.publicar(PartidaIniciada(nivel=1))

    nucleo.bus.suscribir(PartidaIniciada, lambda e: registro.append("evento"))
    nucleo.registrar(Etapa.FLUJO, Publicador())
    nucleo.registrar(Etapa.VISTA, ModuloFalso("VISTA", registro))
    nucleo.avanzar(PASO)
    assert registro == ["evento", "VISTA"]


def test_fraccion_paso() -> None:
    """La fracción del paso siguiente sirve para interpolar al dibujar."""
    nucleo = Nucleo(semilla=1)
    assert nucleo.fraccion_paso == 0.0
    nucleo.avanzar(PASO * 1.25)
    assert nucleo.fraccion_paso == pytest.approx(0.25)
    nucleo.avanzar(PASO * 0.5)
    assert nucleo.fraccion_paso == pytest.approx(0.75)
    nucleo.avanzar(1.0)
    assert nucleo.fraccion_paso == 0.0
