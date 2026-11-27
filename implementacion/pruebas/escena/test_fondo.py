"""Pruebas de los cinco cielos generados y de su caché (RN-20, RF-17)."""

from pathlib import Path

import numpy as np
import pytest
from panda3d.core import Texture

from atalaya.presentacion.escena import cielo, fondo, planetas

#: Lado pequeño para que las pruebas sean rápidas.
LADO = 64
#: Divide la resolución de las texturas de los planetas, también para ir rápido.
DIVISOR = 16


@pytest.fixture(scope="module")
def cielos() -> dict[int, cielo.Caras]:
    return {i: cielo.generar(i, LADO) for i in range(1, 6)}


def test_cinco_cielos_con_su_forma(cielos: dict[int, cielo.Caras]) -> None:
    """Hay un cielo por fondo, con seis caras RGB de 8 bits."""
    assert len(cielo.TEMAS) == fondo.FONDOS == 5
    for caras in cielos.values():
        assert caras.shape == (6, LADO, LADO, 3)
        assert caras.dtype == np.uint8


def test_cada_cielo_sale_siempre_igual(cielos: dict[int, cielo.Caras]) -> None:
    """Con la misma semilla, el mismo cielo: la caché no cambia lo que se ve."""
    assert np.array_equal(cielo.generar(3, LADO), cielos[3])


def test_los_cielos_son_distintos(cielos: dict[int, cielo.Caras]) -> None:
    """Cada fondo tiene su color medio propio."""
    medias = [tuple(np.round(c.reshape(-1, 3).mean(axis=0), 1)) for c in cielos.values()]
    assert len(set(medias)) == 5


def test_cielos_oscuros(cielos: dict[int, cielo.Caras]) -> None:
    """El fondo es oscuro: los enemigos y sus aristas luminosas se distinguen bien."""
    for caras in cielos.values():
        assert caras.mean() < 40


def test_cielo_que_no_existe() -> None:
    with pytest.raises(ValueError, match="no existe"):
        cielo.generar(6, LADO)


def test_nubes_sin_costuras_entre_caras() -> None:
    """Dos caras vecinas comparten los puntos de su borde: al ampliar no hay costura.

    El borde izquierdo de +x (s = −1) es el borde derecho de +z (s = 1).
    """
    nubes = cielo._campos_nubes(cielo.TEMAS[1], 32)
    assert np.allclose(nubes[0][:, 0], nubes[4][:, -1], atol=1e-5)


def test_proyeccion_de_opengl() -> None:
    """Cada dirección cae en la cara y el punto que da la tabla de mapas cúbicos de OpenGL.

    Para cada cara: (eje mayor, s, t) según la especificación de OpenGL.
    """
    tabla = {
        0: lambda x, y, z: (x, -z / x, -y / x),
        1: lambda x, y, z: (-x, z / -x, -y / -x),
        2: lambda x, y, z: (y, x / y, z / y),
        3: lambda x, y, z: (-y, x / -y, -z / -y),
        4: lambda x, y, z: (z, x / z, -y / z),
        5: lambda x, y, z: (-z, -x / -z, -y / -z),
    }
    direcciones = cielo._direcciones_al_azar(np.random.default_rng(2), 500)
    caras, s, t = cielo._proyectar(direcciones)
    for d, cara, si, ti in zip(direcciones, caras, s, t, strict=True):
        mayor, se, te = tabla[int(cara)](*d)
        assert mayor > 0
        assert (si, ti) == pytest.approx((se, te))


def test_direcciones_de_cada_pixel_inversas_de_la_proyeccion() -> None:
    """El centro de cada píxel vuelve a su cara, fila y columna al proyectarlo."""
    lado = 8
    for cara in range(6):
        d = cielo._direcciones_cara(cara, lado).reshape(-1, 3).astype(np.float64)
        caras, s, t = cielo._proyectar(d)
        assert set(caras.tolist()) == {cara}
        columnas = np.floor((s + 1) / 2 * lado).astype(int)
        filas = np.floor((t + 1) / 2 * lado).astype(int)
        assert columnas.tolist() == list(range(lado)) * lado
        assert filas.tolist() == [f for f in range(lado) for _ in range(lado)]


def test_textura_con_las_filas_de_opengl() -> None:
    """La textura guarda las filas tal cual, sin invertirlas, y los colores en BGR."""
    azar = np.random.default_rng(1)
    caras = azar.integers(0, 256, (6, 4, 4, 3), dtype=np.uint8)
    textura = fondo.textura_cielo(caras)
    assert textura.get_texture_type() == Texture.TT_cube_map
    assert bytes(textura.get_ram_image()) == caras[..., ::-1].tobytes()


