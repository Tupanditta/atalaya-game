"""Módulo nucleo: bucle a paso fijo, reloj pausable, bus de eventos y azar con semilla.

Ver `software/modulos/nucleo.md`. El vocabulario del dominio (`dominio`) y las
clases de evento del catálogo (`eventos`) viven en este paquete para que todos
los módulos los compartan; el bucle, el bus y el azar no los usan.
"""

from atalaya.logica.nucleo.azar import Azar, semilla_nueva
from atalaya.logica.nucleo.bucle import MAX_PASOS, PASO, Actualizable, Etapa, Nucleo
from atalaya.logica.nucleo.bus import Bus, Evento

__all__ = [
    "MAX_PASOS",
    "PASO",
    "Actualizable",
    "Azar",
    "Bus",
    "Etapa",
    "Evento",
    "Nucleo",
    "semilla_nueva",
]
