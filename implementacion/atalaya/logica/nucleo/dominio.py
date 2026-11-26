"""Vocabulario común del dominio, usado por los eventos y por los parámetros.

Vive en el núcleo porque todos los módulos pueden usarlo sin crear dependencias
nuevas entre módulos (`modulos/README.md`, «Dependencias permitidas»).
"""

from enum import Enum

#: Vector en el espacio del mundo: (x, y, z), en unidades del mundo.
Vector3 = tuple[float, float, float]


class TipoEnemigo(Enum):
    """Tipo de enemigo según su efecto especial (`reglasNegocio.md`, «Enemigos por tipo»)."""

    SIN_EFECTO = "sin_efecto"
    DESESTABILIZADOR = "desestabilizador"
    ATURDIDOR = "aturdidor"


class Tamano(Enum):
    """Tamaño de un enemigo (RN-06)."""

    PEQUENO = "pequeno"
    MEDIANO = "mediano"
    GRANDE = "grande"


class Entorno(Enum):
    """Entorno de una oleada (RN-44)."""

    NINGUNO = "ninguno"
    NIEBLA = "niebla"
    DESTELLOS = "destellos"


class Mejora(Enum):
    """Mejoras de la estación (RN-47)."""

    BLINDAJE = "blindaje"
    BATERIA = "bateria"
    GENERADOR = "generador"
