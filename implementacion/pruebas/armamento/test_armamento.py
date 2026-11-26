"""Pruebas del módulo armamento (Sprint 2)."""

import math
from typing import TypeVar

import pytest

from atalaya.logica.armamento import Armamento, direccion_disparo
from atalaya.logica.nucleo import PASO, Azar, Bus, Etapa, Evento, Nucleo
from atalaya.logica.nucleo.dominio import Vector3
from atalaya.logica.nucleo.eventos import (
    ApuntadoCambiado,
    DisparoRealizado,
    DisparoSinEnergia,
    EnergiaCambiada,
    PartidaIniciada,
)
from atalaya.logica.nucleo.vectores import angulo_entre
from atalaya.logica.parametros import Parametros
from atalaya.logica.vista import Vista

E = TypeVar("E", bound=Evento)


class MiraFija:
    """Mira de `vista` que siempre apunta en la misma dirección."""

    def __init__(self, direccion: Vector3 = (0.0, 1.0, 0.0)) -> None:
        self.direccion_mira = direccion


class Registro:
    """Anota los eventos que se publican en el bus, en orden."""

    def __init__(self, bus: Bus, *tipos: type[Evento]) -> None:
        self.eventos: list[Evento] = []
        for tipo in tipos:
            bus.suscribir(tipo, self.eventos.append)

    def de(self, tipo: type[E]) -> list[E]:
        return [e for e in self.eventos if isinstance(e, tipo)]

    def limpiar(self) -> None:
        self.eventos.clear()


def _armamento(parametros: Parametros, semilla: int = 1) -> tuple[Armamento, Bus, Registro]:
    bus = Bus()
    registro = Registro(bus, ApuntadoCambiado, DisparoRealizado, DisparoSinEnergia, EnergiaCambiada)
    armamento = Armamento(bus, parametros, MiraFija(), Azar(semilla))
    bus.publicar(PartidaIniciada(nivel=1))
    bus.entregar()
    registro.limpiar()
    return armamento, bus, registro


def _paso(armamento: Armamento, bus: Bus, pulsada: bool) -> None:
    armamento.recibir_disparo(pulsada)
    armamento.actualizar(PASO)
    bus.entregar()


def _mantener(armamento: Armamento, bus: Bus, pulsada: bool, pasos: int) -> None:
    for _ in range(pasos):
        _paso(armamento, bus, pulsada)


def _pasos(segundos: float) -> int:
    pasos = segundos / PASO
    assert pasos == pytest.approx(round(pasos))
    return round(pasos)


def _disparar(armamento: Armamento, bus: Bus) -> None:
    _paso(armamento, bus, True)
    _paso(armamento, bus, False)


def test_s2_t01_rn02_energia_al_maximo(parametros: Parametros) -> None:
    """S2-T01 RN-02: al iniciar la partida, la energía está al máximo."""
    bus = Bus()
    registro = Registro(bus, EnergiaCambiada)
    armamento = Armamento(bus, parametros, MiraFija(), Azar(1))
    _disparar(armamento, bus)
    bus.publicar(PartidaIniciada(nivel=1))
    bus.entregar()
    maxima = parametros.jugador.energia_maxima
    assert armamento.energia == maxima == 100
    assert armamento.energia_maxima == maxima
    assert registro.de(EnergiaCambiada)[-1] == EnergiaCambiada(maxima, maxima)


def test_s2_t02_rn03_rf05_disparo(parametros: Parametros) -> None:
    """S2-T02 RN-03 RF-05: pulsar y soltar la barra dispara y descuenta el coste."""
    armamento, bus, registro = _armamento(parametros)
    _disparar(armamento, bus)
    j = parametros.jugador
    assert len(registro.de(DisparoRealizado)) == 1
    assert registro.de(EnergiaCambiada) == [
        EnergiaCambiada(j.energia_maxima - j.coste_disparo, j.energia_maxima)
    ]
    assert armamento.energia == pytest.approx(90)


def test_s2_t03_rn05_rf11_sin_energia(parametros: Parametros) -> None:
    """S2-T03 RN-05 RF-11: sin energía suficiente, el disparo se bloquea y se avisa."""
    armamento, bus, registro = _armamento(parametros)
    j = parametros.jugador
    disparos = round(j.energia_maxima / j.coste_disparo)
    assert disparos == 10
    for _ in range(disparos):
        _disparar(armamento, bus)
    assert len(registro.de(DisparoRealizado)) == disparos
    assert armamento.energia < j.coste_disparo
    registro.limpiar()
    _paso(armamento, bus, True)
    energia = armamento.energia
    armamento.recibir_disparo(False)
    # Solo se comprueba el paso del suelte: la recarga de ese paso ocurre antes del disparo.
    armamento.actualizar(PASO)
    bus.entregar()
    assert registro.de(DisparoSinEnergia) == [DisparoSinEnergia()]
    assert registro.de(DisparoRealizado) == []
    assert armamento.energia == pytest.approx(energia + j.recarga_energia * PASO)


