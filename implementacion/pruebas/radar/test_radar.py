"""Pruebas del módulo radar: contactos respecto a la cámara (Sprint 3)."""

import math

import pytest

from atalaya.logica.enemigos import EstadoEnemigo, FaseAtaque
from atalaya.logica.nucleo import PASO, Bus
from atalaya.logica.nucleo.dominio import Tamano, TipoEnemigo, Vector3
from atalaya.logica.nucleo.eventos import ApuntadoCambiado
from atalaya.logica.nucleo.vectores import CERO, escalar
from atalaya.logica.parametros import Parametros
from atalaya.logica.radar import ANGULO_MISMA_ALTURA, Altura, Radar
from atalaya.logica.vista import Vista


class EnemigosFalsos:
    def __init__(self) -> None:
        self.activos: list[EstadoEnemigo] = []

    def poner(
        self,
        posicion: Vector3,
        tipo: TipoEnemigo = TipoEnemigo.SIN_EFECTO,
        tamano: Tamano = Tamano.MEDIANO,
        fase: FaseAtaque = FaseAtaque.ACERCANDOSE,
    ) -> None:
        id = len(self.activos) + 1
        self.activos.append(
            EstadoEnemigo(id, tipo, tamano, 20.0, posicion, posicion, CERO, posicion, fase, 0.0)
        )


def _radar(parametros: Parametros) -> tuple[Radar, Vista, EnemigosFalsos, Bus]:
    bus = Bus()
    vista = Vista(bus, parametros)
    enemigos = EnemigosFalsos()
    return Radar(parametros, vista, enemigos), vista, enemigos, bus


def _en_direccion(grados_derecha: float, grados_arriba: float, distancia: float) -> Vector3:
    """Punto a `distancia` con el azimut (hacia la derecha) y la elevación indicados."""
    az, el = math.radians(grados_derecha), math.radians(grados_arriba)
    direccion = (math.cos(el) * math.sin(az), math.cos(el) * math.cos(az), math.sin(el))
    return escalar(direccion, distancia)


def test_s3_t10_rf07_angulo_horario_desde_adelante(parametros: Parametros) -> None:
    """S3-T10 RF-07: delante, derecha, detrás e izquierda dan 0°, 90°, 180° y 270°."""
    radar, _, enemigos, _ = _radar(parametros)
    for posicion in ((0, 500, 0), (500, 0, 0), (0, -500, 0), (-500, 0, 0)):
        enemigos.poner(tuple(float(c) for c in posicion))  # type: ignore[arg-type]
    angulos = [c.angulo for c in radar.contactos]
    assert angulos == pytest.approx([0, 90, 180, 270], abs=1e-9)


def test_s3_t11_rf31_distancia_relativa(parametros: Parametros) -> None:
    """S3-T11 RF-31: a 600 u y a 1200 u, distancia relativa 0,5 y 1."""
    radar, _, enemigos, _ = _radar(parametros)
    assert parametros.ataques.alcance_radar == 1200
    enemigos.poner((0.0, 600.0, 0.0))
    enemigos.poner((0.0, 0.0, -1200.0))
    enemigos.poner((0.0, 1500.0, 0.0))
    distancias = [c.distancia_relativa for c in radar.contactos]
    assert distancias == pytest.approx([0.5, 1, 1])


def test_s3_t12_altura_respecto_a_la_camara(parametros: Parametros) -> None:
    """S3-T12: 20° y 15° por encima, 10° a la misma altura y 20° por debajo."""
    radar, _, enemigos, _ = _radar(parametros)
    assert ANGULO_MISMA_ALTURA == 15
    for elevacion in (20.0, 10.0, 15.0, -20.0, -10.0, -15.0):
        enemigos.poner(_en_direccion(30.0, elevacion, 500.0))
    assert [c.altura for c in radar.contactos] == [
        Altura.POR_ENCIMA,
        Altura.MISMA,
        Altura.POR_ENCIMA,
        Altura.POR_DEBAJO,
        Altura.MISMA,
        Altura.POR_DEBAJO,
    ]


