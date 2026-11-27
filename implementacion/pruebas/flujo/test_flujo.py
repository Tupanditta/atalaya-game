"""Pruebas del flujo: la oleada en curso reparte las acciones y la derrota lleva al resumen."""

import pytest

from atalaya.logica.armamento import Armamento
from atalaya.logica.flujo import Flujo, Pantalla
from atalaya.logica.mejoras import Mejoras
from atalaya.logica.nucleo import PASO, Etapa, Nucleo
from atalaya.logica.nucleo.dominio import Accion, Vector3
from atalaya.logica.nucleo.eventos import DisparoRealizado, EstacionDestruida, PartidaIniciada
from atalaya.logica.parametros import Parametros
from atalaya.logica.vista import ADELANTE, Vista


class AccionesFalsas:
    """Acciones mantenidas que fija la prueba; las pulsaciones se dan en un solo paso."""

    def __init__(self) -> None:
        self.mantenidas: set[Accion] = set()
        self.pulsadas: set[Accion] = set()
        self.raton = (0.0, 0.0)

    def mantenida(self, accion: Accion) -> bool:
        return accion in self.mantenidas

    def recien_pulsada(self, accion: Accion) -> bool:
        return accion in self.pulsadas

    def recien_soltada(self, accion: Accion) -> bool:
        return False

    def puntero(self) -> tuple[float, float]:
        return self.raton


def _flujo(nucleo: Nucleo, parametros: Parametros, acciones: AccionesFalsas, vista: Vista) -> Flujo:
    armamento = Armamento(nucleo.bus, parametros, vista)
    return Flujo(nucleo.bus, acciones, vista, armamento, Mejoras(nucleo.bus, parametros), nucleo)


def _montar(parametros: Parametros) -> tuple[Nucleo, Flujo, Vista, AccionesFalsas]:
    nucleo = Nucleo(semilla=1)
    acciones = AccionesFalsas()
    vista = Vista(nucleo.bus, parametros)
    flujo = _flujo(nucleo, parametros, acciones, vista)
    nucleo.registrar(Etapa.FLUJO, flujo)
    nucleo.registrar(Etapa.VISTA, vista)
    flujo.iniciar_partida()
    return nucleo, flujo, vista, acciones


def _pasos(nucleo: Nucleo, n: int) -> None:
    for _ in range(n):
        nucleo.avanzar(PASO)


def _cerca(a: Vector3, b: Vector3) -> bool:
    return all(abs(x - y) < 1e-9 for x, y in zip(a, b, strict=True))


def test_iniciar_partida(parametros: Parametros) -> None:
    """Iniciar la partida pasa a la oleada en curso y publica PartidaIniciada con el nivel."""
    nucleo = Nucleo(semilla=1)
    recibidos: list[PartidaIniciada] = []
    nucleo.bus.suscribir(PartidaIniciada, recibidos.append)
    flujo = _flujo(nucleo, parametros, AccionesFalsas(), Vista(nucleo.bus, parametros))
    assert flujo.pantalla is Pantalla.MENU_PRINCIPAL
    flujo.iniciar_partida(nivel=3)
    nucleo.bus.entregar()
    assert flujo.pantalla is Pantalla.OLEADA_EN_CURSO
    assert flujo.nivel == 3
    assert recibidos == [PartidaIniciada(nivel=3)]


def test_antes_de_la_partida_no_gira(parametros: Parametros) -> None:
    """Sin pantalla de oleada, las flechas no giran la vista."""
    nucleo = Nucleo(semilla=1)
    acciones = AccionesFalsas()
    vista = Vista(nucleo.bus, parametros)
    nucleo.registrar(Etapa.FLUJO, _flujo(nucleo, parametros, acciones, vista))
    nucleo.registrar(Etapa.VISTA, vista)
    acciones.mantenidas = {Accion.DERECHA}
    _pasos(nucleo, 10)
    assert _cerca(vista.adelante, ADELANTE)


def test_flechas_giran_la_vista(parametros: Parametros) -> None:
    """RF-02: durante la oleada, flecha derecha gira la vista a la derecha."""
    nucleo, _, vista, acciones = _montar(parametros)
    derecha = vista.derecha
    acciones.mantenidas = {Accion.DERECHA}
    _pasos(nucleo, 60)
    assert _cerca(vista.adelante, derecha)


@pytest.mark.parametrize(
    ("mantenidas", "gira_arriba"),
    [
        ({Accion.IZQUIERDA, Accion.DERECHA}, False),
        ({Accion.ARRIBA, Accion.IZQUIERDA, Accion.DERECHA}, True),
        ({Accion.ARRIBA, Accion.ABAJO, Accion.IZQUIERDA, Accion.DERECHA}, False),
    ],
    ids=["izquierda-derecha", "arriba-izquierda-derecha", "cuatro-flechas"],
)
def test_s1_t03_rn26_flechas_opuestas(
    parametros: Parametros, mantenidas: set[Accion], gira_arriba: bool
) -> None:
    """S1-T03 RN-26: las flechas opuestas de un eje se anulan; el otro eje no se ve afectado."""
    nucleo, _, vista, acciones = _montar(parametros)
    arriba = vista.arriba
    acciones.mantenidas = mantenidas
    _pasos(nucleo, 60)
    if gira_arriba:
        assert _cerca(vista.adelante, arriba)
    else:
        assert _cerca(vista.adelante, ADELANTE)


