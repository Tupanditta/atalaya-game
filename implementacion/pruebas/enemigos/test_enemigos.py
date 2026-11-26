"""Pruebas del módulo enemigos: aparición, movimiento e impactos (Sprint 2)."""

import itertools
import math
from dataclasses import dataclass, field
from typing import TypeVar

import pytest

from atalaya.logica.enemigos import (
    Enemigos,
    distancia_impacto,
    mover,
    posicion_aparicion,
    velocidad_llegada,
)
from atalaya.logica.nucleo import PASO, Azar, Bus, Evento
from atalaya.logica.nucleo.dominio import Tamano, TipoEnemigo, Vector3
from atalaya.logica.nucleo.eventos import (
    DisparoRealizado,
    EnemigoAlcanzado,
    EnemigoAparecido,
    EnemigoDestruido,
    EstacionDestruida,
    PartidaAbandonada,
    PartidaIniciada,
    SolicitudAparicion,
)
from atalaya.logica.nucleo.vectores import CERO, norma, normalizar, restar
from atalaya.logica.parametros import Parametros

E = TypeVar("E", bound=Evento)

ADELANTE: Vector3 = (0.0, 1.0, 0.0)


class Registro:
    def __init__(self, bus: Bus, *tipos: type[Evento]) -> None:
        self.eventos: list[Evento] = []
        for tipo in tipos:
            bus.suscribir(tipo, self.eventos.append)

    def de(self, tipo: type[E]) -> list[E]:
        return [e for e in self.eventos if isinstance(e, tipo)]


def _enemigos(parametros: Parametros, semilla: int = 1) -> tuple[Enemigos, Bus, Registro]:
    bus = Bus()
    registro = Registro(bus, EnemigoAparecido, EnemigoAlcanzado, EnemigoDestruido)
    return Enemigos(bus, parametros, Azar(semilla)), bus, registro


def _aparecer(
    enemigos: Enemigos, bus: Bus, parametros: Parametros, tamano: Tamano = Tamano.MEDIANO
) -> int:
    vida = parametros.vida_enemigo(tamano, 1)
    bus.publicar(SolicitudAparicion(TipoEnemigo.SIN_EFECTO, tamano, vida))
    bus.entregar()
    return enemigos.activos[-1].id


def _colocar(enemigos: Enemigos, id: int, posicion: Vector3) -> None:
    """Pone al enemigo `id` en `posicion`, parado. Solo para preparar las pruebas."""
    enemigo = enemigos._activos[id]
    enemigo.posicion = enemigo.posicion_anterior = posicion
    enemigo.velocidad = CERO


def _disparar(bus: Bus, direccion: Vector3 = ADELANTE) -> None:
    bus.publicar(DisparoRealizado(CERO, direccion))
    bus.entregar()


# --- aparición -----------------------------------------------------------------------


def test_s2_t13_rn32_aparicion_lejana(parametros: Parametros) -> None:
    """S2-T13 RN-32: los enemigos aparecen entre 900 y 1000 u, en todas las direcciones."""
    ataques = parametros.ataques
    azar = Azar(13)
    octantes = set()
    for _ in range(1000):
        p = posicion_aparicion(ataques, azar)
        assert ataques.distancia_aparicion_minima <= norma(p) <= ataques.distancia_aparicion_maxima
        octantes.add(tuple(c > 0 for c in p))
    assert ataques.distancia_aparicion_minima == 900
    assert ataques.distancia_aparicion_maxima == 1000
    assert len(octantes) == 8


def test_s2_t14_aparicion(parametros: Parametros) -> None:
    """S2-T14: SolicitudAparicion crea el enemigo y publica EnemigoAparecido."""
    enemigos, bus, registro = _enemigos(parametros)
    bus.publicar(SolicitudAparicion(TipoEnemigo.SIN_EFECTO, Tamano.MEDIANO, 20))
    bus.entregar()
    (estado,) = enemigos.activos
    assert registro.de(EnemigoAparecido) == [
        EnemigoAparecido(estado.id, TipoEnemigo.SIN_EFECTO, Tamano.MEDIANO)
    ]
    assert estado.vida == 20
    assert estado.velocidad == CERO
    assert enemigos.enemigo(estado.id) == estado
    assert enemigos.enemigo(estado.id + 1) is None
    _aparecer(enemigos, bus, parametros)
    assert len({e.id for e in enemigos.activos}) == 2


