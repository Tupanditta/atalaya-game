"""Clases de evento del catálogo de `modulos/README.md`.

El catálogo es el contrato entre módulos: un evento nuevo o un cambio en sus datos
se añade primero al catálogo. Todos los eventos son inmutables.
"""

from dataclasses import dataclass

from atalaya.logica.nucleo.bus import Evento
from atalaya.logica.nucleo.dominio import Entorno, Mejora, Tamano, TipoEnemigo, Vector3

# --- flujo ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PartidaIniciada(Evento):
    nivel: int


@dataclass(frozen=True, slots=True)
class PartidaAbandonada(Evento):
    pass


@dataclass(frozen=True, slots=True)
class PausaCambiada(Evento):
    activa: bool


@dataclass(frozen=True, slots=True)
class TerminarDescansoSolicitado(Evento):
    pass


# --- armamento -----------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ApuntadoCambiado(Evento):
    #: 0 = mira normal, 1 = mira mínima.
    progreso: float


@dataclass(frozen=True, slots=True)
class DisparoRealizado(Evento):
    origen: Vector3
    direccion: Vector3


@dataclass(frozen=True, slots=True)
class DisparoSinEnergia(Evento):
    pass


@dataclass(frozen=True, slots=True)
class EnergiaCambiada(Evento):
    actual: float
    maxima: float


# --- enemigos ------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EnemigoAparecido(Evento):
    id: int
    tipo: TipoEnemigo
    tamano: Tamano


@dataclass(frozen=True, slots=True)
class AvisoDisparo(Evento):
    id_enemigo: int


@dataclass(frozen=True, slots=True)
class ProyectilLanzado(Evento):
    id: int
    tipo_enemigo: TipoEnemigo


@dataclass(frozen=True, slots=True)
class ProyectilImpacta(Evento):
    tipo_enemigo: TipoEnemigo


@dataclass(frozen=True, slots=True)
class EnemigoAlcanzado(Evento):
    id: int
    vida_restante: float


@dataclass(frozen=True, slots=True)
class EnemigoDestruido(Evento):
    id: int
    posicion: Vector3


# --- estacion ------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EstacionDanada(Evento):
    cantidad: float
    integridad: float
    maxima: float


@dataclass(frozen=True, slots=True)
class IntegridadCambiada(Evento):
    actual: float
    maxima: float


@dataclass(frozen=True, slots=True)
class DesestabilizacionIniciada(Evento):
    duracion: float


@dataclass(frozen=True, slots=True)
class DesestabilizacionTerminada(Evento):
    pass


@dataclass(frozen=True, slots=True)
class AturdimientoIniciado(Evento):
    duracion: float


@dataclass(frozen=True, slots=True)
class AturdimientoTerminado(Evento):
    pass


@dataclass(frozen=True, slots=True)
class EstacionDestruida(Evento):
    oleadas_superadas: int


# --- oleadas -------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OleadaIniciada(Evento):
    numero: int
    entorno: Entorno


@dataclass(frozen=True, slots=True)
class SolicitudAparicion(Evento):
    tipo: TipoEnemigo
    tamano: Tamano
    vida: float


@dataclass(frozen=True, slots=True)
class OleadaSuperada(Evento):
    numero: int
    #: Segundos desde que aparece el primer enemigo hasta que se destruye el último.
    tiempo: float
    #: Número de enemigos de la oleada.
    enemigos: int


@dataclass(frozen=True, slots=True)
class DescansoIniciado(Evento):
    duracion: float
    siguiente_oleada: int


@dataclass(frozen=True, slots=True)
class DescansoTerminado(Evento):
    pass


@dataclass(frozen=True, slots=True)
class PartidaGanada(Evento):
    nivel: int


# --- mejoras -------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PuntosObtenidos(Evento):
    obtenidos: int
    disponibles: int
    tiempo: float
    tiempo_referencia: float


@dataclass(frozen=True, slots=True)
class ReparacionAplicada(Evento):
    cantidad: float


@dataclass(frozen=True, slots=True)
class MejoraAplicada(Evento):
    mejora: Mejora
    nivel: int


# --- entorno -------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FondoCambiado(Evento):
    #: Índice del fondo, de 1 a 10.
    indice: int


@dataclass(frozen=True, slots=True)
class EntornoCambiado(Evento):
    entorno: Entorno


@dataclass(frozen=True, slots=True)
class DestelloAviso(Evento):
    pass


@dataclass(frozen=True, slots=True)
class DestelloInicio(Evento):
    pass


@dataclass(frozen=True, slots=True)
class DestelloFin(Evento):
    pass


# --- historia ------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TransmisionDisponible(Evento):
    texto: str
