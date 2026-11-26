"""Pruebas del módulo mejoras, con la reparación y las mejoras aplicadas (Sprint 5)."""

from typing import TypeVar

import pytest

from atalaya.arranque import montar
from atalaya.logica.armamento import Armamento
from atalaya.logica.estacion import Estacion
from atalaya.logica.mejoras import Mejoras, Motivo, puntos_oleada, tiempo_referencia
from atalaya.logica.nucleo import PASO, Bus, Evento
from atalaya.logica.nucleo.dominio import Mejora, TipoEnemigo
from atalaya.logica.nucleo.eventos import (
    DescansoIniciado,
    DescansoTerminado,
    IntegridadCambiada,
    MejoraAplicada,
    OleadaSuperada,
    PartidaIniciada,
    ProyectilImpacta,
    PuntosObtenidos,
    ReparacionAplicada,
)
from atalaya.logica.parametros import Parametros
from atalaya.logica.vista import Vista

E = TypeVar("E", bound=Evento)


class Montaje:
    """`mejoras`, `estacion` y `armamento` en un bus, con los eventos anotados."""

    def __init__(self, parametros: Parametros) -> None:
        self.parametros = parametros
        self.bus = Bus()
        self.estacion = Estacion(self.bus, parametros)
        self.mejoras = Mejoras(self.bus, parametros)
        self.armamento = Armamento(self.bus, parametros, Vista(self.bus, parametros))
        self.eventos: list[Evento] = []
        for tipo in (PuntosObtenidos, ReparacionAplicada, MejoraAplicada, IntegridadCambiada):
            self.bus.suscribir(tipo, self.eventos.append)
        self.bus.publicar(PartidaIniciada(1))
        self.bus.entregar()
        self.eventos.clear()

    def de(self, tipo: type[E]) -> list[E]:
        return [e for e in self.eventos if isinstance(e, tipo)]

    def ganar_puntos(self, puntos: int) -> None:
        """Supera oleadas de 3 enemigos hasta sumar `puntos`, con la menor cantidad de cada."""
        referencia = tiempo_referencia(self.parametros, 3)
        lento = self.parametros.mejoras.puntos_lento
        rapido = self.parametros.mejoras.puntos_rapido
        objetivo = self.mejoras.puntos + puntos
        while self.mejoras.puntos < objetivo:
            if objetivo - self.mejoras.puntos >= rapido:
                tiempo = referencia
            else:
                tiempo = referencia * 100
                assert lento == 1
            self.bus.publicar(OleadaSuperada(1, tiempo, 3))
            self.bus.entregar()
        assert self.mejoras.puntos == objetivo

    def abrir_descanso(self) -> None:
        self.bus.publicar(DescansoIniciado(self.parametros.duracion_descanso(1), 2))
        self.bus.entregar()

    def danar(self, cantidad: float) -> None:
        """Quita `cantidad` de integridad con impactos de desestabilizador."""
        dano = self.parametros.tipos.desestabilizador.dano
        for _ in range(round(cantidad / dano)):
            self.bus.publicar(ProyectilImpacta(TipoEnemigo.DESESTABILIZADOR))
        self.bus.entregar()


@pytest.fixture
def montaje(parametros: Parametros) -> Montaje:
    return Montaje(parametros)


# --- puntos --------------------------------------------------------------------------


def test_s5_t03_rn45_puntos_segun_el_tiempo(parametros: Parametros) -> None:
    """S5-T03 RN-45: 3 enemigos (referencia 25 s) en 25, 25,01, 50, 50,01 y 500 s."""
    referencia = tiempo_referencia(parametros, 3)
    assert referencia == pytest.approx(25)
    m = parametros.mejoras
    medio = referencia * m.factor_tiempo_medio
    casos = [
        (referencia, m.puntos_rapido),
        (referencia + 0.01, m.puntos_medio),
        (medio, m.puntos_medio),
        (medio + 0.01, m.puntos_lento),
        (referencia * 20, m.puntos_lento),
    ]
    assert [p for _, p in casos] == [3, 2, 2, 1, 1]
    for tiempo, puntos in casos:
        assert puntos_oleada(parametros, tiempo, 3) == puntos
        montaje = Montaje(parametros)
        montaje.bus.publicar(OleadaSuperada(1, tiempo, 3))
        montaje.bus.entregar()
        assert montaje.mejoras.puntos == puntos


