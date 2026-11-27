"""Pruebas del módulo estacion: integridad y destrucción (Sprint 3) y efectos (Sprint 4)."""

from typing import TypeVar

import pytest

from atalaya.logica.enemigos import Enemigos
from atalaya.logica.estacion import Estacion
from atalaya.logica.nucleo import PASO, Bus, Etapa, Evento, Nucleo
from atalaya.logica.nucleo.dominio import TipoEnemigo
from atalaya.logica.nucleo.eventos import (
    AturdimientoIniciado,
    AturdimientoTerminado,
    DesestabilizacionIniciada,
    DesestabilizacionTerminada,
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


@pytest.fixture
def parametros(parametros_efectos_fijos: Parametros) -> Parametros:
    """Efectos con su duración de referencia, sin depender del escudo (RN-51)."""
    return parametros_efectos_fijos


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
    oleadas = Oleadas(bus, parametros, nucleo.azar)
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


# --- efectos de los ataques (Sprint 4) -----------------------------------------------


class Efectos:
    """Una estación que avanza paso a paso, con sus eventos anotados junto a su paso."""

    def __init__(self, parametros: Parametros) -> None:
        self.bus = Bus()
        self.estacion = Estacion(self.bus, parametros)
        self.paso = 0
        self.eventos: list[tuple[int, Evento]] = []
        for tipo in (
            DesestabilizacionIniciada,
            DesestabilizacionTerminada,
            AturdimientoIniciado,
            AturdimientoTerminado,
        ):
            self.bus.suscribir(tipo, lambda e: self.eventos.append((self.paso, e)))

    def impacto(self, tipo: TipoEnemigo) -> None:
        self.bus.publicar(ProyectilImpacta(tipo))
        self.bus.entregar()

    def avanzar(self, segundos: float) -> None:
        for _ in range(_pasos(segundos)):
            self.paso += 1
            self.estacion.actualizar(PASO)
            self.bus.entregar()

    def de(self, tipo: type[E]) -> list[tuple[int, E]]:
        return [(p, e) for p, e in self.eventos if isinstance(e, tipo)]


def _pasos(segundos: float) -> int:
    return round(segundos / PASO)


@pytest.mark.parametrize(
    ("tipo", "integridad"),
    [(TipoEnemigo.SIN_EFECTO, 97), (TipoEnemigo.DESESTABILIZADOR, 99), (TipoEnemigo.ATURDIDOR, 98)],
    ids=lambda v: v.value if isinstance(v, TipoEnemigo) else str(v),
)
def test_s4_t04_rn11_dano_por_tipo(
    parametros: Parametros, tipo: TipoEnemigo, integridad: float
) -> None:
    """S4-T04 RN-11: con integridad 100, un impacto deja 97, 99 (desestabilizador) o 98."""
    estacion, bus, _ = _estacion(parametros)
    _impactos(bus, 1, tipo)
    assert estacion.integridad == pytest.approx(integridad)
    assert parametros.tipos.desestabilizador.dano < parametros.tipos.sin_efecto.dano


def test_s4_t05_rn12_desestabilizacion(parametros: Parametros) -> None:
    """S4-T05 RN-12: DesestabilizacionIniciada (3 s) y DesestabilizacionTerminada 3 s después."""
    sim = Efectos(parametros)
    duracion = parametros.tipos.desestabilizador.duracion_efecto
    assert duracion == 3
    sim.impacto(TipoEnemigo.DESESTABILIZADOR)
    assert sim.de(DesestabilizacionIniciada) == [(0, DesestabilizacionIniciada(duracion))]
    assert sim.estacion.desestabilizado
    assert not sim.estacion.aturdido
    assert sim.estacion.tiempo_desestabilizacion == duracion
    sim.avanzar(5)
    ((paso, _),) = sim.de(DesestabilizacionTerminada)
    assert abs(paso - _pasos(duracion)) <= 1
    assert not sim.estacion.desestabilizado
    assert sim.estacion.tiempo_desestabilizacion == 0
    assert sim.de(AturdimientoIniciado) == []


def test_s4_t06_rn12_renovacion(parametros: Parametros) -> None:
    """S4-T06 RN-12: un segundo impacto a los 2 s renueva el efecto; termina a los 5 s."""
    sim = Efectos(parametros)
    sim.impacto(TipoEnemigo.DESESTABILIZADOR)
    sim.avanzar(2)
    sim.impacto(TipoEnemigo.DESESTABILIZADOR)
    assert len(sim.de(DesestabilizacionIniciada)) == 2
    sim.avanzar(6)
    ((paso, _),) = sim.de(DesestabilizacionTerminada)
    assert abs(paso - _pasos(5)) <= 1


def test_rn13_aturdimiento(parametros: Parametros) -> None:
    """RN-13: un impacto aturdidor aturde 1,5 s y publica su inicio y su fin."""
    sim = Efectos(parametros)
    duracion = parametros.tipos.aturdidor.duracion_efecto
    assert duracion == 1.5
    sim.impacto(TipoEnemigo.ATURDIDOR)
    assert sim.de(AturdimientoIniciado) == [(0, AturdimientoIniciado(duracion))]
    assert sim.estacion.aturdido
    assert sim.estacion.tiempo_aturdimiento == duracion
    sim.avanzar(1)
    assert sim.estacion.tiempo_aturdimiento == pytest.approx(duracion - 1)
    sim.avanzar(1)
    ((paso, _),) = sim.de(AturdimientoTerminado)
    assert abs(paso - _pasos(duracion)) <= 1
    assert not sim.estacion.aturdido
    assert sim.de(DesestabilizacionIniciada) == []


def test_s4_t13_rn13_renovacion(parametros: Parametros) -> None:
    """S4-T13 RN-13: un segundo impacto aturdidor a 1 s; un solo fin, a los 2,5 s del primero."""
    sim = Efectos(parametros)
    sim.impacto(TipoEnemigo.ATURDIDOR)
    sim.avanzar(1)
    sim.impacto(TipoEnemigo.ATURDIDOR)
    sim.avanzar(4)
    ((paso, _),) = sim.de(AturdimientoTerminado)
    assert abs(paso - _pasos(2.5)) <= 1


def test_sin_efecto_no_aplica_efectos(parametros: Parametros) -> None:
    """Un impacto sin efecto especial no aturde ni desestabiliza."""
    sim = Efectos(parametros)
    sim.impacto(TipoEnemigo.SIN_EFECTO)
    sim.avanzar(1)
    assert sim.eventos == []
    assert not sim.estacion.aturdido
    assert not sim.estacion.desestabilizado


def test_impacto_que_destruye_no_aplica_efecto(parametros: Parametros) -> None:
    """El impacto que deja la integridad a cero no empieza ningún efecto."""
    sim = Efectos(parametros)
    _impactos(sim.bus, 33)
    assert sim.estacion.integridad == pytest.approx(1)
    sim.impacto(TipoEnemigo.ATURDIDOR)
    assert sim.estacion.destruida
    assert sim.de(AturdimientoIniciado) == []


def test_partida_iniciada_quita_los_efectos(parametros: Parametros) -> None:
    """PartidaIniciada termina los efectos activos sin publicar su fin."""
    sim = Efectos(parametros)
    sim.impacto(TipoEnemigo.ATURDIDOR)
    sim.impacto(TipoEnemigo.DESESTABILIZADOR)
    sim.bus.publicar(PartidaIniciada(nivel=1))
    sim.bus.entregar()
    assert not sim.estacion.aturdido
    assert not sim.estacion.desestabilizado
    sim.avanzar(4)
    assert sim.de(AturdimientoTerminado) == []
    assert sim.de(DesestabilizacionTerminada) == []
