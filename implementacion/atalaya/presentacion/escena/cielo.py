"""Generación de los cinco cielos espaciales con numpy (`design.md`, sección 6; RN-20).

Cada cielo es un mapa cúbico de seis caras: color de fondo, banda galáctica, nebulosas,
polvo oscuro, soles y estrellas. Todo se calcula a partir de la dirección de cada píxel,
así que no hay costuras entre caras. Con la misma semilla, cada cielo sale siempre igual.

Este módulo no usa el motor: devuelve las caras como matrices de numpy. `fondo.py` las
convierte en texturas y las guarda en la caché.

Las nebulosas son suaves, así que se calculan a baja resolución y se amplían. Solo las
estrellas y los soles se dibujan a la resolución final.
"""

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray

from atalaya.presentacion.escena.ruido import fractal, suave

#: Versión del generador. Al cambiar el aspecto de un cielo se sube, para no reutilizar
#: en la caché cielos generados con la versión anterior.
VERSION = 1

#: Lado de cada cara en píxeles. Con 1024 px por cada 90° y 1080 px de alto para 70° de
#: campo de visión, la textura casi nunca se reduce en pantalla y las estrellas no parpadean.
LADO_CARA = 1024

#: Lado de cada cara al calcular nebulosas, banda y polvo, antes de ampliar.
_LADO_NUBES = 256

Color = tuple[float, float, float]
Direccion = tuple[float, float, float]
Caras = NDArray[np.uint8]
#: Campo de valores en coma flotante; se calculan en float32 para ir más rápido.
_Campo = NDArray[np.floating[Any]]


@dataclass(frozen=True)
class Nube:
    """Nebulosa: ruido fractal con un color, concentrado alrededor de una dirección."""

    color: Color
    intensidad: float
    centro: Direccion
    #: Radio angular de la zona de la nebulosa, en grados.
    extension: float
    #: Frecuencia del ruido: más alta, nubes más pequeñas.
    escala: float = 2.2
    #: Valor del ruido desde el que hay nube, de 0 a 1: más alto, menos nube.
    umbral: float = 0.45
    #: Desplazamiento del ruido para que cada nube tenga su propio dibujo.
    semilla: int = 0


@dataclass(frozen=True)
class Sol:
    """Sol del sistema: disco brillante con un halo amplio."""

    direccion: Direccion
    color: Color
    #: Radio del disco, en grados.
    radio: float
    #: Intensidad del halo; el disco siempre satura a blanco teñido.
    halo: float


@dataclass(frozen=True)
class Tema:
    """Aspecto de un cielo."""

    nombre: str
    color_fondo: Color
    #: Normal del plano de la galaxia: la banda galáctica es el gran círculo que le es
    #: perpendicular.
    plano_galaxia: Direccion
    banda: float
    color_banda: Color
    #: Polvo oscuro sobre la banda y las nebulosas, de 0 (nada) a 1 (opaco).
    polvo: float
    estrellas: int
    #: Parte de las estrellas que se concentra en la banda galáctica.
    estrellas_banda: float
    tonos: tuple[Color, ...]
    #: Estrellas brillantes con halo y destellos en cruz.
    brillantes: int
    nubes: tuple[Nube, ...] = ()
    soles: tuple[Sol, ...] = ()
    #: Bulbo central de la galaxia: dirección, color e intensidad.
    nucleo: tuple[Direccion, Color, float] | None = None
    exposicion: float = 1.0
    semilla: int = field(default=0)


_TONOS_CALIDOS = ((1.0, 0.82, 0.66), (1.0, 0.92, 0.82), (1.0, 1.0, 1.0), (0.85, 0.9, 1.0))
_TONOS_FRIOS = ((0.75, 0.85, 1.0), (0.85, 0.92, 1.0), (1.0, 1.0, 1.0), (0.7, 0.9, 1.0))

