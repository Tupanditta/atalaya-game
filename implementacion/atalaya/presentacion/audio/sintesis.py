"""Sonidos y música generados por código con numpy: recursos propios (`design.md`, sección 14).

Ambientación de ópera espacial, de registro grave: disparos bláster con cuerpo, motores
que rugen, explosiones profundas, impactos en el casco de la estación, servos de giro y
el salto hiperespacial. Todo original: ningún sonido de otras obras.

Cada función devuelve las muestras de un sonido mono entre −1 y 1 a `FRECUENCIA`. Los
bucles (motor, zumbido, tono de la mira) son periódicos de forma exacta: sus frecuencias son
múltiplos de 1 / duración y su ruido se genera en el dominio de la frecuencia, así que al
repetirse no hay salto. `a_wav` los convierte en un archivo WAV.
"""

import io
import math
import wave
from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

#: Versión de los sonidos: al cambiar cómo suena alguno se sube, para no reutilizar en la
#: caché sonidos generados con la versión anterior.
VERSION = 2

#: Frecuencia de muestreo, en muestras por segundo.
FRECUENCIA = 44100

#: Fases de la animación del salto, en fracciones de su duración (`escena/salto.py`):
#: el sonido sigue las mismas.
FASES_SALTO = (0.2, 0.3, 0.75, 0.9)

Muestras = NDArray[np.float64]

# --- utilidades --------------------------------------------------------------------------


def _tiempo(duracion: float) -> Muestras:
    return np.arange(round(duracion * FRECUENCIA), dtype=np.float64) / FRECUENCIA


def _azar(semilla: int) -> np.random.Generator:
    return np.random.default_rng(semilla)


def _caida(t: Muestras, constante: float, ataque: float = 0.003) -> Muestras:
    """Subida lineal en `ataque` segundos y caída exponencial con esa constante."""
    subida = np.clip(t / ataque, 0.0, 1.0)
    caida: Muestras = subida * np.exp(-np.maximum(t - ataque, 0.0) / constante)
    return caida


def _final(muestras: Muestras, segundos: float = 0.01) -> Muestras:
    """Apaga los últimos `segundos` para que el sonido no acabe en un chasquido."""
    n = min(len(muestras), int(segundos * FRECUENCIA))
    if n:
        muestras[-n:] *= np.linspace(1.0, 0.0, n)
    return muestras


def _fase_barrido(f0: float, f1: float, t: Muestras, duracion: float) -> Muestras:
    """Fase de un tono que va de `f0` a `f1` en `duracion` (exponencial) y luego sigue."""
    k = math.log(f1 / f0) / duracion
    dentro = 2 * math.pi * f0 * (np.exp(k * np.minimum(t, duracion)) - 1) / k
    fase: Muestras = dentro + 2 * math.pi * f1 * np.maximum(t - duracion, 0.0)
    return fase


def _filtrar(x: Muestras, bajo: float | None = None, alto: float | None = None) -> Muestras:
    """Filtro de paso de banda en frecuencia, de pendiente suave (cuarto orden).

    Se rellena con ceros para que la cola no aparezca al principio.
    """
    relleno = int(0.25 * FRECUENCIA)
    n = len(x) + relleno
    espectro = np.fft.rfft(x, n)
    f = np.fft.rfftfreq(n, 1 / FRECUENCIA)
    respuesta = np.ones_like(f)
    if alto is not None:
        respuesta /= 1 + (f / alto) ** 4
    if bajo is not None:
        respuesta /= 1 + (bajo / np.maximum(f, 1e-3)) ** 4
    filtrado: Muestras = np.fft.irfft(espectro * respuesta, n)[: len(x)]
    return filtrado


def _ruido_periodico(n: int, bajo: float, alto: float, azar: np.random.Generator) -> Muestras:
    """Ruido de banda limitada que se repite exactamente cada `n` muestras."""
    f = np.fft.rfftfreq(n, 1 / FRECUENCIA)
    magnitud = 1 / (1 + (f / alto) ** 4) / (1 + (bajo / np.maximum(f, 1e-3)) ** 4)
    magnitud[0] = 0.0
    fases = azar.uniform(0, 2 * math.pi, len(f))
    ruido: Muestras = np.fft.irfft(magnitud * np.exp(1j * fases), n)
    return ruido / max(float(np.std(ruido)), 1e-9)


def _cuantizar(frecuencia: float, periodo: float) -> float:
    """Frecuencia más cercana que da un número entero de ciclos en `periodo`."""
    return max(1, round(frecuencia * periodo)) / periodo


