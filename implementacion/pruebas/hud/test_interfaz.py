"""Pruebas de la mejora de la interfaz (F6): encendido, cartel, marcas, capa holográfica.

Construyen nodos sin ventana.
"""

import math

import pytest
from panda3d.core import NodePath

from atalaya.logica.parametros import Parametros
from atalaya.presentacion.hud import dibujo
from atalaya.presentacion.hud.cartel import DURACION, CartelOleada
from atalaya.presentacion.hud.componentes import parpadeo_encendido
from atalaya.presentacion.hud.holograma import PERIODO_FRANJA, RECORRIDO_FRANJA, Holograma
from atalaya.presentacion.hud.hud import textos_cartel
from atalaya.presentacion.hud.mira import DURACION_MARCA, Mira


def test_parpadeo_de_encendido() -> None:
    """Parpadea en las primeras décimas y luego queda encendida del todo."""
    valores = [parpadeo_encendido(i / 100) for i in range(20)]
    assert min(valores) < 0.5
    assert len(set(valores)) > 2
    assert parpadeo_encendido(0.2) == 1.0
    assert parpadeo_encendido(5.0) == 1.0


def test_textos_del_cartel(parametros: Parametros) -> None:
    """El sector al llegar a un fondo nuevo; si no, los hostiles."""
    titulo, subtitulo = textos_cartel(parametros, 1, None)
    assert titulo == "OLEADA 1"
    assert subtitulo == "SECTOR 1 · BORDE EXTERIOR"
    assert textos_cartel(parametros, 2, 1)[1] == "4 HOSTILES DETECTADOS"
    assert textos_cartel(parametros, 11, 1)[1] == "SECTOR 2 · NEBULOSA CARMESÍ"


def test_cartel_aparece_y_se_va() -> None:
    raiz = NodePath("hud")
    cartel = CartelOleada(raiz, None, None)
    nodo = raiz.find("**/cartel-oleada")
    cartel.dibujar(1 / 60, True)
    assert nodo.is_hidden()
    cartel.mostrar("OLEADA 3", "5 HOSTILES DETECTADOS")
    cartel.dibujar(1 / 60, True)
    assert not nodo.is_hidden()
    # En pausa o en un menú no se ve, aunque siga su tiempo.
    cartel.dibujar(1 / 60, False)
    assert nodo.is_hidden()
    for _ in range(round(DURACION * 60) + 1):
        cartel.dibujar(1 / 60, True)
    assert nodo.is_hidden()
    assert not cartel.visible


def test_marcas_de_acierto() -> None:
    """La marca de una baja dura más que la de un impacto y no se tapa con este."""
    raiz = NodePath("hud")
    mira = Mira(raiz)
    mira.dibujar(20.0, 0.0, False, (0.0, 0.0), True, 0.0)
    mira.marcar(True)
    mira.marcar(False)
    marca = raiz.find("**/marca")
    assert not marca.is_empty()
    for _ in range(round(DURACION_MARCA[0] * 60) + 2):
        mira.dibujar(20.0, 0.0, False, (0.0, 0.0), True, 1 / 60)
    assert not raiz.find("**/marca").is_empty()
    for _ in range(round(DURACION_MARCA[1] * 60) + 2):
        mira.dibujar(20.0, 0.0, False, (0.0, 0.0), True, 1 / 60)
    assert raiz.find("**/marca").is_empty()


def test_franja_holografica_recorre_la_pantalla() -> None:
    render2d = NodePath("render2d")
    holograma = Holograma(render2d)
    franja = render2d.find("franja")
    alturas = []
    for _ in range(round(RECORRIDO_FRANJA * 60) - 1):
        holograma.dibujar(1 / 60, 1080)
        alturas.append(franja.get_z())
    assert alturas[0] > 1 > -1 > alturas[-1]
    assert alturas == sorted(alturas, reverse=True)
    for _ in range(round((PERIODO_FRANJA - RECORRIDO_FRANJA) * 60) - 30):
        holograma.dibujar(1 / 60, 1080)
    assert franja.is_hidden()


def test_flechas_con_fuente_de_simbolos() -> None:
    """Las flechas van marcadas para la fuente de símbolos; el resto, no."""
    assert dibujo._tramos("↑↓  Navegar") == [("↑↓", True), ("  Navegar", False)]
    assert dibujo.con_simbolos("Pausa") == "Pausa"


@pytest.mark.parametrize("texto", ["SECTOR 1 · BORDE EXTERIOR", "OLEADA 12"])
def test_ancho_de_texto_sin_simbolos(texto: str) -> None:
    assert dibujo.ancho_texto(None, texto, 10) > 0
    assert math.isfinite(dibujo.ancho_texto(None, texto, 10))