def test_s3_t13_rn41_girar_a_la_derecha(parametros: Parametros) -> None:
    """S3-T13 RN-41: tras girar 90° a la derecha, el enemigo de la derecha pasa a 0°."""
    radar, vista, enemigos, _ = _radar(parametros)
    enemigos.poner((500.0, 0.0, 0.0))
    assert radar.contactos[0].angulo == pytest.approx(90)
    for _ in range(round(90 / (parametros.jugador.velocidad_giro * PASO))):
        vista.recibir_ejes(1, 0)
        vista.actualizar(PASO)
    angulo = radar.contactos[0].angulo
    assert min(angulo, 360 - angulo) == pytest.approx(0, abs=1e-6)


def test_s3_t14_rn41_media_vuelta_vertical(parametros: Parametros) -> None:
    """S3-T14 RN-41: tras media vuelta vertical, el enemigo del «arriba» inicial queda debajo."""
    radar, vista, enemigos, _ = _radar(parametros)
    enemigos.poner((0.0, 0.0, 500.0))
    assert radar.contactos[0].altura is Altura.POR_ENCIMA
    for _ in range(round(180 / (parametros.jugador.velocidad_giro * PASO))):
        vista.recibir_ejes(0, 1)
        vista.actualizar(PASO)
    assert radar.contactos[0].altura is Altura.POR_DEBAJO


def test_s3_t15_campo_de_vision_con_zoom(parametros: Parametros) -> None:
    """S3-T15: un enemigo a 20° del centro está en el campo de visión sin zoom y fuera con él."""
    radar, vista, enemigos, bus = _radar(parametros)
    enemigos.poner(_en_direccion(20.0, 0.0, 500.0))
    enemigos.poner(_en_direccion(0.0, -20.0, 500.0))
    vista.actualizar(PASO)
    assert radar.sector_vision == parametros.jugador.campo_vision_normal
    assert [c.en_campo_vision for c in radar.contactos] == [True, True]
    bus.publicar(ApuntadoCambiado(1.0))
    bus.entregar()
    vista.actualizar(PASO)
    assert radar.sector_vision == parametros.jugador.campo_vision_zoom
    assert [c.en_campo_vision for c in radar.contactos] == [False, False]


def test_detras_fuera_del_campo_de_vision(parametros: Parametros) -> None:
    """Un enemigo detrás de la cámara no está en el campo de visión."""
    radar, _, enemigos, _ = _radar(parametros)
    enemigos.poner((0.0, -500.0, 0.0))
    enemigos.poner(CERO)
    assert [c.en_campo_vision for c in radar.contactos] == [False, False]


def test_s3_t16_rn09_todos_los_enemigos(parametros: Parametros) -> None:
    """S3-T16 RN-09: con 6 enemigos activos, el radar devuelve 6 contactos."""
    radar, _, enemigos, _ = _radar(parametros)
    tipos = list(TipoEnemigo)
    tamanos = list(Tamano)
    for i in range(6):
        enemigos.poner(_en_direccion(60.0 * i, 0.0, 400.0 + 100 * i), tipos[i % 3], tamanos[i % 3])
    contactos = radar.contactos
    assert len(contactos) == 6
    assert [c.id for c in contactos] == [1, 2, 3, 4, 5, 6]
    assert [(c.tipo, c.tamano) for c in contactos] == [
        (tipos[i % 3], tamanos[i % 3]) for i in range(6)
    ]


def test_contacto_en_aviso(parametros: Parametros) -> None:
    """El contacto indica si su enemigo muestra el aviso de disparo, para que parpadee."""
    radar, _, enemigos, _ = _radar(parametros)
    for fase in FaseAtaque:
        enemigos.poner((0.0, 500.0, 0.0), fase=fase)
    assert [c.en_aviso for c in radar.contactos] == [f is FaseAtaque.AVISO for f in FaseAtaque]
