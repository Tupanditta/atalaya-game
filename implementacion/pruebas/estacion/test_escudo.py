"""Pruebas del escudo de la estación (RN-51)."""

import pytest

from atalaya.logica.estacion import Estacion
from atalaya.logica.nucleo import Bus, Evento
from atalaya.logica.nucleo.dominio import Mejora, TipoEnemigo
from atalaya.logica.nucleo.eventos import (
    AturdimientoIniciado,
    DesestabilizacionIniciada,
    EscudoCambiado,
    MejoraAplicada,
    PartidaIniciada,
    ProyectilImpacta,
    RegeneracionEscudoAplicada,
)
from atalaya.logica.parametros import Parametros


class Montaje:
    def __init__(self, parametros: Parametros) -> None:
        self.bus = Bus()
        self.estacion = Estacion(self.bus, parametros)
        self.eventos: list[Evento] = []
        for tipo in (EscudoCambiado, DesestabilizacionIniciada, AturdimientoIniciado):
            self.bus.suscribir(tipo, self.eventos.append)

    def publicar(self, *eventos: Evento) -> None:
        for evento in eventos:
            self.bus.publicar(evento)
        self.bus.entregar()

    def impacto(self, tipo: TipoEnemigo) -> None:
        self.publicar(ProyectilImpacta(tipo))


@pytest.fixture
def montaje(parametros: Parametros) -> Montaje:
    return Montaje(parametros)


# --- curva de duración ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("escudo", "desestabilizacion", "aturdimiento"),
    [
        (1.0, 0.3, 0.15),
        (0.8, 1.65, 0.825),
        (0.6, 3.0, 1.5),
        (0.3, 6.5, 3.25),
        (0.0, 10.0, 5.0),
    ],
)
def test_rn51_duracion_segun_el_escudo(
    parametros: Parametros, escudo: float, desestabilizacion: float, aturdimiento: float
) -> None:
    """RN-51: al 100 % casi nada, al 60 % la de referencia y al 0 % la máxima."""
    duracion = parametros.duracion_efecto
    assert duracion(TipoEnemigo.DESESTABILIZADOR, escudo) == pytest.approx(desestabilizacion)
    assert duracion(TipoEnemigo.ATURDIDOR, escudo) == pytest.approx(aturdimiento)
    assert duracion(TipoEnemigo.SIN_EFECTO, escudo) == 0


def test_rn51_la_fraccion_se_limita_entre_0_y_1(parametros: Parametros) -> None:
    duracion = parametros.duracion_efecto
    assert duracion(TipoEnemigo.ATURDIDOR, 1.5) == duracion(TipoEnemigo.ATURDIDOR, 1.0)
    assert duracion(TipoEnemigo.ATURDIDOR, -1.0) == duracion(TipoEnemigo.ATURDIDOR, 0.0)


# --- desgaste ------------------------------------------------------------------------


def test_rn51_empieza_lleno(montaje: Montaje, parametros: Parametros) -> None:
    """RN-02, RN-51: la partida empieza con el escudo al máximo."""
    assert montaje.estacion.escudo == montaje.estacion.escudo_maximo
    assert montaje.estacion.escudo_maximo == parametros.jugador.escudo_maximo == 100


def test_rn51_cada_impacto_con_efecto_gasta_escudo(montaje: Montaje) -> None:
    """RN-51: la duración sale del escudo de antes del impacto; después se gastan 20."""
    for _ in range(6):
        montaje.impacto(TipoEnemigo.DESESTABILIZADOR)
    duraciones = [e.duracion for e in montaje.eventos if isinstance(e, DesestabilizacionIniciada)]
    assert duraciones == pytest.approx([0.3, 1.65, 3.0, 5 + 1 / 3, 7 + 2 / 3, 10.0])
    escudos = [e.actual for e in montaje.eventos if isinstance(e, EscudoCambiado)]
    assert escudos == [80, 60, 40, 20, 0]
    assert montaje.estacion.escudo == 0


def test_rn51_el_aturdidor_tambien_gasta_escudo(montaje: Montaje) -> None:
    montaje.impacto(TipoEnemigo.ATURDIDOR)
    montaje.impacto(TipoEnemigo.ATURDIDOR)
    duraciones = [e.duracion for e in montaje.eventos if isinstance(e, AturdimientoIniciado)]
    assert duraciones == pytest.approx([0.15, 0.825])
    assert montaje.estacion.escudo == 60


def test_rn51_sin_efecto_no_gasta_escudo(montaje: Montaje) -> None:
    """RN-51: los impactos sin efecto no tocan el escudo."""
    montaje.impacto(TipoEnemigo.SIN_EFECTO)
    assert montaje.estacion.escudo == 100
    assert montaje.eventos == []


# --- regeneración y expansión --------------------------------------------------------


def test_rn51_regenerar_sin_pasar_del_maximo(montaje: Montaje) -> None:
    """RN-51: la regeneración suma escudo sin superar el máximo."""
    for _ in range(4):
        montaje.impacto(TipoEnemigo.DESESTABILIZADOR)
    montaje.eventos.clear()
    montaje.publicar(RegeneracionEscudoAplicada(40))
    assert montaje.estacion.escudo == 60
    montaje.publicar(RegeneracionEscudoAplicada(40))
    assert montaje.estacion.escudo == 100
    assert montaje.eventos == [EscudoCambiado(60, 100), EscudoCambiado(100, 100)]


def test_rn51_la_mejora_expande_el_escudo(montaje: Montaje) -> None:
    """RN-51: cada nivel de escudo sube 20 el máximo y el actual."""
    montaje.impacto(TipoEnemigo.ATURDIDOR)
    montaje.eventos.clear()
    montaje.publicar(MejoraAplicada(Mejora.ESCUDO, 1), MejoraAplicada(Mejora.ESCUDO, 2))
    assert (montaje.estacion.escudo, montaje.estacion.escudo_maximo) == (120, 140)
    assert montaje.eventos == [EscudoCambiado(100, 120), EscudoCambiado(120, 140)]


def test_rn51_con_mas_escudo_aguanta_mas_impactos(montaje: Montaje) -> None:
    """RN-51: la duración depende del porcentaje sobre el máximo expandido."""
    montaje.publicar(MejoraAplicada(Mejora.ESCUDO, 5))
    assert montaje.estacion.escudo_maximo == 200
    for _ in range(4):
        montaje.impacto(TipoEnemigo.DESESTABILIZADOR)
    # 200 → 120: el cuarto impacto se calcula con 140 / 200 = 70 %.
    ultimo = [e for e in montaje.eventos if isinstance(e, DesestabilizacionIniciada)][-1]
    assert ultimo.duracion == pytest.approx(3 * (1 - 0.9 * 0.25))
    assert montaje.estacion.escudo == 120


def test_rn49_partida_nueva_reinicia_el_escudo(montaje: Montaje) -> None:
    """RN-49: una partida nueva empieza con el escudo base, lleno y sin mejoras."""
    montaje.publicar(MejoraAplicada(Mejora.ESCUDO, 3))
    montaje.impacto(TipoEnemigo.DESESTABILIZADOR)
    montaje.eventos.clear()
    montaje.publicar(PartidaIniciada(1))
    assert (montaje.estacion.escudo, montaje.estacion.escudo_maximo) == (100, 100)
    assert montaje.eventos == [EscudoCambiado(100, 100)]
