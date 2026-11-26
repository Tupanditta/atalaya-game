"""Azar con semilla del núcleo.

Es el único sitio de la capa lógica que usa el módulo `random`.
"""

import random
from collections.abc import MutableSequence, Sequence
from typing import TypeVar

T = TypeVar("T")

_MAX_SEMILLA = 2**63


def semilla_nueva() -> int:
    """Devuelve una semilla nueva tomada de la entropía del sistema."""
    return random.SystemRandom().randrange(_MAX_SEMILLA)


class Azar:
    """Generador de números al azar de una partida, reproducible con su semilla."""

    def __init__(self, semilla: int) -> None:
        self._semilla = semilla
        self._generador = random.Random(semilla)

    @property
    def semilla(self) -> int:
        """Semilla con la que empezó la secuencia actual."""
        return self._semilla

    def reiniciar(self, semilla: int) -> None:
        """Vuelve a empezar la secuencia con `semilla`."""
        self._semilla = semilla
        self._generador.seed(semilla)

    def aleatorio(self) -> float:
        """Número al azar en el intervalo [0, 1)."""
        return self._generador.random()

    def uniforme(self, minimo: float, maximo: float) -> float:
        """Número al azar entre `minimo` y `maximo`."""
        return self._generador.uniform(minimo, maximo)

    def entero(self, minimo: int, maximo: int) -> int:
        """Entero al azar entre `minimo` y `maximo`, ambos incluidos."""
        return self._generador.randint(minimo, maximo)

    def elegir(self, opciones: Sequence[T]) -> T:
        """Elemento al azar de `opciones`."""
        return self._generador.choice(opciones)

    def barajar(self, elementos: MutableSequence[T]) -> None:
        """Baraja `elementos` en el sitio."""
        self._generador.shuffle(elementos)
