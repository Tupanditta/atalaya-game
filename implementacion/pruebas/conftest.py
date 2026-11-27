"""Utilidades comunes de las pruebas."""

import dataclasses
import json
from typing import Any

import pytest

from atalaya.logica.parametros import Parametros, cargar, ruta_por_defecto


@pytest.fixture(scope="session")
def parametros() -> Parametros:
    """Parámetros del juego cargados de `datos/parametros.json`."""
    return cargar()


@pytest.fixture(scope="session")
def parametros_efectos_fijos() -> Parametros:
    """Parámetros en los que el escudo no cambia la duración de los efectos (RN-51).

    Los efectos duran siempre su duración de referencia, como antes del escudo, para
    probar su mecánica sin depender de lo lleno que esté.
    """
    parametros = cargar()
    jugador = dataclasses.replace(parametros.jugador, factor_minimo_escudo=1.0)
    tipos = parametros.tipos
    fijos = {
        nombre: dataclasses.replace(
            getattr(tipos, nombre), duracion_efecto_maxima=getattr(tipos, nombre).duracion_efecto
        )
        for nombre in ("sin_efecto", "desestabilizador", "aturdidor")
    }
    return dataclasses.replace(
        parametros, jugador=jugador, tipos=dataclasses.replace(tipos, **fijos)
    )


@pytest.fixture
def datos_parametros() -> dict[str, Any]:
    """Copia editable del contenido de `datos/parametros.json`."""
    datos: dict[str, Any] = json.loads(ruta_por_defecto().read_text(encoding="utf-8"))
    return datos