def test_cache_de_cielos(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """La primera vez se genera y se guarda; la segunda se lee de la caché."""
    primera = fondo.cargar_caras(2, LADO, tmp_path)
    assert len(list(tmp_path.glob("*.npz"))) == 1
    assert list(tmp_path.glob("*.tmp")) == []

    def sin_generar(indice: int, lado: int) -> cielo.Caras:
        raise AssertionError("debería leerse de la caché")

    monkeypatch.setattr(cielo, "generar", sin_generar)
    assert np.array_equal(fondo.cargar_caras(2, LADO, tmp_path), primera)


def test_cache_estropeada(tmp_path: Path) -> None:
    """Un archivo de caché estropeado no impide jugar: el cielo se vuelve a generar."""
    ruta = tmp_path / f"cielo-1-v{cielo.VERSION}-{LADO}.npz"
    ruta.write_bytes(b"no es un archivo npz")
    assert np.array_equal(fondo.cargar_caras(1, LADO, tmp_path), cielo.generar(1, LADO))


def test_cache_sin_permiso_de_escritura(tmp_path: Path) -> None:
    """Si no se puede escribir la caché, el cielo se genera igual."""
    archivo = tmp_path / "ocupado"
    archivo.write_text("x")
    # Una carpeta de caché que es un archivo no se puede crear.
    caras = fondo.cargar_caras(1, LADO, archivo / "cielos")
    assert caras.shape == (6, LADO, LADO, 3)


def test_fondos_prepara_todo_en_segundo_plano(tmp_path: Path) -> None:
    """El fondo 1 está listo al crear `Fondos`; el resto llega desde el hilo."""
    fondos = fondo.Fondos(LADO, tmp_path, divisor_planetas=DIVISOR)
    assert fondos.esperar(60)
    for indice in range(1, 6):
        textura = fondos.textura(indice)
        assert textura.get_x_size() == LADO
        assert textura.get_texture_type() == Texture.TT_cube_map
    assert fondos.textura(2) is fondos.textura(2)
    with pytest.raises(ValueError, match="no existe"):
        fondos.textura(0)
    for indice in range(1, 6):
        texturas = fondos.texturas_planetas(indice)
        assert len(texturas) == len(planetas.PAISAJES[indice - 1].planetas)


def test_cache_de_planetas(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Las texturas de los planetas se guardan y se leen igual que el cielo."""
    for indice in (1, 4):
        primera = fondo.cargar_planetas(indice, tmp_path, DIVISOR)
        leidas = fondo.leer_planetas(indice, tmp_path, DIVISOR)
        assert leidas is not None
        for originales, guardadas in zip(primera, leidas, strict=True):
            for original, guardada in zip(originales, guardadas, strict=True):
                assert (original is None) == (guardada is None)
                if original is not None and guardada is not None:
                    assert np.array_equal(original, guardada)
    primera = fondo.cargar_planetas(4, tmp_path, DIVISOR)
    assert [e is not None for _, e, _ in primera] == [False, False, True]

    def sin_generar(indice: int, divisor: int) -> list[fondo.TexturasPlaneta]:
        raise AssertionError("debería leerse de la caché")

    monkeypatch.setattr(planetas, "generar_texturas", sin_generar)
    assert len(fondo.cargar_planetas(4, tmp_path, DIVISOR)) == 3


def test_cache_de_planetas_sin_altura_ni_nubes(tmp_path: Path) -> None:
    """Unas texturas RGB, como las de la versión 1, no se leen: se generan de nuevo."""
    ancho = planetas.ANCHO_GRANDE // DIVISOR
    antigua = tmp_path / f"planetas-1-v{planetas.VERSION}-{ancho}.npz"
    rgb = {f"color{i}": np.zeros((ancho // 2, ancho, 3), np.uint8) for i in range(2)}
    np.savez_compressed(antigua, **rgb)
    assert fondo.leer_planetas(1, tmp_path, DIVISOR) is None
    assert fondo.cargar_planetas(1, tmp_path, DIVISOR)[0][0].shape[-1] == 4


def test_fondos_sin_cache_disponible(tmp_path: Path) -> None:
    """Sin caché donde escribir, el proceso no deja nada y el hilo genera los fondos."""
    archivo = tmp_path / "ocupado"
    archivo.write_text("x")
    fondos = fondo.Fondos(LADO, archivo / "cielos", divisor_planetas=DIVISOR)
    assert fondos.esperar(120)
    assert fondos.textura(5).get_x_size() == LADO
