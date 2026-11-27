"""Pruebas de la animación del salto hiperespacial y de los efectos de combate.

No necesitan ventana: solo crean nodos de la escena y los avanzan en el tiempo.
"""

import math

import pytest
from panda3d.core import NodePath, Vec3

from atalaya.presentacion.escena.efectos import (
    DURACION_EXPLOSION,
    DURACION_RAYO,
    Calentamiento,
    Chispas,
    Destello,
    Efecto,
    Explosion,
    Rayo,
    Sacudida,
    textura_anillo,
    textura_brillo,
)
from atalaya.presentacion.escena.salto import SaltoHiperespacial

PASO = 1 / 60


@pytest.fixture
def escena() -> tuple[NodePath, NodePath, NodePath, NodePath]:
    """Raíz del mundo, cámara, raíz 2D y cielo."""
    render = NodePath("render")
    camara = render.attach_new_node("camara")
    cielo = render.attach_new_node("cielo")
    return render, camara, NodePath("render2d"), cielo


def _avanzar(efecto: Efecto, segundos: float) -> list[bool]:
    """Avanza el efecto como la escena: deja de llamarlo en cuanto termina."""
    vivo: list[bool] = []
    for _ in range(round(segundos / PASO)):
        vivo.append(efecto.avanzar(PASO))
        if not vivo[-1]:
            break
    return vivo


# --- salto -----------------------------------------------------------------------------


def test_salto_cambia_el_cielo_una_vez_oculto(
    escena: tuple[NodePath, NodePath, NodePath, NodePath],
) -> None:
    """El cielo se cambia una sola vez, a mitad del salto, cuando está apagado."""
    _, camara, render2d, cielo = escena
    salto = SaltoHiperespacial(camara, render2d, cielo, textura_brillo(8))
    cambios: list[float] = []
    salto.iniciar(4.0, lambda: cambios.append(cielo.get_color_scale()[0]))
    assert salto.activo
    tiempo = 0.0
    while salto.activo:
        salto.avanzar(PASO, camara)
        tiempo += PASO
    assert len(cambios) == 1
    assert cambios[0] == pytest.approx(0.0, abs=1e-6)
    assert tiempo == pytest.approx(4.0, abs=2 * PASO)
    # Al terminar, la escena queda como estaba: cielo visible y sin abrir el campo de visión.
    assert not cielo.has_color_scale()
    assert salto.apertura == 0.0


def test_salto_abre_el_campo_de_vision_en_el_tunel(
    escena: tuple[NodePath, NodePath, NodePath, NodePath],
) -> None:
    _, camara, render2d, cielo = escena
    salto = SaltoHiperespacial(camara, render2d, cielo, textura_brillo(8))
    salto.iniciar(4.0, lambda: None)
    for _ in range(120):
        salto.avanzar(PASO, camara)
    assert salto.apertura > 5.0
    assert 0.45 < salto.progreso < 0.55


def test_salto_congelado_en_pausa(
    escena: tuple[NodePath, NodePath, NodePath, NodePath],
) -> None:
    """Con dt = 0, como en la pausa, la animación no avanza."""
    _, camara, render2d, cielo = escena
    salto = SaltoHiperespacial(camara, render2d, cielo, textura_brillo(8))
    salto.iniciar(4.0, lambda: None)
    for _ in range(30):
        salto.avanzar(PASO, camara)
    progreso = salto.progreso
    for _ in range(600):
        salto.avanzar(0.0, camara)
    assert salto.progreso == progreso


def test_salto_cancelado_no_cambia_el_cielo(
    escena: tuple[NodePath, NodePath, NodePath, NodePath],
) -> None:
    _, camara, render2d, cielo = escena
    salto = SaltoHiperespacial(camara, render2d, cielo, textura_brillo(8))
    cambios: list[int] = []
    salto.iniciar(4.0, lambda: cambios.append(1))
    for _ in range(60):
        salto.avanzar(PASO, camara)
    salto.cancelar()
    for _ in range(300):
        salto.avanzar(PASO, camara)
    assert cambios == []
    assert not salto.activo
    assert not cielo.has_color_scale()


# --- combate ---------------------------------------------------------------------------


def test_rayo_vuela_como_mucho_0_1_s() -> None:
    """El disparo llega al impacto en 0,1 s como mucho, y nunca en menos de un instante."""
    padre = NodePath("mundo")
    textura = textura_brillo(8)
    lejos = Rayo(padre, textura, Vec3(0, 1, 0), Vec3(0, 1000, 0))
    cerca = Rayo(padre, textura, Vec3(0, 1, 0), Vec3(0, 151, 0))
    assert lejos.duracion_vuelo == pytest.approx(DURACION_RAYO)
    assert 0.03 <= cerca.duracion_vuelo < DURACION_RAYO


def test_efectos_terminan_y_se_borran() -> None:
    padre = NodePath("mundo")
    brillo, anillo = textura_brillo(8), textura_anillo(16)
    punto = Vec3(0, 300, 0)
    efectos: list[Efecto] = [
        Rayo(padre, brillo, Vec3(0, 1, 0), punto),
        Destello(padre, brillo, punto, 10, retraso=0.05),
        Chispas(padre, brillo, punto, 10, retraso=0.05),
        Explosion(padre, brillo, anillo, punto, 18, (1.0, 0.3, 0.3)),
    ]
    vivos = [_avanzar(e, DURACION_EXPLOSION + 0.1) for e in efectos]
    assert all(not v[-1] for v in vivos)
    assert padre.get_num_children() == 0


def test_destello_espera_al_disparo() -> None:
    padre = NodePath("mundo")
    destello = Destello(padre, textura_brillo(8), Vec3(0, 300, 0), 10, retraso=0.1)
    nodo = padre.get_child(0)
    assert nodo.is_hidden()
    _avanzar(destello, 0.12)
    assert not nodo.is_hidden()


def test_restos_de_la_explosion_se_separan() -> None:
    """Cada resto es un nodo propio y sale en su dirección."""
    padre = NodePath("mundo")
    explosion = Explosion(padre, textura_brillo(8), textura_anillo(16), Vec3(0, 300, 0), 18)
    _avanzar(explosion, 0.5)
    restos = padre.find("**/restos").get_children()
    posiciones = {tuple(round(c, 3) for c in resto.get_pos()) for resto in restos}
    assert len(restos) == 6
    assert len(posiciones) == 6


def test_calentamiento_se_quita_solo() -> None:
    padre = NodePath("mundo")
    extra = padre.attach_new_node("extra")
    calentamiento = Calentamiento([Destello(padre, textura_brillo(8), Vec3(0, 1, 0), 1)], [extra])
    assert calentamiento.avanzar(PASO)
    assert not calentamiento.avanzar(PASO)
    assert padre.get_num_children() == 0
    # Si la escena se limpia en el primer fotograma, termina en el acto.
    otro = Calentamiento([], [padre.attach_new_node("x")])
    assert not otro.avanzar(math.inf)
    assert padre.get_num_children() == 0


def test_sacudida_se_apaga() -> None:
    camara = NodePath("camara")
    sacudida = Sacudida()
    sacudida.sacudir(0.5)
    sacudida.avanzar(PASO, camara)
    assert camara.get_hpr().length() > 0
    for _ in range(120):
        camara.set_hpr(0, 0, 0)
        sacudida.avanzar(PASO, camara)
    assert camara.get_hpr().length() == pytest.approx(0.0, abs=1e-6)
