"""Pruebas del módulo oleadas: aparición de enemigos (Sprint 2) y fin de oleada (Sprint 3)."""

import itertools

import pytest

from atalaya.logica.enemigos import Enemigos
from atalaya.logica.nucleo import PASO, Bus, Etapa, Nucleo
from atalaya.logica.nucleo.dominio import Entorno, Tamano, TipoEnemigo
from atalaya.logica.nucleo.eventos import (
    DisparoRealizado,
    EnemigoDestruido,
    EstacionDestruida,
    OleadaIniciada,
    OleadaSuperada,
    PartidaAbandonada,
    PartidaGanada,
    PartidaIniciada,
    SolicitudAparicion,
)
from atalaya.logica.nucleo.vectores import CERO, normalizar
from atalaya.logica.oleadas import Oleadas
from atalaya.logica.parametros import Parametros


class Partida:
    """Oleadas y enemigos conectados en el núcleo, con las solicitudes anotadas por paso."""

    def __init__(self, parametros: Parametros) -> None:
        self.nucleo = Nucleo(semilla=24)
        self.oleadas = Oleadas(self.nucleo.bus, parametros)
        self.enemigos = Enemigos(self.nucleo.bus, parametros, self.nucleo.azar)
        self.nucleo.registrar(Etapa.ENEMIGOS, self.enemigos)
        self.nucleo.registrar(Etapa.OLEADAS, self.oleadas)
        self.paso = 0
        self.solicitudes: list[tuple[int, SolicitudAparicion]] = []
        self.nucleo.bus.suscribir(
            SolicitudAparicion, lambda e: self.solicitudes.append((self.paso, e))
        )

    def avanzar(self, segundos: float) -> None:
        for _ in range(round(segundos / PASO)):
            self.paso += 1
            self.nucleo.avanzar(PASO)

    def destruir_uno(self) -> None:
        """Destruye a un enemigo activo disparándole dos veces justo a su centro."""
        objetivo = self.enemigos.activos[0]
        for _ in range(2):
            self.nucleo.bus.publicar(DisparoRealizado(CERO, normalizar(objetivo.posicion)))
            self.nucleo.bus.entregar()


def test_partida_iniciada_empieza_la_oleada_1(parametros: Parametros) -> None:
    """PartidaIniciada empieza la oleada 1 con el nivel recibido y publica OleadaIniciada."""
    bus = Bus()
    iniciadas: list[OleadaIniciada] = []
    bus.suscribir(OleadaIniciada, iniciadas.append)
    oleadas = Oleadas(bus, parametros)
    assert oleadas.numero == 0
    assert not oleadas.en_curso
    bus.publicar(PartidaIniciada(nivel=3))
    bus.entregar()
    assert iniciadas == [OleadaIniciada(1, Entorno.NINGUNO)]
    assert oleadas.numero == 1
    assert oleadas.nivel == 3
    assert oleadas.en_curso
    assert oleadas.restantes == parametros.composicion_oleada(1).numero_enemigos == 3


def test_solicitudes_de_la_oleada(parametros: Parametros) -> None:
    """Las solicitudes llevan tipo sin efecto, tamaño mediano y la vida del nivel (RN-22)."""
    bus = Bus()
    solicitudes: list[SolicitudAparicion] = []
    bus.suscribir(SolicitudAparicion, solicitudes.append)
    oleadas = Oleadas(bus, parametros)
    bus.publicar(PartidaIniciada(nivel=3))
    bus.entregar()
    for _ in range(round(10 / PASO)):
        oleadas.actualizar(PASO)
        bus.entregar()
    vida = parametros.vida_enemigo(Tamano.MEDIANO, 3)
    assert solicitudes == [SolicitudAparicion(TipoEnemigo.SIN_EFECTO, Tamano.MEDIANO, vida)] * 3
    assert oleadas.pendientes == 0
    assert oleadas.activos == 3


def test_s2_t24_rn43_rf09_ritmo_y_maximo(parametros: Parametros) -> None:
    """S2-T24 RN-43 RF-09: una aparición cada 2 s como mucho, y nunca más de 6 activos."""
    partida = Partida(parametros)
    partida.oleadas.iniciar_oleada(10)
    assert partida.oleadas.pendientes == parametros.composicion_oleada(10).numero_enemigos == 8
    partida.avanzar(12)
    pasos = [paso for paso, _ in partida.solicitudes]
    intervalo = round(parametros.ataques.intervalo_aparicion / PASO)
    assert all(b - a >= intervalo for a, b in itertools.pairwise(pasos))
    maximo = parametros.ataques.enemigos_activos_maximos
    assert maximo == 6
    assert partida.oleadas.activos == len(partida.enemigos.activos) == maximo
    assert partida.oleadas.pendientes == 2
    partida.avanzar(10)
    assert len(partida.solicitudes) == maximo
    assert len(partida.enemigos.activos) == maximo


def test_s2_t25_rn43_reposicion(parametros: Parametros) -> None:
    """S2-T25 RN-43: al destruir un enemigo, en 2 s o menos vuelve a haber 6 activos."""
    partida = Partida(parametros)
    destruidos: list[EnemigoDestruido] = []
    partida.nucleo.bus.suscribir(EnemigoDestruido, destruidos.append)
    partida.oleadas.iniciar_oleada(10)
    maximo = parametros.ataques.enemigos_activos_maximos
    while partida.oleadas.activos < maximo:
        partida.avanzar(PASO)
    # Se destruye justo después de una aparición, el peor caso para el ritmo.
    for vez in range(1, 3):
        partida.destruir_uno()
        assert len(destruidos) == vez
        assert partida.oleadas.activos == maximo - 1
        partida.avanzar(parametros.ataques.intervalo_aparicion)
        assert partida.oleadas.activos == len(partida.enemigos.activos) == maximo
    assert partida.oleadas.pendientes == 0
    partida.destruir_uno()
    partida.avanzar(10)
    assert partida.oleadas.activos == maximo - 1


