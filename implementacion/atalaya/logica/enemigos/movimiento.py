"""Movimiento con inercia de los enemigos y elección de destinos (RN-29 a RN-33, RN-42).

La estación está en el origen. Las funciones son puras salvo por el azar que reciben.
"""

import math

from atalaya.logica.nucleo.azar import Azar
from atalaya.logica.nucleo.dominio import Vector3
from atalaya.logica.nucleo.vectores import (
    CERO,
    escalar,
    girar_hacia,
    limitar,
    norma,
    normalizar,
    producto_escalar,
    restar,
    sumar,
)
from atalaya.logica.parametros.modelo import Ataques, DatosTamano

#: Separación angular, vista desde la estación, entre la posición y el nuevo destino.
#: Con un azimut al azar, los destinos cambian la dirección en horizontal y en vertical
#: (RN-29). Es un detalle del movimiento, no un valor de juego de `reglasNegocio.md`.
ANGULO_DESTINO_MINIMO = 10.0
ANGULO_DESTINO_MAXIMO = 40.0

#: Intentos para encontrar un destino más lejano que la distancia de llegada.
_INTENTOS_DESTINO = 20

#: Parte de la aceleración que se reserva para frenar ante los límites de distancia.
#: La otra parte cubre la tendencia a alejarse al moverse de lado (aceleración centrífuga).
_FRACCION_FRENADO = 0.5

#: Margen, en unidades, con el que la red de seguridad deja la posición dentro de la capa.
_MARGEN = 1e-6


def direccion_al_azar(azar: Azar) -> Vector3:
    """Dirección uniforme en la esfera."""
    z = azar.uniforme(-1.0, 1.0)
    angulo = azar.uniforme(0.0, 2 * math.pi)
    r = math.sqrt(max(0.0, 1 - z * z))
    return (r * math.cos(angulo), r * math.sin(angulo), z)


def posicion_aparicion(ataques: Ataques, azar: Azar) -> Vector3:
    """Punto de aparición: dirección al azar, a la distancia de aparición (RN-32)."""
    distancia = azar.uniforme(
        ataques.distancia_aparicion_minima, ataques.distancia_aparicion_maxima
    )
    return escalar(direccion_al_azar(azar), distancia)


def elegir_destino(posicion: Vector3, ataques: Ataques, azar: Azar) -> Vector3:
    """Nuevo destino cerca de la dirección actual, entre la distancia mínima y la máxima.

    Fuera del alcance de disparo, el destino queda dentro del alcance (RN-42).
    """
    distancia = norma(posicion)
    hasta = (
        ataques.alcance_disparo if distancia > ataques.alcance_disparo else ataques.distancia_maxima
    )
    radial = normalizar(posicion) if distancia > 0 else (0.0, 1.0, 0.0)
    destino = posicion
    for _ in range(_INTENTOS_DESTINO):
        direccion = girar_hacia(
            radial,
            azar.uniforme(ANGULO_DESTINO_MINIMO, ANGULO_DESTINO_MAXIMO),
            azar.uniforme(0.0, 360.0),
        )
        destino = escalar(direccion, azar.uniforme(ataques.distancia_minima, hasta))
        if norma(restar(destino, posicion)) > 2 * ataques.distancia_llegada:
            break
    return destino


def velocidad_llegada(posicion: Vector3, destino: Vector3, tamano: DatosTamano) -> Vector3:
    """Velocidad deseada hacia `destino`: la máxima, o menos para poder frenar a tiempo.

    Empieza a frenar cuando la distancia al destino es la que necesita para detenerse
    con su aceleración máxima (`reglasNegocio.md`, «Enemigos por tamaño»).
    """
    hacia = restar(destino, posicion)
    distancia = norma(hacia)
    if distancia == 0:
        return CERO
    rapidez = min(tamano.velocidad_maxima, math.sqrt(2 * tamano.aceleracion_maxima * distancia))
    return escalar(hacia, rapidez / distancia)


def _rapidez_segura(hueco: float, aceleracion: float, dt: float) -> float:
    """Rapidez máxima hacia un límite a `hueco` unidades que aún permite frenar antes.

    Es la solución de v² = 2·a·(hueco − v·dt): con ella, tras moverse un paso, el
    enemigo sigue pudiendo frenar con la aceleración `a` sin cruzar el límite.
    """
    ad = aceleracion * dt
    return -ad + math.sqrt(ad * ad + 2 * aceleracion * max(0.0, hueco))


def mover(
    posicion: Vector3,
    velocidad: Vector3,
    destino: Vector3,
    tamano: DatosTamano,
    ataques: Ataques,
    dt: float,
) -> tuple[Vector3, Vector3]:
    """Avanza un paso de persecución con inercia (RN-33) sin salir de la capa (RN-30, RN-31).

    El cambio de velocidad en un paso nunca supera la aceleración máxima × `dt`, y la
    velocidad nunca supera la máxima. Cerca de un límite de distancia, la velocidad
    radial se frena de forma gradual. Devuelve la nueva posición y la nueva velocidad.
    """
    a = tamano.aceleracion_maxima
    cambio_maximo = a * dt
    deseada = velocidad_llegada(posicion, destino, tamano)

    distancia = norma(posicion)
    radial = normalizar(posicion)
    frenado = a * _FRACCION_FRENADO
    hacia_dentro = _rapidez_segura(distancia - ataques.distancia_minima, frenado, dt)
    hacia_fuera = _rapidez_segura(ataques.distancia_maxima - distancia, frenado, dt)

    # La velocidad deseada respeta los límites radiales.
    deseada_radial = producto_escalar(deseada, radial)
    recortada = min(hacia_fuera, max(-hacia_dentro, deseada_radial))
    deseada = sumar(deseada, escalar(radial, recortada - deseada_radial))

    v_radial = producto_escalar(velocidad, radial)
    if -hacia_dentro <= v_radial <= hacia_fuera:
        cambio = limitar(restar(deseada, velocidad), cambio_maximo)
    else:
        # Fuera de los límites radiales, corregir la velocidad radial hacia la deseada, que
        # ya los respeta, tiene prioridad. Lo que sobra de aceleración se usa de lado,
        # perpendicular a la dirección radial.
        necesario = recortada - v_radial
        cambio_radial = max(-cambio_maximo, min(cambio_maximo, necesario))
        resto = math.sqrt(max(0.0, cambio_maximo**2 - cambio_radial**2))
        diferencia = restar(deseada, velocidad)
        lateral = sumar(diferencia, escalar(radial, -producto_escalar(diferencia, radial)))
        cambio = sumar(escalar(radial, cambio_radial), limitar(lateral, resto))

    nueva_velocidad = limitar(sumar(velocidad, cambio), tamano.velocidad_maxima)
    nueva_posicion = sumar(posicion, escalar(nueva_velocidad, dt))
    return _dentro_de_la_capa(nueva_posicion, ataques), nueva_velocidad


def _dentro_de_la_capa(posicion: Vector3, ataques: Ataques) -> Vector3:
    """Red de seguridad numérica: la posición nunca sale de la capa permitida.

    Solo actúa en el borde exterior al moverse de lado, por la curvatura de la esfera,
    y corrige fracciones de unidad. El margen evita que el redondeo deje la posición fuera.
    """
    distancia = norma(posicion)
    if distancia < ataques.distancia_minima:
        return escalar(posicion, (ataques.distancia_minima + _MARGEN) / distancia)
    if distancia > ataques.distancia_maxima:
        return escalar(posicion, (ataques.distancia_maxima - _MARGEN) / distancia)
    return posicion
