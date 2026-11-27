"""Ruido de valor en 3D y fractal, con numpy, para generar texturas por código.

Lo usan los cielos (`cielo.py`) y los planetas (`planetas.py`). Se calcula sobre
direcciones o puntos del espacio, así que las texturas de esferas no tienen costuras.
"""

from typing import Any

import numpy as np
from numpy.typing import NDArray

#: Campo de valores en coma flotante; se calculan en float32 para ir más rápido.
Campo = NDArray[np.floating[Any]]

#: Lado de la red de valores al azar del ruido. El ruido se repite cada 128 unidades,
#: más que el tamaño de la esfera en la octava más fina, así que no se nota.
_LADO_RED = 128
#: Red con una capa más en cada eje, copia de la primera: así los vecinos de un punto
#: se leen con desplazamientos fijos, sin dar la vuelta a los índices.
_LADO_COPIA = _LADO_RED + 1
_valores = np.random.default_rng(20261127).random((_LADO_RED,) * 3, dtype=np.float32)
_RED = np.pad(_valores, ((0, 1), (0, 1), (0, 1)), mode="wrap").ravel()
_VECINOS = [
    dx * _LADO_COPIA * _LADO_COPIA + dy * _LADO_COPIA + dz
    for dz in (0, 1)
    for dy in (0, 1)
    for dx in (0, 1)
]


def ruido(p: Campo, semilla: int) -> Campo:
    """Ruido de valor en 3D, suave, entre 0 y 1, en los puntos `p` de forma `(..., 3)`.

    Cada semilla desplaza los puntos dentro de la red, así que da otro dibujo.
    """
    desplazados = p + np.float32(semilla % 997) * np.asarray([17.31, 7.77, 29.13], np.float32)
    base = np.floor(desplazados)
    f = desplazados - base
    f = f * f * (3.0 - 2.0 * f)
    i = base.astype(np.int32) & np.int32(_LADO_RED - 1)
    indice = (i[..., 0] * _LADO_COPIA + i[..., 1]) * _LADO_COPIA + i[..., 2]
    fx, fy, fz = f[..., 0], f[..., 1], f[..., 2]
    v = [_RED.take(indice + desplazamiento) for desplazamiento in _VECINOS]
    # Interpolación en x, luego en y, luego en z.
    x0 = v[0] + (v[1] - v[0]) * fx
    x1 = v[2] + (v[3] - v[2]) * fx
    x2 = v[4] + (v[5] - v[4]) * fx
    x3 = v[6] + (v[7] - v[6]) * fx
    y0 = x0 + (x1 - x0) * fy
    y1 = x2 + (x3 - x2) * fy
    resultado: Campo = y0 + (y1 - y0) * fz
    return resultado


def fractal(p: Campo, semilla: int, octavas: int = 4) -> Campo:
    """Suma de octavas de ruido, normalizada entre 0 y 1."""
    total = np.zeros(p.shape[:-1], dtype=np.float32)
    amplitud, peso = 1.0, 0.0
    for octava in range(octavas):
        total += np.float32(amplitud) * ruido(p * np.float32(2.0**octava), semilla + 101 * octava)
        peso += amplitud
        amplitud *= 0.5
    return total / np.float32(peso)


def suave(x: Campo, a: float, b: float) -> Campo:
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return (t * t * (3.0 - 2.0 * t)).astype(np.float32)
