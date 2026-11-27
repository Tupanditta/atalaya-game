"""Pruebas del contenido del manual (Sprint 6): sus cifras salen de `parametros` (CU-10).

Solo prueban el contenido, que se calcula sin ventana; el dibujo se revisa a mano
(S6-M03).
"""

from typing import Any

from atalaya.logica.nucleo.dominio import Tamano, TipoEnemigo
from atalaya.logica.parametros import Parametros, desde_datos
from atalaya.presentacion.hud.estilo import cifra
from atalaya.presentacion.hud.manual import (
    filas_controles,
    filas_mejoras,
    notas_controles,
    notas_enemigos,
    notas_tamanos,
    tarjetas_enemigos,
    tarjetas_tamanos,
    textos_entornos,
)


def _filas(tarjeta: Any) -> dict[str, str]:
    return dict(tarjeta.filas)


def test_cifra_con_coma_decimal() -> None:
    assert cifra(1.5) == "1,5"
    assert cifra(10.0) == "10"
    assert cifra(0.25) == "0,25"


def test_cu10_tipos_de_enemigo(parametros: Parametros) -> None:
    """CU-10: los tres tipos con su daño, recarga y efecto de los parámetros."""
    tarjetas = dict(tarjetas_enemigos(parametros))
    assert list(tarjetas) == list(TipoEnemigo)
    sin_efecto = _filas(tarjetas[TipoEnemigo.SIN_EFECTO])
    assert sin_efecto["Daño"] == "3"
    assert sin_efecto["Recarga"] == "1 s"
    assert sin_efecto["Efecto"] == "ninguno"
    aturdidor = _filas(tarjetas[TipoEnemigo.ATURDIDOR])
    assert aturdidor["Efecto"] == "no puedes girar ni\ndisparar 0,15 a 5 s"
    desestabilizador = _filas(tarjetas[TipoEnemigo.DESESTABILIZADOR])
    assert desestabilizador["Efecto"] == "pantalla y mira\ntiemblan 0,3 a 10 s"
    assert aturdidor["Aparece desde"] == "oleada 10"
    assert "0,3 s antes de disparar" in notas_enemigos(parametros)[0]
    assert "al 60 % duran 3 s y 1,5 s" in notas_enemigos(parametros)[2]


def test_cu10_a1_vida_segun_el_nivel(parametros: Parametros) -> None:
    """CU-10 A1: la vida de los tamaños es la del nivel indicado (RN-22)."""
    nivel_1 = dict(tarjetas_tamanos(parametros, 1))
    nivel_3 = dict(tarjetas_tamanos(parametros, 3))
    assert list(nivel_1) == list(Tamano)
    assert _filas(nivel_1[Tamano.PEQUENO])["Vida"] == "10"
    assert _filas(nivel_3[Tamano.PEQUENO])["Vida"] == "15"
    assert _filas(nivel_3[Tamano.GRANDE])["Vida"] == "60"
    assert _filas(nivel_1[Tamano.GRANDE])["Velocidad"] == "320 u/s"
    # El de zona de impacto más pequeña es el más difícil de acertar.
    assert _filas(nivel_1[Tamano.PEQUENO])["Para acertar"] == "difícil"
    assert _filas(nivel_1[Tamano.GRANDE])["Para acertar"] == "fácil"
    assert "nivel 3" in notas_tamanos(parametros, 3)[0]


def test_cu10_controles_entornos_y_mejoras(parametros: Parametros) -> None:
    """CU-10: controles, entornos y mejoras con sus cifras."""
    assert any("gasta 10 de energía" in accion for _, accion in filas_controles(parametros))
    assert "se recarga a 8 por segundo" in notas_controles(parametros)[0]
    niebla, destellos = textos_entornos(parametros)
    assert niebla[0] == "NIEBLA"
    assert any("250 u" in r for r in niebla[1])
    assert any("1,5 s" in r for r in destellos[1])
    reparar, blindaje, regenerar, escudo, *_ = filas_mejoras(parametros)
    assert reparar == ("REPARAR", "+20 integridad, sin pasar del máximo", "1 punto", "sin límite")
    assert blindaje == ("BLINDAJE", "+10 integridad máxima por nivel", "2 puntos", "10")
    assert regenerar == (
        "REGENERAR ESCUDO",
        "+40 escudo, sin pasar del máximo",
        "1 punto",
        "sin límite",
    )
    assert escudo == ("ESCUDO", "+20 escudo máximo por nivel", "2 puntos", "10")


def test_s6_m03_el_manual_sigue_a_los_parametros(datos_parametros: dict[str, Any]) -> None:
    """S6-M03 (parte automática): un valor cambiado en `parametros.json` se ve en el manual."""
    datos_parametros["tipos"]["aturdidor"]["dano"] = 7
    datos_parametros["tamanos"]["pequeno"]["vida"] = 12
    datos_parametros["mejoras"]["generador"]["coste"] = 3
    p = desde_datos(datos_parametros)
    assert _filas(dict(tarjetas_enemigos(p))[TipoEnemigo.ATURDIDOR])["Daño"] == "7"
    assert _filas(dict(tarjetas_tamanos(p, 1))[Tamano.PEQUENO])["Vida"] == "12"
    assert filas_mejoras(p)[-1][2] == "3 puntos"
