"""Cuaterniones de rotación para la orientación de la cámara (`design.md`, sección 5).

Convención de ejes del mundo y de la cámara, la misma que usa el motor gráfico:
x a la derecha, y hacia delante, z hacia arriba. Un cuaternión de orientación lleva
los ejes locales de la cámara a sus direcciones en el mundo.
"""

import math
from dataclasses import dataclass

from atalaya.logica.nucleo.dominio import Vector3

#: Por encima de este producto escalar, la interpolación esférica se aproxima con la lineal.
_CASI_IGUALES = 0.9995


@dataclass(frozen=True, slots=True)
class Cuaternion:
    """Cuaternión w + xi + yj + zk. Las rotaciones usan cuaterniones de norma 1."""

    w: float
    x: float
    y: float
    z: float

    @staticmethod
    def identidad() -> "Cuaternion":
        """Rotación nula."""
        return Cuaternion(1.0, 0.0, 0.0, 0.0)

    @staticmethod
    def rotacion(eje: Vector3, grados: float) -> "Cuaternion":
        """Rotación de `grados` alrededor de `eje` (de norma 1), con la regla de la mano derecha."""
        mitad = math.radians(grados) / 2
        seno = math.sin(mitad)
        return Cuaternion(math.cos(mitad), eje[0] * seno, eje[1] * seno, eje[2] * seno)

    def __mul__(self, otro: "Cuaternion") -> "Cuaternion":
        """Producto de Hamilton: `a * b` aplica primero `b` y después `a`."""
        a, b = self, otro
        return Cuaternion(
            a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
            a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
            a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
            a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w,
        )

    def producto_escalar(self, otro: "Cuaternion") -> float:
        """Producto escalar de los cuatro componentes."""
        return self.w * otro.w + self.x * otro.x + self.y * otro.y + self.z * otro.z

    def norma(self) -> float:
        """Norma del cuaternión."""
        return math.sqrt(self.producto_escalar(self))

    def normalizado(self) -> "Cuaternion":
        """Cuaternión con la misma dirección y norma 1."""
        n = self.norma()
        return Cuaternion(self.w / n, self.x / n, self.y / n, self.z / n)

    def conjugado(self) -> "Cuaternion":
        """Rotación inversa, si el cuaternión tiene norma 1."""
        return Cuaternion(self.w, -self.x, -self.y, -self.z)

    def rotar(self, v: Vector3) -> Vector3:
        """Aplica la rotación al vector `v`."""
        p = self * Cuaternion(0.0, v[0], v[1], v[2]) * self.conjugado()
        return (p.x, p.y, p.z)


def angulo_entre(a: Cuaternion, b: Cuaternion) -> float:
    """Ángulo en grados de la rotación que lleva la orientación `a` a la `b`."""
    coseno = min(1.0, abs(a.producto_escalar(b)))
    return math.degrees(2 * math.acos(coseno))


def interpolar(a: Cuaternion, b: Cuaternion, t: float) -> Cuaternion:
    """Interpolación esférica de `a` (t = 0) a `b` (t = 1) por el camino más corto."""
    coseno = a.producto_escalar(b)
    if coseno < 0:
        b = Cuaternion(-b.w, -b.x, -b.y, -b.z)
        coseno = -coseno
    if coseno > _CASI_IGUALES:
        return Cuaternion(
            a.w + (b.w - a.w) * t,
            a.x + (b.x - a.x) * t,
            a.y + (b.y - a.y) * t,
            a.z + (b.z - a.z) * t,
        ).normalizado()
    theta = math.acos(coseno)
    seno = math.sin(theta)
    fa = math.sin((1 - t) * theta) / seno
    fb = math.sin(t * theta) / seno
    return Cuaternion(
        fa * a.w + fb * b.w,
        fa * a.x + fb * b.x,
        fa * a.y + fb * b.y,
        fa * a.z + fb * b.z,
    ).normalizado()
