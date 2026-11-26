"""Contactos del radar respecto a la cámara (`modulos/radar.md`).

Sin estado propio: cada consulta se calcula con el estado actual de `vista` y `enemigos`.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from atalaya.logica.enemigos import EstadoEnemigo, FaseAtaque
from atalaya.logica.nucleo.dominio import Tamano, TipoEnemigo, Vector3
from atalaya.logica.nucleo.vectores import angulo_entre, norma, producto_escalar
from atalaya.logica.parametros.modelo import Parametros

#: Por debajo de este ángulo con el plano horizontal de la cámara, el enemigo está
#: «a la misma altura» (`modulos/radar.md`). Es un detalle de presentación del radar,
#: no un valor de juego de `reglasNegocio.md`.
ANGULO_MISMA_ALTURA = 15.0

#: Margen para que un ángulo calculado como 15° exactos no cambie por redondeo.
_TOLERANCIA = 1e-9


class Altura(Enum):
    """Altura de un contacto respecto al plano horizontal de la cámara."""

    POR_ENCIMA = "por_encima"
    MISMA = "misma"
    POR_DEBAJO = "por_debajo"


@dataclass(frozen=True, slots=True)
class Contacto:
    """Lo que el radar muestra de un enemigo activo."""

    id: int
    #: Grados en sentido horario desde «adelante» (arriba en el radar), de 0 a 360.
    angulo: float
    #: Distancia a la estación dividida por el alcance del radar, de 0 a 1.
    distancia_relativa: float
    altura: Altura
    tipo: TipoEnemigo
    tamano: Tamano
    en_campo_vision: bool
    #: Indica si el enemigo está mostrando su aviso de disparo, para que el HUD lo resalte.
    en_aviso: bool


class Camara(Protocol):
    """Lo que `radar` consulta a `vista`: sus ejes y su campo de visión."""

    @property
    def adelante(self) -> Vector3: ...

    @property
    def derecha(self) -> Vector3: ...

    @property
    def arriba(self) -> Vector3: ...

    @property
    def campo_vision(self) -> float: ...


class ListaEnemigos(Protocol):
    """Lo que `radar` consulta a `enemigos`: los enemigos activos."""

    @property
    def activos(self) -> Sequence[EstadoEnemigo]: ...


class Radar:
    """Traduce la posición de cada enemigo a lo que muestra el radar (RF-07, RN-41)."""

    def __init__(self, parametros: Parametros, camara: Camara, enemigos: ListaEnemigos) -> None:
        self._alcance = parametros.ataques.alcance_radar
        self._camara = camara
        self._enemigos = enemigos

    @property
    def sector_vision(self) -> float:
        """Apertura del campo de visión actual, en grados, para dibujarlo en el radar."""
        return self._camara.campo_vision

    @property
    def contactos(self) -> tuple[Contacto, ...]:
        """Un contacto por enemigo activo, en orden de aparición (RN-09)."""
        return tuple(self._contacto(e) for e in self._enemigos.activos)

    def _contacto(self, enemigo: EstadoEnemigo) -> Contacto:
        c = self._camara
        p = enemigo.posicion
        delante = producto_escalar(p, c.adelante)
        derecha = producto_escalar(p, c.derecha)
        arriba = producto_escalar(p, c.arriba)
        angulo = math.degrees(math.atan2(derecha, delante)) % 360.0
        elevacion = math.degrees(math.atan2(arriba, math.hypot(delante, derecha)))
        if abs(elevacion) < ANGULO_MISMA_ALTURA - _TOLERANCIA:
            altura = Altura.MISMA
        else:
            altura = Altura.POR_ENCIMA if elevacion > 0 else Altura.POR_DEBAJO
        distancia = norma(p)
        # El campo de visión se trata como un cono con la apertura del sector del radar.
        en_campo = distancia > 0 and angulo_entre(p, c.adelante) <= c.campo_vision / 2
        return Contacto(
            id=enemigo.id,
            angulo=angulo,
            distancia_relativa=min(1.0, distancia / self._alcance),
            altura=altura,
            tipo=enemigo.tipo,
            tamano=enemigo.tamano,
            en_campo_vision=en_campo,
            en_aviso=enemigo.fase is FaseAtaque.AVISO,
        )
