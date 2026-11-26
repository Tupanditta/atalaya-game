"""Pruebas del descanso entre oleadas (Sprint 5)."""

import pytest

from atalaya.logica.nucleo import PASO, Azar, Bus, Evento
from atalaya.logica.nucleo.eventos import (
    DescansoIniciado,
    DescansoTerminado,
    EnemigoDestruido,
    EstacionDestruida,
    OleadaIniciada,
    OleadaSuperada,
    PartidaIniciada,
    SolicitudAparicion,
    TerminarDescansoSolicitado,
)
from atalaya.logica.nucleo.vectores import CERO
from atalaya.logica.oleadas import Oleadas
from atalaya.logica.parametros import Parametros


class Partida:
    """Oleadas en un bus propio, con cada evento anotado junto al paso en que llega."""

    def __init__(self, parametros: Parametros, nivel: int = 1) -> None:
        self.bus = Bus()
        self.oleadas = Oleadas(self.bus, parametros, Azar(5))
        self.paso = 0
        self.eventos: list[tuple[int, Evento]] = []
        tipos: list[type[Evento]] = [
            OleadaSuperada,
            DescansoIniciado,
            DescansoTerminado,
            OleadaIniciada,
            SolicitudAparicion,
        ]
        for tipo in tipos:
            self.bus.suscribir(tipo, lambda e: self.eventos.append((self.paso, e)))
        self.bus.publicar(PartidaIniciada(nivel))
        self.bus.entregar()

    def avanzar(self, pasos: int = 1) -> None:
        for _ in range(pasos):
            self.paso += 1
            self.oleadas.actualizar(PASO)
            self.bus.entregar()

    def superar_oleada(self) -> None:
        """Destruye a cada enemigo en cuanto aparece hasta superar la oleada en curso."""
        while self.oleadas.en_curso:
            self.avanzar()
            for _ in range(self.oleadas.activos):
                self.bus.publicar(EnemigoDestruido(0, CERO))
            self.bus.entregar()

    def de(self, tipo: type[Evento]) -> list[tuple[int, Evento]]:
        return [(paso, e) for paso, e in self.eventos if isinstance(e, tipo)]


def test_s5_t01_rn18_descanso_entre_oleadas(parametros: Parametros) -> None:
    """S5-T01 RN-18: tras superar la oleada 1 hay un descanso de 20 s sin apariciones."""
    partida = Partida(parametros)
    partida.superar_oleada()
    inicio = partida.paso
    duracion = parametros.duracion_descanso(1)
    assert duracion == pytest.approx(20)
    despues = [e for paso, e in partida.eventos if paso == inicio]
    superada = next(e for e in despues if isinstance(e, OleadaSuperada))
    assert despues.index(superada) < despues.index(DescansoIniciado(duracion, 2))
    assert partida.oleadas.en_descanso
    assert partida.oleadas.tiempo_descanso == pytest.approx(duracion)
    partida.eventos.clear()
    partida.avanzar(round(duracion / PASO) - 1)
    assert partida.eventos == []
    assert partida.oleadas.numero == 1
    partida.avanzar()
    fin = partida.paso
    assert [e for _, e in partida.de(DescansoTerminado)] == [DescansoTerminado()]
    assert partida.de(DescansoTerminado)[0][0] == fin
    assert partida.de(OleadaIniciada) == [(fin, OleadaIniciada(2, parametros.entorno_oleada(2)))]
    assert fin - inicio == pytest.approx(duracion / PASO, abs=1)
    terminado = partida.eventos.index(partida.de(DescansoTerminado)[0])
    assert terminado < partida.eventos.index(partida.de(OleadaIniciada)[0])
    assert not partida.oleadas.en_descanso
    assert partida.oleadas.en_curso
    assert partida.oleadas.numero == 2


def test_s5_t02_rf44_terminar_descanso_antes_de_tiempo(parametros: Parametros) -> None:
    """S5-T02 RF-44: TerminarDescansoSolicitado a los 5 s cierra el descanso en ese paso."""
    partida = Partida(parametros)
    partida.superar_oleada()
    partida.avanzar(round(5 / PASO))
    partida.eventos.clear()
    partida.bus.publicar(TerminarDescansoSolicitado())
    partida.bus.entregar()
    assert [e for _, e in partida.de(DescansoTerminado)] == [DescansoTerminado()]
    assert partida.de(OleadaIniciada)[0][1] == OleadaIniciada(2, parametros.entorno_oleada(2))
    assert partida.oleadas.en_curso
    # Ni el fin de la cuenta atrás ni otra solicitud vuelven a terminar el descanso.
    partida.bus.publicar(TerminarDescansoSolicitado())
    partida.avanzar(round(20 / PASO))
    assert len(partida.de(DescansoTerminado)) == 1


def test_terminar_descanso_fuera_del_descanso_no_hace_nada(parametros: Parametros) -> None:
    """Durante una oleada, TerminarDescansoSolicitado no cambia nada."""
    partida = Partida(parametros)
    partida.avanzar()
    partida.bus.publicar(TerminarDescansoSolicitado())
    partida.bus.entregar()
    assert partida.de(DescansoTerminado) == []
    assert partida.oleadas.numero == 1


def test_rn22_descanso_segun_el_nivel(parametros: Parametros) -> None:
    """RN-22: en el nivel 3 el descanso dura lo que marca `parametros` para ese nivel."""
    partida = Partida(parametros, nivel=3)
    partida.superar_oleada()
    duracion = parametros.duracion_descanso(3)
    assert partida.de(DescansoIniciado)[0][1] == DescansoIniciado(duracion, 2)
    inicio = partida.paso
    while not partida.de(DescansoTerminado):
        partida.avanzar()
    assert partida.paso - inicio == pytest.approx(duracion / PASO, abs=1)


def test_estacion_destruida_en_el_descanso_lo_detiene(parametros: Parametros) -> None:
    """Si la estación cae durante el descanso, no empieza la siguiente oleada."""
    partida = Partida(parametros)
    partida.superar_oleada()
    partida.bus.publicar(EstacionDestruida(1))
    partida.bus.entregar()
    assert not partida.oleadas.en_descanso
    assert partida.oleadas.tiempo_descanso == 0
    partida.avanzar(round(30 / PASO))
    assert partida.de(DescansoTerminado) == []
    assert not partida.oleadas.en_curso


def test_partida_nueva_en_el_descanso_empieza_en_la_oleada_1(parametros: Parametros) -> None:
    """PartidaIniciada durante el descanso lo cierra y empieza otra vez la oleada 1."""
    partida = Partida(parametros)
    partida.superar_oleada()
    partida.bus.publicar(PartidaIniciada(1))
    partida.bus.entregar()
    assert not partida.oleadas.en_descanso
    assert partida.oleadas.numero == 1
    assert partida.oleadas.en_curso
