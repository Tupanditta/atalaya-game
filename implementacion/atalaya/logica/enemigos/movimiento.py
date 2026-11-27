"""Movimiento con inercia de los enemigos y sus maniobras (RN-29 a RN-33, RN-42).

La estación está en el origen. Cada enemigo repite en bucle tres maniobras: ataque
(se lanza hacia la estación y la sobrepasa muy cerca), retirada (se aleja describiendo
curvas hasta la distancia máxima) y espera (patrulla lejos, de lado, un momento).
Las funciones son puras salvo por el azar que reciben.
"""

import math
from enum import Enum

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
    producto_vectorial,
    restar,
    sumar,
)
from atalaya.logica.parametros.modelo import Ataques, DatosTamano


class Maniobra(Enum):
    """Maniobra de un enemigo (`modulos/enemigos.md`, «Comportamiento de un enemigo»)."""

    #: Se lanza a toda velocidad hacia un punto junto a la estación y la sobrepasa.
    ATAQUE = "ataque"
    #: Se aleja describiendo curvas hasta la distancia de espera.
    RETIRADA = "retirada"
    #: Se mantiene lejos, patrullando de lado alrededor de la estación, antes de volver a
    #: atacar.
    ESPERA = "espera"


#: Distancias de los puntos de paso de la retirada, en fracción de la distancia máxima.
#: Con ellos, el enemigo se aleja describiendo curvas y no en línea recta (RN-29).
#: Son detalles del movimiento, no valores de juego de `reglasNegocio.md`.
_TRAMOS_RETIRADA = ((0.40, 0.65), (0.65, 0.85))

#: Giro, en grados, de cada tramo de la retirada respecto al anterior.
_GIRO_RETIRADA_MINIMO = 20.0
_GIRO_RETIRADA_MAXIMO = 45.0

#: Patrulla de espera: ángulo, visto desde la estación, entre un punto y el siguiente, y
#: desvío máximo del sentido de la marcha en cada punto, en grados.
_ARCO_PATRULLA = 25.0
_DESVIO_PATRULLA = 50.0
#: Rapidez de la patrulla, en fracción de la velocidad máxima, y rapidez con la que
#: corrige la distancia a la estación, en unidades por segundo por cada unidad de error.
_RAPIDEZ_PATRULLA = 0.5
_CORRECCION_PATRULLA = 2.0

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


def punto_pasada(posicion: Vector3, tamano: DatosTamano, ataques: Ataques, azar: Azar) -> Vector3:
    """Punto junto a la estación por el que el enemigo la sobrepasa en su ataque.

    Queda de lado respecto a la dirección del enemigo, a la distancia de pasada más el
    radio de su zona de impacto: los enemigos grandes pasan algo más lejos (RN-31).
    """
    radial = normalizar(posicion) if norma(posicion) > 0 else (0.0, 1.0, 0.0)
    lado = girar_hacia(radial, 90.0, azar.uniforme(0.0, 360.0))
    distancia = (
        azar.uniforme(ataques.distancia_pasada_minima, ataques.distancia_pasada_maxima)
        + tamano.radio_impacto
    )
    return escalar(lado, distancia)


def ruta_retirada(rumbo: Vector3, ataques: Ataques, azar: Azar) -> list[Vector3]:
    """Puntos de paso de la retirada, del primero al último, donde el enemigo espera.

    Cada tramo gira un poco respecto al anterior, hacia un lado al azar, y queda más
    lejos. El último está a la distancia de aparición, dentro del radar (RN-30).
    `rumbo` es la dirección en la que el enemigo sobrepasa la estación, de longitud 1.
    """
    ruta = []
    direccion = rumbo
    for minima, maxima in _TRAMOS_RETIRADA:
        direccion = _girar_al_azar(direccion, azar)
        ruta.append(escalar(direccion, azar.uniforme(minima, maxima) * ataques.distancia_maxima))
    direccion = _girar_al_azar(direccion, azar)
    distancia = azar.uniforme(
        ataques.distancia_aparicion_minima, ataques.distancia_aparicion_maxima
    )
    ruta.append(escalar(direccion, distancia))
    return ruta


def punto_patrulla(posicion: Vector3, velocidad: Vector3, ataques: Ataques, azar: Azar) -> Vector3:
    """Siguiente punto de la patrulla de espera: lejos, de lado y algo girado.

    Sigue más o menos el sentido de la marcha alrededor de la estación, a la distancia de
    aparición, así que el enemigo espera moviéndose sin salir del radar (RN-30). La
    distancia a la que patrulla la mantiene `velocidad_patrulla`.
    """
    radial = normalizar(posicion)
    lateral = restar(velocidad, escalar(radial, producto_escalar(velocidad, radial)))
    if norma(lateral) < 1e-6:
        lado = girar_hacia(radial, 90.0, azar.uniforme(0.0, 360.0))
    else:
        # Gira el sentido de la marcha alrededor de la línea de la estación.
        lateral = normalizar(lateral)
        giro = math.radians(azar.uniforme(-_DESVIO_PATRULLA, _DESVIO_PATRULLA))
        lado = sumar(
            escalar(lateral, math.cos(giro)),
            escalar(producto_vectorial(radial, lateral), math.sin(giro)),
        )
    angulo = math.radians(_ARCO_PATRULLA)
    direccion = normalizar(
        sumar(escalar(radial, math.cos(angulo)), escalar(lado, math.sin(angulo)))
    )
    distancia = azar.uniforme(
        ataques.distancia_aparicion_minima, ataques.distancia_aparicion_maxima
    )
    return escalar(direccion, distancia)


