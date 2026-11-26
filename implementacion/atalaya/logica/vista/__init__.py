"""Módulo vista: orientación de la cámara, giro, zoom y desvío por temblor.

Ver `software/modulos/vista.md`.
"""

from atalaya.logica.vista.cuaternion import Cuaternion, angulo_entre, interpolar
from atalaya.logica.vista.vista import ADELANTE, ARRIBA, DERECHA, Vista, eje_de_flechas

__all__ = [
    "ADELANTE",
    "ARRIBA",
    "DERECHA",
    "Cuaternion",
    "Vista",
    "angulo_entre",
    "eje_de_flechas",
    "interpolar",
]
