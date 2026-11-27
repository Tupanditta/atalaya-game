"""Pruebas de vista con los efectos de los ataques: desvío y aturdimiento (Sprint 4)."""

import dataclasses
import math

import pytest

from atalaya.logica.armamento import Armamento
from atalaya.logica.estacion import Estacion
from atalaya.logica.nucleo import PASO, Etapa, Nucleo
from atalaya.logica.nucleo.dominio import TipoEnemigo
from atalaya.logica.nucleo.eventos import (
    AturdimientoTerminado,
    DesestabilizacionIniciada,
    DesestabilizacionTerminada,
    DisparoRealizado,
    PartidaIniciada,
    ProyectilImpacta,
)
from atalaya.logica.nucleo.vectores import angulo_entre
from atalaya.logica.parametros import Parametros
from atalaya.logica.vista import Vista


@pytest.fixture
def parametros(parametros_efectos_fijos: Parametros) -> Parametros:
    """Efectos con su duración de referencia, sin depender del escudo (RN-51)."""
    return parametros_efectos_fijos


#: Margen numérico para comparar ángulos calculados.
_TOLERANCIA = 1e-6


class Partida:
    """Vista y estación conectadas en el núcleo, como en el juego."""

    def __init__(self, parametros: Parametros) -> None:
        self.nucleo = Nucleo(semilla=4)
        self.bus = self.nucleo.bus
        self.vista = Vista(self.bus, parametros)
        self.estacion = Estacion(self.bus, parametros)
        self.nucleo.registrar(Etapa.VISTA, self.vista)
        self.nucleo.registrar(Etapa.ESTACION, self.estacion)

    def impacto(self, tipo: TipoEnemigo) -> None:
        self.bus.publicar(ProyectilImpacta(tipo))
        self.bus.entregar()

    def avanzar(self, horizontal: int = 0, vertical: int = 0) -> None:
        self.vista.recibir_ejes(horizontal, vertical)
        self.nucleo.avanzar(PASO)


def _pasos(segundos: float) -> int:
    return round(segundos / PASO)


def test_sin_desestabilizacion_no_hay_desvio(parametros: Parametros) -> None:
    """Sin desestabilización, la mira apunta justo al centro de la vista."""
    partida = Partida(parametros)
    for _ in range(_pasos(1)):
        partida.avanzar()
    assert partida.vista.desvio == (0.0, 0.0)
    assert partida.vista.direccion_mira == partida.vista.adelante


def test_s4_t07_rn12_desvio_de_la_mira(parametros: Parametros) -> None:
    """S4-T07 RN-12: durante 3 s la mira se desvía hasta 2°, como mucho 0,5° por paso.

    Al terminar la desestabilización, el desvío vuelve a 0 sin saltos.
    """
    ataques = parametros.ataques
    assert (ataques.desvio_maximo, ataques.velocidad_desvio) == (2, 30)
    cambio_maximo = ataques.velocidad_desvio * PASO
    assert cambio_maximo == pytest.approx(0.5)
    partida = Partida(parametros)
    vista = partida.vista
    terminadas: list[DesestabilizacionTerminada] = []
    partida.bus.suscribir(DesestabilizacionTerminada, terminadas.append)
    partida.impacto(TipoEnemigo.DESESTABILIZADOR)
    anterior = vista.direccion_mira
    separaciones = []
    while not terminadas:
        partida.avanzar()
        direccion = vista.direccion_mira
        separacion = angulo_entre(direccion, vista.adelante)
        assert separacion <= ataques.desvio_maximo + _TOLERANCIA
        assert math.hypot(*vista.desvio) <= ataques.desvio_maximo + _TOLERANCIA
        assert angulo_entre(direccion, anterior) <= cambio_maximo + _TOLERANCIA
        separaciones.append(separacion)
        anterior = direccion
    assert len(separaciones) == pytest.approx(_pasos(3), abs=1)
    # La mira se separa de verdad del centro, y no siempre lo mismo: tiembla.
    assert max(separaciones) > ataques.desvio_maximo / 2
    assert max(separaciones) - min(separaciones[_pasos(0.5) :]) > 0.5
    # Al terminar vuelve a 0 sin saltos, en lo que tarda en recorrer el desvío máximo.
    for _ in range(math.ceil(ataques.desvio_maximo / cambio_maximo)):
        partida.avanzar()
        direccion = vista.direccion_mira
        assert angulo_entre(direccion, anterior) <= cambio_maximo + _TOLERANCIA
        anterior = direccion
    assert vista.desvio == (0.0, 0.0)
    assert vista.direccion_mira == vista.adelante