def _girar_al_azar(direccion: Vector3, azar: Azar) -> Vector3:
    return girar_hacia(
        direccion,
        azar.uniforme(_GIRO_RETIRADA_MINIMO, _GIRO_RETIRADA_MAXIMO),
        azar.uniforme(0.0, 360.0),
    )


def ha_sobrepasado(posicion: Vector3, punto: Vector3, rumbo: Vector3) -> bool:
    """Indica si el enemigo ha cruzado el plano que pasa por `punto`, perpendicular a `rumbo`."""
    return producto_escalar(restar(posicion, punto), rumbo) >= 0


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


def velocidad_patrulla(
    posicion: Vector3, destino: Vector3, radio: float, tamano: DatosTamano
) -> Vector3:
    """Velocidad deseada al patrullar: de lado hacia `destino` y a `radio` de la estación.

    Solo usa la parte lateral de la dirección al destino, a media velocidad, y corrige
    poco a poco la distancia a la estación hacia `radio`.
    """
    radial = normalizar(posicion)
    hacia = restar(destino, posicion)
    lateral = restar(hacia, escalar(radial, producto_escalar(hacia, radial)))
    rapidez = tamano.velocidad_maxima * _RAPIDEZ_PATRULLA
    lado = escalar(normalizar(lateral), rapidez) if norma(lateral) > 1e-6 else CERO
    error = (radio - norma(posicion)) * _CORRECCION_PATRULLA
    return sumar(lado, escalar(radial, max(-rapidez, min(rapidez, error))))


def velocidad_paso(posicion: Vector3, destino: Vector3, tamano: DatosTamano) -> Vector3:
    """Velocidad deseada hacia `destino` sin frenar: la máxima, para pasar de largo."""
    hacia = restar(destino, posicion)
    distancia = norma(hacia)
    if distancia == 0:
        return CERO
    return escalar(hacia, tamano.velocidad_maxima / distancia)


def _rapidez_segura(hueco: float, aceleracion: float, dt: float) -> float:
    """Rapidez máxima hacia un límite a `hueco` unidades que aún permite frenar antes.

    Es la solución de v² = 2·a·(hueco − v·dt): con ella, tras moverse un paso, el
    enemigo sigue pudiendo frenar con la aceleración `a` sin cruzar el límite.
    """
    ad = aceleracion * dt
    return -ad + math.sqrt(ad * ad + 2 * aceleracion * max(0.0, hueco))


def _libra_el_minimo(posicion: Vector3, velocidad: Vector3, minima: float) -> bool:
    """Indica si, siguiendo recto con `velocidad`, el enemigo no bajaría de `minima`.

    Un enemigo que pasa de lado no necesita frenar su acercamiento: su trayectoria
    recta ya deja la estación a más de la distancia mínima.
    """
    acercamiento = -producto_escalar(posicion, velocidad)
    if acercamiento <= 0:
        return True
    avance = acercamiento / producto_escalar(velocidad, velocidad)
    return norma(sumar(posicion, escalar(velocidad, avance))) >= minima


def mover(
    posicion: Vector3,
    velocidad: Vector3,
    destino: Vector3,
    tamano: DatosTamano,
    ataques: Ataques,
    dt: float,
    frenar: bool = True,
    patrulla: float | None = None,
) -> tuple[Vector3, Vector3]:
    """Avanza un paso de persecución con inercia (RN-33) sin salir de la capa (RN-30, RN-31).

    Con `frenar`, se detiene en `destino`; sin él, pasa de largo a toda velocidad. Con
    `patrulla`, se mueve de lado hacia `destino` a esa distancia de la estación. El
    cambio de velocidad en un paso nunca supera la aceleración máxima × `dt`, y la
    velocidad nunca supera la máxima. Cerca de un límite de distancia, la velocidad
    radial se frena de forma gradual. Devuelve la nueva posición y la nueva velocidad.
    """
    a = tamano.aceleracion_maxima
    cambio_maximo = a * dt
    if patrulla is not None:
        deseada = velocidad_patrulla(posicion, destino, patrulla, tamano)
    elif frenar:
        deseada = velocidad_llegada(posicion, destino, tamano)
    else:
        deseada = velocidad_paso(posicion, destino, tamano)

    distancia = norma(posicion)
    radial = normalizar(posicion)
    frenado = a * _FRACCION_FRENADO
    minima = ataques.distancia_minima
    if _libra_el_minimo(posicion, deseada, minima) and _libra_el_minimo(
        posicion, velocidad, minima
    ):
        # Pasa de lado: no hace falta frenar el acercamiento.
        hacia_dentro = math.inf
    else:
        hacia_dentro = _rapidez_segura(distancia - minima, frenado, dt)
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