def _chispazos(t: Muestras, ritmo: float, constante: float, azar: np.random.Generator) -> Muestras:
    """Crepitar: impulsos sueltos al azar cuya frecuencia se apaga con el tiempo."""
    probabilidad = ritmo / FRECUENCIA * np.exp(-t / constante)
    impulsos = (azar.random(len(t)) < probabilidad) * azar.uniform(-1, 1, len(t))
    return impulsos.astype(np.float64)


def _armonicos(fase: Muestras, numero: int) -> Muestras:
    """Diente de sierra limitado a `numero` armónicos: brillante pero sin aliasing."""
    suma = np.zeros_like(fase)
    for k in range(1, numero + 1):
        suma += np.sin(k * fase) / k
    return suma


def _normalizar(x: Muestras, pico: float = 0.9) -> Muestras:
    maximo = float(np.max(np.abs(x)))
    normalizado: Muestras = x * (pico / maximo) if maximo > 0 else x
    return normalizado


def _saturar(x: Muestras, empuje: float) -> Muestras:
    """Saturación suave: da cuerpo y algo de aspereza."""
    saturado: Muestras = np.tanh(empuje * x) / math.tanh(empuje)
    return saturado


# --- disparos e impactos -----------------------------------------------------------------


def disparo() -> Muestras:
    """Disparo bláster propio: chirrido que cae con ecos de muelle y un golpe grave, 0,4 s.

    Varias copias del barrido, cada una un poco más tarde y más débil, imitan la
    dispersión de un muelle golpeado. Debajo, un golpe grave da cuerpo y profundidad.
    """
    d = 0.4
    t = _tiempo(d)
    azar = _azar(11)
    y = np.zeros_like(t)
    ecos = ((0.0, 1.0), (0.005, 0.6), (0.011, 0.42), (0.018, 0.28), (0.027, 0.16))
    for retraso, fuerza in ecos:
        tt = np.maximum(t - retraso, 0.0)
        fase = _fase_barrido(1900, 160, tt, 0.2)
        tono = np.sin(fase) + 0.35 * np.sin(2 * fase + 0.7)
        y += fuerza * tono * _caida(tt, 0.09, 0.002) * (t >= retraso)
    cuerpo = np.sin(_fase_barrido(200, 60, t, 0.12)) * _caida(t, 0.07, 0.002)
    ruido = _filtrar(azar.normal(size=len(t)), bajo=1500, alto=6000)
    chasquido = ruido * _caida(t, 0.005, 0.0005)
    y = _saturar(y, 1.5) + 0.9 * cuerpo + 0.25 * chasquido
    return _final(_normalizar(_filtrar(y, alto=7000)))


def disparo_enemigo() -> Muestras:
    """Disparo de un enemigo: grave y áspero, 0,4 s."""
    d = 0.4
    t = _tiempo(d)
    y = np.zeros_like(t)
    for retraso, fuerza in ((0.0, 1.0), (0.007, 0.5), (0.015, 0.28)):
        tt = np.maximum(t - retraso, 0.0)
        fase = _fase_barrido(950, 95, tt, 0.25)
        y += fuerza * np.tanh(3.0 * np.sin(fase)) * _caida(tt, 0.1, 0.003) * (t >= retraso)
    return _final(_normalizar(_filtrar(y, alto=3000)))


def aviso(duracion: float) -> Muestras:
    """Carga del aviso de disparo de un enemigo: tono grave que sube y vibra cada vez más."""
    t = _tiempo(duracion)
    u = t / duracion
    fase = _fase_barrido(130, 650, t, duracion)
    trem = 0.6 + 0.4 * np.sin(2 * math.pi * (7 * t + 8 * t * u))
    tono = np.sin(fase) + 0.45 * np.sin(2 * fase + 0.5) + 0.2 * np.sin(3 * fase)
    y = tono * trem * (0.3 + 0.7 * u**1.5)
    return _final(_normalizar(y, 0.8), 0.03)


def impacto() -> Muestras:
    """Impacto en un enemigo: golpe metálico grave con chispas, 0,35 s."""
    d = 0.35
    t = _tiempo(d)
    azar = _azar(21)
    y = np.zeros_like(t)
    for frecuencia, fuerza, constante in (
        (620, 1.0, 0.11),
        (915, 0.7, 0.09),
        (1330, 0.45, 0.06),
        (1790, 0.3, 0.05),
        (140, 0.9, 0.08),
    ):
        y += fuerza * np.sin(2 * math.pi * frecuencia * t) * _caida(t, constante, 0.001)
    golpe = _filtrar(azar.normal(size=len(t)), alto=2500) * _caida(t, 0.015, 0.0005)
    chispas = _filtrar(_chispazos(t, 700, 0.08, azar), bajo=900, alto=4000)
    y = 0.6 * y + 0.8 * golpe + 1.2 * chispas
    return _final(_normalizar(y))


