"""Pruebas de los ataques de los enemigos: aviso, proyectil y recarga (Sprint 3)."""

import dataclasses
import math
from typing import TypeVar

import pytest

from atalaya.logica.enemigos import RADIO_ESTACION, Enemigos, FaseAtaque, Maniobra
from atalaya.logica.nucleo import PASO, Azar, Bus, Evento
from atalaya.logica.nucleo.dominio import Tamano, TipoEnemigo, Vector3
from atalaya.logica.nucleo.eventos import (
    AvisoDisparo,
    DisparoRealizado,
    EstacionDestruida,
    PartidaAbandonada,
    PartidaIniciada,
    ProyectilImpacta,
    ProyectilLanzado,
    SolicitudAparicion,
)
from atalaya.logica.nucleo.vectores import CERO, escalar, norma, normalizar, producto_escalar
from atalaya.logica.parametros import Parametros

E = TypeVar("E", bound=Evento)


class Simulacion:
    """Un módulo `enemigos` con sus eventos anotados junto al paso en que se publican."""

    def __init__(self, parametros: Parametros, semilla: int = 3) -> None:
        self.parametros = parametros
        self.bus = Bus()
        self.enemigos = Enemigos(self.bus, parametros, Azar(semilla))
        self.paso = 0
        self.eventos: list[tuple[int, Evento]] = []
        for tipo in (AvisoDisparo, ProyectilLanzado, ProyectilImpacta):
            self.bus.suscribir(tipo, lambda e: self.eventos.append((self.paso, e)))

    def aparecer(self, tipo: TipoEnemigo = TipoEnemigo.SIN_EFECTO) -> int:
        vida = self.parametros.vida_enemigo(Tamano.MEDIANO, 1)
        self.bus.publicar(SolicitudAparicion(tipo, Tamano.MEDIANO, vida))
        self.bus.entregar()
        return self.enemigos.activos[-1].id

    def colocar(self, id: int, posicion: Vector3) -> None:
        """Pone al enemigo `id` en `posicion`, parado y empezando un ataque.

        Solo para preparar las pruebas.
        """
        enemigo = self.enemigos._activos[id]
        enemigo.posicion = enemigo.posicion_anterior = posicion
        enemigo.velocidad = CERO
        self.enemigos._empezar_ataque(enemigo)

    def avanzar(self, pasos: int = 1) -> None:
        for _ in range(pasos):
            self.paso += 1
            self.enemigos.actualizar(PASO)
            self.bus.entregar()

    def avanzar_hasta(self, tipo: type[Evento], maximo: int) -> int:
        """Avanza hasta que se publica un evento de `tipo`; devuelve su paso."""
        antes = len(self.de(tipo))
        for _ in range(maximo):
            self.avanzar()
            if len(self.de(tipo)) > antes:
                return self.paso
        raise AssertionError(f"No se publicó {tipo.__name__} en {maximo} pasos")

    def destruir(self, id: int) -> None:
        """Dispara a su centro hasta destruir al enemigo `id`."""
        while (enemigo := self.enemigos.enemigo(id)) is not None:
            self.bus.publicar(DisparoRealizado(CERO, normalizar(enemigo.posicion)))
            self.bus.entregar()

    def de(self, tipo: type[E]) -> list[tuple[int, E]]:
        return [(p, e) for p, e in self.eventos if isinstance(e, tipo)]


def _siempre_al_alcance(parametros: Parametros) -> Parametros:
    """Parámetros en los que la capa de movimiento queda dentro del alcance de disparo."""
    a = parametros.ataques
    ataques = dataclasses.replace(
        a,
        distancia_maxima=a.alcance_disparo,
        distancia_aparicion_minima=a.alcance_disparo - 100,
        distancia_aparicion_maxima=a.alcance_disparo,
    )
    return dataclasses.replace(parametros, ataques=ataques)


def _pasos(segundos: float) -> int:
    return round(segundos / PASO)


def _huecos(sim: Simulacion, tipo: TipoEnemigo) -> list[int]:
    """Pasos entre cada lanzamiento y el aviso siguiente."""
    avisos = [p for p, _ in sim.de(AvisoDisparo)]
    lanzados = [p for p, e in sim.de(ProyectilLanzado) if e.tipo_enemigo is tipo]
    assert len(lanzados) >= 4
    return [s - lanzado for lanzado, s in zip(lanzados, avisos[1:], strict=False)]


