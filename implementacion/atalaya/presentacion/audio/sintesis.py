"""Efectos de sonido generados por código: recursos propios (`design.md`, sección 14).

Versión mínima de S3, más el aturdimiento de S4. Cada función devuelve las muestras de
un sonido mono entre −1 y 1; `a_wav` las convierte en un archivo WAV en memoria. Los
sonidos definitivos en OGG llegan en S9 (`design.md`, sección 7).
"""

import io
import math
import random
import struct
import wave
from collections.abc import Callable, Sequence

#: Frecuencia de muestreo, en muestras por segundo.
FRECUENCIA = 22050

#: Azar solo para el ruido de los sonidos; con semilla fija, cada sonido sale siempre igual.
_SEMILLA_RUIDO = 7


def _muestras(duracion: float, onda: Callable[[float], float]) -> list[float]:
    return [onda(i / FRECUENCIA) for i in range(int(duracion * FRECUENCIA))]


def _envolvente(t: float, duracion: float, ataque: float = 0.005) -> float:
    """Subida corta y caída exponencial hasta el final."""
    if t < ataque:
        return t / ataque
    return math.exp(-4.0 * (t - ataque) / max(1e-6, duracion - ataque))


def _barrido(f0: float, f1: float, duracion: float) -> Callable[[float], float]:
    """Fase de un tono que cambia de frecuencia de forma exponencial de f0 a f1."""
    k = math.log(f1 / f0) / duracion

    def fase(t: float) -> float:
        return 2 * math.pi * f0 * (math.exp(k * t) - 1) / k

    return fase


def disparo() -> list[float]:
    """Rayo propio: barrido descendente brillante, 0,18 s."""
    d = 0.18
    fase = _barrido(1600.0, 260.0, d)

    def onda(t: float) -> float:
        tono = math.sin(fase(t)) + 0.35 * math.sin(2 * fase(t))
        return 0.55 * tono * _envolvente(t, d)

    return _muestras(d, onda)


def aviso(duracion: float) -> list[float]:
    """Carga del aviso de disparo: tono que sube con trémolo, tan largo como el aviso."""
    fase = _barrido(320.0, 1100.0, duracion)

    def onda(t: float) -> float:
        tremolo = 0.6 + 0.4 * math.sin(2 * math.pi * 14 * t)
        subida = min(1.0, t / (0.6 * duracion))
        final = min(1.0, (duracion - t) / 0.03)
        return 0.45 * math.sin(fase(t)) * tremolo * (0.35 + 0.65 * subida) * final

    return _muestras(duracion, onda)


def impacto() -> list[float]:
    """Impacto en un enemigo: golpe metálico corto, 0,14 s."""
    d = 0.14
    azar = random.Random(_SEMILLA_RUIDO)

    def onda(t: float) -> float:
        golpe = azar.uniform(-1, 1) * math.exp(-60 * t)
        ping = math.sin(2 * math.pi * 1250 * t) * math.exp(-25 * t)
        return 0.5 * golpe + 0.4 * ping

    return _muestras(d, onda)


def explosion() -> list[float]:
    """Explosión: ruido grave filtrado que se apaga, 0,9 s."""
    d = 0.9
    azar = random.Random(_SEMILLA_RUIDO)
    filtrado = 0.0
    muestras = []
    for i in range(int(d * FRECUENCIA)):
        t = i / FRECUENCIA
        # Filtro de paso bajo que se cierra con el tiempo: del estallido al rumor.
        corte = 0.35 * math.exp(-3 * t) + 0.03
        filtrado += corte * (azar.uniform(-1, 1) - filtrado)
        rumor = math.sin(2 * math.pi * 55 * t) * math.exp(-5 * t)
        muestras.append((1.6 * filtrado + 0.35 * rumor) * _envolvente(t, d, 0.004))
    return muestras


def sin_energia() -> list[float]:
    """Falta de energía (RF-11): dos pitidos graves y secos."""
    d = 0.26

    def onda(t: float) -> float:
        dentro = t < 0.09 or 0.15 <= t < 0.24
        cuadrada = 1.0 if math.sin(2 * math.pi * 180 * t) >= 0 else -1.0
        return 0.28 * cuadrada if dentro else 0.0

    return _muestras(d, onda)


def alarma() -> list[float]:
    """Alarma de daño (RF-14): dos tonos alternos, 0,4 s."""
    d = 0.4

    def onda(t: float) -> float:
        frecuencia = 880.0 if (t // 0.1) % 2 == 0 else 660.0
        diente = 2 * ((t * frecuencia) % 1.0) - 1
        final = min(1.0, (d - t) / 0.03)
        return 0.3 * diente * final

    return _muestras(d, onda)


def aturdimiento() -> list[float]:
    """Aturdimiento (RN-13): zumbido grave que baja y vibra, como un sistema que se apaga.

    Dura 0,7 s, menos que el aturdimiento más corto, para no tapar el sonido de la partida.
    """
    d = 0.7
    fase = _barrido(420.0, 90.0, d)

    def onda(t: float) -> float:
        # El temblor de amplitud a 14 Hz da la sensación de sistemas inestables.
        temblor = 0.65 + 0.35 * math.sin(2 * math.pi * 14 * t)
        tono = math.sin(fase(t)) + 0.35 * math.sin(2 * fase(t) + 0.5)
        return 0.32 * tono * temblor * _envolvente(t, d, 0.02)

    return _muestras(d, onda)


def a_wav(muestras: Sequence[float]) -> bytes:
    """Archivo WAV mono de 16 bits con las muestras, recortadas a [−1, 1]."""
    datos = b"".join(struct.pack("<h", round(32767 * max(-1.0, min(1.0, m)))) for m in muestras)
    salida = io.BytesIO()
    with wave.open(salida, "wb") as archivo:
        archivo.setnchannels(1)
        archivo.setsampwidth(2)
        archivo.setframerate(FRECUENCIA)
        archivo.writeframes(datos)
    return salida.getvalue()