def test_s2_t04_rn04_recarga(parametros: Parametros) -> None:
    """S2-T04 RN-04: la energía se recarga con el tiempo hasta la máxima, sin superarla."""
    armamento, bus, _ = _armamento(parametros)
    _disparar(armamento, bus)
    j = parametros.jugador
    assert armamento.energia == pytest.approx(90)
    _mantener(armamento, bus, False, _pasos(1))
    assert armamento.energia == pytest.approx(90 + j.recarga_energia)
    assert armamento.energia == pytest.approx(98)
    _mantener(armamento, bus, False, _pasos(1))
    assert armamento.energia == j.energia_maxima == 100


def test_s2_t05_rn04_recarga_apuntando(parametros: Parametros) -> None:
    """S2-T05 RN-04: con la barra pulsada, la energía sube igual que sin apuntar."""
    apuntando, bus_a, _ = _armamento(parametros)
    sin_apuntar, bus_s, _ = _armamento(parametros)
    _disparar(apuntando, bus_a)
    _disparar(sin_apuntar, bus_s)
    _mantener(apuntando, bus_a, True, 30)
    _mantener(sin_apuntar, bus_s, False, 30)
    assert apuntando.progreso_apuntado > 0
    assert apuntando.energia == pytest.approx(sin_apuntar.energia)
    assert apuntando.energia > 90


@pytest.mark.parametrize(
    ("segundos", "progreso"), [(0.75, 0.5), (1.5, 1.0), (3.0, 1.0)], ids=["0,75s", "1,5s", "3s"]
)
def test_s2_t06_rn38_rf32_reduccion_de_la_mira(
    parametros: Parametros, segundos: float, progreso: float
) -> None:
    """S2-T06 RN-38 RF-32: la mira se reduce de forma continua hasta su tamaño mínimo."""
    armamento, bus, registro = _armamento(parametros)
    j = parametros.jugador
    assert armamento.radio_mira == j.mira_normal == 3
    radios = []
    for _ in range(_pasos(segundos)):
        _paso(armamento, bus, True)
        radios.append(armamento.radio_mira)
    assert armamento.progreso_apuntado == pytest.approx(progreso)
    assert registro.de(ApuntadoCambiado)[-1].progreso == pytest.approx(progreso)
    assert all(r >= j.mira_minima for r in radios)
    assert radios == sorted(radios, reverse=True)
    if progreso == 1:
        assert armamento.radio_mira == j.mira_minima == 0.5


def test_s2_t07_rn38_vuelta_de_la_mira(parametros: Parametros) -> None:
    """S2-T07 RN-38: al soltar la barra, la mira vuelve a su tamaño normal en 0,2 s."""
    armamento, bus, _ = _armamento(parametros)
    _mantener(armamento, bus, True, _pasos(parametros.jugador.tiempo_apuntado))
    assert armamento.progreso_apuntado == 1
    _mantener(armamento, bus, False, _pasos(0.1))
    assert 0 < armamento.progreso_apuntado < 1
    _mantener(armamento, bus, False, _pasos(0.1))
    assert armamento.progreso_apuntado == 0
    assert armamento.radio_mira == parametros.jugador.mira_normal


def test_s2_t08_rn39_zoom_con_vista(parametros: Parametros) -> None:
    """S2-T08 RN-39: con vista conectada, apuntar 1,5 s lleva el campo de visión a 25°."""
    nucleo = Nucleo(semilla=1)
    registro = Registro(nucleo.bus, ApuntadoCambiado)
    vista = Vista(nucleo.bus, parametros)
    armamento = Armamento(nucleo.bus, parametros, vista, nucleo.azar)
    nucleo.registrar(Etapa.VISTA, vista)
    nucleo.registrar(Etapa.ARMAMENTO, armamento)
    # `vista` se actualiza antes que `armamento`: aplica el apuntado en el paso siguiente.
    for _ in range(_pasos(parametros.jugador.tiempo_apuntado) + 1):
        armamento.recibir_disparo(True)
        nucleo.avanzar(PASO)
    assert registro.de(ApuntadoCambiado)[-1].progreso == 1
    assert vista.campo_vision == parametros.jugador.campo_vision_zoom == 25


