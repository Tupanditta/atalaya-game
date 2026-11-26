"""Pruebas del módulo vista (Sprint 1)."""

import math

import pytest

from atalaya.logica.nucleo import PASO, Bus
from atalaya.logica.nucleo.dominio import Vector3
from atalaya.logica.nucleo.eventos import ApuntadoCambiado, PartidaIniciada
from atalaya.logica.parametros import Parametros
from atalaya.logica.vista import ADELANTE, ARRIBA, DERECHA, Cuaternion, Vista, angulo_entre


def _vista(parametros: Parametros) -> tuple[Vista, Bus]:
    bus = Bus()
    return Vista(bus, parametros), bus


def _girar(vista: Vista, horizontal: int, vertical: int, pasos: int) -> None:
    for _ in range(pasos):
        vista.recibir_ejes(horizontal, vertical)
        vista.actualizar(PASO)


def _pasos_para(grados: float, parametros: Parametros) -> int:
    """Pasos sin zoom que hacen falta para girar `grados`."""
    pasos = grados / (parametros.jugador.velocidad_giro * PASO)
    assert pasos == pytest.approx(round(pasos))
    return round(pasos)


def _cerca(a: Vector3, b: Vector3) -> bool:
    return all(abs(x - y) < 1e-9 for x, y in zip(a, b, strict=True))


def _angulo(a: Vector3, b: Vector3) -> float:
    escalar = sum(x * y for x, y in zip(a, b, strict=True))
    return math.degrees(math.acos(max(-1.0, min(1.0, escalar))))


def test_orientacion_inicial(parametros: Parametros) -> None:
    """Al crearse, la cámara mira hacia delante con el campo de visión normal."""
    vista, _ = _vista(parametros)
    assert _cerca(vista.adelante, ADELANTE)
    assert _cerca(vista.arriba, ARRIBA)
    assert _cerca(vista.derecha, DERECHA)
    assert vista.campo_vision == parametros.jugador.campo_vision_normal
    assert vista.direccion_mira == vista.adelante


def test_s1_t01_rf02_giro_a_la_derecha(parametros: Parametros) -> None:
    """S1-T01 RF-02: flecha derecha durante 60 pasos gira 90° hacia la derecha inicial."""
    vista, _ = _vista(parametros)
    derecha_inicial = vista.derecha
    _girar(vista, 1, 0, _pasos_para(90, parametros))
    assert _cerca(vista.adelante, derecha_inicial)


def test_rf02_giro_a_la_izquierda(parametros: Parametros) -> None:
    """RF-02: flecha izquierda durante 60 pasos gira 90° hacia la izquierda inicial."""
    vista, _ = _vista(parametros)
    izquierda = tuple(-c for c in vista.derecha)
    _girar(vista, -1, 0, _pasos_para(90, parametros))
    assert _cerca(vista.adelante, izquierda)  # type: ignore[arg-type]


def test_s1_t02_rf03_giro_hacia_arriba(parametros: Parametros) -> None:
    """S1-T02 RF-03: flecha arriba durante 60 pasos lleva «adelante» al «arriba» inicial."""
    vista, _ = _vista(parametros)
    arriba_inicial = vista.arriba
    _girar(vista, 0, 1, _pasos_para(90, parametros))
    assert _cerca(vista.adelante, arriba_inicial)


def test_rf03_giro_hacia_abajo(parametros: Parametros) -> None:
    """RF-03: flecha abajo durante 60 pasos lleva «adelante» al «abajo» inicial."""
    vista, _ = _vista(parametros)
    abajo = tuple(-c for c in vista.arriba)
    _girar(vista, 0, -1, _pasos_para(90, parametros))
    assert _cerca(vista.adelante, abajo)  # type: ignore[arg-type]


def test_s1_t04_rf21_giro_combinado(parametros: Parametros) -> None:
    """S1-T04 RF-21: arriba y derecha a la vez giran en los dos ejes en el mismo paso."""
    vista, _ = _vista(parametros)
    _girar(vista, 1, 1, 1)
    adelante = vista.adelante
    assert adelante[0] > 0, "debe girar hacia la derecha"
    assert adelante[2] > 0, "debe girar hacia arriba"


def test_s1_t05_rn41_giro_tras_media_vuelta(parametros: Parametros) -> None:
    """S1-T05 RN-41: tras media vuelta vertical, el giro lateral sigue siendo el de la cámara."""
    vista, _ = _vista(parametros)
    arriba_inicial = vista.arriba
    _girar(vista, 0, 1, _pasos_para(180, parametros))
    assert _cerca(vista.arriba, tuple(-c for c in arriba_inicial))  # type: ignore[arg-type]
    derecha_antes = vista.derecha
    _girar(vista, 1, 0, _pasos_para(90, parametros))
    assert _cerca(vista.adelante, derecha_antes)


def test_s1_t06_rn41_vuelta_completa(parametros: Parametros) -> None:
    """S1-T06 RN-41: una vuelta vertical completa vuelve a la orientación inicial."""
    vista, _ = _vista(parametros)
    inicial = vista.orientacion
    _girar(vista, 0, 1, _pasos_para(360, parametros))
    assert angulo_entre(vista.orientacion, inicial) == pytest.approx(0.0, abs=1e-5)
    assert _cerca(vista.adelante, ADELANTE)
    assert _cerca(vista.arriba, ARRIBA)