#: Los cinco cielos, uno por cada tramo de 10 oleadas (RN-20).
TEMAS: tuple[Tema, ...] = (
    Tema(
        nombre="Borde exterior",
        color_fondo=(0.004, 0.005, 0.012),
        plano_galaxia=(0.2, -0.3, 0.93),
        banda=0.14,
        color_banda=(0.8, 0.72, 0.6),
        polvo=0.35,
        estrellas=9000,
        estrellas_banda=0.3,
        tonos=_TONOS_CALIDOS,
        brillantes=14,
        nubes=(
            Nube((0.60, 0.34, 0.15), 0.24, (-0.6, 0.5, 0.2), 60, escala=1.8, semilla=1),
            Nube((0.22, 0.30, 0.58), 0.16, (0.5, -0.7, -0.3), 55, escala=2.0, semilla=2),
        ),
        soles=(
            Sol((0.62, 0.72, 0.30), (1.0, 0.72, 0.38), 0.9, 0.55),
            Sol((0.57, 0.76, 0.28), (1.0, 0.56, 0.30), 0.6, 0.35),
        ),
        semilla=11,
    ),
    Tema(
        nombre="Nebulosa carmesí",
        color_fondo=(0.008, 0.003, 0.008),
        plano_galaxia=(0.8, 0.1, 0.6),
        banda=0.08,
        color_banda=(0.8, 0.6, 0.6),
        polvo=0.75,
        estrellas=12000,
        estrellas_banda=0.3,
        tonos=_TONOS_CALIDOS,
        brillantes=22,
        nubes=(
            Nube((0.72, 0.10, 0.22), 0.68, (0.1, 0.9, 0.3), 80, escala=1.9, semilla=3),
            Nube((0.45, 0.12, 0.55), 0.40, (-0.5, 0.6, -0.4), 70, escala=2.4, semilla=4),
            Nube(
                (1.0, 0.48, 0.38), 0.30, (0.2, 0.85, 0.45), 25, escala=3.2, umbral=0.55, semilla=5
            ),
            Nube((0.30, 0.08, 0.20), 0.25, (0.0, -0.9, -0.2), 70, escala=2.0, semilla=6),
        ),
        semilla=22,
    ),
    Tema(
        nombre="Sistema helado",
        color_fondo=(0.003, 0.007, 0.014),
        plano_galaxia=(-0.4, 0.2, 0.9),
        banda=0.12,
        color_banda=(0.62, 0.72, 0.9),
        polvo=0.4,
        estrellas=10000,
        estrellas_banda=0.35,
        tonos=_TONOS_FRIOS,
        brillantes=18,
        nubes=(
            Nube((0.04, 0.58, 0.66), 0.46, (-0.7, 0.3, 0.5), 65, escala=2.1, semilla=7),
            Nube((0.30, 0.50, 0.95), 0.26, (0.6, 0.4, -0.6), 60, escala=2.6, semilla=8),
        ),
        soles=(Sol((-0.35, 0.85, 0.40), (0.85, 0.92, 1.0), 0.45, 0.30),),
        semilla=33,
    ),
    Tema(
        nombre="Gigante gaseoso",
        color_fondo=(0.006, 0.004, 0.012),
        plano_galaxia=(0.3, 0.6, 0.75),
        banda=0.10,
        color_banda=(0.75, 0.65, 0.8),
        polvo=0.5,
        estrellas=10000,
        estrellas_banda=0.3,
        tonos=_TONOS_CALIDOS,
        brillantes=16,
        nubes=(
            Nube((0.42, 0.18, 0.62), 0.36, (0.7, -0.2, 0.5), 75, escala=2.0, semilla=9),
            Nube((0.85, 0.52, 0.18), 0.22, (-0.4, -0.7, 0.3), 55, escala=2.5, semilla=10),
            Nube((0.25, 0.12, 0.40), 0.20, (-0.3, 0.8, -0.4), 70, escala=1.8, semilla=11),
        ),
        soles=(Sol((0.75, 0.55, -0.20), (1.0, 0.9, 0.75), 0.7, 0.45),),
        semilla=44,
    ),
    Tema(
        nombre="Núcleo galáctico",
        color_fondo=(0.005, 0.005, 0.010),
        plano_galaxia=(0.0, 0.25, 0.97),
        banda=0.2,
        color_banda=(0.95, 0.78, 0.55),
        polvo=0.85,
        estrellas=16000,
        estrellas_banda=0.55,
        tonos=_TONOS_CALIDOS,
        brillantes=28,
        nubes=(
            Nube((0.10, 0.66, 0.42), 0.32, (-0.6, -0.5, 0.5), 50, escala=2.3, semilla=12),
            Nube((0.52, 0.20, 0.72), 0.34, (0.6, -0.4, -0.6), 55, escala=2.3, semilla=13),
        ),
        nucleo=((0.0, 1.0, -0.25), (1.0, 0.7, 0.38), 0.45),
        semilla=55,
    ),
)