def test_rn45_cronometro_con_error_de_coma_flotante(parametros: Parametros) -> None:
    """RN-45: un tiempo de 25 s sumado paso a paso cuenta como 25 s."""
    tiempo = 0.0
    for _ in range(round(25 / PASO)):
        tiempo += PASO
    assert puntos_oleada(parametros, tiempo, 3) == parametros.mejoras.puntos_rapido


def test_s5_t04_rf43_puntos_obtenidos(montaje: Montaje, parametros: Parametros) -> None:
    """S5-T04 RF-43: PuntosObtenidos lleva puntos obtenidos, disponibles y tiempos."""
    montaje.bus.publicar(OleadaSuperada(4, 30.0, 5))
    montaje.bus.entregar()
    referencia = tiempo_referencia(parametros, 5)
    assert referencia == pytest.approx(35)
    assert montaje.de(PuntosObtenidos) == [PuntosObtenidos(3, 3, 30.0, referencia)]
    resultado = montaje.mejoras.resultado
    assert resultado is not None
    assert (resultado.numero, resultado.tiempo, resultado.puntos) == (4, 30.0, 3)
    assert resultado.tiempo_referencia == referencia


def test_s5_t05_rn45_los_puntos_se_acumulan(montaje: Montaje, parametros: Parametros) -> None:
    """S5-T05 RN-45: 3 puntos y después 2 sin gastar dan 5 disponibles."""
    referencia = tiempo_referencia(parametros, 3)
    montaje.bus.publicar(OleadaSuperada(1, referencia, 3))
    montaje.bus.publicar(OleadaSuperada(2, referencia * 1.5, 3))
    montaje.bus.entregar()
    assert montaje.mejoras.puntos == 5
    assert [e.disponibles for e in montaje.de(PuntosObtenidos)] == [3, 5]


# --- reparación ----------------------------------------------------------------------


def test_s5_t06_rn48_fuera_del_descanso(montaje: Montaje) -> None:
    """S5-T06 RN-48: durante una oleada no se puede reparar ni mejorar."""
    montaje.ganar_puntos(6)
    montaje.danar(30)
    montaje.eventos.clear()
    assert montaje.mejoras.reparar() is Motivo.FUERA_DEL_DESCANSO
    for mejora in Mejora:
        assert montaje.mejoras.mejorar(mejora) is Motivo.FUERA_DEL_DESCANSO
    # También después de que el descanso se cierre.
    montaje.abrir_descanso()
    montaje.bus.publicar(DescansoTerminado())
    montaje.bus.entregar()
    assert montaje.mejoras.reparar() is Motivo.FUERA_DEL_DESCANSO
    montaje.bus.entregar()
    assert montaje.eventos == []
    assert montaje.mejoras.puntos == 6


def test_s5_t07_rn46_reparar(montaje: Montaje) -> None:
    """S5-T07 RN-46, RF-41: integridad 70 con 3 puntos; reparar tres veces da 90 y 100."""
    montaje.danar(30)
    assert montaje.estacion.integridad == 70
    montaje.ganar_puntos(3)
    montaje.abrir_descanso()
    assert montaje.mejoras.reparar() is None
    montaje.bus.entregar()
    assert montaje.estacion.integridad == 90
    assert montaje.mejoras.reparar() is None
    montaje.bus.entregar()
    assert montaje.estacion.integridad == 100
    assert montaje.mejoras.reparar() is Motivo.INTEGRIDAD_MAXIMA
    montaje.bus.entregar()
    assert montaje.estacion.integridad == 100
    assert montaje.mejoras.puntos == 1
    assert montaje.de(ReparacionAplicada) == [ReparacionAplicada(20), ReparacionAplicada(20)]


def test_rn46_reparaciones_en_el_mismo_paso(montaje: Montaje) -> None:
    """Dos reparaciones antes de que `estacion` confirme la primera no gastan de más."""
    montaje.danar(10)
    montaje.ganar_puntos(3)
    montaje.abrir_descanso()
    assert montaje.mejoras.reparar() is None
    assert montaje.mejoras.reparar() is Motivo.INTEGRIDAD_MAXIMA
    montaje.bus.entregar()
    assert montaje.estacion.integridad == 100
    assert montaje.mejoras.puntos == 2


def test_s5_t08_reparar_sin_puntos(montaje: Montaje) -> None:
    """S5-T08: con integridad 70 y sin puntos, reparar no hace nada."""
    montaje.danar(30)
    montaje.abrir_descanso()
    montaje.eventos.clear()
    assert montaje.mejoras.reparar() is Motivo.SIN_PUNTOS
    montaje.bus.entregar()
    assert montaje.eventos == []
    assert montaje.estacion.integridad == 70


