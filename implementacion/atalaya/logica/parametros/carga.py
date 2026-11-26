"""Carga y validación del archivo de parámetros (`modulos/parametros.md`)."""

import dataclasses
import json
import math
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar, get_type_hints

from atalaya.logica.parametros.modelo import Parametros

#: Versión del formato de `parametros.json` que entiende este código.
VERSION = 1

T = TypeVar("T")


class ErrorParametros(Exception):
    """El archivo de parámetros falta o es incorrecto. Es un fallo de instalación."""


def ruta_por_defecto() -> Path:
    """Ruta de `datos/parametros.json`, junto al código del juego."""
    return Path(__file__).resolve().parents[3] / "datos" / "parametros.json"


def cargar(ruta: Path | None = None) -> Parametros:
    """Lee y valida el archivo de parámetros."""
    ruta = ruta_por_defecto() if ruta is None else ruta
    try:
        texto = ruta.read_text(encoding="utf-8")
    except OSError as error:
        raise ErrorParametros(
            f"No se puede leer el archivo de parámetros {ruta}: {error}"
        ) from error
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as error:
        raise ErrorParametros(
            f"El archivo de parámetros {ruta} no es JSON válido: {error}"
        ) from error
    return desde_datos(datos)


def desde_datos(datos: object) -> Parametros:
    """Valida el contenido ya leído del archivo de parámetros y construye los grupos."""
    if not isinstance(datos, dict):
        raise ErrorParametros("La raíz del archivo de parámetros debe ser un objeto")
    datos = dict(datos)
    version = datos.pop("version", None)
    if type(version) is not int or version != VERSION:
        raise ErrorParametros(f"El valor 'version' debe ser {VERSION}; se ha leído {version!r}")
    parametros = _construir(Parametros, datos, "")
    _comprobar_relaciones(parametros)
    return parametros


def _construir(clase: type[T], datos: object, ruta: str) -> T:
    if not isinstance(datos, dict):
        raise ErrorParametros(f"El valor '{ruta}' debe ser un objeto")
    tipos = get_type_hints(clase)
    campos = [campo.name for campo in dataclasses.fields(clase)]  # type: ignore[arg-type]
    valores: dict[str, Any] = {}
    for nombre in campos:
        completo = f"{ruta}.{nombre}" if ruta else nombre
        if nombre not in datos:
            raise ErrorParametros(f"Falta el valor '{completo}'")
        valores[nombre] = _convertir(tipos[nombre], datos[nombre], completo)
    for nombre in datos:
        if nombre not in campos:
            completo = f"{ruta}.{nombre}" if ruta else nombre
            raise ErrorParametros(f"Valor desconocido '{completo}'")
    return clase(**valores)


def _convertir(tipo: type, valor: object, ruta: str) -> object:
    if dataclasses.is_dataclass(tipo):
        return _construir(tipo, valor, ruta)
    if tipo is int:
        if type(valor) is not int:
            raise ErrorParametros(f"El valor '{ruta}' debe ser un número entero; es {valor!r}")
        numero: float = valor
    elif tipo is float:
        if type(valor) not in (int, float):
            raise ErrorParametros(f"El valor '{ruta}' debe ser un número; es {valor!r}")
        numero = float(valor)  # type: ignore[arg-type]
        if not math.isfinite(numero):
            raise ErrorParametros(f"El valor '{ruta}' debe ser un número finito; es {valor!r}")
    else:  # pragma: no cover - solo si se añade un campo de un tipo no previsto
        raise TypeError(f"Tipo de parámetro no previsto en '{ruta}': {tipo}")
    if numero < 0:
        raise ErrorParametros(f"El valor '{ruta}' no puede ser negativo; es {valor!r}")
    return numero


# Relaciones entre valores: (descripción, comprobación). La descripción nombra los valores.
_RELACIONES: list[tuple[str, Callable[[Parametros], bool]]] = [
    (
        "ataques.distancia_minima < ataques.alcance_disparo",
        lambda p: p.ataques.distancia_minima < p.ataques.alcance_disparo,
    ),
    (
        "ataques.alcance_disparo < ataques.distancia_maxima",
        lambda p: p.ataques.alcance_disparo < p.ataques.distancia_maxima,
    ),
    (
        "ataques.distancia_maxima < ataques.alcance_radar",
        lambda p: p.ataques.distancia_maxima < p.ataques.alcance_radar,
    ),
    (
        "ataques.distancia_aparicion_minima <= ataques.distancia_aparicion_maxima",
        lambda p: p.ataques.distancia_aparicion_minima <= p.ataques.distancia_aparicion_maxima,
    ),
    (
        "ataques.distancia_aparicion_maxima <= ataques.distancia_maxima",
        lambda p: p.ataques.distancia_aparicion_maxima <= p.ataques.distancia_maxima,
    ),
    (
        "ataques.distancia_minima < ataques.distancia_aparicion_minima",
        lambda p: p.ataques.distancia_minima < p.ataques.distancia_aparicion_minima,
    ),
    (
        "jugador.mira_minima < jugador.mira_normal",
        lambda p: p.jugador.mira_minima < p.jugador.mira_normal,
    ),
    (
        "jugador.campo_vision_zoom < jugador.campo_vision_normal",
        lambda p: p.jugador.campo_vision_zoom < p.jugador.campo_vision_normal,
    ),
    (
        "jugador.coste_disparo <= jugador.energia_maxima",
        lambda p: p.jugador.coste_disparo <= p.jugador.energia_maxima,
    ),
    (
        "entornos.niebla_visibilidad_completa < entornos.niebla_invisible",
        lambda p: p.entornos.niebla_visibilidad_completa < p.entornos.niebla_invisible,
    ),
    (
        "entornos.destellos_intervalo_minimo <= entornos.destellos_intervalo_maximo",
        lambda p: p.entornos.destellos_intervalo_minimo <= p.entornos.destellos_intervalo_maximo,
    ),
    (
        "0 < nivel.factor_descanso < 1",
        lambda p: 0 < p.nivel.factor_descanso < 1,
    ),
    (
        "oleadas.divisor_enemigos > 0",
        lambda p: p.oleadas.divisor_enemigos > 0,
    ),
    (
        "oleadas.divisor_efecto > 0",
        lambda p: p.oleadas.divisor_efecto > 0,
    ),
    (
        "entornos.intervalo_oleadas > 0",
        lambda p: p.entornos.intervalo_oleadas > 0,
    ),
]


def _comprobar_relaciones(parametros: Parametros) -> None:
    for descripcion, se_cumple in _RELACIONES:
        if not se_cumple(parametros):
            raise ErrorParametros(f"No se cumple la relación {descripcion}")