def generar(indice: int, lado: int = LADO_CARA) -> Caras:
    """Las seis caras del cielo `indice` (de 1 a 5), en RGB de 8 bits.

    Forma `(6, lado, lado, 3)`. Caras en el orden +x, −x, +y, −y, +z, −z, con el
    convenio de los mapas cúbicos de OpenGL: la columna crece con s y la fila con t
    (`_proyectar`).
    """
    if not 1 <= indice <= len(TEMAS):
        raise ValueError(f"El cielo {indice} no existe: van de 1 a {len(TEMAS)}")
    tema = TEMAS[indice - 1]
    azar = np.random.default_rng(tema.semilla)
    nubes = _campos_nubes(tema, min(lado, _LADO_NUBES))
    imagen = _estrellas(tema, azar, lado)
    for cara in range(6):
        ampliada = _ampliar(nubes[cara], lado)
        # El polvo oscurece las nubes y las estrellas que hay detrás; los soles, no.
        imagen[cara] += ampliada[..., :3]
        imagen[cara] *= ampliada[..., 3:4]
        if tema.soles:
            imagen[cara] += _soles(tema, _direcciones_cara(cara, lado))
    imagen += np.asarray(tema.color_fondo, dtype=np.float32)
    # Curva de exposición: los brillos fuertes se acercan a 1 sin cortarse de golpe.
    # Las operaciones se hacen en el sitio para no crear copias de la imagen entera.
    imagen *= np.float32(-tema.exposicion * 1.6)
    np.exp(imagen, out=imagen)
    np.subtract(np.float32(255.5), imagen * np.float32(255.0), out=imagen)
    # Un poco de ruido, en mosaico, evita escalones de color en los degradados oscuros.
    tramado = azar.random((64, 64, 1), dtype=np.float32) - np.float32(0.5)
    repeticiones = (lado + 63) // 64
    imagen += np.tile(tramado, (repeticiones, repeticiones, 1))[:lado, :lado]
    np.clip(imagen, 0.0, 255.0, out=imagen)
    return imagen.astype(np.uint8)


# --- geometría -----------------------------------------------------------------------


def _direcciones_cara(cara: int, lado: int, bordes: bool = False) -> _Campo:
    """Dirección unitaria del centro de cada píxel de `cara`; forma `(lado, lado, 3)`.

    Inversa de `_proyectar`: (s, t) en [−1, 1]; la columna crece con s y la fila con t.
    Con `bordes`, la primera y la última fila y columna caen justo en el borde de la
    cara: dos caras vecinas comparten esos puntos, y al ampliar no queda costura.
    """
    centros: _Campo
    if bordes:
        centros = np.linspace(-1.0, 1.0, lado, dtype=np.float32)
    else:
        centros = (np.arange(lado, dtype=np.float32) + 0.5) / lado * 2.0 - 1.0
    t, s = np.meshgrid(centros, centros, indexing="ij")
    uno = np.ones_like(s)
    ejes = {
        0: (uno, -t, -s),
        1: (-uno, -t, s),
        2: (s, uno, t),
        3: (s, -uno, -t),
        4: (s, -t, uno),
        5: (-s, -t, -uno),
    }[cara]
    d = np.stack(ejes, axis=-1)
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    return d.astype(np.float32)


def _unitario(v: Direccion) -> NDArray[np.float32]:
    a = np.asarray(v, dtype=np.float32)
    return a / np.float32(np.linalg.norm(a))