def _comprobar_recarga(sim: Simulacion, recarga: float, tipo: TipoEnemigo) -> None:
    """Moviéndose libremente, entre un lanzamiento y el aviso siguiente pasa al menos la recarga.

    Puede pasar más, porque el enemigo no dispara mientras se retira ni mientras espera.
    """
    assert all(h >= _pasos(recarga) - 1 for h in _huecos(sim, tipo))


def _comprobar_recarga_fijo(parametros: Parametros, recarga: float, tipo: TipoEnemigo) -> None:
    """Con el enemigo atacando siempre a 500 u, entre lanzamiento y aviso pasa justo la recarga."""
    sim = Simulacion(parametros)
    id = sim.aparecer(tipo)
    for _ in range(_pasos(20)):
        sim.colocar(id, (0.0, 500.0, 0.0))
        sim.avanzar()
    assert all(abs(h - _pasos(recarga)) <= 1 for h in _huecos(sim, tipo))


def test_empieza_acercandose_con_la_recarga_terminada(parametros: Parametros) -> None:
    """Un enemigo recién aparecido está en fase de acercamiento y puede atacar."""
    sim = Simulacion(parametros)
    enemigo = sim.enemigos.enemigo(sim.aparecer())
    assert enemigo is not None
    assert enemigo.fase is FaseAtaque.ACERCANDOSE
    assert enemigo.tiempo_fase == 0


def test_s3_t01_rn42_solo_dispara_dentro_del_alcance(parametros: Parametros) -> None:
    """S3-T01 RN-42: sin aviso a más de 700 u; en 30 s entra en el alcance y avisa."""
    sim = Simulacion(parametros)
    id = sim.aparecer()
    sim.colocar(id, (0.0, 800.0, 0.0))
    alcance = parametros.ataques.alcance_disparo
    assert alcance == 700
    for _ in range(_pasos(30)):
        sim.avanzar()
        enemigo = sim.enemigos.enemigo(id)
        assert enemigo is not None
        if sim.de(AvisoDisparo):
            assert norma(enemigo.posicion) <= alcance
            break
        assert norma(enemigo.posicion) > alcance
    assert [e for _, e in sim.de(AvisoDisparo)] == [AvisoDisparo(id)]
    enemigo = sim.enemigos.enemigo(id)
    assert enemigo is not None
    assert enemigo.fase is FaseAtaque.AVISO


def test_s3_t02_rn34_proyectil_un_segundo_despues_del_aviso(parametros: Parametros) -> None:
    """S3-T02 RN-34: ProyectilLanzado llega 0,3 s (±1 paso) después de AvisoDisparo."""
    sim = Simulacion(parametros)
    id = sim.aparecer()
    sim.colocar(id, (0.0, 500.0, 0.0))
    aviso = sim.avanzar_hasta(AvisoDisparo, 10)
    lanzado = sim.avanzar_hasta(ProyectilLanzado, _pasos(2))
    assert abs((lanzado - aviso) - _pasos(parametros.ataques.duracion_aviso)) <= 1
    ((_, evento),) = sim.de(ProyectilLanzado)
    assert evento.tipo_enemigo is TipoEnemigo.SIN_EFECTO
    (proyectil,) = sim.enemigos.proyectiles
    assert proyectil.id == evento.id
    enemigo = sim.enemigos.enemigo(id)
    assert enemigo is not None
    assert enemigo.fase is FaseAtaque.RECARGA


def test_s3_t03_rn34_destruido_durante_el_aviso(parametros: Parametros) -> None:
    """S3-T03 RN-34: si se destruye al enemigo durante el aviso, no lanza el proyectil."""
    sim = Simulacion(parametros)
    id = sim.aparecer()
    sim.colocar(id, (0.0, 500.0, 0.0))
    sim.avanzar_hasta(AvisoDisparo, 10)
    sim.avanzar(_pasos(parametros.ataques.duracion_aviso / 2))
    sim.destruir(id)
    sim.avanzar(_pasos(3))
    assert sim.de(ProyectilLanzado) == []
    assert sim.enemigos.proyectiles == ()


def test_s3_t04_rn14_recarga_entre_ataques(parametros: Parametros) -> None:
    """S3-T04 RN-14: entre un ProyectilLanzado y el siguiente AvisoDisparo pasa al menos 1 s."""
    sim = Simulacion(_siempre_al_alcance(parametros))
    sim.aparecer()
    sim.avanzar(_pasos(40))
    assert parametros.tipos.sin_efecto.recarga == 1
    _comprobar_recarga(sim, 1, TipoEnemigo.SIN_EFECTO)
    _comprobar_recarga_fijo(parametros, 1, TipoEnemigo.SIN_EFECTO)


