"""Pruebas de los fondos y del salto hiperespacial entre ellos (RN-20, RF-17; S8-T01)."""

import dataclasses

import pytest

from atalaya.arranque import montar
from atalaya.logica.entorno import EntornoEspacial
from atalaya.logica.nucleo import PASO, Azar, Bus, Evento
from atalaya.logica.nucleo.eventos import (
    DescansoTerminado,
    DisparoRealizado,
    EnemigoDestruido,
    FondoCambiado,
    OleadaIniciada,
    PartidaAbandonada,
    PartidaGanada,
    PartidaIniciada,
    SaltoIniciado,
    SaltoTerminado,
    SolicitudAparicion,
    TerminarDescansoSolicitado,
)
from atalaya.logica.nucleo.vectores import CERO
from atalaya.logica.oleadas import Oleadas
from atalaya.logica.parametros import Parametros

#: Oleadas tras cuyo descanso hay salto: una por cada cambio de fondo.
OLEADAS_CON_SALTO = {10, 20, 30, 40}


class Partida:
    """Oleadas y entorno en un bus propio, con cada evento anotado junto a su paso."""

    def __init__(self, parametros: Parametros) -> None:
        self.bus = Bus()
        self.oleadas = Oleadas(self.bus, parametros, Azar(5))
        self.entorno = EntornoEspacial(self.bus, parametros)
        self.paso = 0
        self.eventos: list[tuple[int, Evento]] = []
        tipos: list[type[Evento]] = [
            DescansoTerminado,
            SaltoIniciado,
            SaltoTerminado,
            FondoCambiado,
            OleadaIniciada,
            SolicitudAparicion,
            PartidaGanada,
        ]
        for tipo in tipos:
            self.bus.suscribir(tipo, lambda e: self.eventos.append((self.paso, e)))
        self.bus.publicar(PartidaIniciada(1))
        self.bus.entregar()

    def avanzar(self, pasos: int = 1) -> None:
        for _ in range(pasos):
            self.paso += 1
            self.oleadas.actualizar(PASO)
            self.entorno.actualizar(PASO)
            self.bus.entregar()

    def superar_oleada(self) -> None:
        """Destruye a cada enemigo en cuanto aparece hasta superar la oleada en curso."""
        while self.oleadas.en_curso:
            self.avanzar()
            for _ in range(self.oleadas.activos):
                self.bus.publicar(EnemigoDestruido(0, CERO))
            self.bus.entregar()

    def llegar_al_descanso_de(self, numero: int) -> None:
        """Empieza la oleada `numero` y la supera: queda abierto su descanso."""
        self.oleadas.iniciar_oleada(numero)
        self.bus.entregar()
        self.superar_oleada()
        assert self.oleadas.en_descanso

    def terminar_descanso(self) -> None:
        """El jugador elige continuar: el descanso termina en el siguiente paso."""
        self.bus.publicar(TerminarDescansoSolicitado())
        self.avanzar()

    def de(self, tipo: type[Evento]) -> list[Evento]:
        return [e for _, e in self.eventos if isinstance(e, tipo)]


def test_rn20_fondo_de_cada_oleada(parametros: Parametros) -> None:
    """RN-20: 5 fondos, uno por cada tramo de 10 oleadas, y salto solo entre tramos."""
    assert parametros.oleadas.fondos == 5
    assert parametros.oleadas.oleadas_por_fondo == 10
    esperado = {1: 1, 10: 1, 11: 2, 20: 2, 21: 3, 31: 4, 40: 4, 41: 5, 50: 5}
    for numero, fondo in esperado.items():
        assert parametros.fondo_oleada(numero) == fondo
    con_salto = {n for n in range(1, 51) if parametros.hay_salto_tras(n)}
    assert con_salto == OLEADAS_CON_SALTO


def test_fondos_en_ciclo_con_un_fondo_por_oleada(parametros: Parametros) -> None:
    """Con más tramos que fondos, los fondos se repiten en orden y siempre hay salto."""
    cada_oleada = dataclasses.replace(
        parametros, oleadas=dataclasses.replace(parametros.oleadas, oleadas_por_fondo=1)
    )
    assert [cada_oleada.fondo_oleada(n) for n in range(1, 12)] == [1, 2, 3, 4, 5] * 2 + [1]
    assert all(cada_oleada.hay_salto_tras(n) for n in range(1, 50))
    assert not cada_oleada.hay_salto_tras(50)


def test_s8_t01_sin_salto_tras_la_oleada_9(parametros: Parametros) -> None:
    """S8-T01: tras el descanso de la oleada 9 la oleada 10 empieza sin salto."""
    partida = Partida(parametros)
    assert partida.entorno.fondo == 1
    partida.llegar_al_descanso_de(9)
    partida.eventos.clear()
    partida.terminar_descanso()
    assert partida.de(SaltoIniciado) == []
    assert partida.de(OleadaIniciada) == [OleadaIniciada(10, parametros.entorno_oleada(10))]
    assert partida.entorno.fondo == 1