def _ampliar(campo: _Campo, lado: int) -> _Campo:
    """Amplía una cara `(n, n, c)`, muestreada con bordes, a `(lado, lado, c)`."""
    n = campo.shape[0]
    if n == lado:
        return campo.copy()
    posiciones = (np.arange(lado, dtype=np.float32) + 0.5) / lado * (n - 1)
    i0 = np.floor(posiciones).astype(np.int64)
    i1 = np.minimum(i0 + 1, n - 1)
    f = (posiciones - i0)[:, None, None]
    filas = campo[i0] * (1 - f) + campo[i1] * f
    g = (posiciones - i0)[None, :, None]
    ampliado: _Campo = (filas[:, i0] * (1 - g) + filas[:, i1] * g).astype(np.float32)
    return ampliado


# --- capas ---------------------------------------------------------------------------


def _campos_nubes(tema: Tema, n: int) -> _Campo:
    """Color de nebulosas y banda (canales 0 a 2) y paso de luz del polvo (canal 3).

    Forma `(6, n, n, 4)`. El polvo vale 1 donde no hay y baja hasta 1 − polvo.
    """
    d = np.stack([_direcciones_cara(c, n, bordes=True) for c in range(6)])
    color = np.zeros((6, n, n, 3), dtype=np.float32)
    # Deformación del espacio: las nubes salen en filamentos y no en manchas redondas.
    deformacion = np.stack(
        [fractal(d * 1.7 + np.float32(k * 5.3), tema.semilla + 7 * k, 3) for k in range(3)],
        axis=-1,
    )
    p = d + (deformacion - 0.5) * np.float32(0.6)
    normal = _unitario(tema.plano_galaxia)
    altura = d @ normal
    banda = np.exp(-(altura**2) / np.float32(2 * 0.18**2))
    textura_banda = fractal(p * 2.5, tema.semilla + 1, 5)
    brillo_banda = banda * suave(textura_banda, 0.2, 0.8) * np.float32(tema.banda)
    if tema.nucleo is not None:
        direccion, color_nucleo, fuerza = tema.nucleo
        cercania = np.clip(d @ _unitario(direccion), -1.0, 1.0)
        angulo = np.arccos(cercania)
        bulbo = np.exp(-(angulo**2) / np.float32(2 * 0.32**2)) * np.exp(
            -(altura**2) / np.float32(2 * 0.2**2)
        )
        color += (bulbo * np.float32(fuerza))[..., None] * np.asarray(color_nucleo, np.float32)
    color += brillo_banda[..., None] * np.asarray(tema.color_banda, dtype=np.float32)
    for nube in tema.nubes:
        cercania = np.clip(d @ _unitario(nube.centro), -1.0, 1.0)
        angulo = np.degrees(np.arccos(cercania))
        zona = np.exp(-((angulo / nube.extension) ** 2))
        ruido = fractal(p * np.float32(nube.escala), tema.semilla + 1000 + 31 * nube.semilla)
        densidad = suave(ruido, nube.umbral, nube.umbral + 0.3) * zona
        # Brillo interior más intenso donde la nube es más densa.
        densidad = densidad * (0.55 + 0.45 * densidad)
        color += (densidad * np.float32(nube.intensidad))[..., None] * np.asarray(
            nube.color, dtype=np.float32
        )
    # Polvo en filamentos finos sobre las nubes y en nubes oscuras a lo largo del plano
    # de la galaxia, como las franjas oscuras de una vía láctea.
    ruido_polvo = fractal(p * 4.0 + np.float32(19.1), tema.semilla + 2, 5)
    venas = suave(1.0 - np.abs(ruido_polvo - 0.5) * 2.0, 0.65, 0.95)
    manchas = suave(fractal(p * 3.0 + np.float32(7.7), tema.semilla + 3, 5), 0.48, 0.72)
    plano = np.exp(-(altura**2) / np.float32(2 * 0.07**2))
    oscuridad = np.clip(0.6 * venas + manchas * plano, 0.0, 1.0)
    presencia = np.clip(banda * 1.3 + np.clip(color.sum(axis=-1) * 2.0, 0.0, 1.0), 0.0, 1.0)
    paso = 1.0 - np.float32(tema.polvo) * oscuridad * presencia
    return np.concatenate([color, paso[..., None].astype(np.float32)], axis=-1)