def _angulos(parametros: Parametros, radio: float, n: int) -> list[float]:
    azar = Azar(2024)
    centro: Vector3 = (0.0, 1.0, 0.0)
    return [angulo_entre(centro, direccion_disparo(centro, radio, azar)) for _ in range(n)]


def test_s2_t09_rn37_dispersion_mira_normal(parametros: Parametros) -> None:
    """S2-T09 RN-37: el impacto es uniforme dentro del círculo de la mira normal."""
    radio = parametros.jugador.mira_normal
    angulos = _angulos(parametros, radio, 10_000)
    assert max(angulos) <= radio + 1e-9
    # En un círculo uniforme, el radio medio es 2/3 del radio y la mitad del radio
    # encierra un cuarto de los puntos.
    assert sum(angulos) / len(angulos) == pytest.approx(2 * radio / 3, abs=0.05)
    dentro = sum(1 for a in angulos if a <= radio / 2) / len(angulos)
    assert dentro == pytest.approx(0.25, abs=0.015)


def test_s2_t10_rn37_dispersion_mira_minima(parametros: Parametros) -> None:
    """S2-T10 RN-37: con la mira mínima, todos los disparos caen dentro de 0,5°."""
    radio = parametros.jugador.mira_minima
    assert max(_angulos(parametros, radio, 10_000)) <= radio + 1e-9


def test_rn37_disparo_usa_la_mira_al_soltar(parametros: Parametros) -> None:
    """RN-37: el disparo usa el tamaño de mira del momento de soltar, alrededor de la mira."""
    bus = Bus()
    registro = Registro(bus, DisparoRealizado)
    direccion: Vector3 = (1.0, 0.0, 0.0)
    armamento = Armamento(bus, parametros, MiraFija(direccion), Azar(7))
    for _ in range(200):
        _mantener(armamento, bus, True, _pasos(parametros.jugador.tiempo_apuntado))
        _paso(armamento, bus, False)
        _mantener(armamento, bus, False, _pasos(parametros.jugador.tiempo_apuntado))
    disparos = registro.de(DisparoRealizado)
    assert len(disparos) == 200
    assert all(d.origen == (0.0, 0.0, 0.0) for d in disparos)
    assert all(
        angulo_entre(direccion, d.direccion) <= parametros.jugador.mira_minima + 1e-9
        for d in disparos
    )
    assert all(math.isclose(sum(c * c for c in d.direccion), 1.0) for d in disparos)


def test_s2_t11_rn23_rnf05_disparo_en_el_paso_del_suelte(parametros: Parametros) -> None:
    """S2-T11 RN-23 RNF-05: DisparoRealizado se publica en el mismo paso en que se suelta."""
    nucleo = Nucleo(semilla=1)
    pasos_disparo: list[int] = []
    paso_actual = [0]
    nucleo.bus.suscribir(DisparoRealizado, lambda _: pasos_disparo.append(paso_actual[0]))
    armamento = Armamento(nucleo.bus, parametros, MiraFija(), nucleo.azar)
    nucleo.registrar(Etapa.ARMAMENTO, armamento)
    for paso in range(1, 21):
        paso_actual[0] = paso
        armamento.recibir_disparo(paso < 10)
        nucleo.avanzar(PASO)
    assert pasos_disparo == [10]


def test_s2_t12_cancelar_apuntado(parametros: Parametros) -> None:
    """S2-T12: tras cancelar, el primer suelte no dispara; el siguiente sí."""
    armamento, bus, registro = _armamento(parametros)
    _mantener(armamento, bus, True, 30)
    armamento.cancelar_apuntado()
    _mantener(armamento, bus, True, 30)
    _paso(armamento, bus, False)
    assert registro.de(DisparoRealizado) == []
    _mantener(armamento, bus, False, _pasos(parametros.jugador.tiempo_vuelta_mira))
    assert armamento.progreso_apuntado == 0
    _disparar(armamento, bus)
    assert len(registro.de(DisparoRealizado)) == 1


def test_cancelar_sin_barra_pulsada_no_bloquea(parametros: Parametros) -> None:
    """Cancelar sin la barra pulsada no impide el siguiente disparo."""
    armamento, bus, registro = _armamento(parametros)
    armamento.cancelar_apuntado()
    _disparar(armamento, bus)
    assert len(registro.de(DisparoRealizado)) == 1


def test_mira_sin_cambios_no_publica(parametros: Parametros) -> None:
    """Sin apuntar y con la energía llena, no se publican eventos."""
    armamento, bus, registro = _armamento(parametros)
    _mantener(armamento, bus, False, 10)
    assert registro.eventos == []