def test_barra_espaciadora_llega_a_armamento(parametros: Parametros) -> None:
    """Durante la oleada, mantener la barra espaciadora hace apuntar a armamento (RN-38)."""
    nucleo = Nucleo(semilla=1)
    acciones = AccionesFalsas()
    vista = Vista(nucleo.bus, parametros)
    armamento = Armamento(nucleo.bus, parametros, vista)
    flujo = Flujo(nucleo.bus, acciones, vista, armamento, Mejoras(nucleo.bus, parametros), nucleo)
    nucleo.registrar(Etapa.FLUJO, flujo)
    nucleo.registrar(Etapa.ARMAMENTO, armamento)
    flujo.iniciar_partida()
    acciones.mantenidas = {Accion.DISPARO}
    _pasos(nucleo, 30)
    assert armamento.progreso_apuntado > 0


# --- resumen de fin de partida (Sprint 3) --------------------------------------------


def _montar_con_armamento(
    parametros: Parametros,
) -> tuple[Nucleo, Flujo, Vista, Armamento, AccionesFalsas]:
    nucleo = Nucleo(semilla=1)
    acciones = AccionesFalsas()
    vista = Vista(nucleo.bus, parametros)
    armamento = Armamento(nucleo.bus, parametros, vista)
    flujo = Flujo(nucleo.bus, acciones, vista, armamento, Mejoras(nucleo.bus, parametros), nucleo)
    nucleo.registrar(Etapa.FLUJO, flujo)
    nucleo.registrar(Etapa.VISTA, vista)
    nucleo.registrar(Etapa.ARMAMENTO, armamento)
    flujo.iniciar_partida(nivel=2)
    return nucleo, flujo, vista, armamento, acciones


def test_cu06_a3_estacion_destruida_muestra_el_resumen(parametros: Parametros) -> None:
    """CU-06 A3: al caer la estación se pasa al resumen con las oleadas superadas."""
    nucleo, flujo, vista, _, acciones = _montar_con_armamento(parametros)
    _pasos(nucleo, 1)
    nucleo.bus.publicar(EstacionDestruida(oleadas_superadas=4))
    _pasos(nucleo, 1)
    assert flujo.pantalla is Pantalla.RESUMEN
    assert flujo.oleadas_superadas == 4
    assert flujo.nivel == 2
    # En el resumen, las flechas ya no giran la vista.
    acciones.mantenidas = {Accion.DERECHA}
    _pasos(nucleo, 30)
    assert _cerca(vista.adelante, ADELANTE)


def test_derrota_con_la_barra_pulsada_no_dispara(parametros: Parametros) -> None:
    """Soltar la barra después de la derrota no dispara y la mira vuelve a la normal."""
    nucleo, _, _, armamento, acciones = _montar_con_armamento(parametros)
    disparos: list[DisparoRealizado] = []
    nucleo.bus.suscribir(DisparoRealizado, disparos.append)
    acciones.mantenidas = {Accion.DISPARO}
    _pasos(nucleo, 30)
    assert armamento.progreso_apuntado > 0
    nucleo.bus.publicar(EstacionDestruida(oleadas_superadas=0))
    _pasos(nucleo, 1)
    acciones.mantenidas = set()
    _pasos(nucleo, 30)
    assert disparos == []
    assert armamento.progreso_apuntado == 0


def test_resumen_intro_vuelve_a_jugar(parametros: Parametros) -> None:
    """CU-01 A2: en el resumen, Intro empieza otra partida con el mismo nivel."""
    nucleo, flujo, _, _, acciones = _montar_con_armamento(parametros)
    iniciadas: list[PartidaIniciada] = []
    nucleo.bus.suscribir(PartidaIniciada, iniciadas.append)
    _pasos(nucleo, 1)
    nucleo.bus.publicar(EstacionDestruida(oleadas_superadas=3))
    _pasos(nucleo, 1)
    acciones.pulsadas = {Accion.CONFIRMAR}
    _pasos(nucleo, 1)
    acciones.pulsadas = set()
    _pasos(nucleo, 1)
    assert iniciadas == [PartidaIniciada(nivel=2), PartidaIniciada(nivel=2)]
    assert flujo.pantalla is Pantalla.OLEADA_EN_CURSO
    assert flujo.oleadas_superadas == 0


def test_resumen_esc_no_hace_nada(parametros: Parametros) -> None:
    """En el resumen, Esc no pausa ni cierra el juego: solo valen sus opciones."""
    nucleo, flujo, _, _, acciones = _montar_con_armamento(parametros)
    nucleo.bus.publicar(EstacionDestruida(oleadas_superadas=0))
    _pasos(nucleo, 1)
    acciones.pulsadas = {Accion.PAUSA}
    _pasos(nucleo, 1)
    assert flujo.pantalla is Pantalla.RESUMEN
    assert not flujo.salir_solicitado
    assert not nucleo.en_pausa


def test_raton_mueve_la_mira(parametros: Parametros) -> None:
    """Durante la oleada, la posición del ratón llega a `vista` como posición de la mira."""
    nucleo, _, vista, acciones = _montar(parametros)
    acciones.raton = (0.5, -0.25)
    _pasos(nucleo, 1)
    assert vista.puntero == (0.5, -0.25)


def test_en_el_resumen_el_raton_no_mueve_la_mira(parametros: Parametros) -> None:
    """Tras la derrota, mover el ratón ya no mueve la mira."""
    nucleo, _, vista, _, acciones = _montar_con_armamento(parametros)
    nucleo.bus.publicar(EstacionDestruida(oleadas_superadas=0))
    _pasos(nucleo, 1)
    acciones.raton = (0.5, 0.5)
    _pasos(nucleo, 5)
    assert vista.puntero == (0.0, 0.0)
