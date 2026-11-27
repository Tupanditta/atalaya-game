"""Pruebas de carga y validación de parámetros (Sprint 0)."""

import dataclasses
import json
from pathlib import Path
from typing import Any

import pytest

from atalaya.logica.nucleo.dominio import Mejora, Tamano, TipoEnemigo
from atalaya.logica.parametros import ErrorParametros, Parametros, cargar, desde_datos


def test_s0_t09_carga_y_solo_lectura(parametros: Parametros) -> None:
    """S0-T09 parametros, carga: carga sin errores y los grupos son de solo lectura."""
    assert parametros.jugador.coste_disparo == 10
    with pytest.raises(dataclasses.FrozenInstanceError):
        parametros.jugador.coste_disparo = 0  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        parametros.tamanos.pequeno.vida = 1  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        parametros.jugador = parametros.jugador  # type: ignore[misc]


def test_consulta_por_tamano_tipo_y_mejora(parametros: Parametros) -> None:
    """Los grupos por tamaño, tipo y mejora se consultan con el vocabulario del dominio."""
    assert parametros.tamanos.de(Tamano.GRANDE) is parametros.tamanos.grande
    assert parametros.tipos.de(TipoEnemigo.ATURDIDOR).recarga == 2
    assert parametros.mejoras.de(Mejora.GENERADOR).efecto == 1


def test_s0_t10_valor_ausente(datos_parametros: dict[str, Any]) -> None:
    """S0-T10 parametros, valor ausente: el error nombra el valor que falta."""
    del datos_parametros["jugador"]["coste_disparo"]
    with pytest.raises(ErrorParametros, match=r"jugador\.coste_disparo"):
        desde_datos(datos_parametros)


def test_s0_t11_valor_numerico_como_texto(datos_parametros: dict[str, Any]) -> None:
    """S0-T11 parametros, tipo: un valor numérico escrito como texto da un error que lo nombra."""
    datos_parametros["ataques"]["velocidad_proyectil"] = "300"
    with pytest.raises(ErrorParametros, match=r"ataques\.velocidad_proyectil"):
        desde_datos(datos_parametros)


@pytest.mark.parametrize(
    ("grupo", "clave", "valor", "relacion"),
    [
        ("ataques", "distancia_minima", 800, "ataques.distancia_minima < ataques.alcance_disparo"),
        (
            "ataques",
            "distancia_pasada_minima",
            20,
            "ataques.distancia_minima < ataques.distancia_pasada_minima",
        ),
        (
            "ataques",
            "distancia_pasada_maxima",
            35,
            "ataques.distancia_pasada_minima <= ataques.distancia_pasada_maxima",
        ),
        (
            "ataques",
            "distancia_pasada_maxima",
            750,
            "ataques.distancia_pasada_maxima < ataques.alcance_disparo",
        ),
        (
            "ataques",
            "alcance_disparo",
            1000,
            "ataques.alcance_disparo < ataques.distancia_maxima",
        ),
        ("ataques", "distancia_maxima", 1200, "ataques.distancia_maxima < ataques.alcance_radar"),
        ("jugador", "mira_minima", 3, "jugador.mira_minima < jugador.mira_normal"),
        ("jugador", "escudo_maximo", 0, "jugador.escudo_maximo > 0"),
        ("jugador", "umbral_escudo", 0, "0 < jugador.umbral_escudo < 100"),
        ("jugador", "umbral_escudo", 100, "0 < jugador.umbral_escudo < 100"),
        ("jugador", "factor_minimo_escudo", 1.5, "jugador.factor_minimo_escudo <= 1"),
    ],
)
def test_s0_t12_relaciones(
    datos_parametros: dict[str, Any], grupo: str, clave: str, valor: float, relacion: str
) -> None:
    """S0-T12 parametros, relaciones: cada relación incumplida da un error que la nombra."""
    datos_parametros[grupo][clave] = valor
    with pytest.raises(ErrorParametros) as error:
        desde_datos(datos_parametros)
    assert relacion in str(error.value)


def test_rn51_duracion_maxima_no_menor_que_la_de_referencia(
    datos_parametros: dict[str, Any],
) -> None:
    """RN-51: con el escudo vacío, un efecto no puede durar menos que en el umbral."""
    datos_parametros["tipos"]["aturdidor"]["duracion_efecto_maxima"] = 1
    with pytest.raises(ErrorParametros) as error:
        desde_datos(datos_parametros)
    assert "tipos.*.duracion_efecto <= tipos.*.duracion_efecto_maxima" in str(error.value)


@pytest.mark.parametrize(
    ("ruta", "valor", "mensaje"),
    [
        (("jugador", "energia_maxima"), True, r"jugador\.energia_maxima"),
        (("jugador", "energia_maxima"), -1, r"jugador\.energia_maxima.*negativo"),
        (("ataques", "enemigos_activos_maximos"), 6.5, r"ataques\.enemigos_activos_maximos"),
        (("tamanos", "pequeno"), 10, r"tamanos\.pequeno"),
        (("version",), 99, r"version"),
        (("version",), "1", r"version"),
    ],
)
def test_valores_invalidos(
    datos_parametros: dict[str, Any], ruta: tuple[str, ...], valor: object, mensaje: str
) -> None:
    """Booleanos, negativos, decimales en enteros, grupos mal formados y versiones desconocidas."""
    destino = datos_parametros
    for clave in ruta[:-1]:
        destino = destino[clave]
    destino[ruta[-1]] = valor
    with pytest.raises(ErrorParametros, match=mensaje):
        desde_datos(datos_parametros)


def test_valor_desconocido(datos_parametros: dict[str, Any]) -> None:
    """Una clave que no existe se rechaza, para detectar erratas en el archivo."""
    datos_parametros["jugador"]["coste_dispar"] = 10
    with pytest.raises(ErrorParametros, match=r"jugador\.coste_dispar"):
        desde_datos(datos_parametros)


def test_archivo_ausente(tmp_path: Path) -> None:
    """Si el archivo falta, el error indica la ruta."""
    ruta = tmp_path / "no_existe.json"
    with pytest.raises(ErrorParametros, match=r"no_existe\.json"):
        cargar(ruta)


def test_archivo_no_json(tmp_path: Path) -> None:
    """Si el archivo no es JSON válido, se indica."""
    ruta = tmp_path / "roto.json"
    ruta.write_text("{ esto no es json", encoding="utf-8")
    with pytest.raises(ErrorParametros, match="JSON"):
        cargar(ruta)


def test_raiz_no_objeto(tmp_path: Path) -> None:
    """La raíz del archivo debe ser un objeto."""
    ruta = tmp_path / "lista.json"
    ruta.write_text(json.dumps([1, 2]), encoding="utf-8")
    with pytest.raises(ErrorParametros, match="objeto"):
        cargar(ruta)
