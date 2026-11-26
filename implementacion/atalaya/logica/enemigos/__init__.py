"""Módulo enemigos: enemigos, movimiento, ataques, proyectiles e impactos.

Ver `software/modulos/enemigos.md`.
"""

from atalaya.logica.enemigos.enemigos import (
    RADIO_ESTACION,
    Enemigos,
    EstadoEnemigo,
    EstadoProyectil,
    FaseAtaque,
    distancia_impacto,
)
from atalaya.logica.enemigos.movimiento import (
    elegir_destino,
    mover,
    posicion_aparicion,
    velocidad_llegada,
)

__all__ = [
    "RADIO_ESTACION",
    "Enemigos",
    "EstadoEnemigo",
    "EstadoProyectil",
    "FaseAtaque",
    "distancia_impacto",
    "elegir_destino",
    "mover",
    "posicion_aparicion",
    "velocidad_llegada",
]
