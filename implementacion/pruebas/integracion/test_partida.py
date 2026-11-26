"""Pruebas de integración de una partida completa sin ventana (Sprint 3).

Montan los módulos como en el juego real, con un teclado falso, y juegan con el
jugador automático de `sprints.md` («Convenciones de las pruebas»).
"""

import math

import pytest

from atalaya.arranque import Juego, montar
from atalaya.logica.flujo import Pantalla
from atalaya.logica.nucleo import PASO
from atalaya.logica.nucleo.dominio import TipoEnemigo
from atalaya.logica.nucleo.eventos import (
    EstacionDestruida,
    OleadaSuperada,
    ProyectilImpacta,
)
from atalaya.logica.nucleo.vectores import angulo_entre, norma, producto_escalar
from atalaya.logica.parametros import Parametros


class TecladoFalso:
    def __init__(self) -> None:
        self.teclas: set[str] = set()

    def pulsadas(self, teclas: frozenset[str]) -> frozenset[str]:
        return frozenset(self.teclas) & teclas

    def tiene_foco(self) -> bool:
        return True


class JugadorAutomatico:
    """Juega sin teclado real: solo pulsa y suelta las mismas teclas que el jugador.

    En cada paso gira con los ejes de giro hacia el enemigo más cercano. Mantiene la
    barra espaciadora para reducir la mira y la suelta cuando la mira entera está
    sobre la zona de impacto del enemigo.
    """

    #: Error de puntería por debajo del cual empieza a apuntar con la barra.
    ANGULO_APUNTAR = 15.0

    def __init__(self, juego: Juego, teclado: TecladoFalso, parametros: Parametros) -> None:
        self._juego = juego
        self._teclado = teclado
        self._parametros = parametros
        self._barra = False

    def jugar(self) -> None:
        """Decide las teclas de este paso y avanza un paso de simulación."""
        self._teclado.teclas = self._decidir()
        self._juego.nucleo.avanzar(PASO)

    def _decidir(self) -> set[str]:
        juego, p = self._juego, self._parametros
        vista, armamento = juego.vista, juego.armamento
        enemigos = juego.enemigos.activos
        if not enemigos:
            return {"space"} if self._barra else set()
        objetivo = min(enemigos, key=lambda e: norma(e.posicion))
        posicion = objetivo.posicion
        distancia = norma(posicion)
        error = angulo_entre(posicion, vista.adelante)
        radio = p.tamanos.de(objetivo.tamano).radio_impacto
        zona = math.degrees(math.asin(min(1.0, radio / distancia)))
        energia = armamento.energia >= p.jugador.coste_disparo
        if self._barra and energia and error + armamento.radio_mira <= zona:
            # Soltar la barra dispara; en este paso no se gira para no mover la mira.
            self._barra = False
            return set()
        if not self._barra and error < self.ANGULO_APUNTAR:
            self._barra = True
        teclas = {"space"} if self._barra else set()
        paso = p.jugador.velocidad_giro * vista.campo_vision / p.jugador.campo_vision_normal * PASO
        delante = producto_escalar(posicion, vista.adelante)
        horizontal = math.degrees(math.atan2(producto_escalar(posicion, vista.derecha), delante))
        vertical = math.degrees(math.atan2(producto_escalar(posicion, vista.arriba), delante))
        if horizontal > paso / 2:
            teclas.add("arrow_right")
        elif horizontal < -paso / 2:
            teclas.add("arrow_left")
        if vertical > paso / 2:
            teclas.add("arrow_up")
        elif vertical < -paso / 2:
            teclas.add("arrow_down")
        return teclas


def test_estacion_destruida_lleva_al_resumen(parametros: Parametros) -> None:
    """CU-06 A3: con los módulos montados, 34 impactos destruyen la estación y paran todo."""
    teclado = TecladoFalso()
    juego = montar(parametros, teclado, semilla=5)
    destruidas: list[EstacionDestruida] = []
    juego.nucleo.bus.suscribir(EstacionDestruida, destruidas.append)
    juego.flujo.iniciar_partida()
    for _ in range(round(5 / PASO)):
        juego.nucleo.avanzar(PASO)
    assert juego.enemigos.activos
    for _ in range(34):
        juego.nucleo.bus.publicar(ProyectilImpacta(TipoEnemigo.SIN_EFECTO))
    juego.nucleo.avanzar(PASO)
    assert destruidas == [EstacionDestruida(0)]
    assert juego.estacion.integridad == 0
    assert juego.flujo.pantalla is Pantalla.RESUMEN
    assert juego.enemigos.activos == ()
    assert juego.radar.contactos == ()
    assert not juego.oleadas.en_curso
    # Intro vuelve a jugar desde la oleada 1 con la estación intacta.
    teclado.teclas = {"enter"}
    juego.nucleo.avanzar(PASO)
    teclado.teclas = set()
    juego.nucleo.avanzar(PASO)
    assert juego.flujo.pantalla is Pantalla.OLEADA_EN_CURSO
    assert juego.oleadas.numero == 1
    assert juego.estacion.integridad == parametros.jugador.integridad_maxima


@pytest.mark.lenta
def test_s3_t19_jugador_automatico_supera_cinco_oleadas(parametros: Parametros) -> None:
    """S3-T19 integración: el jugador automático supera las oleadas 1 a 5 sin perder."""
    teclado = TecladoFalso()
    juego = montar(parametros, teclado, semilla=19)
    superadas: list[OleadaSuperada] = []
    destruidas: list[EstacionDestruida] = []
    juego.nucleo.bus.suscribir(OleadaSuperada, superadas.append)
    juego.nucleo.bus.suscribir(EstacionDestruida, destruidas.append)
    jugador = JugadorAutomatico(juego, teclado, parametros)
    juego.flujo.iniciar_partida()
    for _ in range(round(600 / PASO)):
        jugador.jugar()
        if len(superadas) == 5 or destruidas:
            break
    assert destruidas == []
    assert [s.numero for s in superadas] == [1, 2, 3, 4, 5]
    assert juego.estacion.integridad > 0
    assert juego.oleadas.numero == 6
