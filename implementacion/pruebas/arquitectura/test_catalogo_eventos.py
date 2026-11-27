"""S0-T21: las clases de evento coinciden con el catálogo de `modulos/README.md`."""

import dataclasses
import inspect
import re
from pathlib import Path

import pytest

from atalaya.logica.nucleo import Evento, eventos
from atalaya.logica.nucleo.dominio import Entorno, Mejora, Tamano, TipoEnemigo, Vector3

MODULOS_README = Path(__file__).resolve().parents[3] / "software" / "modulos" / "README.md"

#: Datos de cada evento según el catálogo, con su tipo. Una fila del catálogo con
#: dos eventos («Iniciada / Terminada») lleva la duración solo en el de inicio.
DATOS: dict[str, dict[str, object]] = {
    "PartidaIniciada": {"nivel": int},
    "PartidaAbandonada": {},
    "PausaCambiada": {"activa": bool},
    "ApuntadoCambiado": {"progreso": float},
    "DisparoRealizado": {"origen": Vector3, "direccion": Vector3},
    "DisparoSinEnergia": {},
    "EnergiaCambiada": {"actual": float, "maxima": float},
    "EnemigoAparecido": {"id": int, "tipo": TipoEnemigo, "tamano": Tamano},
    "AvisoDisparo": {"id_enemigo": int},
    "ProyectilLanzado": {"id": int, "tipo_enemigo": TipoEnemigo},
    "ProyectilImpacta": {"tipo_enemigo": TipoEnemigo},
    "EnemigoAlcanzado": {"id": int, "vida_restante": float},
    "EnemigoDestruido": {"id": int, "posicion": Vector3},
    "EstacionDanada": {"cantidad": float, "integridad": float, "maxima": float},
    "IntegridadCambiada": {"actual": float, "maxima": float},
    "EscudoCambiado": {"actual": float, "maxima": float},
    "DesestabilizacionIniciada": {"duracion": float},
    "DesestabilizacionTerminada": {},
    "AturdimientoIniciado": {"duracion": float},
    "AturdimientoTerminado": {},
    "EstacionDestruida": {"oleadas_superadas": int},
    "OleadaIniciada": {"numero": int, "entorno": Entorno},
    "SolicitudAparicion": {"tipo": TipoEnemigo, "tamano": Tamano, "vida": float},
    "OleadaSuperada": {"numero": int, "tiempo": float, "enemigos": int},
    "DescansoIniciado": {"duracion": float, "siguiente_oleada": int},
    "DescansoTerminado": {},
    "SaltoIniciado": {"fondo": int, "duracion": float},
    "SaltoTerminado": {},
    "TerminarDescansoSolicitado": {},
    "PartidaGanada": {"nivel": int},
    "PuntosObtenidos": {
        "obtenidos": int,
        "disponibles": int,
        "tiempo": float,
        "tiempo_referencia": float,
    },
    "ReparacionAplicada": {"cantidad": float},
    "RegeneracionEscudoAplicada": {"cantidad": float},
    "MejoraAplicada": {"mejora": Mejora, "nivel": int},
    "FondoCambiado": {"indice": int},
    "EntornoCambiado": {"entorno": Entorno},
    "DestelloAviso": {},
    "DestelloInicio": {},
    "DestelloFin": {},
    "TransmisionDisponible": {"texto": str},
}


def _catalogo() -> set[str]:
    texto = MODULOS_README.read_text(encoding="utf-8")
    seccion = texto.split("## Catálogo de eventos", 1)[1]
    nombres: set[str] = set()
    for linea in seccion.splitlines():
        coincidencia = re.match(r"^\| ([A-Z][\w /]*?) \|", linea)
        if coincidencia and coincidencia.group(1) != "Evento":
            nombres.update(n.strip() for n in coincidencia.group(1).split("/"))
    return nombres


def _clases() -> dict[str, type[Evento]]:
    return {
        nombre: clase
        for nombre, clase in inspect.getmembers(eventos, inspect.isclass)
        if issubclass(clase, Evento) and clase is not Evento
    }


def test_s0_t21_una_clase_por_evento() -> None:
    """S0-T21: existe una clase por evento del catálogo y ninguna más."""
    catalogo = _catalogo()
    assert len(catalogo) == 40
    assert set(_clases()) == catalogo
    assert set(DATOS) == catalogo


@pytest.mark.parametrize("nombre", sorted(DATOS))
def test_s0_t21_datos_del_evento(nombre: str) -> None:
    """S0-T21: cada clase tiene los datos del catálogo y es inmutable."""
    clase = _clases()[nombre]
    assert dataclasses.is_dataclass(clase)
    campos = {campo.name: campo.type for campo in dataclasses.fields(clase)}
    assert campos == DATOS[nombre]
    assert clase.__dataclass_params__.frozen  # type: ignore[attr-defined]