def test_solo_dispara_al_atacar(parametros: Parametros) -> None:
    """Solo avisa y dispara mientras se lanza hacia la estación, no al retirarse ni al esperar."""
    sim = Simulacion(parametros)
    id = sim.aparecer()
    maniobras = []
    for _ in range(_pasos(120)):
        avisos = len(sim.de(AvisoDisparo))
        sim.avanzar()
        if len(sim.de(AvisoDisparo)) > avisos:
            enemigo = sim.enemigos.enemigo(id)
            assert enemigo is not None
            maniobras.append(enemigo.maniobra)
    assert len(maniobras) >= 6
    assert set(maniobras) == {Maniobra.ATAQUE}


def test_s3_t05_rn35_proyectil_en_linea_recta(parametros: Parametros) -> None:
    """S3-T05 RN-35: el proyectil va recto al centro a 300 u/s e impacta a (d − 5)/300 s."""
    sim = Simulacion(parametros)
    id = sim.aparecer()
    # El enemigo se mantiene a 600 u durante todo el aviso.
    while not sim.de(ProyectilLanzado):
        sim.colocar(id, (0.0, 600.0, 0.0))
        sim.avanzar()
    lanzado = sim.paso
    # Sin su enemigo, no sale otro proyectil mientras se mide este (RN-36).
    sim.destruir(id)
    (proyectil,) = sim.enemigos.proyectiles
    salida = proyectil.posicion
    # En el paso del lanzamiento, el enemigo ya ha empezado a moverse: menos de 1 u.
    assert norma(salida) == pytest.approx(600, abs=1)
    rapidez = parametros.ataques.velocidad_proyectil
    assert rapidez == 300
    assert norma(proyectil.velocidad) == pytest.approx(rapidez)
    assert normalizar(proyectil.velocidad) == pytest.approx(escalar(normalizar(salida), -1))
    # Mientras vuela, sigue sobre la recta que une la salida con el centro.
    sim.avanzar(30)
    (proyectil,) = sim.enemigos.proyectiles
    assert normalizar(proyectil.posicion) == pytest.approx(normalizar(salida))
    assert norma(proyectil.posicion) == pytest.approx(norma(salida) - rapidez * 30 * PASO)
    impacto = sim.avanzar_hasta(ProyectilImpacta, _pasos(3))
    esperado = (norma(salida) - RADIO_ESTACION) / rapidez
    assert esperado == pytest.approx((600 - 5) / 300, abs=0.01)
    assert abs((impacto - lanzado) * PASO - esperado) <= PASO + 1e-9
    assert [e for _, e in sim.de(ProyectilImpacta)] == [ProyectilImpacta(TipoEnemigo.SIN_EFECTO)]
    assert sim.enemigos.proyectiles == ()


def test_proyectil_mas_lejano_tarda_mas(parametros: Parametros) -> None:
    """CU-06: un proyectil disparado desde más lejos tarda más en llegar."""
    tiempos = []
    for distancia in (300.0, 650.0):
        sim = Simulacion(parametros)
        sim.colocar(sim.aparecer(), (distancia, 0.0, 0.0))
        lanzado = sim.avanzar_hasta(ProyectilLanzado, _pasos(2))
        tiempos.append(sim.avanzar_hasta(ProyectilImpacta, _pasos(3)) - lanzado)
    assert tiempos[0] < tiempos[1]


def test_proyectil_que_cruzaria_el_centro_impacta(parametros: Parametros) -> None:
    """Un proyectil que en un paso pasaría de largo el radio de la estación también impacta."""
    sim = Simulacion(parametros)
    sim.colocar(sim.aparecer(), (0.0, 0.0, 400.0))
    sim.avanzar_hasta(ProyectilLanzado, _pasos(2))
    proyectil = next(iter(sim.enemigos._proyectiles.values()))
    # A 2 u del centro: el siguiente paso de 5 u lo dejaría al otro lado.
    proyectil.posicion = escalar(normalizar(proyectil.posicion), 2.0)
    sim.avanzar()
    assert len(sim.de(ProyectilImpacta)) == 1


