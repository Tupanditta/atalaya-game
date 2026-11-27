"""Pruebas de armamento durante el aturdimiento (Sprint 4)."""

import pytest

from atalaya.logica.armamento import Armamento
from atalaya.logica.estacion import Estacion
from atalaya.logica.nucleo import PASO, Etapa, Evento, Nucleo
from atalaya.logica.nucleo.dominio import TipoEnemigo, Vector3
from atalaya.logica.nucleo.eventos import (
    AturdimientoTerminado,
    DisparoRealizado,
    DisparoSinEnergia,
    PartidaIniciada,
    ProyectilImpacta,
)
from atalaya.logica.parametros import Parametros


@pytest.fixture
def parametros(parametros_efectos_fijos: Parametros) -> Parametros:
    """Efectos con su duración de referencia, sin depender del escudo (RN-51)."""
    return parametros_efectos_fijos


class MiraFija:
    """Mira de `vista` que siempre apunta en la misma dirección."""

    direccion_mira: Vector3 = (0.0, 1.0, 0.0)


class Partida:
    """Armamento y estación conectados en el núcleo, con los disparos anotados."""

    def __init__(self, parametros: Parametros) -> None:
        self.nucleo = Nucleo(semilla=12)
        self.bus = self.nucleo.bus
        self.armamento = Armamento(self.bus, parametros, MiraFija())
        self.estacion = Estacion(self.bus, parametros)
        self.nucleo.registrar(Etapa.ARMAMENTO, self.armamento)
        self.nucleo.registrar(Etapa.ESTACION, self.estacion)
        self.disparos: list[Evento] = []
        self.terminados: list[AturdimientoTerminado] = []
        self.bus.suscribir(DisparoRealizado, self.disparos.append)
        self.bus.suscribir(DisparoSinEnergia, self.disparos.append)
        self.bus.suscribir(AturdimientoTerminado, self.terminados.append)
        self.bus.publicar(PartidaIniciada(nivel=1))
        self.bus.entregar()

    def aturdir(self) -> None:
        self.bus.publicar(ProyectilImpacta(TipoEnemigo.ATURDIDOR))
        self.bus.entregar()

    def mantener(self, pulsada: bool, segundos: float = PASO) -> None:
        for _ in range(round(segundos / PASO)):
            self.armamento.recibir_disparo(pulsada)
            self.nucleo.avanzar(PASO)

    def hasta_fin_del_aturdimiento(self, pulsada: bool) -> None:
        while not self.terminados:
            self.mantener(pulsada)


def test_s4_t10_rn13_soltar_aturdido_no_dispara(parametros: Parametros) -> None:
    """S4-T10 RN-13: soltar la barra durante el aturdimiento no dispara."""
    partida = Partida(parametros)
    partida.mantener(True, 0.5)
    partida.aturdir()
    partida.mantener(True, 0.2)
    partida.mantener(False, 0.2)
    assert partida.disparos == []


def test_rn13_pulsar_y_soltar_aturdido_no_dispara(parametros: Parametros) -> None:
    """RN-13: pulsar y soltar la barra durante el aturdimiento tampoco dispara."""
    partida = Partida(parametros)
    partida.aturdir()
    partida.mantener(True, 0.3)
    partida.mantener(False, 0.2)
    partida.mantener(True, 0.3)
    partida.mantener(False, 0.2)
    assert partida.disparos == []
    assert partida.armamento.aturdido


def test_s4_t11_rn38_aturdimiento_cancela_el_apuntado(parametros: Parametros) -> None:
    """S4-T11 RN-38: el aturdimiento devuelve la mira a su tamaño normal.

    Tras el aturdimiento, con la barra aún pulsada, no se apunta ni se dispara hasta
    soltarla y pulsarla otra vez.
    """
    partida = Partida(parametros)
    armamento = partida.armamento
    partida.mantener(True, 1.0)
    assert armamento.progreso_apuntado > 0.5
    partida.aturdir()
    partida.mantener(True, parametros.jugador.tiempo_vuelta_mira + PASO)
    assert armamento.progreso_apuntado == 0
    partida.hasta_fin_del_aturdimiento(pulsada=True)
    assert not armamento.aturdido
    partida.mantener(True, 1.0)
    assert armamento.progreso_apuntado == 0
    partida.mantener(False)
    assert partida.disparos == []
    partida.mantener(True, 0.5)
    assert armamento.progreso_apuntado > 0
    partida.mantener(False)
    assert len(partida.disparos) == 1
    assert isinstance(partida.disparos[0], DisparoRealizado)


def test_s4_t12_rn04_recarga_durante_el_aturdimiento(parametros: Parametros) -> None:
    """S4-T12 RN-04: aturdido 1,5 s con energía 50, la energía sube a 62."""
    partida = Partida(parametros)
    partida.armamento._energia = 50.0
    partida.aturdir()
    partida.hasta_fin_del_aturdimiento(pulsada=False)
    esperada = 50 + parametros.jugador.recarga_energia * parametros.tipos.aturdidor.duracion_efecto
    assert esperada == 62
    assert partida.armamento.energia == pytest.approx(
        esperada, abs=parametros.jugador.recarga_energia * PASO + 1e-9
    )


def test_partida_iniciada_quita_el_aturdimiento(parametros: Parametros) -> None:
    """PartidaIniciada deja de bloquear el disparo."""
    partida = Partida(parametros)
    partida.aturdir()
    partida.bus.publicar(PartidaIniciada(nivel=1))
    partida.bus.entregar()
    assert not partida.armamento.aturdido
    partida.mantener(True)
    partida.mantener(False)
    assert len(partida.disparos) == 1