def test_s8_t01_salto_tras_la_oleada_10(parametros: Parametros) -> None:
    """S8-T01: descanso, salto de 4 s sin enemigos y oleada 11 en el fondo 2."""
    partida = Partida(parametros)
    partida.llegar_al_descanso_de(10)
    partida.eventos.clear()
    partida.terminar_descanso()
    inicio = partida.paso
    duracion = parametros.oleadas.duracion_salto
    assert duracion == pytest.approx(4)
    assert [e for _, e in partida.eventos] == [DescansoTerminado(), SaltoIniciado(2, duracion)]
    assert partida.oleadas.en_salto
    assert not partida.oleadas.en_descanso
    assert not partida.oleadas.en_curso
    assert partida.oleadas.tiempo_salto == pytest.approx(duracion)
    assert partida.entorno.fondo_destino == 2
    partida.eventos.clear()
    # Durante el salto no pasa nada: ni apariciones ni oleada nueva.
    partida.avanzar(round(duracion / PASO) - 1)
    assert partida.eventos == []
    assert partida.entorno.fondo == 1
    partida.avanzar()
    # Los tres llegan en el mismo paso, con el salto terminado antes que lo demás.
    llegada = [e for paso, e in partida.eventos if paso - inicio == round(duracion / PASO)]
    assert llegada[0] == SaltoTerminado()
    assert FondoCambiado(2) in llegada
    assert OleadaIniciada(11, parametros.entorno_oleada(11)) in llegada
    assert not partida.oleadas.en_salto
    assert partida.oleadas.en_curso
    assert partida.entorno.fondo == 2
    assert partida.entorno.fondo_destino is None


def test_s8_t01_salto_tras_la_oleada_40(parametros: Parametros) -> None:
    """S8-T01: tras el descanso de la oleada 40 el salto lleva al fondo 5."""
    partida = Partida(parametros)
    partida.llegar_al_descanso_de(40)
    partida.eventos.clear()
    partida.terminar_descanso()
    assert partida.de(SaltoIniciado) == [SaltoIniciado(5, parametros.oleadas.duracion_salto)]


def test_salto_tambien_al_agotar_el_descanso(parametros: Parametros) -> None:
    """El salto empieza igual si el descanso termina por tiempo."""
    partida = Partida(parametros)
    partida.llegar_al_descanso_de(20)
    partida.eventos.clear()
    partida.avanzar(round(parametros.duracion_descanso(1) / PASO))
    assert partida.de(SaltoIniciado) == [SaltoIniciado(3, parametros.oleadas.duracion_salto)]


def test_s8_t01_una_partida_recorre_los_5_fondos(parametros: Parametros) -> None:
    """S8-T01: las 50 oleadas pasan por los 5 fondos, con 4 saltos, hasta la victoria."""
    partida = Partida(parametros)
    while not partida.de(PartidaGanada):
        partida.superar_oleada()
        if partida.oleadas.en_descanso:
            partida.terminar_descanso()
        while partida.oleadas.en_salto:
            partida.avanzar()
    saltos = [e for e in partida.de(SaltoIniciado) if isinstance(e, SaltoIniciado)]
    assert [e.fondo for e in saltos] == [2, 3, 4, 5]
    assert partida.de(FondoCambiado) == [FondoCambiado(i) for i in (2, 3, 4, 5)]
    assert len(partida.de(SaltoTerminado)) == 4
    assert partida.entorno.fondo == 5


def test_abandonar_durante_el_salto(parametros: Parametros) -> None:
    """Abandonar en pleno salto no cambia el fondo; la partida nueva vuelve al fondo 1."""
    partida = Partida(parametros)
    partida.llegar_al_descanso_de(20)
    partida.terminar_descanso()
    partida.avanzar(round(parametros.oleadas.duracion_salto / PASO))
    assert partida.entorno.fondo == 3
    partida.llegar_al_descanso_de(30)
    partida.terminar_descanso()
    assert partida.oleadas.en_salto
    partida.eventos.clear()
    partida.bus.publicar(PartidaAbandonada())
    partida.avanzar(round(parametros.oleadas.duracion_salto / PASO) + 1)
    assert not partida.oleadas.en_salto
    assert partida.eventos == []
    assert partida.entorno.fondo == 3
    assert partida.entorno.fondo_destino is None
    partida.bus.publicar(PartidaIniciada(1))
    partida.bus.entregar()
    assert partida.de(FondoCambiado) == [FondoCambiado(1)]
    assert partida.entorno.fondo == 1


class TecladoFalso:
    def __init__(self) -> None:
        self.teclas: set[str] = set()

    def pulsadas(self, teclas: frozenset[str]) -> frozenset[str]:
        return frozenset(self.teclas) & teclas

    def tiene_foco(self) -> bool:
        return True


def test_sin_disparo_durante_el_salto(parametros: Parametros) -> None:
    """RN-20: durante el salto la barra espaciadora no dispara; al llegar, sí."""
    teclado = TecladoFalso()
    juego = montar(parametros, teclado, semilla=3)
    disparos: list[DisparoRealizado] = []
    juego.nucleo.bus.suscribir(DisparoRealizado, disparos.append)
    juego.flujo.iniciar_partida()
    juego.nucleo.avanzar(PASO)

    def pulsar_y_soltar_barra() -> None:
        teclado.teclas = {"space"}
        for _ in range(30):
            juego.nucleo.avanzar(PASO)
        teclado.teclas = set()
        for _ in range(5):
            juego.nucleo.avanzar(PASO)

    juego.nucleo.bus.publicar(SaltoIniciado(2, parametros.oleadas.duracion_salto))
    pulsar_y_soltar_barra()
    assert disparos == []
    juego.nucleo.bus.publicar(SaltoTerminado())
    pulsar_y_soltar_barra()
    assert len(disparos) == 1