def _soles(tema: Tema, direcciones: _Campo) -> _Campo:
    """Luz de los soles en cada píxel de una cara: disco más halo."""
    luz = np.zeros(direcciones.shape, dtype=np.float32)
    for sol in tema.soles:
        cercania = np.clip(direcciones @ _unitario(sol.direccion), -1.0, 1.0)
        if float(cercania.max()) < math.cos(math.radians(40)):
            continue
        angulo = np.degrees(np.arccos(cercania))
        disco = suave(np.float32(sol.radio * 1.15) - angulo, 0.0, sol.radio * 0.3) * 6.0
        halo = np.float32(sol.halo) * (
            np.exp(-angulo / np.float32(2.5)) + 0.35 * np.exp(-angulo / np.float32(12.0))
        )
        luz += (disco + halo)[..., None] * np.asarray(sol.color, dtype=np.float32)
    return luz


def _estrellas(tema: Tema, azar: np.random.Generator, lado: int) -> _Campo:
    """Estrellas sobre las seis caras; forma `(6, lado, lado, 3)`."""
    escala = lado / LADO_CARA
    numero = int(tema.estrellas * escala**2)
    en_banda = int(numero * tema.estrellas_banda)
    direcciones = _direcciones_al_azar(azar, numero - en_banda)
    direcciones = np.concatenate([direcciones, _direcciones_banda(azar, tema, en_banda)])
    brillo = (0.25 + 0.75 * azar.random(len(direcciones)) ** 3).astype(np.float32)
    tonos = np.asarray(tema.tonos, dtype=np.float32)[
        azar.integers(0, len(tema.tonos), len(direcciones))
    ]
    imagen = np.zeros((6, lado, lado, 3), dtype=np.float32)
    _salpicar(imagen, direcciones, brillo, tonos, escala)
    # Estrellas brillantes: halo amplio y destellos en cruz.
    grandes = _direcciones_al_azar(azar, tema.brillantes)
    tonos_grandes = np.asarray(tema.tonos, dtype=np.float32)[
        azar.integers(0, len(tema.tonos), tema.brillantes)
    ]
    fuerza = (0.6 + 0.4 * azar.random(tema.brillantes)).astype(np.float32)
    _brillantes(imagen, grandes, fuerza, tonos_grandes, escala)
    return imagen


def _direcciones_al_azar(azar: np.random.Generator, n: int) -> NDArray[np.float64]:
    z = azar.uniform(-1, 1, n)
    angulo = azar.uniform(0, 2 * math.pi, n)
    r = np.sqrt(1 - z * z)
    return np.stack([r * np.cos(angulo), r * np.sin(angulo), z], axis=-1)