def test_reparacion_con_la_estacion_destruida(montaje: Montaje) -> None:
    """Una ReparacionAplicada con la estación destruida no la recupera."""
    montaje.danar(montaje.estacion.integridad)
    assert montaje.estacion.destruida
    montaje.bus.publicar(ReparacionAplicada(20))
    montaje.bus.publicar(MejoraAplicada(Mejora.BLINDAJE, 1))
    montaje.bus.entregar()
    assert montaje.estacion.integridad == 0
    assert montaje.estacion.integridad_maxima == 100


# --- mejoras -------------------------------------------------------------------------


def test_s5_t09_rn47_blindaje(montaje: Montaje) -> None:
    """S5-T09 RN-47: con integridad 80 de 100, el blindaje da 90 de 110 por 2 puntos."""
    montaje.danar(20)
    montaje.ganar_puntos(3)
    montaje.abrir_descanso()
    assert montaje.mejoras.mejorar(Mejora.BLINDAJE) is None
    montaje.bus.entregar()
    assert montaje.mejoras.nivel(Mejora.BLINDAJE) == 1
    assert (montaje.estacion.integridad, montaje.estacion.integridad_maxima) == (90, 110)
    assert montaje.mejoras.puntos == 1
    assert montaje.de(MejoraAplicada) == [MejoraAplicada(Mejora.BLINDAJE, 1)]
    assert montaje.de(IntegridadCambiada)[-1] == IntegridadCambiada(90, 110)


def test_s5_t10_rn47_nivel_maximo(montaje: Montaje) -> None:
    """S5-T10 RN-47: el blindaje se compra 5 veces; la sexta no hace nada."""
    montaje.ganar_puntos(15)
    montaje.abrir_descanso()
    for _ in range(5):
        assert montaje.mejoras.mejorar(Mejora.BLINDAJE) is None
        montaje.bus.entregar()
    assert montaje.mejoras.nivel(Mejora.BLINDAJE) == montaje.mejoras.nivel_maximo(Mejora.BLINDAJE)
    assert montaje.mejoras.nivel(Mejora.BLINDAJE) == 5
    assert montaje.mejoras.mejorar(Mejora.BLINDAJE) is Motivo.NIVEL_MAXIMO
    montaje.bus.entregar()
    assert montaje.mejoras.puntos == 5
    assert montaje.estacion.integridad_maxima == 150
    assert montaje.estacion.integridad == 150
    assert len(montaje.de(MejoraAplicada)) == 5


def test_s5_t11_rn47_bateria(montaje: Montaje) -> None:
    """S5-T11 RN-47: la batería sube la energía máxima a 110."""
    montaje.ganar_puntos(3)
    montaje.abrir_descanso()
    assert montaje.mejoras.mejorar(Mejora.BATERIA) is None
    montaje.bus.entregar()
    assert montaje.armamento.energia_maxima == 110
    # La energía no salta: la recarga la lleva a la nueva máxima.
    assert montaje.armamento.energia == 100
    for _ in range(round(2 / PASO)):
        montaje.armamento.actualizar(PASO)
    assert montaje.armamento.energia == pytest.approx(110)


def test_s5_t12_rn47_generador(montaje: Montaje) -> None:
    """S5-T12 RN-47: con el generador se recargan 9 de energía por segundo."""
    montaje.ganar_puntos(3)
    montaje.abrir_descanso()
    assert montaje.mejoras.mejorar(Mejora.GENERADOR) is None
    montaje.bus.entregar()
    assert montaje.armamento.recarga_energia == 9
    armamento = montaje.armamento
    coste = montaje.parametros.jugador.coste_disparo
    # Se vacía la energía disparando: pulsar en un paso y soltar en el siguiente.
    while armamento.energia >= coste:
        armamento.recibir_disparo(True)
        armamento.actualizar(PASO)
        armamento.recibir_disparo(False)
        armamento.actualizar(PASO)
    inicial = armamento.energia
    for _ in range(round(1 / PASO)):
        armamento.actualizar(PASO)
    assert armamento.energia - inicial == pytest.approx(9)


def test_s5_t13_mejora_sin_puntos(montaje: Montaje) -> None:
    """S5-T13: con 1 punto, ninguna mejora se puede comprar."""
    montaje.ganar_puntos(1)
    montaje.abrir_descanso()
    montaje.eventos.clear()
    for mejora in Mejora:
        assert montaje.mejoras.mejorar(mejora) is Motivo.SIN_PUNTOS
    montaje.bus.entregar()
    assert montaje.eventos == []
    assert montaje.mejoras.puntos == 1


