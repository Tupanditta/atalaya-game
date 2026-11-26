"""Módulo enemigos: enemigos, movimiento, ataques, proyectiles e impactos.

Ver `software/modulos/enemigos.md`.
"""

from atalaya.logica.enemigos.enemigos import Enemigos, EstadoEnemigo, distancia_impacto
from atalaya.logica.enemigos.movimiento import (
    elegir_destino,
    mover,
    posicion_aparicion,
    velocidad_llegada,
)

__all__ = [
    "Enemigos",
    "EstadoEnemigo",
    "distancia_impacto",
    "elegir_destino",
    "mover",
    "posicion_aparicion",
    "velocidad_llegada",
]
