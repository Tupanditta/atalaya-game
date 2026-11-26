"""Enemigos activos: aparición, movimiento y resolución del disparo (`modulos/enemigos.md`).

Los ataques y los proyectiles llegan en S3.
"""

import math
from dataclasses import dataclass

from atalaya.logica.enemigos.movimiento import elegir_destino, mover, posicion_aparicion
from atalaya.logica.nucleo.azar import Azar
from atalaya.logica.nucleo.bus import Bus
from atalaya.logica.nucleo.dominio import Tamano, TipoEnemigo, Vector3
from atalaya.logica.nucleo.eventos import (
    DisparoRealizado,
    EnemigoAlcanzado,
    EnemigoAparecido,
    EnemigoDestruido,
    EstacionDestruida,
    PartidaAbandonada,
    PartidaIniciada,
    SolicitudAparicion,
)
from atalaya.logica.nucleo.vectores import CERO, norma, producto_escalar, restar
from atalaya.logica.parametros.modelo import Parametros

#: Por debajo de esta vida, el enemigo se considera destruido.
_TOLERANCIA_VIDA = 1e-9


@dataclass(frozen=True, slots=True)
class EstadoEnemigo:
    """Estado de un enemigo activo, de solo lectura para quien lo consulta."""

    id: int
    tipo: TipoEnemigo
    tamano: Tamano
    vida: float
    posicion: Vector3
    #: Posición al principio del último paso, para interpolar al dibujar.
    posicion_anterior: Vector3
    velocidad: Vector3
    destino: Vector3


@dataclass(slots=True)
class _Enemigo:
    id: int
    tipo: TipoEnemigo
    tamano: Tamano
    vida: float
    posicion: Vector3
    posicion_anterior: Vector3
    velocidad: Vector3
    destino: Vector3

    def estado(self) -> EstadoEnemigo:
        return EstadoEnemigo(
            self.id,
            self.tipo,
            self.tamano,
            self.vida,
            self.posicion,
            self.posicion_anterior,
            self.velocidad,
            self.destino,
        )


def distancia_impacto(
    origen: Vector3, direccion: Vector3, centro: Vector3, radio: float
) -> float | None:
    """Distancia desde `origen` a la que la línea del disparo entra en la esfera.

    `direccion` tiene longitud 1. Devuelve `None` si la línea no corta la esfera o si
    la esfera queda detrás del origen (`design.md`, sección 5, «Impacto»).
    """
    relativo = restar(centro, origen)
    b = producto_escalar(relativo, direccion)
    c = producto_escalar(relativo, relativo) - radio * radio
    discriminante = b * b - c
    if discriminante < 0:
        return None
    raiz = math.sqrt(discriminante)
    if b + raiz < 0:
        return None
    return max(0.0, b - raiz)


class Enemigos:
    """Crea, mueve y daña a los enemigos de la oleada."""

    def __init__(self, bus: Bus, parametros: Parametros, azar: Azar) -> None:
        self._bus = bus
        self._parametros = parametros
        self._azar = azar
        self._activos: dict[int, _Enemigo] = {}
        self._siguiente_id = 1
        bus.suscribir(SolicitudAparicion, self._al_solicitar_aparicion)
        bus.suscribir(DisparoRealizado, self._al_disparar)
        bus.suscribir(PartidaIniciada, self._al_terminar_o_empezar)
        bus.suscribir(PartidaAbandonada, self._al_terminar_o_empezar)
        bus.suscribir(EstacionDestruida, self._al_terminar_o_empezar)

    # --- operaciones -----------------------------------------------------------------

    def actualizar(self, dt: float) -> None:
        """Mueve a cada enemigo hacia su destino y le da otro al llegar (RN-33)."""
        ataques = self._parametros.ataques
        for enemigo in self._activos.values():
            if norma(restar(enemigo.destino, enemigo.posicion)) < ataques.distancia_llegada:
                enemigo.destino = elegir_destino(enemigo.posicion, ataques, self._azar)
            enemigo.posicion_anterior = enemigo.posicion
            enemigo.posicion, enemigo.velocidad = mover(
                enemigo.posicion,
                enemigo.velocidad,
                enemigo.destino,
                self._parametros.tamanos.de(enemigo.tamano),
                ataques,
                dt,
            )

    # --- consultas -------------------------------------------------------------------

    @property
    def activos(self) -> tuple[EstadoEnemigo, ...]:
        """Enemigos activos, en orden de aparición."""
        return tuple(e.estado() for e in self._activos.values())

    def enemigo(self, id: int) -> EstadoEnemigo | None:
        """Estado del enemigo `id`, o `None` si no está activo."""
        enemigo = self._activos.get(id)
        return None if enemigo is None else enemigo.estado()

    # --- eventos ---------------------------------------------------------------------

    def _al_solicitar_aparicion(self, evento: SolicitudAparicion) -> None:
        ataques = self._parametros.ataques
        posicion = posicion_aparicion(ataques, self._azar)
        enemigo = _Enemigo(
            id=self._siguiente_id,
            tipo=evento.tipo,
            tamano=evento.tamano,
            vida=evento.vida,
            posicion=posicion,
            posicion_anterior=posicion,
            velocidad=CERO,
            destino=elegir_destino(posicion, ataques, self._azar),
        )
        self._siguiente_id += 1
        self._activos[enemigo.id] = enemigo
        self._bus.publicar(EnemigoAparecido(enemigo.id, enemigo.tipo, enemigo.tamano))

    def _al_disparar(self, evento: DisparoRealizado) -> None:
        """Daña al enemigo más cercano cuya esfera de impacto corta el disparo (RN-07)."""
        alcanzado: _Enemigo | None = None
        mas_cerca = math.inf
        for enemigo in self._activos.values():
            radio = self._parametros.tamanos.de(enemigo.tamano).radio_impacto
            distancia = distancia_impacto(evento.origen, evento.direccion, enemigo.posicion, radio)
            if distancia is not None and distancia < mas_cerca:
                alcanzado, mas_cerca = enemigo, distancia
        if alcanzado is None:
            return
        alcanzado.vida = max(0.0, alcanzado.vida - self._parametros.jugador.dano_disparo)
        if alcanzado.vida <= _TOLERANCIA_VIDA:
            del self._activos[alcanzado.id]
            self._bus.publicar(EnemigoDestruido(alcanzado.id, alcanzado.posicion))
        else:
            self._bus.publicar(EnemigoAlcanzado(alcanzado.id, alcanzado.vida))

    def _al_terminar_o_empezar(self, evento: object) -> None:
        self._activos.clear()