def _direcciones_banda(azar: np.random.Generator, tema: Tema, n: int) -> NDArray[np.float64]:
    """Direcciones cerca del gran círculo de la banda galáctica."""
    normal = np.asarray(_unitario(tema.plano_galaxia), dtype=np.float64)
    auxiliar = np.array([1.0, 0.0, 0.0]) if abs(normal[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u = np.cross(normal, auxiliar)
    u /= np.linalg.norm(u)
    v = np.cross(normal, u)
    angulo = azar.uniform(0, 2 * math.pi, n)
    altura = np.clip(azar.normal(0, 0.12, n), -0.9, 0.9)
    r = np.sqrt(1 - altura**2)
    direcciones: NDArray[np.float64] = (
        r[:, None] * (np.cos(angulo)[:, None] * u + np.sin(angulo)[:, None] * v)
        + altura[:, None] * normal
    )
    return direcciones


def _proyectar(
    d: NDArray[np.float64],
) -> tuple[NDArray[np.int64], NDArray[np.float64], NDArray[np.float64]]:
    """Cara (0 a 5: +x, −x, +y, −y, +z, −z) y coordenadas (s, t) en [−1, 1] de cada dirección."""
    x, y, z = d[:, 0], d[:, 1], d[:, 2]
    ax, ay, az = np.abs(x), np.abs(y), np.abs(z)
    cara = np.where(
        (ax >= ay) & (ax >= az),
        np.where(x > 0, 0, 1),
        np.where(ay >= az, np.where(y > 0, 2, 3), np.where(z > 0, 4, 5)),
    )
    s = np.select(
        [cara == 0, cara == 1, cara == 2, cara == 3, cara == 4],
        [-z / ax, z / ax, x / ay, x / ay, x / az],
        -x / az,
    )
    t = np.select(
        [cara == 0, cara == 1, cara == 2, cara == 3, cara == 4],
        [-y / ax, -y / ax, z / ay, -z / ay, -y / az],
        -y / az,
    )
    return cara.astype(np.int64), s, t


def _salpicar(
    imagen: _Campo,
    direcciones: NDArray[np.float64],
    brillo: _Campo,
    tonos: _Campo,
    escala: float,
) -> None:
    """Dibuja estrellas suaves sumando luz a los píxeles de alrededor de cada una.

    En las esquinas de una cara cada píxel abarca menos ángulo que en el centro: el
    radio en píxeles crece hacia las esquinas para que las estrellas se vean iguales.
    """
    lado = imagen.shape[1]
    cara, s, t = _proyectar(direcciones)
    x = (s + 1) / 2 * lado
    y = (t + 1) / 2 * lado
    radio = np.where(brillo > 0.7, 1.6, 1.0) * (1 + s * s + t * t) ** 0.75 * max(escala, 0.5)
    alcance = 4
    for dy in range(-alcance, alcance + 1):
        for dx in range(-alcance, alcance + 1):
            px = np.floor(x).astype(np.int64) + dx
            py = np.floor(y).astype(np.int64) + dy
            distancia = np.hypot(px + 0.5 - x, py + 0.5 - y)
            intensidad = brillo * np.maximum(0.0, 1 - distancia / (radio + 0.5)) ** 2
            dentro = (px >= 0) & (px < lado) & (py >= 0) & (py < lado) & (intensidad > 0)
            np.add.at(
                imagen,
                (cara[dentro], py[dentro], px[dentro]),
                intensidad[dentro, None].astype(np.float32) * tonos[dentro],
            )


def _brillantes(
    imagen: _Campo,
    direcciones: NDArray[np.float64],
    fuerza: _Campo,
    tonos: _Campo,
    escala: float,
) -> None:
    """Estrellas muy brillantes: núcleo, halo y cuatro destellos en cruz."""
    lado = imagen.shape[1]
    cara, s, t = _proyectar(direcciones)
    alcance = max(4, round(22 * escala))
    offsets = np.arange(-alcance, alcance + 1)
    oy, ox = np.meshgrid(offsets, offsets, indexing="ij")
    r = np.hypot(ox, oy).astype(np.float32) / np.float32(max(escala, 0.25))
    nucleo = np.exp(-(r**2) / 2.0)
    halo = 0.18 * np.exp(-r / 4.0)
    cruz = 0.35 * (np.exp(-np.abs(oy) * 1.5) * np.exp(-np.abs(ox) / 7.0)) + 0.35 * (
        np.exp(-np.abs(ox) * 1.5) * np.exp(-np.abs(oy) / 7.0)
    )
    patron = (nucleo + halo + cruz).astype(np.float32)
    for i in range(len(direcciones)):
        cx = int((s[i] + 1) / 2 * lado)
        cy = int((t[i] + 1) / 2 * lado)
        y0, y1 = max(0, cy - alcance), min(lado, cy + alcance + 1)
        x0, x1 = max(0, cx - alcance), min(lado, cx + alcance + 1)
        if y0 >= y1 or x0 >= x1:
            continue
        trozo = patron[
            y0 - (cy - alcance) : y1 - (cy - alcance), x0 - (cx - alcance) : x1 - (cx - alcance)
        ]
        imagen[cara[i], y0:y1, x0:x1] += (trozo * fuerza[i])[..., None] * tonos[i]
