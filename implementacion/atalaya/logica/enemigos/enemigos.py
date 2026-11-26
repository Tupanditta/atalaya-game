"""Enemigos activos: aparición, movimiento, ataques, proyectiles e impactos.

Ver `modulos/enemigos.md`. Cada tamaño tiene su vida, su velocidad y su zona de impacto
(RN-06), y cada tipo su tiempo de recarga (RN-14). El efecto de cada tipo sobre el
jugador no se aplica aquí: lo aplica `estacion` al recibir ProyectilImpacta.
"""

import math
from dataclasses import dataclass
from enum import Enum

from atalaya.logica.enemigos.movimiento import elegir_destino, mover, posicion_aparicion
from atalaya.logica.nucleo.azar import Azar
from atalaya.logica.nucleo.bus import Bus
from atalaya.logica.nucleo.dominio import Tamano, TipoEnemigo, Vector3
from atalaya.logica.nucleo.eventos import (
    AvisoDisparo,
    DisparoRealizado,
    EnemigoAlcanzado,
    EnemigoAparecido,
    EnemigoDestruido,
    EstacionDestruida,
    PartidaAbandonada,
    PartidaIniciada,
    ProyectilImpacta,
    ProyectilLanzado,
    SolicitudAparicion,
)
from atalaya.logica.nucleo.vectores import (
    CERO,
    escalar,
    norma,
    normalizar,
    producto_escalar,
    restar,
    sumar,
)
from atalaya.logica.parametros.modelo import Parametros

#: Por debajo de esta vida, el enemigo se considera destruido.
_TOLERANCIA_VIDA = 1e-9

#: Margen para que la suma de pasos en coma flotante no retrase un paso el fin de una fase.
_TOLERANCIA_TIEMPO = 1e-9

#: Un proyectil alcanza la estación al entrar en este radio, en unidades del mundo
#: (`design.md`, sección 5, «Proyectiles enemigos»). Es un detalle de la simulación,
#: no un valor de juego de `reglasNegocio.md`.
RADIO_ESTACION = 5.0


class FaseAtaque(Enum):
    """Fase de ataque de un enemigo (`modulos/enemigos.md`, «Estado que gestiona»)."""

    #: Recarga terminada: avisa en cuanto está dentro del alcance de disparo (RN-42).
    ACERCANDOSE = "acercandose"
    #: Muestra el aviso de disparo antes de lanzar el proyectil (RN-34).
    AVISO = "aviso"
    #: Espera el tiempo de recarga de su tipo antes de volver a atacar (RN-14).
    RECARGA = "recarga"


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
    fase: FaseAtaque
    #: Tiempo que le queda a la fase de aviso o de recarga; 0 al acercarse.
    tiempo_fase: float


@dataclass(frozen=True, slots=True)
class EstadoProyectil:
    """Estado de un proyectil en vuelo, de solo lectura para quien lo consulta."""

    #: Identificador del proyectil, el mismo de su ProyectilLanzado.
    id: int
    tipo_enemigo: TipoEnemigo
    posicion: Vector3
    #: Posición al principio del último paso, para interpolar al dibujar.
    posicion_anterior: Vector3
    velocidad: Vector3


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
    fase: FaseAtaque = FaseAtaque.ACERCANDOSE
    tiempo_fase: float = 0.0

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
            self.fase,
            self.tiempo_fase,
        )


