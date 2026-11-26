"""Utilidades comunes de las pruebas."""

import json
from typing import Any

import pytest

from atalaya.logica.parametros import Parametros, cargar, ruta_por_defecto


@pytest.fixture(scope="session")
def parametros() -> Parametros:
    """Parámetros del juego cargados de `datos/parametros.json`."""
    return cargar()


@pytest.fixture
def datos_parametros() -> dict[str, Any]:
    """Copia editable del contenido de `datos/parametros.json`."""
    datos: dict[str, Any] = json.loads(ruta_por_defecto().read_text(encoding="utf-8"))
    return datos