# --- movimiento ----------------------------------------------------------------------


@dataclass
class Trayectoria:
    tamano: Tamano
    posiciones: list[Vector3] = field(default_factory=list)
    velocidades: list[Vector3] = field(default_factory=list)


def _simular(parametros: Parametros, tamanos: list[Tamano], segundos: float) -> list[Trayectoria]:
    enemigos, bus, _ = _enemigos(parametros, semilla=300)
    ids = [_aparecer(enemigos, bus, parametros, t) for t in tamanos]
    trayectorias = {i: Trayectoria(t) for i, t in zip(ids, tamanos, strict=True)}
    for estado in enemigos.activos:
        trayectorias[estado.id].posiciones.append(estado.posicion)
        trayectorias[estado.id].velocidades.append(estado.velocidad)
    for _ in range(round(segundos / PASO)):
        enemigos.actualizar(PASO)
        for estado in enemigos.activos:
            trayectorias[estado.id].posiciones.append(estado.posicion)
            trayectorias[estado.id].velocidades.append(estado.velocidad)
    return list(trayectorias.values())


@pytest.fixture(scope="module")
def trayectorias(parametros: Parametros) -> list[Trayectoria]:
    """6 enemigos medianos durante 300 s simulados."""
    return _simular(parametros, [Tamano.MEDIANO] * 6, 300)


@pytest.fixture(scope="module")
def trayectorias_tamanos(parametros: Parametros) -> list[Trayectoria]:
    """Dos enemigos de cada tamaño durante 300 s simulados."""
    return _simular(parametros, [t for t in Tamano for _ in range(2)], 300)


def test_s2_t15_rn30_rn31_limites_de_distancia(
    parametros: Parametros, trayectorias: list[Trayectoria]
) -> None:
    """S2-T15 RN-30 RN-31: la distancia de cada enemigo está siempre entre 150 y 1000 u."""
    ataques = parametros.ataques
    for t in trayectorias:
        distancias = [norma(p) for p in t.posiciones]
        assert min(distancias) >= ataques.distancia_minima
        assert max(distancias) <= ataques.distancia_maxima


def test_rn30_se_acercan_y_se_alejan(trayectorias: list[Trayectoria]) -> None:
    """RN-30: durante la oleada, los enemigos se acercan y se alejan de la estación."""
    for t in trayectorias:
        distancias = [norma(p) for p in t.posiciones]
        assert max(distancias) - min(distancias) > 300


def _comprobar_inercia(parametros: Parametros, t: Trayectoria) -> None:
    datos = parametros.tamanos.de(t.tamano)
    for v in t.velocidades:
        assert norma(v) <= datos.velocidad_maxima + 1e-9
    cambio_maximo = datos.aceleracion_maxima * PASO
    for a, b in zip(t.velocidades, t.velocidades[1:], strict=False):
        assert norma(restar(b, a)) <= cambio_maximo + 1e-9


def test_s2_t16_rn33_velocidad_e_inercia(
    parametros: Parametros, trayectorias: list[Trayectoria]
) -> None:
    """S2-T16 RN-33: velocidad ≤ 70 u/s y cambio de velocidad ≤ 35 u/s² × 1/60 s por paso."""
    datos = parametros.tamanos.mediano
    assert datos.velocidad_maxima == 70
    assert datos.aceleracion_maxima * PASO == pytest.approx(0.583, abs=1e-3)
    for t in trayectorias:
        _comprobar_inercia(parametros, t)
        # Las posiciones avanzan con la velocidad, sin saltos ni correcciones (RN-33).
        for p, q, v in zip(t.posiciones, t.posiciones[1:], t.velocidades[1:], strict=False):
            assert norma(restar(restar(q, p), (v[0] * PASO, v[1] * PASO, v[2] * PASO))) < 1e-9


def test_rn06_rn31_rn33_todos_los_tamanos(
    parametros: Parametros, trayectorias_tamanos: list[Trayectoria]
) -> None:
    """RN-06 RN-31 RN-33: los límites y la inercia se cumplen con los tres tamaños."""
    ataques = parametros.ataques
    for t in trayectorias_tamanos:
        _comprobar_inercia(parametros, t)
        distancias = [norma(p) for p in t.posiciones]
        assert min(distancias) >= ataques.distancia_minima
        assert max(distancias) <= ataques.distancia_maxima


