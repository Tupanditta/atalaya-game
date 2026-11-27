"""Prueba de integración de la pausa (Sprint 6): pausar no cambia la partida (RN-50).

Monta los módulos como en el juego real, con un teclado falso, y compara dos
simulaciones con la misma semilla y las mismas entradas; una de ellas se pausa.
"""

from atalaya.arranque import Juego, montar
from atalaya.logica.flujo import Pantalla
from atalaya.logica.nucleo import PASO
from atalaya.logica.parametros import Parametros

#: Paso de partida en el que se pausa y pasos que dura la pausa (10 s).
PASO_PAUSA = 600
PASOS_EN_PAUSA = 600
#: Pasos de partida que se comparan.
PASOS_PARTIDA = 1500


class TecladoFalso:
    def __init__(self) -> None:
        self.teclas: set[str] = set()

    def pulsadas(self, teclas: frozenset[str]) -> frozenset[str]:
        return frozenset(self.teclas) & teclas

    def tiene_foco(self) -> bool:
        return True


def _teclas_de_partida(paso: int) -> set[str]:
    """Entradas que dependen solo del paso de partida: giros y disparos periódicos.

    En el paso de la pausa la barra está suelta, así que ninguna simulación cancela
    un apuntado.
    """
    teclas: set[str] = set()
    if paso < 400:
        teclas.add("arrow_right")
    elif paso < 900:
        teclas.add("arrow_up")
    else:
        teclas.add("arrow_left")
    if paso % 90 < 60:
        teclas.add("space")
    return teclas


def _estado(juego: Juego) -> tuple[object, ...]:
    """Estado de la partida: enemigos, proyectiles, energía, cronómetro, aviso,
    aturdimiento, desestabilización y orientación."""
    estacion, oleadas = juego.estacion, juego.oleadas
    return (
        juego.enemigos.activos,
        juego.enemigos.proyectiles,
        juego.armamento.energia,
        juego.armamento.progreso_apuntado,
        oleadas.numero,
        oleadas.cronometro,
        oleadas.restantes,
        estacion.integridad,
        estacion.tiempo_aturdimiento,
        estacion.tiempo_desestabilizacion,
        juego.vista.orientacion,
        juego.vista.desvio,
    )


def _simular(parametros: Parametros, pausar: bool) -> tuple[object, ...]:
    teclado = TecladoFalso()
    juego = montar(parametros, teclado, semilla=21)
    juego.flujo.iniciar_partida()
    partida = 0
    pasos_reales = 0
    pausado_en: int | None = None
    while partida < PASOS_PARTIDA:
        teclas = _teclas_de_partida(partida)
        if pausar and partida == PASO_PAUSA:
            if pausado_en is None:
                pausado_en = pasos_reales
                teclas.add("escape")
            elif pasos_reales - pausado_en == PASOS_EN_PAUSA:
                teclas.add("escape")
        teclado.teclas = teclas
        partida += juego.nucleo.avanzar(PASO)
        pasos_reales += 1
        if pausado_en is not None and partida == PASO_PAUSA:
            assert juego.flujo.pantalla is Pantalla.PAUSA
    if pausar:
        assert pasos_reales == PASOS_PARTIDA + PASOS_EN_PAUSA
    assert juego.flujo.pantalla is Pantalla.OLEADA_EN_CURSO
    return _estado(juego)


def test_s6_t05_rn50_la_pausa_no_cambia_la_partida(parametros: Parametros) -> None:
    """S6-T05 RN-50: tras los mismos pasos de partida, el estado es idéntico con y sin una
    pausa de 10 s en el paso 600."""
    sin_pausa = _simular(parametros, pausar=False)
    con_pausa = _simular(parametros, pausar=True)
    enemigos = sin_pausa[0]
    assert isinstance(enemigos, tuple)
    assert enemigos, "la prueba necesita enemigos activos"
    assert con_pausa == sin_pausa