@dataclass(slots=True)
class _Proyectil:
    id: int
    tipo_enemigo: TipoEnemigo
    posicion: Vector3
    posicion_anterior: Vector3
    velocidad: Vector3

    def estado(self) -> EstadoProyectil:
        return EstadoProyectil(
            self.id, self.tipo_enemigo, self.posicion, self.posicion_anterior, self.velocidad
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
    """Crea, mueve y daña a los enemigos de la oleada, y lanza sus proyectiles."""

    def __init__(self, bus: Bus, parametros: Parametros, azar: Azar) -> None:
        self._bus = bus
        self._parametros = parametros
        self._azar = azar
        self._activos: dict[int, _Enemigo] = {}
        self._proyectiles: dict[int, _Proyectil] = {}
        self._siguiente_id = 1
        self._siguiente_proyectil = 1
        bus.suscribir(SolicitudAparicion, self._al_solicitar_aparicion)
        bus.suscribir(DisparoRealizado, self._al_disparar)
        bus.suscribir(PartidaIniciada, self._al_terminar_o_empezar)
        bus.suscribir(PartidaAbandonada, self._al_terminar_o_empezar)
        bus.suscribir(EstacionDestruida, self._al_terminar_o_empezar)

    # --- operaciones -----------------------------------------------------------------

    def actualizar(self, dt: float) -> None:
        """Mueve proyectiles y enemigos, y avanza las fases de ataque.

        Los proyectiles se mueven antes que los enemigos: uno lanzado en este paso sale
        de la posición de su enemigo y empieza a avanzar en el paso siguiente.
        """
        self._mover_proyectiles(dt)
        self._mover_enemigos(dt)
        for enemigo in self._activos.values():
            self._atacar(enemigo, dt)

    # --- consultas -------------------------------------------------------------------

    @property
    def activos(self) -> tuple[EstadoEnemigo, ...]:
        """Enemigos activos, en orden de aparición."""
        return tuple(e.estado() for e in self._activos.values())

    def enemigo(self, id: int) -> EstadoEnemigo | None:
        """Estado del enemigo `id`, o `None` si no está activo."""
        enemigo = self._activos.get(id)
        return None if enemigo is None else enemigo.estado()

    @property
    def proyectiles(self) -> tuple[EstadoProyectil, ...]:
        """Proyectiles en vuelo, en orden de lanzamiento."""
        return tuple(p.estado() for p in self._proyectiles.values())

    # --- internos --------------------------------------------------------------------

    def _mover_enemigos(self, dt: float) -> None:
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

    def _atacar(self, enemigo: _Enemigo, dt: float) -> None:
        """Avanza la fase de ataque: recarga, aviso y lanzamiento (RN-14, RN-34, RN-42)."""
        ataques = self._parametros.ataques
        if enemigo.fase is FaseAtaque.RECARGA:
            enemigo.tiempo_fase -= dt
            if enemigo.tiempo_fase > _TOLERANCIA_TIEMPO:
                return
            enemigo.fase, enemigo.tiempo_fase = FaseAtaque.ACERCANDOSE, 0.0
        if enemigo.fase is FaseAtaque.ACERCANDOSE:
            # Con la recarga terminada, el aviso empieza en el mismo paso.
            if norma(enemigo.posicion) <= ataques.alcance_disparo:
                enemigo.fase, enemigo.tiempo_fase = FaseAtaque.AVISO, ataques.duracion_aviso
                self._bus.publicar(AvisoDisparo(enemigo.id))
            return
        enemigo.tiempo_fase -= dt
        if enemigo.tiempo_fase <= _TOLERANCIA_TIEMPO:
            self._lanzar(enemigo)
            enemigo.fase = FaseAtaque.RECARGA
            enemigo.tiempo_fase = self._parametros.tipos.de(enemigo.tipo).recarga

    def _lanzar(self, enemigo: _Enemigo) -> None:
        """Lanza un proyectil desde el enemigo hacia el centro de la estación (RN-35)."""
        rapidez = self._parametros.ataques.velocidad_proyectil
        velocidad = escalar(normalizar(enemigo.posicion), -rapidez)
        proyectil = _Proyectil(
            self._siguiente_proyectil, enemigo.tipo, enemigo.posicion, enemigo.posicion, velocidad
        )
        self._siguiente_proyectil += 1
        self._proyectiles[proyectil.id] = proyectil
        self._bus.publicar(ProyectilLanzado(proyectil.id, enemigo.tipo))

    def _mover_proyectiles(self, dt: float) -> None:
        """Avanza los proyectiles en línea recta; al llegar, impactan y desaparecen (RN-36)."""
        for proyectil in list(self._proyectiles.values()):
            proyectil.posicion_anterior = proyectil.posicion
            proyectil.posicion = sumar(proyectil.posicion, escalar(proyectil.velocidad, dt))
            # Si en un paso cruzara el centro, la posición quedaría en el sentido de la
            # velocidad: también cuenta como impacto.
            cruzado = producto_escalar(proyectil.posicion, proyectil.velocidad) > 0
            if cruzado or norma(proyectil.posicion) <= RADIO_ESTACION + _TOLERANCIA_TIEMPO:
                del self._proyectiles[proyectil.id]
                self._bus.publicar(ProyectilImpacta(proyectil.tipo_enemigo))

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
        """Daña al enemigo más cercano cuya esfera de impacto corta el disparo (RN-07).

        Un enemigo destruido durante su aviso deja de existir y no llega a disparar (RN-34).
        """
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
        self._proyectiles.clear()