def _recta(parametros: Parametros) -> tuple[list[float], list[float], Vector3]:
    """Enemigo parado a 500 u persiguiendo un destino fijo a 300 u, de lado."""
    datos = parametros.tamanos.mediano
    posicion: Vector3 = (0.0, 500.0, 0.0)
    destino: Vector3 = (300.0, 500.0, 0.0)
    velocidad = CERO
    rapideces = []
    distancias = []
    for _ in range(600):
        posicion, velocidad = mover(posicion, velocidad, destino, datos, parametros.ataques, PASO)
        rapideces.append(norma(velocidad))
        distancias.append(norma(restar(destino, posicion)))
        if distancias[-1] < parametros.ataques.distancia_llegada:
            break
    return rapideces, distancias, velocidad


def test_s2_t16_rn33_aceleracion_desde_parado(parametros: Parametros) -> None:
    """S2-T16 RN-33: desde parado, llega a la velocidad máxima en 2 s (±1 paso)."""
    rapideces, _, _ = _recta(parametros)
    maxima = parametros.tamanos.mediano.velocidad_maxima
    primera = next(i for i, r in enumerate(rapideces) if r >= maxima - 1e-9) + 1
    assert primera * PASO == pytest.approx(2.0, abs=PASO + 1e-9)


def test_s2_t17_rn33_frenado_al_llegar(parametros: Parametros) -> None:
    """S2-T17 RN-33: con un destino fijo en línea recta, frena de forma gradual al llegar."""
    rapideces, distancias, velocidad = _recta(parametros)
    datos = parametros.tamanos.mediano
    assert distancias[-1] < parametros.ataques.distancia_llegada
    # Empieza a frenar a la distancia que necesita para detenerse: v² / (2·a) = 70 u.
    frenado = datos.velocidad_maxima**2 / (2 * datos.aceleracion_maxima)
    tramo = [r for r, d in zip(rapideces, distancias, strict=True) if d < frenado - 1]
    assert len(tramo) > 5
    assert tramo == sorted(tramo, reverse=True)
    assert tramo[-1] < datos.velocidad_maxima - 5
    for a, b in itertools.pairwise(rapideces):
        assert abs(b - a) <= datos.aceleracion_maxima * PASO + 1e-9
    # Sigue la línea recta hacia el destino.
    assert normalizar(velocidad) == pytest.approx((1.0, 0.0, 0.0), abs=1e-9)


def test_s2_t17_rn33_nuevo_destino_al_llegar(parametros: Parametros) -> None:
    """S2-T17 RN-33: el destino solo cambia al quedar a menos de 50 u de él."""
    enemigos, bus, _ = _enemigos(parametros, semilla=17)
    id = _aparecer(enemigos, bus, parametros)
    llegada = parametros.ataques.distancia_llegada
    cambios = 0
    for _ in range(round(120 / PASO)):
        antes = enemigos.enemigo(id)
        assert antes is not None
        enemigos.actualizar(PASO)
        despues = enemigos.enemigo(id)
        assert despues is not None
        if despues.destino != antes.destino:
            cambios += 1
            assert norma(restar(antes.destino, antes.posicion)) < llegada
            assert norma(restar(despues.destino, antes.posicion)) > llegada
        else:
            assert norma(restar(antes.destino, antes.posicion)) >= llegada
    assert cambios >= 3


def test_s2_t18_rn29_trayectoria_en_tres_dimensiones(trayectorias: list[Trayectoria]) -> None:
    """S2-T18 RN-29: cada enemigo cambia de dirección en horizontal y en vertical."""
    for t in trayectorias:
        moviendose = [v for v in t.velocidades if norma(v) > 1]
        verticales = [v[2] for v in moviendose]
        assert max(verticales) > 5
        assert min(verticales) < -5
        rumbos = [math.degrees(math.atan2(v[0], v[1])) for v in moviendose]
        assert any(abs(b - a) > 1e-6 for a, b in itertools.pairwise(rumbos))
        # El rumbo horizontal recorre un abanico amplio: no sigue una sola dirección.
        senos = [math.sin(math.radians(r)) for r in rumbos]
        cosenos = [math.cos(math.radians(r)) for r in rumbos]
        assert max(senos) - min(senos) > 0.5 or max(cosenos) - min(cosenos) > 0.5