@pytest.mark.parametrize(
    "evento",
    [PartidaAbandonada(), EstacionDestruida(oleadas_superadas=0)],
    ids=["PartidaAbandonada", "EstacionDestruida"],
)
def test_detener_las_oleadas(parametros: Parametros, evento: object) -> None:
    """PartidaAbandonada y EstacionDestruida detienen las apariciones."""
    partida = Partida(parametros)
    partida.oleadas.iniciar_oleada(10)
    partida.avanzar(1)
    partida.nucleo.bus.publicar(evento)  # type: ignore[arg-type]
    partida.nucleo.bus.entregar()
    antes = len(partida.solicitudes)
    partida.avanzar(10)
    assert len(partida.solicitudes) == antes
    assert not partida.oleadas.en_curso
    assert partida.oleadas.restantes == 0
    assert partida.enemigos.activos == ()


# --- fin de oleada (Sprint 3) --------------------------------------------------------


def _destruir_todos(partida: Partida, segundos_maximos: float = 60) -> None:
    """Destruye a cada enemigo en cuanto aparece, hasta que no quedan en la oleada."""
    numero = partida.oleadas.numero
    for _ in range(round(segundos_maximos / PASO)):
        if partida.oleadas.numero != numero:
            return
        while partida.enemigos.activos:
            partida.destruir_uno()
        partida.avanzar(PASO)
    raise AssertionError("La oleada no ha terminado")


def test_s3_t17_rn15_fin_de_oleada(parametros: Parametros) -> None:
    """S3-T17 RN-15: destruir los 3 enemigos de la oleada 1 la supera y empieza la 2."""
    partida = Partida(parametros)
    eventos: list[object] = []
    partida.nucleo.bus.suscribir(OleadaSuperada, eventos.append)
    partida.nucleo.bus.suscribir(OleadaIniciada, eventos.append)
    partida.nucleo.bus.publicar(PartidaIniciada(nivel=1))
    partida.nucleo.bus.entregar()
    eventos.clear()
    _destruir_todos(partida)
    assert len(eventos) == 2
    superada, iniciada = eventos
    assert isinstance(superada, OleadaSuperada)
    assert (superada.numero, superada.enemigos) == (1, 3)
    assert iniciada == OleadaIniciada(2, parametros.entorno_oleada(2))
    assert partida.oleadas.numero == 2
    assert partida.oleadas.en_curso
    assert partida.oleadas.restantes == parametros.composicion_oleada(2).numero_enemigos


def test_s3_t18_cronometro(parametros: Parametros) -> None:
    """S3-T18: el último enemigo destruido 20 s después de aparecer el primero da 20 s."""
    partida = Partida(parametros)
    superadas: list[OleadaSuperada] = []
    partida.nucleo.bus.suscribir(OleadaSuperada, superadas.append)
    partida.oleadas.iniciar_oleada(1)
    partida.avanzar(PASO)
    (primera, _), *_ = partida.solicitudes
    assert partida.oleadas.cronometro == 0
    while partida.oleadas.pendientes:
        partida.avanzar(PASO)
    partida.destruir_uno()
    partida.destruir_uno()
    partida.avanzar((primera + round(20 / PASO) - partida.paso) * PASO)
    assert partida.oleadas.cronometro == pytest.approx(20, abs=PASO)
    partida.destruir_uno()
    (superada,) = superadas
    assert superada.tiempo == pytest.approx(20, abs=PASO + 1e-9)
    # La oleada siguiente empieza con el cronómetro parado hasta su primera aparición.
    assert partida.oleadas.cronometro == 0
    partida.avanzar(PASO)
    assert partida.oleadas.cronometro == 0


def test_rn19_ultima_oleada_gana_la_partida(parametros: Parametros) -> None:
    """RN-19: superar la última oleada publica PartidaGanada en lugar de OleadaSuperada."""
    bus = Bus()
    ganadas: list[PartidaGanada] = []
    superadas: list[OleadaSuperada] = []
    bus.suscribir(PartidaGanada, ganadas.append)
    bus.suscribir(OleadaSuperada, superadas.append)
    oleadas = Oleadas(bus, parametros)
    bus.publicar(PartidaIniciada(nivel=2))
    bus.entregar()
    ultima = parametros.oleadas.numero_oleadas
    oleadas.iniciar_oleada(ultima)
    while oleadas.restantes:
        oleadas.actualizar(PASO)
        bus.entregar()
        for _ in range(oleadas.activos):
            bus.publicar(EnemigoDestruido(0, CERO))
        bus.entregar()
    assert ganadas == [PartidaGanada(2)]
    assert superadas == []
    assert not oleadas.en_curso
    assert oleadas.numero == ultima


def test_destruccion_fuera_de_oleada_no_cuenta(parametros: Parametros) -> None:
    """Un EnemigoDestruido sin oleada en curso no cambia nada."""
    bus = Bus()
    superadas: list[OleadaSuperada] = []
    bus.suscribir(OleadaSuperada, superadas.append)
    oleadas = Oleadas(bus, parametros)
    bus.publicar(EnemigoDestruido(1, CERO))
    bus.entregar()
    assert superadas == []
    assert oleadas.numero == 0
