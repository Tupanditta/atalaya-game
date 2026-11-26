"""Pruebas de integración del arranque sin ventana (Sprint 1).

Montan los módulos como en el juego real, con un teclado falso en lugar del motor.
"""

import pytest

from atalaya.arranque import montar
from atalaya.logica.flujo import Pantalla
from atalaya.logica.nucleo import PASO
from atalaya.logica.nucleo.dominio import TipoEnemigo
from atalaya.logica.nucleo.eventos import DisparoRealizado, ProyectilImpacta
from atalaya.logica.parametros import Parametros


class TecladoFalso:
    def __init__(self) -> None:
        self.teclas: set[str] = set()

    def pulsadas(self, teclas: frozenset[str]) -> frozenset[str]:
        return frozenset(self.teclas) & teclas

    def tiene_foco(self) -> bool:
        return True


def test_flecha_derecha_gira_la_vista(parametros: Parametros) -> None:
    """RF-02: con los módulos montados, mantener la flecha derecha 1 s gira 90°."""
    teclado = TecladoFalso()
    juego = montar(parametros, teclado, semilla=1)
    juego.flujo.iniciar_partida()
    derecha = juego.vista.derecha
    teclado.teclas = {"arrow_right"}
    for _ in range(60):
        juego.nucleo.avanzar(PASO)
    assert juego.flujo.pantalla is Pantalla.OLEADA_EN_CURSO
    assert juego.vista.adelante == pytest.approx(derecha, abs=1e-9)


def test_rnf02_respuesta_en_el_mismo_paso(parametros: Parametros) -> None:
    """RNF-02: la vista empieza a girar en el mismo paso en que se pulsa y para al soltar."""
    teclado = TecladoFalso()
    juego = montar(parametros, teclado, semilla=1)
    juego.flujo.iniciar_partida()
    juego.nucleo.avanzar(PASO)
    inicial = juego.vista.orientacion
    teclado.teclas = {"arrow_up"}
    juego.nucleo.avanzar(PASO)
    girada = juego.vista.orientacion
    assert girada != inicial
    teclado.teclas = set()
    juego.nucleo.avanzar(PASO)
    assert juego.vista.orientacion == girada


def test_esc_cierra_el_juego(parametros: Parametros) -> None:
    """Provisional hasta S6: Esc pide cerrar el juego."""
    teclado = TecladoFalso()
    juego = montar(parametros, teclado, semilla=1)
    juego.flujo.iniciar_partida()
    teclado.teclas = {"escape"}
    juego.nucleo.avanzar(PASO)
    assert juego.flujo.salir_solicitado


def test_s2_partida_con_enemigos_y_disparo(parametros: Parametros) -> None:
    """S2: al empezar aparecen enemigos que se mueven y la barra espaciadora dispara."""
    from atalaya.logica.nucleo.eventos import DisparoRealizado

    teclado = TecladoFalso()
    juego = montar(parametros, teclado, semilla=2)
    disparos: list[DisparoRealizado] = []
    juego.nucleo.bus.suscribir(DisparoRealizado, disparos.append)
    juego.flujo.iniciar_partida()
    for _ in range(60):
        juego.nucleo.avanzar(PASO)
    (enemigo,) = juego.enemigos.activos
    assert enemigo.posicion != enemigo.posicion_anterior
    assert juego.oleadas.numero == 1
    teclado.teclas = {"space"}
    # El tiempo de apuntado completo; `vista` aplica el zoom en el paso siguiente.
    for _ in range(round(parametros.jugador.tiempo_apuntado / PASO) + 1):
        juego.nucleo.avanzar(PASO)
    assert juego.armamento.progreso_apuntado == 1
    assert juego.vista.campo_vision == parametros.jugador.campo_vision_zoom
    teclado.teclas = set()
    juego.nucleo.avanzar(PASO)
    assert len(disparos) == 1
    assert juego.armamento.energia == pytest.approx(
        parametros.jugador.energia_maxima - parametros.jugador.coste_disparo
    )


class RatonFalso:
    def __init__(self, posicion: tuple[float, float]) -> None:
        self._posicion = posicion

    def posicion(self) -> tuple[float, float] | None:
        return self._posicion


def test_el_disparo_sale_hacia_la_mira_del_raton(parametros: Parametros) -> None:
    """El disparo sale hacia donde el ratón ha puesto la mira, dentro de su dispersión."""
    from atalaya.logica.nucleo.eventos import DisparoRealizado
    from atalaya.logica.nucleo.vectores import angulo_entre

    teclado = TecladoFalso()
    juego = montar(parametros, teclado, semilla=3, raton=RatonFalso((0.6, 0.4)))
    disparos: list[DisparoRealizado] = []
    juego.nucleo.bus.suscribir(DisparoRealizado, disparos.append)
    juego.flujo.iniciar_partida()
    juego.nucleo.avanzar(PASO)
    teclado.teclas = {"space"}
    juego.nucleo.avanzar(PASO)
    teclado.teclas = set()
    juego.nucleo.avanzar(PASO)
    (disparo,) = disparos
    assert juego.vista.puntero == (0.6, 0.4)
    mira = juego.vista.direccion_mira
    assert angulo_entre(mira, juego.vista.adelante) > 20
    assert angulo_entre(disparo.direccion, mira) <= parametros.jugador.mira_normal + 1e-9


def test_wasd_y_clic(parametros: Parametros) -> None:
    """D gira la vista como la flecha derecha, y el clic izquierdo dispara al soltarlo."""
    from atalaya.logica.nucleo.eventos import DisparoRealizado

    teclado = TecladoFalso()
    juego = montar(parametros, teclado, semilla=1)
    disparos: list[DisparoRealizado] = []
    juego.nucleo.bus.suscribir(DisparoRealizado, disparos.append)
    juego.flujo.iniciar_partida()
    derecha = juego.vista.derecha
    teclado.teclas = {"d"}
    for _ in range(60):
        juego.nucleo.avanzar(PASO)
    assert juego.vista.adelante == pytest.approx(derecha, abs=1e-9)
    teclado.teclas = {"mouse1"}
    juego.nucleo.avanzar(PASO)
    teclado.teclas = set()
    juego.nucleo.avanzar(PASO)
    assert len(disparos) == 1


def test_s4_aturdimiento_con_los_modulos_montados(parametros: Parametros) -> None:
    """RN-13: un impacto aturdidor bloquea el giro y el disparo hasta que termina."""
    teclado = TecladoFalso()
    juego = montar(parametros, teclado, semilla=2)
    disparos: list[DisparoRealizado] = []
    juego.nucleo.bus.suscribir(DisparoRealizado, disparos.append)
    juego.flujo.iniciar_partida()
    juego.nucleo.bus.publicar(ProyectilImpacta(TipoEnemigo.ATURDIDOR))
    juego.nucleo.avanzar(PASO)
    assert juego.estacion.aturdido
    inicial = juego.vista.orientacion
    teclado.teclas = {"arrow_right", "space"}
    juego.nucleo.avanzar(PASO)
    teclado.teclas = {"arrow_right"}
    for _ in range(round(1 / PASO)):
        juego.nucleo.avanzar(PASO)
    assert juego.vista.orientacion == inicial
    assert disparos == []
    for _ in range(round(1 / PASO)):
        juego.nucleo.avanzar(PASO)
    assert not juego.estacion.aturdido
    assert juego.vista.orientacion != inicial
