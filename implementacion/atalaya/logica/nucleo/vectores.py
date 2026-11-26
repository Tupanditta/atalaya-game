"""Operaciones con vectores del espacio (`dominio.Vector3`).

Viven en el núcleo para que todos los módulos lógicos las compartan sin crear
dependencias nuevas entre ellos.
"""

import math

from atalaya.logica.nucleo.dominio import Vector3

CERO: Vector3 = (0.0, 0.0, 0.0)


def sumar(a: Vector3, b: Vector3) -> Vector3:
    """a + b."""
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def restar(a: Vector3, b: Vector3) -> Vector3:
    """a − b."""
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def escalar(v: Vector3, k: float) -> Vector3:
    """v × k."""
    return (v[0] * k, v[1] * k, v[2] * k)


def producto_escalar(a: Vector3, b: Vector3) -> float:
    """Producto escalar de `a` y `b`."""
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def producto_vectorial(a: Vector3, b: Vector3) -> Vector3:
    """Producto vectorial a × b."""
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def norma(v: Vector3) -> float:
    """Longitud de `v`."""
    return math.sqrt(producto_escalar(v, v))


def normalizar(v: Vector3) -> Vector3:
    """Vector de longitud 1 con la dirección de `v`. `v` no puede ser nulo."""
    n = norma(v)
    if n == 0:
        raise ValueError("No se puede normalizar el vector nulo")
    return (v[0] / n, v[1] / n, v[2] / n)


def limitar(v: Vector3, maximo: float) -> Vector3:
    """`v` con su longitud recortada a `maximo`, sin cambiar su dirección."""
    n = norma(v)
    if n <= maximo:
        return v
    return escalar(v, maximo / n)


def perpendiculares(d: Vector3) -> tuple[Vector3, Vector3]:
    """Dos vectores de longitud 1, perpendiculares entre sí y a `d` (de longitud 1)."""
    # Se parte del eje del mundo menos alineado con `d`, para evitar errores numéricos.
    auxiliar: Vector3 = (1.0, 0.0, 0.0) if abs(d[0]) < 0.9 else (0.0, 1.0, 0.0)
    e1 = normalizar(producto_vectorial(d, auxiliar))
    e2 = producto_vectorial(d, e1)
    return e1, e2


def girar_hacia(d: Vector3, angulo: float, azimut: float) -> Vector3:
    """Dirección que forma `angulo` grados con `d` (de longitud 1), en el azimut indicado.

    El azimut, en grados, elige hacia qué lado de `d` se separa la dirección.
    """
    e1, e2 = perpendiculares(d)
    a = math.radians(angulo)
    z = math.radians(azimut)
    lado = sumar(escalar(e1, math.cos(z)), escalar(e2, math.sin(z)))
    return normalizar(sumar(escalar(d, math.cos(a)), escalar(lado, math.sin(a))))


def angulo_entre(a: Vector3, b: Vector3) -> float:
    """Ángulo en grados entre dos vectores no nulos."""
    coseno = producto_escalar(a, b) / (norma(a) * norma(b))
    return math.degrees(math.acos(max(-1.0, min(1.0, coseno))))