def impacto_estacion() -> Muestras:
    """Proyectil que golpea la estación: golpe sordo en el casco, quejido metálico y
    traqueteo, 0,9 s. Acompaña a la turbulencia de la imagen."""
    d = 0.9
    t = _tiempo(d)
    azar = _azar(25)
    golpe = np.sin(_fase_barrido(75, 32, t, 0.35)) * _caida(t, 0.25, 0.003)
    quejido = np.zeros_like(t)
    vibrato = 1 + 0.01 * np.sin(2 * math.pi * 5 * t)
    for frecuencia, fuerza in ((118, 1.0), (173, 0.7), (262, 0.45), (367, 0.25)):
        quejido += fuerza * np.sin(2 * math.pi * frecuencia * t * vibrato)
    quejido *= _caida(t, 0.3, 0.01)
    traqueteo = _filtrar(_chispazos(t, 600, 0.2, azar), bajo=120, alto=1200)
    rugido = _filtrar(azar.normal(size=len(t)), alto=300) * _caida(t, 0.2, 0.004)
    y = 1.3 * golpe + 0.35 * _normalizar(quejido) + 0.45 * _normalizar(traqueteo)
    y += 0.8 * _normalizar(rugido)
    return _final(_normalizar(_saturar(y, 1.4)), 0.05)


def explosion() -> Muestras:
    """Explosión: golpe subgrave, rugido de ruido grave y una cola de crujidos, 2,5 s."""
    d = 2.5
    t = _tiempo(d)
    azar = _azar(31)
    golpe = np.sin(_fase_barrido(70, 24, t, 0.9)) * _caida(t, 0.6, 0.004)
    rugido = _filtrar(azar.normal(size=len(t)), alto=320) * _caida(t, 0.75, 0.006)
    ruido = _filtrar(azar.normal(size=len(t)), bajo=300, alto=2200)
    estallido = ruido * _caida(t, 0.05, 0.001)
    crujidos = _filtrar(_chispazos(t, 400, 0.7, azar), bajo=200, alto=1600)
    y = 1.3 * golpe + 1.7 * _normalizar(rugido) + 0.35 * _normalizar(estallido)
    y += 0.6 * _normalizar(crujidos) * _caida(t, 1.1, 0.05)
    return _final(_normalizar(_saturar(y, 1.5), 0.95), 0.08)


# --- motores, zumbidos y bucles ----------------------------------------------------------


def motor() -> Muestras:
    """Motor de un enemigo, en bucle de 1,5 s: rugido grave con un aullido de ruido.

    Suena desde la posición del enemigo. La suma de los motores de todas las naves es el
    sonido de fondo de la oleada; cada uno se oye más grave y más fuerte cuanto más cerca.
    """
    periodo = 1.5
    t = _tiempo(periodo)
    azar = _azar(41)
    # 88 ciclos en el bucle: par, así el subarmónico también lo cierra.
    f0 = _cuantizar(58.7, periodo)
    vibrato = _cuantizar(4, periodo)
    fase = 2 * math.pi * f0 * t + 0.8 * np.sin(2 * math.pi * vibrato * t)
    diente = _armonicos(fase, 12)
    # Subarmónico a media frecuencia, solo si sigue cerrando el bucle.
    sub = np.sin(fase / 2) if round(f0 * periodo) % 2 == 0 else np.zeros_like(t)
    aullido = _ruido_periodico(len(t), 220, 800, azar)
    pulso = 0.75 + 0.25 * np.sin(2 * math.pi * _cuantizar(2.7, periodo) * t)
    y = 0.45 * _normalizar(diente) + 0.25 * sub + 0.55 * _normalizar(aullido) * pulso
    return _normalizar(y, 0.85)


