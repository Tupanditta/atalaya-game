"""Pruebas del paisaje de cada fondo: planetas, asteroides y polvo (RN-20).

Construyen los nodos sin ventana.
"""

import math

import numpy as np
import pytest
from panda3d.core import NodePath, Shader, Vec3

from atalaya.logica.parametros import Parametros
from atalaya.presentacion.escena import fondo, planetas
from atalaya.presentacion.escena.efectos import textura_brillo
from atalaya.presentacion.escena.paisaje import (
    DISTANCIA_PLANETAS,
    Paisaje,
    TexturasMotor,
    forma_roca,
)
from atalaya.presentacion.escena.sombreado import PROGRAMAS, Sombreado

DIVISOR = 16


class _SombreadoFalso(Sombreado):
    """Devuelve los programas sin compilar: basta para ver qué nodos los llevan."""

    def __init__(self) -> None:
        super().__init__(None)

    def programa(self, nombre: str) -> Shader | None:
        vertice, fragmento = PROGRAMAS[nombre]
        return Shader.make(Shader.SL_GLSL, vertice, fragmento)


@pytest.fixture(scope="module")
def texturas() -> dict[int, list[TexturasMotor]]:
    return {
        indice: [fondo.texturas_motor(t) for t in planetas.generar_texturas(indice, DIVISOR)]
        for indice in range(1, 6)
    }


def test_un_paisaje_por_fondo() -> None:
    assert len(planetas.PAISAJES) == 5
    # Cada fondo tiene algo además del cielo: planetas o asteroides.
    for paisaje in planetas.PAISAJES:
        assert paisaje.planetas or paisaje.asteroides