def test_desvio_con_la_mira_fuera_del_centro(parametros: Parametros) -> None:
    """RN-12: con la mira movida por el ratón, el desvío se aplica alrededor de ese punto."""
    partida = Partida(parametros)
    vista = partida.vista
    vista.recibir_puntero(0.6, -0.4)
    partida.avanzar()
    sin_desvio = vista.direccion_mira
    partida.impacto(TipoEnemigo.DESESTABILIZADOR)
    for _ in range(_pasos(1)):
        partida.avanzar()
    assert vista.desvio != (0.0, 0.0)
    separacion = angulo_entre(vista.direccion_mira, sin_desvio)
    assert 0 < separacion <= parametros.ataques.desvio_maximo + _TOLERANCIA
    assert separacion == pytest.approx(math.hypot(*vista.desvio), abs=_TOLERANCIA)


def test_desvio_hacia_la_derecha_y_hacia_arriba(parametros: Parametros) -> None:
    """El desvío (derecha, arriba) lleva la mira hacia la derecha y hacia arriba de la vista."""
    partida = Partida(parametros)
    vista = partida.vista
    partida.impacto(TipoEnemigo.DESESTABILIZADOR)
    vista._desvio = (1.0, 0.0)
    derecha = vista.direccion_mira
    vista._desvio = (0.0, 1.0)
    arriba = vista.direccion_mira
    assert angulo_entre(derecha, vista.derecha) < 90
    assert angulo_entre(derecha, vista.adelante) == pytest.approx(1.0)
    assert angulo_entre(arriba, vista.arriba) < 90
    assert angulo_entre(arriba, vista.adelante) == pytest.approx(1.0)


def test_s4_t08_rn12_disparo_desviado(parametros: Parametros) -> None:
    """S4-T08 RN-12 RN-37: 1000 disparos desestabilizados van justo a la mira desviada."""
    # Disparar sin gastar energía, para encadenar los 1000 disparos.
    jugador = dataclasses.replace(parametros.jugador, coste_disparo=0.0)
    gratis = dataclasses.replace(parametros, jugador=jugador)
    partida = Partida(gratis)
    armamento = Armamento(partida.bus, gratis, partida.vista)
    partida.nucleo.registrar(Etapa.ARMAMENTO, armamento)
    disparos: list[DisparoRealizado] = []
    partida.bus.suscribir(DisparoRealizado, disparos.append)
    desviados = 0
    while len(disparos) < 1000:
        if not partida.estacion.desestabilizado:
            partida.impacto(TipoEnemigo.DESESTABILIZADOR)
            # Se deja que el desvío crezca antes de seguir disparando.
            for _ in range(_pasos(0.5)):
                partida.avanzar()
        armamento.recibir_disparo(True)
        partida.avanzar()
        armamento.recibir_disparo(False)
        antes = len(disparos)
        partida.avanzar()
        assert len(disparos) == antes + 1
        mira = partida.vista.direccion_mira
        assert angulo_entre(disparos[-1].direccion, mira) <= _TOLERANCIA
        if angulo_entre(mira, partida.vista.adelante) > 0.5:
            desviados += 1
    assert desviados > 500


def test_s4_t09_rn13_aturdido_no_gira(parametros: Parametros) -> None:
    """S4-T09 RN-13: aturdido, la flecha derecha no gira la vista; al terminar, sí."""
    partida = Partida(parametros)
    vista = partida.vista
    terminados: list[AturdimientoTerminado] = []
    partida.bus.suscribir(AturdimientoTerminado, terminados.append)
    inicial = vista.orientacion
    partida.impacto(TipoEnemigo.ATURDIDOR)
    assert vista.aturdido
    pasos = 0
    while not terminados:
        partida.avanzar(horizontal=1)
        pasos += 1
        if not terminados:
            assert vista.orientacion == inicial
    assert pasos == pytest.approx(_pasos(parametros.tipos.aturdidor.duracion_efecto), abs=1)
    assert not vista.aturdido
    partida.avanzar(horizontal=1)
    assert vista.orientacion != inicial


def test_aturdido_la_mira_sigue_al_raton(parametros: Parametros) -> None:
    """RN-13: aturdido no se gira, pero el ratón sigue moviendo la mira por la pantalla."""
    partida = Partida(parametros)
    partida.impacto(TipoEnemigo.ATURDIDOR)
    partida.vista.recibir_puntero(0.3, 0.2)
    partida.avanzar()
    assert partida.vista.puntero == (0.3, 0.2)


def test_partida_iniciada_quita_desvio_y_aturdimiento(parametros: Parametros) -> None:
    """PartidaIniciada deja la vista sin desvío y sin bloqueo de giro."""
    partida = Partida(parametros)
    partida.impacto(TipoEnemigo.ATURDIDOR)
    partida.bus.publicar(DesestabilizacionIniciada(3.0))
    partida.bus.entregar()
    for _ in range(_pasos(0.5)):
        partida.avanzar()
    assert partida.vista.desvio != (0.0, 0.0)
    partida.bus.publicar(PartidaIniciada(nivel=1))
    partida.bus.entregar()
    assert partida.vista.desvio == (0.0, 0.0)
    assert not partida.vista.aturdido
    for _ in range(_pasos(0.5)):
        partida.avanzar()
    assert partida.vista.desvio == (0.0, 0.0)
