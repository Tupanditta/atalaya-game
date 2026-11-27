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
    Maniobra,
    ha_sobrepasado,
    mover,
    posicion_aparicion,
    punto_pasada,
    punto_patrulla,
    ruta_retirada,
    velocidad_llegada,
    velocidad_paso,
)

__all__ = [
    "RADIO_ESTACION",
    "Enemigos",
    "EstadoEnemigo",
    "EstadoProyectil",
    "FaseAtaque",
    "Maniobra",
    "distancia_impacto",
    "ha_sobrepasado",
    "mover",
    "posicion_aparicion",
    "punto_pasada",
    "punto_patrulla",
    "ruta_retirada",
    "velocidad_llegada",
    "velocidad_paso",
]