def test_texturas_de_planetas(texturas: object) -> None:
    """Mapas de latitud y longitud del doble de ancho que de alto; los volcánicos brillan."""
    for paisaje in planetas.PAISAJES:
        for planeta in paisaje.planetas:
            color, emisivo, nubes = planetas.texturas_planeta(planeta, DIVISOR)
            ancho = planetas.ancho_textura(planeta, DIVISOR)
            assert color.shape == (ancho // 2, ancho, 4)
            assert color.dtype == np.uint8
            volcanico = planeta.superficie is planetas.Superficie.VOLCANICO
            assert (emisivo is not None) == volcanico
            assert (nubes is not None) == (planeta.nubes > 0)
            if nubes is not None:
                assert nubes.shape == (ancho // 4, ancho // 2)


def test_relieve_en_el_alfa() -> None:
    """La altura ocupa casi todo el rango; el gigante gaseoso no tiene relieve."""
    for paisaje in planetas.PAISAJES:
        for planeta in paisaje.planetas:
            alfa = planetas.texturas_planeta(planeta, 8)[0][..., 3]
            if planeta.superficie is planetas.Superficie.GASEOSO:
                assert int(alfa.max()) - int(alfa.min()) <= 1
            else:
                assert int(alfa.max()) - int(alfa.min()) > 200


def test_nubes_con_la_cobertura_pedida() -> None:
    """La parte cubierta de nubes se acerca a `Planeta.nubes`; ningún gaseoso tiene."""
    for paisaje in planetas.PAISAJES:
        for planeta in paisaje.planetas:
            if planeta.superficie is planetas.Superficie.GASEOSO:
                assert planeta.nubes == 0
            if planeta.nubes > 0:
                nubes = planetas.textura_nubes(planeta, 128)
                cubierta = float((nubes > 0).mean())
                assert abs(cubierta - planeta.nubes) < 0.05


def test_texturas_sin_costura_en_el_meridiano() -> None:
    """La primera y la última columna del mapa son vecinas: casi del mismo color."""
    planeta = planetas.PAISAJES[3].planetas[0]
    color, _, _ = planetas.texturas_planeta(planeta, 4)
    diferencia = np.abs(color[:, 0].astype(int) - color[:, -1].astype(int)).mean()
    assert diferencia < 12
    # Las nubes tienen bordes nítidos: la costura no cambia más que dos columnas vecinas.
    nubes = planetas.textura_nubes(planetas.PAISAJES[1].planetas[0], 256).astype(int)
    vecinas = np.abs(np.diff(nubes, axis=1)).mean()
    assert np.abs(nubes[:, 0] - nubes[:, -1]).mean() < 2 * vecinas


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


def test_preparar_y_mostrar(texturas: dict[int, list[TexturasMotor]]) -> None:
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
    texturas: dict[int, list[TexturasMotor]],
) -> None:
    """La esfera es compartida, pero cada planeta muestra su propia textura."""
    raiz = NodePath("espacio")
    paisaje = Paisaje(raiz, textura_brillo(8))
    paisaje.mostrar(4, texturas[4])
    superficies = raiz.find_all_matches("**/superficie")
    assert superficies.get_num_paths() == 3
    usadas = [superficies.get_path(i).get_texture() for i in range(3)]
    assert usadas == [color for color, _, _ in texturas[4]]


def test_sin_shaders_el_aspecto_de_siempre(texturas: dict[int, list[TexturasMotor]]) -> None:
    """Sin GLSL: halo en tarjeta, segunda esfera de lava y ningún shader."""
    raiz = NodePath("espacio")
    Paisaje(raiz, textura_brillo(8), Sombreado(None)).mostrar(5, texturas[5])
    assert not raiz.find("**/lava").is_empty()
    assert raiz.find("**/atmosfera").node().get_num_geoms() == 1
    for nodo in raiz.find_all_matches("**/superficie"):
        assert nodo.get_shader() is None


def test_con_shaders(texturas: dict[int, list[TexturasMotor]]) -> None:
    """Cada superficie lleva el shader y su textura; atmósfera en esfera; sin lava aparte."""
    raiz = NodePath("espacio")
    paisaje = Paisaje(raiz, textura_brillo(8), _SombreadoFalso())
    for indice in range(1, 6):
        paisaje.mostrar(indice, texturas[indice])
        escena = raiz.find(f"**/paisaje-{indice}")
        assert escena.find("**/lava").is_empty()
        superficies = escena.find_all_matches("**/superficie")
        for i, nodo in enumerate(superficies):
            assert nodo.get_shader() is not None
            assert nodo.get_shader_input("tex_color").get_texture() == texturas[indice][i][0]
        especificaciones = planetas.PAISAJES[indice - 1].planetas
        con_atmosfera = sum(p.atmosfera is not None for p in especificaciones)
        cascaras = escena.find_all_matches("**/atmosfera")
        assert cascaras.get_num_paths() == con_atmosfera
        for nodo in cascaras:
            assert nodo.get_shader() is not None
    # El paisaje 4 ya está guardado (oculto): se busca también entre lo oculto.
    anillos = raiz.find("**/paisaje-4;+s").find("**/anillos;+s")
    assert anillos.get_shader() is not None


def test_todos_los_paisajes_se_animan(
    texturas: dict[int, list[TexturasMotor]],
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


def test_luz_hacia_la_estacion(texturas: dict[int, list[TexturasMotor]]) -> None:
    """El sol del paisaje alumbra desde la dirección del sol del cielo hacia la estación."""
    raiz = NodePath("espacio")
    paisaje = Paisaje(raiz, textura_brillo(8))
    paisaje.mostrar(3, texturas[3])
    sol = raiz.find("**/sol-paisaje")
    hacia = raiz.get_relative_vector(sol, Vec3(0, 1, 0))
    esperado = -Vec3(*planetas.PAISAJES[2].luz_direccion).normalized()
    assert (hacia - esperado).length() < 1e-4


@pytest.mark.parametrize(("subdivisiones", "vertices"), [(2, 162), (3, 642)])
def test_forma_de_las_rocas(subdivisiones: int, vertices: int) -> None:
    """Malla cerrada, sin triángulos degenerados, normales suaves y hendiduras oscuras."""
    for semilla in range(8):
        forma = forma_roca(semilla, subdivisiones)
        assert forma.puntos.shape == (vertices, 3)
        assert forma.triangulos.shape == (20 * 4**subdivisiones, 3)
        assert np.allclose(np.linalg.norm(forma.normales, axis=1), 1.0, atol=1e-4)
        a, b, c = (forma.puntos[forma.triangulos[:, k]] for k in range(3))
        cruz = np.cross(b - a, c - a)
        assert (np.linalg.norm(cruz, axis=1) > 1e-6).all()
        # Casi todas las caras miran hacia fuera (un cráter hondo puede girar alguna).
        assert (np.einsum("ij,ij->i", cruz, a + b + c) > 0).mean() > 0.97
        gris = forma.colores[:, 0]
        assert gris.std() > 0.05
        assert gris.min() >= 0.3
        # Irregular, pero sin picos: ningún vértice se va muy lejos ni cae al centro.
        radios = np.linalg.norm(forma.puntos, axis=1)
        assert 0.3 < radios.min() < radios.max() < 2.0


def test_cinturon_en_pocas_geometrias(texturas: dict[int, list[TexturasMotor]]) -> None:
    """Cada grupo del cinturón queda en una sola geometría; las rocas llevan el shader."""
    raiz = NodePath("espacio")
    Paisaje(raiz, textura_brillo(8), _SombreadoFalso()).mostrar(2, texturas[2])
    grupos = raiz.find_all_matches("**/cinturon-*")
    assert grupos.get_num_paths() == 6
    for grupo in grupos:
        assert grupo.find_all_matches("**/+GeomNode").get_num_paths() == 1
    assert raiz.find("**/asteroides").get_shader() is not None
    cercanas = raiz.find_all_matches("**/roca-cercana")
    assert cercanas.get_num_paths() == planetas.PAISAJES[1].asteroides.cercanos  # type: ignore[union-attr]


def test_muestras_para_calentar_los_shaders() -> None:
    """Una pieza por shader del paisaje; sin shaders, ninguna."""
    assert Paisaje(NodePath("espacio"), textura_brillo(8), Sombreado(None)).muestras(Vec3()) == []
    sombreado = _SombreadoFalso()
    sombreado.activo = True
    raiz = NodePath("espacio")
    muestras = Paisaje(raiz, textura_brillo(8), sombreado).muestras(Vec3(0, 7000, 0))
    assert len(muestras) == 1
    piezas = muestras[0].find_all_matches("muestra-*")
    nombres = sorted(p.get_name() for p in piezas)
    assert nombres == ["muestra-anillos", "muestra-atmosfera", "muestra-planeta", "muestra-roca"]
    for pieza in piezas:
        assert pieza.get_shader() is not None