def zumbido() -> Muestras:
    """Zumbido de la estación, en bucle de 4 s: armónicos graves que laten despacio.

    Provisional: el sonido propio de la estación se definirá más adelante.
    """
    periodo = 4.0
    t = _tiempo(periodo)
    azar = _azar(51)
    f0 = _cuantizar(45, periodo)
    y = np.zeros_like(t)
    for k, fuerza in ((1, 1.0), (2, 0.5), (3, 0.25), (5, 0.08)):
        # Dos tonos casi iguales: el batido da vida al zumbido.
        y += fuerza * (np.sin(2 * math.pi * k * f0 * t) + np.sin(2 * math.pi * (k * f0 + 0.5) * t))
    aire = _ruido_periodico(len(t), 60, 300, azar)
    return _normalizar(_normalizar(y) + 0.25 * aire, 0.8)


def apuntado() -> Muestras:
    """Tono de la mira al apuntar, en bucle de 0,5 s; su velocidad sube con el apuntado."""
    periodo = 0.5
    t = _tiempo(periodo)
    f = _cuantizar(330, periodo)
    trem = 0.7 + 0.3 * np.sin(2 * math.pi * _cuantizar(8, periodo) * t)
    y = (np.sin(2 * math.pi * f * t) + 0.3 * np.sin(4 * math.pi * f * t)) * trem
    return _normalizar(y, 0.7)


# --- avisos de la estación ---------------------------------------------------------------


def sin_energia() -> Muestras:
    """Falta de energía (RF-11): dos golpes secos y graves, 0,3 s."""
    t = _tiempo(0.3)
    y = np.zeros_like(t)
    for inicio in (0.0, 0.14):
        tt = np.maximum(t - inicio, 0.0)
        golpe = np.tanh(4 * np.sin(2 * math.pi * 105 * tt)) * _caida(tt, 0.035, 0.002)
        y += golpe * (t >= inicio)
    return _final(_normalizar(_filtrar(y, alto=1800), 0.8))


