"""Pruebas del bus de eventos y de los eventos inmutables (Sprint 0)."""

import dataclasses
from dataclasses import dataclass

import pytest

from atalaya.logica.nucleo import Bus, Evento
from atalaya.logica.nucleo.eventos import EnergiaCambiada


@dataclass(frozen=True, slots=True)
class EventoA(Evento):
    valor: int


@dataclass(frozen=True, slots=True)
class EventoB(Evento):
    valor: int


@dataclass(frozen=True, slots=True)
class EventoC(Evento):
    valor: int


def test_s0_t06_entrega_en_orden_de_publicacion() -> None:
    """S0-T06 bus de eventos: A, B y C llegan en el mismo paso y en orden de publicación."""
    bus = Bus()
    recibidos: list[Evento] = []

    def al_recibir_a(evento: EventoA) -> None:
        recibidos.append(evento)
        bus.publicar(EventoC(3))

    bus.suscribir(EventoA, al_recibir_a)
    bus.suscribir(EventoB, recibidos.append)
    bus.suscribir(EventoC, recibidos.append)
    bus.publicar(EventoA(1))
    bus.publicar(EventoB(2))
    bus.entregar()
    assert recibidos == [EventoA(1), EventoB(2), EventoC(3)]
    assert not bus.pendientes


def test_varios_suscriptores_en_orden_de_suscripcion() -> None:
    """Los suscriptores de un mismo evento lo reciben en el orden en que se suscribieron."""
    bus = Bus()
    orden: list[str] = []
    bus.suscribir(EventoA, lambda e: orden.append("primero"))
    bus.suscribir(EventoA, lambda e: orden.append("segundo"))
    bus.publicar(EventoA(1))
    bus.entregar()
    assert orden == ["primero", "segundo"]


def test_evento_sin_suscriptores() -> None:
    """Un evento sin suscriptores se descarta sin error."""
    bus = Bus()
    bus.publicar(EventoA(1))
    bus.entregar()
    assert not bus.pendientes


def test_ciclo_de_eventos_infinito() -> None:
    """Un ciclo de eventos sin fin se detiene con un error en lugar de bloquear el juego."""
    bus = Bus()
    bus.suscribir(EventoA, lambda e: bus.publicar(EventoA(e.valor + 1)))
    bus.publicar(EventoA(0))
    with pytest.raises(RuntimeError, match="ciclo"):
        bus.entregar()


def test_s0_t07_eventos_inmutables() -> None:
    """S0-T07 eventos inmutables: cambiar un campo de un evento publicado lanza un error."""
    bus = Bus()
    recibidos: list[EnergiaCambiada] = []
    bus.suscribir(EnergiaCambiada, recibidos.append)
    bus.publicar(EnergiaCambiada(actual=50.0, maxima=100.0))
    bus.entregar()
    with pytest.raises(dataclasses.FrozenInstanceError):
        recibidos[0].actual = 0.0  # type: ignore[misc]
