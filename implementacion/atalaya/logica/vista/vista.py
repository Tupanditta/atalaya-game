"""Orientación de la cámara, giro, zoom y posición de la mira (`modulos/vista.md`).

El desvío de la mira por desestabilización y el bloqueo por aturdimiento llegan en S4.
"""

import math

from atalaya.logica.nucleo.bus import Bus
from atalaya.logica.nucleo.dominio import Vector3
from atalaya.logica.nucleo.eventos import ApuntadoCambiado, PartidaIniciada
from atalaya.logica.nucleo.vectores import escalar, normalizar, sumar
from atalaya.logica.parametros.modelo import Parametros
from atalaya.logica.vista.cuaternion import Cuaternion

#: Ejes locales de la cámara (`cuaternion.py`, convención de ejes).
DERECHA: Vector3 = (1.0, 0.0, 0.0)
ADELANTE: Vector3 = (0.0, 1.0, 0.0)
ARRIBA: Vector3 = (0.0, 0.0, 1.0)

_VALORES_EJE = (-1, 0, 1)

#: Límite horizontal de la mira, en medias alturas de pantalla: cubre pantallas de
#: hasta 4:1. La presentación la limita antes al ancho real de la pantalla.
_PUNTERO_HORIZONTAL_MAXIMO = 4.0


def eje_de_flechas(negativa: bool, positiva: bool) -> int:
    """Valor de un eje de giro a partir de sus dos flechas.

    Las dos flechas opuestas pulsadas a la vez dan 0 (RN-26).
    """
    return int(positiva) - int(negativa)


class Vista:
    """Hacia dónde mira el jugador y cuánto zoom tiene (RN-01: solo hay orientación)."""

    def __init__(self, bus: Bus, parametros: Parametros) -> None:
        self._jugador = parametros.jugador
        self._orientacion = Cuaternion.identidad()
        self._anterior = self._orientacion
        self._progreso_apuntado = 0.0
        self._campo_vision = self._jugador.campo_vision_normal
        self._horizontal = 0
        self._vertical = 0
        self._puntero = (0.0, 0.0)
        self._puntero_recibido = (0.0, 0.0)
        bus.suscribir(ApuntadoCambiado, self._al_cambiar_apuntado)
        bus.suscribir(PartidaIniciada, self._al_iniciar_partida)

    # --- operaciones -----------------------------------------------------------------

    def recibir_ejes(self, horizontal: int, vertical: int) -> None:
        """Ejes de giro de este paso, cada uno −1, 0 o +1.

        Horizontal +1 gira a la derecha; vertical +1 gira hacia arriba. Se aplican en el
        siguiente `actualizar` y después se olvidan, para que el giro no quede atascado.
        """
        if horizontal not in _VALORES_EJE or vertical not in _VALORES_EJE:
            raise ValueError(f"Ejes de giro no válidos: ({horizontal}, {vertical})")
        self._horizontal = horizontal
        self._vertical = vertical

    def recibir_puntero(self, x: float, y: float) -> None:
        """Posición de la mira en la pantalla, que el jugador mueve con el ratón.

        Se mide desde el centro de la pantalla en medias alturas de pantalla: `y` va de
        −1 (borde inferior) a +1 (borde superior) y `x` es positiva hacia la derecha.
        Se aplica en el siguiente `actualizar`, así que en pausa la mira no se mueve.
        """
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError(f"Posición de la mira no válida: ({x}, {y})")
        limite = _PUNTERO_HORIZONTAL_MAXIMO
        self._puntero_recibido = (max(-limite, min(limite, x)), max(-1.0, min(1.0, y)))

    def actualizar(self, dt: float) -> None:
        """Ajusta el campo de visión al apuntado (RN-39) y gira la cámara (RN-40, RN-41)."""
        self._anterior = self._orientacion
        self._puntero = self._puntero_recibido
        j = self._jugador
        self._campo_vision = (
            j.campo_vision_normal
            + (j.campo_vision_zoom - j.campo_vision_normal) * self._progreso_apuntado
        )
        if self._horizontal or self._vertical:
            grados = j.velocidad_giro * (self._campo_vision / j.campo_vision_normal) * dt
            # Giro lateral sobre el eje vertical de la cámara: hacia la derecha es negativo
            # alrededor de z. Giro vertical sobre su eje horizontal: hacia arriba es positivo
            # alrededor de x. Multiplicar por la derecha aplica el giro en ejes locales.
            giro = Cuaternion.rotacion(ARRIBA, -self._horizontal * grados) * Cuaternion.rotacion(
                DERECHA, self._vertical * grados
            )
            self._orientacion = (self._orientacion * giro).normalizado()
        self._horizontal = 0
        self._vertical = 0

    # --- consultas -------------------------------------------------------------------

    @property
    def orientacion(self) -> Cuaternion:
        """Orientación de la cámara al final del último paso."""
        return self._orientacion

    @property
    def orientacion_anterior(self) -> Cuaternion:
        """Orientación al principio del último paso, para interpolar al dibujar."""
        return self._anterior

    @property
    def campo_vision(self) -> float:
        """Campo de visión vertical actual, en grados."""
        return self._campo_vision

    @property
    def adelante(self) -> Vector3:
        """Eje «adelante» de la cámara en el mundo."""
        return self._orientacion.rotar(ADELANTE)

    @property
    def arriba(self) -> Vector3:
        """Eje «arriba» de la cámara en el mundo."""
        return self._orientacion.rotar(ARRIBA)

    @property
    def derecha(self) -> Vector3:
        """Eje «derecha» de la cámara en el mundo."""
        return self._orientacion.rotar(DERECHA)

    @property
    def puntero(self) -> tuple[float, float]:
        """Posición de la mira en la pantalla, en medias alturas desde el centro."""
        return self._puntero

    @property
    def direccion_mira(self) -> Vector3:
        """Dirección real de la mira: la del punto de la pantalla donde está la mira.

        Con la perspectiva de la cámara, un punto a `y` medias alturas del centro está a
        `y` × tan(campo de visión ÷ 2) sobre el eje «adelante». Hasta S4 no hay desvío.
        """
        x, y = self._puntero
        if x == 0 and y == 0:
            return self.adelante
        t = math.tan(math.radians(self._campo_vision) / 2)
        lateral = sumar(escalar(self.derecha, x * t), escalar(self.arriba, y * t))
        return normalizar(sumar(self.adelante, lateral))

    # --- eventos ---------------------------------------------------------------------

    def _al_cambiar_apuntado(self, evento: ApuntadoCambiado) -> None:
        self._progreso_apuntado = min(1.0, max(0.0, evento.progreso))

    def _al_iniciar_partida(self, evento: PartidaIniciada) -> None:
        self._orientacion = Cuaternion.identidad()
        self._anterior = self._orientacion
        self._progreso_apuntado = 0.0
        self._campo_vision = self._jugador.campo_vision_normal
        self._horizontal = 0
        self._vertical = 0
        self._puntero = (0.0, 0.0)
        self._puntero_recibido = (0.0, 0.0)
