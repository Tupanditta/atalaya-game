"""Pruebas del módulo estacion: integridad y destrucción (Sprint 3)."""

from typing import TypeVar

import pytest

from atalaya.logica.enemigos import Enemigos
from atalaya.logica.estacion import Estacion
from atalaya.logica.nucleo import PASO, Bus, Etapa, Evento, Nucleo
from atalaya.logica.nucleo.dominio import TipoEnemigo
from atalaya.logica.nucleo.eventos import (
    EstacionDanada,
    EstacionDestruida,
    IntegridadCambiada,
    OleadaSuperada,
    PartidaIniciada,
    ProyectilImpacta,
    ProyectilLanzado,
    SolicitudAparicion,
)
from atalaya.logica.oleadas import Oleadas
from atalaya.logica.parametros import Parametros

E = TypeVar("E", bound=Evento)


class Registro:
    def __init__(self, bus: Bus, *tipos: type[Evento]) -> None:
        self.eventos: list[Evento] = []
        for tipo in tipos:
            bus.suscribir(tipo, self.eventos.append)

    def de(self, tipo: type[E]) -> list[E]:
        return [e for e in self.eventos if isinstance(e, tipo)]


def _estacion(parametros: Parametros) -> tuple[Estacion, Bus, Registro]:
    bus = Bus()
    registro = Registro(bus, EstacionDanada, IntegridadCambiada, EstacionDestruida)
    return Estacion(bus, parametros), bus, registro


def _impactos(bus: Bus, n: int, tipo: TipoEnemigo = TipoEnemigo.SIN_EFECTO) -> None:
    for _ in range(n):
        bus.publicar(ProyectilImpacta(tipo))
        bus.entregar()


def test_integridad_inicial(parametros: Parametros) -> None:
    """RN-02: la estación empieza con la integridad máxima."""
    estacion, _, _ = _estacion(parametros)
    assert estacion.integridad == estacion.integridad_maxima == 100
    assert not estacion.destruida


def test_s3_t07_rn10_impacto_sin_efecto(parametros: Parametros) -> None:
    """S3-T07 RN-10: un impacto sin efecto deja 97 y publica EstacionDanada e IntegridadCambiada."""
    estacion, bus, registro = _estacion(parametros)
    _impactos(bus, 1)
    dano = parametros.tipos.sin_efecto.dano
    assert dano == 3
    assert estacion.integridad == pytest.approx(97)
    assert registro.eventos == [EstacionDanada(3, 97, 100), IntegridadCambiada(97, 100)]


@pytest.mark.parametrize("tipo", list(TipoEnemigo), ids=lambda t: t.value)
def test_rn10_dano_segun_el_tipo(parametros: Parametros, tipo: TipoEnemigo) -> None:
    """RN-10: cada tipo resta su propio daño."""
    estacion, bus, _ = _estacion(parametros)
    _impactos(bus, 1, tipo)
    assert estacion.integridad == pytest.approx(100 - parametros.tipos.de(tipo).dano)


def test_s3_t08_rn17_destruccion_una_sola_vez(parametros: Parametros) -> None:
    """S3-T08 RN-17: el impacto 34 deja 0 sin negativos; EstacionDestruida una sola vez."""
    estacion, bus, registro = _estacion(parametros)
    _impactos(bus, 33)
    assert estacion.integridad == pytest.approx(1)
    assert registro.de(EstacionDestruida) == []
    _impactos(bus, 1)
    assert estacion.integridad == 0
    assert estacion.destruida
    assert registro.de(EstacionDanada)[-1] == EstacionDanada(pytest.approx(1), 0, 100)
    assert registro.de(IntegridadCambiada)[-1] == IntegridadCambiada(0, 100)
    assert registro.de(EstacionDestruida) == [EstacionDestruida(0)]
    antes = len(registro.eventos)
    _impactos(bus, 1)
    assert estacion.integridad == 0
    assert len(registro.eventos) == antes


def test_estacion_destruida_cuenta_las_oleadas_superadas(parametros: Parametros) -> None:
    """EstacionDestruida lleva el número de oleadas superadas en la partida."""
    _, bus, registro = _estacion(parametros)
    for numero in (1, 2, 3):
        bus.publicar(OleadaSuperada(numero, 30.0, 3))
    bus.entregar()
    _impactos(bus, 34)
    assert registro.de(EstacionDestruida) == [EstacionDestruida(3)]


def test_partida_iniciada_restablece_la_estacion(parametros: Parametros) -> None:
    """PartidaIniciada devuelve la integridad a la máxima y la estación vuelve a recibir daño."""
    estacion, bus, registro = _estacion(parametros)
    bus.publicar(OleadaSuperada(1, 30.0, 3))
    _impactos(bus, 34)
    bus.publicar(PartidaIniciada(nivel=1))
    bus.entregar()
    assert estacion.integridad == 100
    assert not estacion.destruida
    assert registro.de(IntegridadCambiada)[-1] == IntegridadCambiada(100, 100)
    _impactos(bus, 34)
    assert registro.de(EstacionDestruida) == [EstacionDestruida(1), EstacionDestruida(0)]


def test_s3_t09_estacion_destruida_detiene_la_partida(parametros: Parametros) -> None:
    """S3-T09: con la estación destruida no quedan enemigos y no hay más apariciones."""
    nucleo = Nucleo(semilla=9)
    bus = nucleo.bus
    enemigos = Enemigos(bus, parametros, nucleo.azar)
    oleadas = Oleadas(bus, parametros)
    Estacion(bus, parametros)
    nucleo.registrar(Etapa.ENEMIGOS, enemigos)
    nucleo.registrar(Etapa.OLEADAS, oleadas)
    solicitudes: list[SolicitudAparicion] = []
    lanzados: list[ProyectilLanzado] = []
    bus.suscribir(SolicitudAparicion, solicitudes.append)
    bus.suscribir(ProyectilLanzado, lanzados.append)
    oleadas.iniciar_oleada(10)
    for _ in range(round(60 / PASO)):
        nucleo.avanzar(PASO)
        if enemigos.proyectiles and len(enemigos.activos) >= 2:
            break
    assert enemigos.proyectiles
    assert oleadas.pendientes > 0
    _impactos(bus, 34)
    assert enemigos.activos == ()
    assert enemigos.proyectiles == ()
    antes = len(solicitudes), len(lanzados)
    for _ in range(round(10 / PASO)):
        nucleo.avanzar(PASO)
    assert (len(solicitudes), len(lanzados)) == antes
    assert not oleadas.en_curso