def test_rn42_fuera_del_alcance_se_acerca(parametros: Parametros) -> None:
    """RN-42: fuera del alcance de disparo, el destino queda dentro del alcance."""
    from atalaya.logica.enemigos import elegir_destino

    ataques = parametros.ataques
    azar = Azar(42)
    for _ in range(500):
        destino = elegir_destino(posicion_aparicion(ataques, azar), ataques, azar)
        assert ataques.distancia_minima <= norma(destino) <= ataques.alcance_disparo + 1e-9


def test_velocidad_llegada_en_el_destino(parametros: Parametros) -> None:
    """En el propio destino, la velocidad deseada es nula."""
    destino: Vector3 = (0.0, 500.0, 0.0)
    assert velocidad_llegada(destino, destino, parametros.tamanos.mediano) == CERO


# --- impactos ------------------------------------------------------------------------


def test_s2_t19_rn07_destruccion(parametros: Parametros) -> None:
    """S2-T19 RN-07: dos disparos destruyen a un enemigo mediano a 500 u."""
    enemigos, bus, registro = _enemigos(parametros)
    id = _aparecer(enemigos, bus, parametros)
    posicion: Vector3 = (0.0, 500.0, 0.0)
    _colocar(enemigos, id, posicion)
    _disparar(bus)
    assert registro.de(EnemigoAlcanzado) == [EnemigoAlcanzado(id, 10)]
    _disparar(bus)
    assert registro.de(EnemigoDestruido) == [EnemigoDestruido(id, posicion)]
    assert enemigos.activos == ()
    _disparar(bus)
    assert len(registro.de(EnemigoAlcanzado)) == 1


def test_s2_t20_impacto_el_mas_cercano(parametros: Parametros) -> None:
    """S2-T20: con dos enemigos alineados, solo se daña el más cercano."""
    enemigos, bus, registro = _enemigos(parametros)
    lejano = _aparecer(enemigos, bus, parametros)
    cercano = _aparecer(enemigos, bus, parametros)
    _colocar(enemigos, lejano, (0.0, 600.0, 0.0))
    _colocar(enemigos, cercano, (0.0, 300.0, 0.0))
    _disparar(bus)
    assert registro.de(EnemigoAlcanzado) == [EnemigoAlcanzado(cercano, 10)]
    estado = enemigos.enemigo(lejano)
    assert estado is not None
    assert estado.vida == 20


@pytest.mark.parametrize(("margen", "acierta"), [(-1.0, True), (1.0, False)])
def test_s2_t21_impacto_esfera(parametros: Parametros, margen: float, acierta: bool) -> None:
    """S2-T21: la zona de impacto es una esfera con el radio del tamaño.

    Un enemigo mediano desplazado del eje 1 u menos que su radio recibe el disparo; 1 u
    más, no.
    """
    desvio = parametros.tamanos.mediano.radio_impacto + margen
    enemigos, bus, registro = _enemigos(parametros)
    id = _aparecer(enemigos, bus, parametros)
    _colocar(enemigos, id, (desvio, 500.0, 0.0))
    _disparar(bus)
    assert bool(registro.de(EnemigoAlcanzado)) is acierta


def test_s2_t22_impacto_sentido(parametros: Parametros) -> None:
    """S2-T22: un enemigo justo detrás de la estación no recibe el disparo."""
    enemigos, bus, registro = _enemigos(parametros)
    id = _aparecer(enemigos, bus, parametros)
    _colocar(enemigos, id, (0.0, -500.0, 0.0))
    _disparar(bus)
    assert registro.eventos == registro.de(EnemigoAparecido)


def test_distancia_impacto() -> None:
    """La distancia de impacto es la de entrada en la esfera, y 0 si el origen está dentro."""
    assert distancia_impacto(CERO, ADELANTE, (0.0, 500.0, 0.0), 12) == pytest.approx(488)
    assert distancia_impacto(CERO, ADELANTE, (0.0, 5.0, 0.0), 12) == 0
    assert distancia_impacto(CERO, ADELANTE, (0.0, -500.0, 0.0), 12) is None
    assert distancia_impacto(CERO, ADELANTE, (13.0, 500.0, 0.0), 12) is None


