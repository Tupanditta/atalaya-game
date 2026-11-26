"""Módulo entrada: teclado, ratón y acciones del jugador.

Ver `software/modulos/entrada.md`. El adaptador del motor (`panda.py`) no se importa
aquí, para que `Entrada` se pueda usar y probar sin Panda3D.
"""

from atalaya.presentacion.entrada.entrada import TECLAS, Entrada, FuenteRaton, FuenteTeclado

__all__ = ["TECLAS", "Entrada", "FuenteRaton", "FuenteTeclado"]