def test_s3_t06_rn36_proyectil_sigue_sin_su_enemigo(parametros: Parametros) -> None:
    """S3-T06 RN-36: destruido el enemigo, su proyectil sigue y publica ProyectilImpacta."""
    sim = Simulacion(parametros)
    id = sim.aparecer()
    sim.colocar(id, (0.0, 600.0, 0.0))
    sim.avanzar_hasta(ProyectilLanzado, _pasos(2))
    sim.avanzar(10)
    sim.destruir(id)
    assert sim.enemigos.activos == ()
    assert len(sim.enemigos.proyectiles) == 1
    sim.avanzar_hasta(ProyectilImpacta, _pasos(3))
    assert len(sim.enemigos.proyectiles) == 0


def test_aviso_continua_al_salir_del_alcance(parametros: Parametros) -> None:
    """Un aviso ya empezado termina con su proyectil aunque el enemigo se aleje."""
    sim = Simulacion(parametros)
    id = sim.aparecer()
    sim.colocar(id, (0.0, 699.0, 0.0))
    sim.avanzar_hasta(AvisoDisparo, 10)
    sim.colocar(id, (0.0, 900.0, 0.0))
    sim.avanzar_hasta(ProyectilLanzado, _pasos(1.1))


def test_cada_tipo_usa_su_recarga(parametros: Parametros) -> None:
    """RN-14: el tiempo de recarga es el del tipo del enemigo."""
    sim = Simulacion(parametros)
    id = sim.aparecer(TipoEnemigo.ATURDIDOR)
    sim.colocar(id, (0.0, 500.0, 0.0))
    sim.avanzar_hasta(ProyectilLanzado, _pasos(2))
    enemigo = sim.enemigos.enemigo(id)
    assert enemigo is not None
    assert enemigo.tiempo_fase == pytest.approx(parametros.tipos.aturdidor.recarga)
    ((_, lanzado),) = sim.de(ProyectilLanzado)
    assert lanzado.tipo_enemigo is TipoEnemigo.ATURDIDOR


@pytest.mark.parametrize(
    "evento",
    [PartidaIniciada(nivel=1), PartidaAbandonada(), EstacionDestruida(oleadas_superadas=0)],
    ids=["PartidaIniciada", "PartidaAbandonada", "EstacionDestruida"],
)
def test_limpieza_de_proyectiles(parametros: Parametros, evento: Evento) -> None:
    """Al empezar o terminar la partida no quedan enemigos ni proyectiles."""
    sim = Simulacion(parametros)
    sim.colocar(sim.aparecer(), (0.0, 600.0, 0.0))
    sim.avanzar_hasta(ProyectilLanzado, _pasos(2))
    assert sim.enemigos.proyectiles
    sim.bus.publicar(evento)
    sim.bus.entregar()
    assert sim.enemigos.activos == ()
    assert sim.enemigos.proyectiles == ()
    sim.avanzar(_pasos(3))
    assert sim.de(ProyectilImpacta) == []


def test_proyectiles_en_orden_y_con_su_posicion_anterior(parametros: Parametros) -> None:
    """La consulta de proyectiles da la posición anterior para interpolar al dibujar."""
    sim = Simulacion(parametros)
    sim.colocar(sim.aparecer(), (0.0, 600.0, 0.0))
    sim.avanzar_hasta(ProyectilLanzado, _pasos(2))
    sim.avanzar()
    (proyectil,) = sim.enemigos.proyectiles
    avance = norma(proyectil.posicion_anterior) - norma(proyectil.posicion)
    assert avance == pytest.approx(parametros.ataques.velocidad_proyectil * PASO)
    assert producto_escalar(proyectil.posicion, proyectil.velocidad) < 0
    assert not math.isclose(norma(proyectil.posicion), 0)


@pytest.mark.parametrize(
    ("tipo", "recarga"),
    [(TipoEnemigo.SIN_EFECTO, 1), (TipoEnemigo.DESESTABILIZADOR, 0.75), (TipoEnemigo.ATURDIDOR, 2)],
    ids=lambda v: v.value if isinstance(v, TipoEnemigo) else str(v),
)
def test_s4_t14_rn14_recarga_por_tipo(
    parametros: Parametros, tipo: TipoEnemigo, recarga: float
) -> None:
    """S4-T14 RN-14: recarga entre disparos de 1 s (sin efecto), 0,75 s y 2 s (aturdidor)."""
    assert parametros.tipos.de(tipo).recarga == recarga
    sim = Simulacion(_siempre_al_alcance(parametros))
    sim.aparecer(tipo)
    sim.avanzar(_pasos(40))
    _comprobar_recarga(sim, recarga, tipo)
    _comprobar_recarga_fijo(parametros, recarga, tipo)