@pytest.mark.parametrize(
    "evento",
    [PartidaIniciada(nivel=1), PartidaAbandonada(), EstacionDestruida(oleadas_superadas=0)],
    ids=["PartidaIniciada", "PartidaAbandonada", "EstacionDestruida"],
)
def test_s2_t23_limpieza(parametros: Parametros, evento: Evento) -> None:
    """S2-T23: al empezar o terminar la partida no quedan enemigos."""
    enemigos, bus, _ = _enemigos(parametros)
    for _ in range(3):
        _aparecer(enemigos, bus, parametros)
    assert len(enemigos.activos) == 3
    bus.publicar(evento)
    bus.entregar()
    assert enemigos.activos == ()


# --- tamaños (Sprint 4) --------------------------------------------------------------


def test_s4_t01_rn06_rn33_velocidad_y_aceleracion_por_tamano(
    parametros: Parametros, trayectorias_tamanos: list[Trayectoria]
) -> None:
    """S4-T01 RN-06 RN-33: velocidad ≤ 110, 70 y 40 u/s; cambio por paso ≤ aceleración × 1/60 s."""
    t = parametros.tamanos
    assert (t.pequeno.velocidad_maxima, t.mediano.velocidad_maxima, t.grande.velocidad_maxima) == (
        110,
        70,
        40,
    )
    assert (
        t.pequeno.aceleracion_maxima,
        t.mediano.aceleracion_maxima,
        t.grande.aceleracion_maxima,
    ) == (55, 35, 20)
    maximas: dict[Tamano, float] = {}
    for trayectoria in trayectorias_tamanos:
        _comprobar_inercia(parametros, trayectoria)
        rapidez = max(norma(v) for v in trayectoria.velocidades)
        maximas[trayectoria.tamano] = max(maximas.get(trayectoria.tamano, 0.0), rapidez)
    # Cada tamaño llega a su velocidad máxima: los pequeños van claramente más rápido.
    for tamano, rapidez in maximas.items():
        assert rapidez == pytest.approx(t.de(tamano).velocidad_maxima, rel=0.05)
    assert maximas[Tamano.PEQUENO] > maximas[Tamano.MEDIANO] > maximas[Tamano.GRANDE]


@pytest.mark.parametrize(
    ("tamano", "margen", "acierta"),
    [
        (Tamano.PEQUENO, -1.0, True),
        (Tamano.PEQUENO, 1.0, False),
        (Tamano.GRANDE, -1.0, True),
        (Tamano.GRANDE, 1.0, False),
    ],
)
def test_s4_t02_rn06_zona_de_impacto_por_tamano(
    parametros: Parametros, tamano: Tamano, margen: float, acierta: bool
) -> None:
    """S4-T02 RN-06: la zona de impacto de cada tamaño es una esfera con su radio.

    A mayor tamaño, mayor zona de impacto. Desplazado del eje 1 u menos que su radio
    recibe el disparo; 1 u más, no.
    """
    t = parametros.tamanos
    assert t.pequeno.radio_impacto < t.mediano.radio_impacto < t.grande.radio_impacto
    desvio = t.de(tamano).radio_impacto + margen
    enemigos, bus, registro = _enemigos(parametros)
    id = _aparecer(enemigos, bus, parametros, tamano)
    _colocar(enemigos, id, (desvio, 500.0, 0.0))
    _disparar(bus)
    alcanzado = bool(registro.de(EnemigoAlcanzado) or registro.de(EnemigoDestruido))
    assert alcanzado is acierta


@pytest.mark.parametrize(
    ("tamano", "disparos"), [(Tamano.PEQUENO, 1), (Tamano.MEDIANO, 2), (Tamano.GRANDE, 4)]
)
def test_s4_t03_rn06_disparos_por_tamano(
    parametros: Parametros, tamano: Tamano, disparos: int
) -> None:
    """S4-T03 RN-06: en nivel 1, el pequeño cae con 1 disparo; el mediano, 2; el grande, 4."""
    enemigos, bus, registro = _enemigos(parametros)
    id = _aparecer(enemigos, bus, parametros, tamano)
    _colocar(enemigos, id, (0.0, 500.0, 0.0))
    for _ in range(disparos - 1):
        _disparar(bus)
    assert registro.de(EnemigoDestruido) == []
    assert len(registro.de(EnemigoAlcanzado)) == disparos - 1
    _disparar(bus)
    assert [e.id for e in registro.de(EnemigoDestruido)] == [id]
    assert enemigos.activos == ()
