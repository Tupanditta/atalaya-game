"""Pruebas de los valores derivados por nivel y por oleada (Sprint 0)."""

import pytest

from atalaya.logica.nucleo.dominio import Entorno, Tamano, TipoEnemigo
from atalaya.logica.parametros import Parametros


def test_s0_t13_rn22_vida(parametros: Parametros) -> None:
    """S0-T13 RN-22, vida: pequeño nivel 1 = 10; pequeño nivel 3 = 15; grande nivel 5 = 80."""
    assert parametros.vida_enemigo(Tamano.PEQUENO, 1) == pytest.approx(10)
    assert parametros.vida_enemigo(Tamano.PEQUENO, 3) == pytest.approx(15)
    assert parametros.vida_enemigo(Tamano.GRANDE, 5) == pytest.approx(80)


def test_s0_t14_rn18_rn22_descanso(parametros: Parametros) -> None:
    """S0-T14 RN-18, RN-22: descanso de 20 s, 17,75 s y 15,8375 s; baja y siempre supera 5 s."""
    assert parametros.duracion_descanso(1) == pytest.approx(20)
    assert parametros.duracion_descanso(2) == pytest.approx(17.75)
    assert parametros.duracion_descanso(3) == pytest.approx(15.8375)
    anterior = parametros.duracion_descanso(1)
    for nivel in range(2, 200):
        actual = parametros.duracion_descanso(nivel)
        assert 5 < actual < anterior
        anterior = actual


def test_s0_t15_rn16_composicion(parametros: Parametros) -> None:
    """S0-T15 RN-16: enemigos y tipos por oleada; el número nunca baja."""
    esperados = {1: 3, 2: 4, 5: 5, 10: 8, 50: 28}
    for numero, enemigos in esperados.items():
        assert parametros.composicion_oleada(numero).numero_enemigos == enemigos

    solo_sin_efecto = frozenset({TipoEnemigo.SIN_EFECTO})
    con_desestabilizadores = solo_sin_efecto | {TipoEnemigo.DESESTABILIZADOR}
    anterior = 0
    for numero in range(1, 51):
        composicion = parametros.composicion_oleada(numero)
        assert composicion.numero_enemigos >= anterior
        anterior = composicion.numero_enemigos
        if numero <= 4:
            assert composicion.tipos_permitidos == solo_sin_efecto
            assert composicion.maximo_con_efecto == 0
        else:
            if numero <= 9:
                assert composicion.tipos_permitidos == con_desestabilizadores
            else:
                assert composicion.tipos_permitidos == frozenset(TipoEnemigo)
            assert composicion.maximo_con_efecto == composicion.numero_enemigos // 3


@pytest.mark.parametrize(
    ("numero", "entorno"),
    [
        (1, Entorno.NINGUNO),
        (14, Entorno.NINGUNO),
        (15, Entorno.NIEBLA),
        (16, Entorno.NINGUNO),
        (18, Entorno.DESTELLOS),
        (21, Entorno.NIEBLA),
        (45, Entorno.NIEBLA),
        (48, Entorno.DESTELLOS),
        (50, Entorno.NINGUNO),
    ],
)
def test_s0_t16_rn44_entorno(parametros: Parametros, numero: int, entorno: Entorno) -> None:
    """S0-T16 RN-44: entorno por número de oleada."""
    assert parametros.entorno_oleada(numero) is entorno


@pytest.mark.parametrize("numero", [0, 51])
def test_oleada_fuera_de_rango(parametros: Parametros, numero: int) -> None:
    """Las oleadas van de 1 al número de oleadas de la partida."""
    with pytest.raises(ValueError, match="oleada"):
        parametros.composicion_oleada(numero)
    with pytest.raises(ValueError, match="oleada"):
        parametros.entorno_oleada(numero)


def test_nivel_fuera_de_rango(parametros: Parametros) -> None:
    """El nivel de dificultad empieza en 1."""
    with pytest.raises(ValueError, match="nivel"):
        parametros.vida_enemigo(Tamano.PEQUENO, 0)
    with pytest.raises(ValueError, match="nivel"):
        parametros.duracion_descanso(0)
