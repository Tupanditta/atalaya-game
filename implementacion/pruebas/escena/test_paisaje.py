"""Pruebas del paisaje de cada fondo: planetas, asteroides y polvo (RN-20).

Construyen los nodos sin ventana.
"""

import math

import numpy as np
import pytest
from panda3d.core import NodePath, Texture, Vec3

from atalaya.logica.parametros import Parametros
from atalaya.presentacion.escena import fondo, planetas
from atalaya.presentacion.escena.efectos import textura_brillo
from atalaya.presentacion.escena.paisaje import DISTANCIA_PLANETAS, Paisaje

DIVISOR = 16


@pytest.fixture(scope="module")
def texturas() -> dict[int, list[tuple[Texture, Texture | None]]]:
    resultado = {}
    for indice in range(1, 6):
        resultado[indice] = [
            (fondo.textura_planeta(c), None if e is None else fondo.textura_planeta(e))
            for c, e in planetas.generar_texturas(indice, DIVISOR)
        ]
    return resultado


def test_un_paisaje_por_fondo() -> None:
    assert len(planetas.PAISAJES) == 5
    # Cada fondo tiene algo además del cielo: planetas o asteroides.
    for paisaje in planetas.PAISAJES:
        assert paisaje.planetas or paisaje.asteroides


def test_texturas_de_planetas(texturas: object) -> None:
    """Mapas de latitud y longitud del doble de ancho que de alto; los volcánicos brillan."""
    for paisaje in planetas.PAISAJES:
        for planeta in paisaje.planetas:
            color, emisivo = planetas.texturas_planeta(planeta, DIVISOR)
            ancho = planetas.ancho_textura(planeta, DIVISOR)
            assert color.shape == (ancho // 2, ancho, 3)
            assert color.dtype == np.uint8
            volcanico = planeta.superficie is planetas.Superficie.VOLCANICO
            assert (emisivo is not None) == volcanico


def test_texturas_sin_costura_en_el_meridiano() -> None:
    """La primera y la última columna del mapa son vecinas: casi del mismo color."""
    planeta = planetas.PAISAJES[3].planetas[0]
    color, _ = planetas.texturas_planeta(planeta, 4)
    diferencia = np.abs(color[:, 0].astype(int) - color[:, -1].astype(int)).mean()
    assert diferencia < 12


def test_decorado_mas_alla_del_radar(parametros: Parametros) -> None:
    """Planetas y asteroides quedan detrás de enemigos y proyectiles: nunca los tapan."""
    alcance = parametros.ataques.alcance_radar
    for paisaje in planetas.PAISAJES:
        for planeta in paisaje.planetas:
            radio = DISTANCIA_PLANETAS * math.tan(math.radians(planeta.tamano))
            extremo = radio * (planeta.anillos[2] if planeta.anillos else 1.0)
            assert DISTANCIA_PLANETAS - extremo > alcance
            # Y dentro del plano lejano de la cámara (9000 u).
            assert DISTANCIA_PLANETAS + extremo < 9000
        if paisaje.asteroides is not None:
            assert paisaje.asteroides.distancia[0] * 0.85 > alcance


def test_preparar_y_mostrar(texturas: dict[int, list[tuple[Texture, Texture | None]]]) -> None:
    """Un paisaje preparado queda oculto; al mostrarlo, oculta el anterior."""
    raiz = NodePath("espacio")
    paisaje = Paisaje(raiz, textura_brillo(8))
    paisaje.mostrar(1, texturas[1])
    paisaje.preparar(3, texturas[3])
    assert paisaje.preparado(3)
    visibles = [n.get_name() for n in raiz.find("paisaje").get_children()]
    assert "paisaje-1" in visibles
    assert "paisaje-3" not in visibles
    paisaje.mostrar(3, texturas[3])
    visibles = [n.get_name() for n in raiz.find("paisaje").get_children()]
    assert visibles.count("paisaje-3") == 1
    assert "paisaje-1" not in visibles
    assert paisaje.actual == 3


def test_cada_planeta_con_su_textura(
    texturas: dict[int, list[tuple[Texture, Texture | None]]],
) -> None:
    """La esfera es compartida, pero cada planeta muestra su propia textura."""
    raiz = NodePath("espacio")
    paisaje = Paisaje(raiz, textura_brillo(8))
    paisaje.mostrar(4, texturas[4])
    superficies = raiz.find_all_matches("**/superficie")
    assert superficies.get_num_paths() == 3
    usadas = [superficies.get_path(i).get_texture() for i in range(3)]
    assert usadas == [color for color, _ in texturas[4]]


def test_todos_los_paisajes_se_animan(
    texturas: dict[int, list[tuple[Texture, Texture | None]]],
) -> None:
    raiz = NodePath("espacio")
    paisaje = Paisaje(raiz, textura_brillo(8))
    for indice in range(1, 6):
        paisaje.mostrar(indice, texturas[indice])
        antes = [n.get_hpr() for n in raiz.find_all_matches("**/giro")]
        for _ in range(60):
            paisaje.avanzar(1 / 60)
        despues = [n.get_hpr() for n in raiz.find_all_matches("**/giro")]
        assert all(a != d for a, d in zip(antes, despues, strict=True))


def test_luz_hacia_la_estacion(texturas: dict[int, list[tuple[Texture, Texture | None]]]) -> None:
    """El sol del paisaje alumbra desde la dirección del sol del cielo hacia la estación."""
    raiz = NodePath("espacio")
    paisaje = Paisaje(raiz, textura_brillo(8))
    paisaje.mostrar(3, texturas[3])
    sol = raiz.find("**/sol-paisaje")
    hacia = raiz.get_relative_vector(sol, Vec3(0, 1, 0))
    esperado = -Vec3(*planetas.PAISAJES[2].luz_direccion).normalized()
    assert (hacia - esperado).length() < 1e-4