def alarma() -> Muestras:
    """Alarma de daño (RF-14): bocina grave de dos tonos, 0,6 s."""
    t = _tiempo(0.6)
    frecuencia = np.where((t // 0.15) % 2 == 0, 330.0, 247.0)
    fase = 2 * math.pi * np.cumsum(frecuencia) / FRECUENCIA
    diente = _armonicos(fase, 9)
    y = _filtrar(diente, alto=1800) * np.clip((0.6 - t) / 0.05, 0, 1)
    return _final(_normalizar(y, 0.8))


def aturdimiento() -> Muestras:
    """Aturdimiento (RN-13): sistemas que se apagan, tono que cae con chisporroteo, 0,9 s."""
    d = 0.9
    t = _tiempo(d)
    azar = _azar(61)
    fase = _fase_barrido(380, 38, t, d)
    temblor = 0.65 + 0.35 * np.sin(2 * math.pi * 12 * t)
    tono = (np.sin(fase) + 0.45 * np.sin(2 * fase + 0.5)) * temblor
    chispas = _filtrar(_chispazos(t, 450, 0.3, azar), bajo=800, alto=3500)
    y = tono * _caida(t, 0.35, 0.02) + 1.1 * chispas
    return _final(_normalizar(y, 0.85), 0.05)


def giro_inicio() -> Muestras:
    """Arranque del giro de la cámara: servo que se pone en marcha, 0,22 s."""
    d = 0.22
    t = _tiempo(d)
    azar = _azar(65)
    fase = _fase_barrido(80, 135, t, d)
    servo = _armonicos(fase, 8) * np.clip(t / 0.03, 0, 1) * _caida(t, 0.09, 0.02)
    roce = _filtrar(azar.normal(size=len(t)), bajo=250, alto=1100) * _caida(t, 0.07, 0.015)
    clic = np.sin(2 * math.pi * 95 * t) * _caida(t, 0.015, 0.001)
    y = 0.6 * _normalizar(servo) + 0.3 * _normalizar(roce) + 0.5 * clic
    return _final(_normalizar(y, 0.75), 0.03)


def giro_fin() -> Muestras:
    """Parada del giro de la cámara: el servo baja y encaja con un golpe sordo, 0,2 s."""
    d = 0.2
    t = _tiempo(d)
    azar = _azar(66)
    fase = _fase_barrido(135, 70, t, 0.12)
    servo = _armonicos(fase, 8) * _caida(t, 0.05, 0.005)
    tope = np.sin(_fase_barrido(90, 50, t, 0.08)) * _caida(t, 0.05, 0.002)
    golpe = _filtrar(azar.normal(size=len(t)), alto=1200) * _caida(t, 0.012, 0.0005)
    y = 0.45 * _normalizar(servo) + 0.8 * tope + 0.3 * golpe
    return _final(_normalizar(y, 0.75), 0.03)


# --- interfaz ----------------------------------------------------------------------------


def menu_mover() -> Muestras:
    """Mover la selección: pitido corto y grave de ordenador, 0,05 s."""
    t = _tiempo(0.05)
    tono = np.sin(2 * math.pi * 1000 * t) + 0.15 * np.sin(2 * math.pi * 2000 * t)
    y = tono * _caida(t, 0.014, 0.001)
    return _final(_normalizar(y, 0.6), 0.005)


def menu_confirmar() -> Muestras:
    """Confirmar: dos pitidos que suben, 0,18 s."""
    t = _tiempo(0.18)
    y = np.zeros_like(t)
    for inicio, frecuencia in ((0.0, 660.0), (0.075, 880.0)):
        tt = np.maximum(t - inicio, 0.0)
        tono = np.tanh(2 * np.sin(2 * math.pi * frecuencia * tt))
        y += tono * _caida(tt, 0.045, 0.002) * (t >= inicio)
    return _final(_normalizar(_filtrar(y, alto=4000), 0.7))


def menu_error() -> Muestras:
    """Opción no disponible (CU-11, A2): zumbido grave y áspero, 0,22 s."""
    t = _tiempo(0.22)
    y = np.sign(np.sin(2 * math.pi * 120 * t)) + 0.6 * np.sign(np.sin(2 * math.pi * 128 * t))
    y = _filtrar(y, alto=1500) * np.clip(t / 0.005, 0, 1)
    return _final(_normalizar(y, 0.7), 0.03)


# --- salto -------------------------------------------------------------------------------


def salto(duracion: float) -> Muestras:
    """Salto hiperespacial, con las fases de su animación (`FASES_SALTO`).

    Un zumbido que sube en la carga, un estampido y un soplo al arrancar, un rumor
    grave y ondulante en el túnel, otro estampido al salir y la cola que se apaga.
    """
    t = _tiempo(duracion)
    u = t / duracion
    azar = _azar(71)
    carga, arranque, _, salida = FASES_SALTO
    ta, ts = arranque * duracion, salida * duracion
    # Carga: tono que sube y se hace más intenso hasta el arranque.
    gemido = np.sin(_fase_barrido(90, 700, t, ta)) + 0.35 * np.sin(
        2 * _fase_barrido(90, 700, t, ta)
    )
    gemido *= np.interp(u, [0, carga, arranque, arranque + 0.03], [0, 0.6, 1.0, 0])
    # Arranque y salida: golpe grave y soplo de ruido.
    golpes = np.zeros_like(t)
    for instante, fuerza in ((ta, 1.0), (ts, 0.75)):
        tg = np.maximum(t - instante, 0.0)
        golpe = np.sin(_fase_barrido(62, 22, tg, 0.7)) * _caida(tg, 0.45, 0.004)
        golpes += fuerza * golpe * (t >= instante)
    soplo = _filtrar(azar.normal(size=len(t)), bajo=150, alto=2800)
    soplo *= np.interp(
        u,
        [0, carga, arranque, arranque + 0.08, salida - 0.03, salida, salida + 0.1, 1],
        [0, 0.15, 1.0, 0.35, 0.35, 0.9, 0.2, 0],
    )
    # Túnel: rumor grave que ondula.
    rumor = _filtrar(azar.normal(size=len(t)), alto=160)
    rumor *= (0.7 + 0.3 * np.sin(2 * math.pi * 3.0 * t)) * np.interp(
        u, [0, arranque, arranque + 0.05, salida - 0.05, salida + 0.05, 1], [0, 0, 1, 1, 0.3, 0]
    )
    y = (
        0.45 * _normalizar(gemido)
        + 1.0 * golpes
        + 0.5 * _normalizar(soplo)
        + 0.8 * _normalizar(rumor)
    )
    return _final(_normalizar(_saturar(y, 1.2)), 0.1)


# --- archivo -----------------------------------------------------------------------------


def a_wav(muestras: Sequence[float] | Muestras) -> bytes:
    """Archivo WAV mono de 16 bits con las muestras, recortadas a [−1, 1]."""
    datos = np.clip(np.asarray(muestras, dtype=np.float64), -1.0, 1.0)
    enteros = np.round(datos * 32767).astype("<i2")
    salida = io.BytesIO()
    with wave.open(salida, "wb") as archivo:
        archivo.setnchannels(1)
        archivo.setsampwidth(2)
        archivo.setframerate(FRECUENCIA)
        archivo.writeframes(enteros.tobytes())
    return salida.getvalue()