def test_s5_t15_opciones_disponibles(montaje: Montaje) -> None:
    """S5-T15: solo están disponibles las opciones que se pueden comprar."""
    m = montaje.mejoras
    montaje.abrir_descanso()
    # Sin puntos y con la integridad al máximo.
    assert m.motivo_reparar() is Motivo.INTEGRIDAD_MAXIMA
    assert {m.motivo_mejorar(x) for x in Mejora} == {Motivo.SIN_PUNTOS}
    # Con 1 punto y daño: solo se puede reparar.
    montaje.danar(30)
    montaje.ganar_puntos(1)
    assert m.motivo_reparar() is None
    assert {m.motivo_mejorar(x) for x in Mejora} == {Motivo.SIN_PUNTOS}
    # Con 2 puntos: todo; con el blindaje al máximo, el blindaje no.
    montaje.ganar_puntos(11)
    assert m.motivo_reparar() is None
    assert {m.motivo_mejorar(x) for x in Mejora} == {None}
    for _ in range(5):
        m.mejorar(Mejora.BLINDAJE)
    montaje.bus.entregar()
    assert m.motivo_mejorar(Mejora.BLINDAJE) is Motivo.NIVEL_MAXIMO
    assert m.motivo_mejorar(Mejora.BATERIA) is None
    assert m.puntos == 2
    m.mejorar(Mejora.BATERIA)
    montaje.bus.entregar()
    # Sin puntos: nada disponible.
    assert m.motivo_reparar() is Motivo.SIN_PUNTOS
    assert m.motivo_mejorar(Mejora.GENERADOR) is Motivo.SIN_PUNTOS
    # Fuera del descanso, nada.
    montaje.bus.publicar(DescansoTerminado())
    montaje.bus.entregar()
    assert m.motivo_reparar() is Motivo.FUERA_DEL_DESCANSO
    assert {m.motivo_mejorar(x) for x in Mejora} == {Motivo.FUERA_DEL_DESCANSO}


def test_consultas_de_costes_y_niveles(montaje: Montaje, parametros: Parametros) -> None:
    """Los costes, efectos y niveles máximos son los de `parametros`."""
    m = montaje.mejoras
    assert (m.coste_reparacion, m.cantidad_reparacion) == (1, 20)
    for mejora in Mejora:
        datos = parametros.mejoras.de(mejora)
        assert (m.coste(mejora), m.efecto(mejora)) == (datos.coste, datos.efecto)
        assert (m.nivel(mejora), m.nivel_maximo(mejora)) == (0, datos.niveles_maximos)
    assert m.resultado is None
    assert not m.en_descanso
    montaje.abrir_descanso()
    assert m.en_descanso


# --- partida nueva -------------------------------------------------------------------


class TecladoFalso:
    def pulsadas(self, teclas: frozenset[str]) -> frozenset[str]:
        return frozenset()

    def tiene_foco(self) -> bool:
        return True


def test_s5_t14_rn49_partida_nueva_sin_mejoras(parametros: Parametros) -> None:
    """S5-T14 RN-49, RN-02: una partida nueva empieza sin puntos ni mejoras."""
    juego = montar(parametros, TecladoFalso(), semilla=14)
    juego.flujo.iniciar_partida()
    juego.nucleo.avanzar(PASO)
    bus = juego.nucleo.bus
    referencia = tiempo_referencia(parametros, 3)
    for numero in range(1, 5):
        bus.publicar(OleadaSuperada(numero, referencia, 3))
    bus.publicar(DescansoIniciado(20, 2))
    bus.entregar()
    for mejora in Mejora:
        assert juego.mejoras.mejorar(mejora) is None
    bus.entregar()
    assert juego.mejoras.puntos > 0
    assert juego.armamento.energia_maxima > 100
    assert juego.estacion.integridad_maxima > 100
    juego.flujo.iniciar_partida()
    juego.nucleo.avanzar(PASO)
    assert juego.mejoras.puntos == 0
    assert all(juego.mejoras.nivel(mejora) == 0 for mejora in Mejora)
    assert not juego.mejoras.en_descanso
    assert juego.mejoras.resultado is None
    assert (juego.armamento.energia, juego.armamento.energia_maxima) == (100, 100)
    assert (juego.estacion.integridad, juego.estacion.integridad_maxima) == (100, 100)
    assert juego.armamento.recarga_energia == 8