def test_s1_t07_estabilidad_numerica(parametros: Parametros) -> None:
    """S1-T07: tras 100 000 pasos de giro combinado, norma 1 y ejes ortonormales."""
    vista, _ = _vista(parametros)
    ejes = [(1, 1), (1, -1), (-1, 1), (0, 1), (1, 0), (-1, -1)]
    for paso in range(100_000):
        horizontal, vertical = ejes[(paso // 997) % len(ejes)]
        vista.recibir_ejes(horizontal, vertical)
        vista.actualizar(PASO)
    assert vista.orientacion.norma() == pytest.approx(1.0, abs=1e-9)
    a, b, c = vista.adelante, vista.arriba, vista.derecha
    for eje in (a, b, c):
        assert math.sqrt(sum(x * x for x in eje)) == pytest.approx(1.0, abs=1e-9)
    for u, v in ((a, b), (a, c), (b, c)):
        assert sum(x * y for x, y in zip(u, v, strict=True)) == pytest.approx(0.0, abs=1e-9)


def test_s1_t08_rn40_giro_mas_lento_con_zoom(parametros: Parametros) -> None:
    """S1-T08 RN-40: con la mira mínima, un paso gira 1,5° × 25/70."""
    vista, bus = _vista(parametros)
    bus.publicar(ApuntadoCambiado(progreso=1.0))
    bus.entregar()
    _girar(vista, 1, 0, 1)
    j = parametros.jugador
    esperado = j.velocidad_giro * PASO * j.campo_vision_zoom / j.campo_vision_normal
    assert esperado == pytest.approx(1.5 * 25 / 70)
    assert _angulo(vista.adelante, ADELANTE) == pytest.approx(esperado, abs=1e-9)


@pytest.mark.parametrize("progreso", [0.0, 0.5, 1.0])
def test_s1_t09_rn39_campo_de_vision(parametros: Parametros, progreso: float) -> None:
    """S1-T09 RN-39, RF-33: el campo de visión sigue al progreso del apuntado."""
    vista, bus = _vista(parametros)
    bus.publicar(ApuntadoCambiado(progreso=progreso))
    bus.entregar()
    vista.actualizar(PASO)
    j = parametros.jugador
    if progreso == 0.0:
        assert vista.campo_vision == pytest.approx(j.campo_vision_normal) == 70
    elif progreso == 1.0:
        assert vista.campo_vision == pytest.approx(j.campo_vision_zoom) == 25
    else:
        assert j.campo_vision_zoom < vista.campo_vision < j.campo_vision_normal


def test_s1_t10_rnf04_giro_constante(parametros: Parametros) -> None:
    """S1-T10 RNF-04: flecha derecha durante 120 pasos gira exactamente 1,5° cada paso."""
    vista, _ = _vista(parametros)
    esperado = parametros.jugador.velocidad_giro * PASO
    assert esperado == pytest.approx(1.5)
    for _ in range(120):
        antes = vista.adelante
        _girar(vista, 1, 0, 1)
        assert _angulo(antes, vista.adelante) == pytest.approx(esperado, abs=1e-6)


def test_s1_t11_partida_iniciada_restablece(parametros: Parametros) -> None:
    """S1-T11: PartidaIniciada restablece la orientación inicial y el campo de visión normal."""
    vista, bus = _vista(parametros)
    bus.publicar(ApuntadoCambiado(progreso=1.0))
    bus.entregar()
    _girar(vista, 1, 1, 30)
    vista.recibir_ejes(1, 1)
    assert vista.campo_vision != parametros.jugador.campo_vision_normal
    bus.publicar(PartidaIniciada(nivel=1))
    bus.entregar()
    assert vista.orientacion == Cuaternion.identidad()
    assert vista.orientacion_anterior == Cuaternion.identidad()
    assert vista.campo_vision == parametros.jugador.campo_vision_normal
    # Ni el zoom ni un giro pendiente sobreviven al reinicio.
    vista.actualizar(PASO)
    assert vista.orientacion == Cuaternion.identidad()
    assert vista.campo_vision == parametros.jugador.campo_vision_normal


def test_sin_ejes_no_gira(parametros: Parametros) -> None:
    """Los ejes de un paso se olvidan después: sin nuevos ejes, la vista no gira."""
    vista, _ = _vista(parametros)
    _girar(vista, 1, 0, 1)
    orientacion = vista.orientacion
    vista.actualizar(PASO)
    assert vista.orientacion == orientacion
    assert vista.orientacion_anterior == orientacion


def test_orientacion_anterior_es_la_del_paso_previo(parametros: Parametros) -> None:
    """La orientación anterior es la que había al empezar el último paso."""
    vista, _ = _vista(parametros)
    _girar(vista, 1, 0, 5)
    previa = vista.orientacion
    _girar(vista, 1, 0, 1)
    assert vista.orientacion_anterior == previa
    assert vista.orientacion != previa


def test_apuntado_fuera_de_rango_se_limita(parametros: Parametros) -> None:
    """Un progreso de apuntado fuera de [0, 1] se limita a ese intervalo."""
    vista, bus = _vista(parametros)
    bus.publicar(ApuntadoCambiado(progreso=2.0))
    bus.entregar()
    vista.actualizar(PASO)
    assert vista.campo_vision == pytest.approx(parametros.jugador.campo_vision_zoom)
    bus.publicar(ApuntadoCambiado(progreso=-1.0))
    bus.entregar()
    vista.actualizar(PASO)
    assert vista.campo_vision == pytest.approx(parametros.jugador.campo_vision_normal)


@pytest.mark.parametrize(("horizontal", "vertical"), [(2, 0), (0, -2)])
def test_ejes_no_validos(parametros: Parametros, horizontal: int, vertical: int) -> None:
    """Los ejes solo admiten −1, 0 y +1."""
    vista, _ = _vista(parametros)
    with pytest.raises(ValueError, match="Ejes de giro"):
        vista.recibir_ejes(horizontal, vertical)
