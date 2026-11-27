"""Paisaje de cada fondo: planetas, lunas, asteroides y polvo (`design.md`, sección 6).

Aquí está qué hay en cada uno de los cinco fondos y cómo se generan con numpy las
texturas de los planetas. No usa el motor: `paisaje.py` construye los nodos y
`fondo.py` guarda las texturas en la caché junto al cielo.

Todo está más lejos que el alcance del radar, así que nunca tapa a un enemigo ni a un
proyectil: es decorado.
"""

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np
from numpy.typing import NDArray

from atalaya.presentacion.escena.ruido import Campo, fractal, suave

#: Versión de las texturas de los planetas. Al cambiar su aspecto se sube, para no
#: reutilizar en la caché texturas generadas con la versión anterior.
VERSION = 2

#: Ancho de la textura de un planeta grande (y de uno pequeño); el alto es la mitad.
ANCHO_GRANDE = 1024
ANCHO_PEQUENO = 512
#: Radio angular, en grados, desde el que un planeta se considera grande.
_TAMANO_GRANDE = 7.0

Color = tuple[float, float, float]
Direccion = tuple[float, float, float]
Textura = NDArray[np.uint8]
#: Texturas de un planeta: color con la altura en el alfa, luz propia y nubes.
Texturas = tuple[Textura, Textura | None, Textura | None]


class Superficie(Enum):
    """Aspecto de la superficie de un planeta."""

    DESIERTO = "desierto"
    ROCOSO = "rocoso"
    GASEOSO = "gaseoso"
    HELADO = "helado"
    VOLCANICO = "volcanico"


@dataclass(frozen=True)
class Planeta:
    """Planeta o luna, siempre a la misma distancia y con su tamaño aparente."""

    superficie: Superficie
    #: Colores de la superficie: dos de base y uno de detalle (en los volcánicos, el
    #: de la lava, que brilla también en la cara oscura).
    colores: tuple[Color, Color, Color]
    direccion: Direccion
    #: Radio angular, en grados.
    tamano: float
    atmosfera: Color | None = None
    #: Anillos: color y radios interior y exterior, en radios del planeta.
    anillos: tuple[Color, float, float] | None = None
    #: Inclinación del eje: rumbo, cabeceo y alabeo, en grados.
    inclinacion: tuple[float, float, float] = (0.0, 0.0, 0.0)
    #: Giro sobre su eje, en grados por segundo.
    giro: float = 0.4
    #: Cobertura de nubes, de 0 (sin nubes) a 1, y su color.
    nubes: float = 0.0
    color_nubes: Color = (1.0, 1.0, 1.0)
    semilla: int = 0


@dataclass(frozen=True)
class Asteroides:
    """Campo de asteroides concentrado alrededor de una dirección."""

    centro: Direccion
    #: Radio angular del campo, en grados.
    extension: float
    numero: int
    color: Color
    #: Distancias mínima y máxima a la estación.
    distancia: tuple[float, float] = (1500.0, 2800.0)
    #: Radios mínimo y máximo de las rocas.
    tamano: tuple[float, float] = (6.0, 40.0)
    #: Rocas grandes y cercanas que giran sobre sí mismas.
    cercanos: int = 6
    semilla: int = 0


@dataclass(frozen=True)
class Paisaje:
    """Todo lo que hay en un fondo, además del cielo."""

    #: Dirección en que está la luz principal (el sol del cielo) y su color.
    luz_direccion: Direccion
    luz_color: Color
    planetas: tuple[Planeta, ...] = ()
    asteroides: Asteroides | None = None
    #: Color del polvo espacial que flota cerca de la estación.
    polvo: Color = (0.8, 0.8, 0.9)


_GRIS = ((0.42, 0.4, 0.38), (0.6, 0.58, 0.55), (0.25, 0.24, 0.23))

#: Los cinco paisajes, en el orden de los fondos (RN-20). Las luces apuntan a los soles
#: de `cielo.TEMAS`; donde no hay sol, al corazón de la nebulosa o de la galaxia.
PAISAJES: tuple[Paisaje, ...] = (
    Paisaje(
        luz_direccion=(0.62, 0.72, 0.30),
        luz_color=(1.0, 0.86, 0.68),
        planetas=(
            Planeta(
                Superficie.DESIERTO,
                ((0.78, 0.58, 0.36), (0.58, 0.38, 0.22), (0.9, 0.76, 0.55)),
                (-0.55, 0.55, -0.3),
                9.0,
                atmosfera=(1.0, 0.72, 0.45),
                inclinacion=(0, 0, 12),
                nubes=0.3,
                color_nubes=(0.95, 0.82, 0.64),
                semilla=1,
            ),
            Planeta(Superficie.ROCOSO, _GRIS, (-0.36, 0.66, -0.16), 1.6, semilla=2),
        ),
        asteroides=Asteroides((0.7, -0.6, 0.1), 35, 70, (0.5, 0.42, 0.34), semilla=3),
        polvo=(1.0, 0.85, 0.65),
    ),
    Paisaje(
        luz_direccion=(0.2, 0.85, 0.45),
        luz_color=(1.0, 0.62, 0.62),
        planetas=(
            Planeta(
                Superficie.ROCOSO,
                ((0.32, 0.18, 0.2), (0.18, 0.1, 0.12), (0.5, 0.3, 0.3)),
                (0.62, -0.48, 0.42),
                5.0,
                atmosfera=(1.0, 0.35, 0.45),
                nubes=0.5,
                color_nubes=(1.0, 0.9, 0.9),
                semilla=4,
            ),
        ),
        asteroides=Asteroides(
            (-0.55, -0.2, -0.5), 45, 170, (0.55, 0.4, 0.36), cercanos=9, semilla=5
        ),
        polvo=(1.0, 0.55, 0.65),
    ),
    Paisaje(
        luz_direccion=(-0.35, 0.85, 0.40),
        luz_color=(0.85, 0.92, 1.0),
        planetas=(
            Planeta(
                Superficie.HELADO,
                ((0.82, 0.9, 0.96), (0.55, 0.72, 0.88), (0.2, 0.38, 0.6)),
                (0.75, 0.45, -0.35),
                12.0,
                atmosfera=(0.55, 0.85, 1.0),
                inclinacion=(0, 0, -18),
                nubes=0.4,
                semilla=6,
            ),
            Planeta(Superficie.ROCOSO, _GRIS, (0.5, 0.68, -0.12), 1.4, semilla=7),
            Planeta(
                Superficie.HELADO,
                ((0.75, 0.8, 0.85), (0.5, 0.6, 0.7), (0.3, 0.4, 0.55)),
                (0.82, 0.2, -0.6),
                2.2,
                semilla=8,
            ),
        ),
        asteroides=Asteroides((-0.6, -0.3, 0.25), 28, 80, (0.62, 0.7, 0.78), semilla=9),
        polvo=(0.7, 0.88, 1.0),
    ),
    Paisaje(
        luz_direccion=(0.75, 0.55, -0.20),
        luz_color=(1.0, 0.92, 0.8),
        planetas=(
            Planeta(
                Superficie.GASEOSO,
                ((0.62, 0.4, 0.72), (0.88, 0.62, 0.36), (0.95, 0.85, 0.7)),
                (-0.45, 0.82, 0.16),
                15.0,
                atmosfera=(0.75, 0.55, 1.0),
                anillos=((0.85, 0.75, 0.65), 1.35, 2.3),
                inclinacion=(20, 18, -22),
                giro=0.6,
                semilla=10,
            ),
            Planeta(Superficie.ROCOSO, _GRIS, (-0.05, 0.95, 0.3), 1.5, semilla=11),
            Planeta(
                Superficie.VOLCANICO,
                ((0.2, 0.12, 0.1), (0.35, 0.2, 0.14), (1.0, 0.45, 0.1)),
                (-0.75, 0.55, -0.2),
                2.0,
                semilla=12,
            ),
        ),
        polvo=(0.85, 0.75, 1.0),
    ),
    Paisaje(
        luz_direccion=(0.0, 1.0, -0.25),
        luz_color=(1.0, 0.82, 0.6),
        planetas=(
            Planeta(
                Superficie.VOLCANICO,
                ((0.16, 0.1, 0.09), (0.3, 0.18, 0.13), (1.0, 0.42, 0.08)),
                (0.55, 0.6, 0.45),
                7.5,
                atmosfera=(1.0, 0.45, 0.2),
                nubes=0.35,
                color_nubes=(0.32, 0.28, 0.26),
                semilla=13,
            ),
        ),
        asteroides=Asteroides(
            (-0.6, -0.6, -0.4), 32, 110, (0.45, 0.38, 0.34), cercanos=7, semilla=14
        ),
        polvo=(1.0, 0.8, 0.55),
    ),
)


def ancho_textura(planeta: Planeta, divisor: int = 1) -> int:
    """Ancho de la textura del planeta: más detalle para los que se ven grandes.

    `divisor` reduce la resolución (las pruebas la usan para ir rápido).
    """
    return (ANCHO_GRANDE if planeta.tamano >= _TAMANO_GRANDE else ANCHO_PEQUENO) // divisor


def generar_texturas(indice: int, divisor: int = 1) -> list[Texturas]:
    """Texturas de los planetas del fondo `indice` (`texturas_planeta`)."""
    return [texturas_planeta(p, divisor) for p in PAISAJES[indice - 1].planetas]


def texturas_planeta(planeta: Planeta, divisor: int = 1) -> Texturas:
    """Texturas de `planeta`: color con la altura, luz propia (volcánicos) y nubes.

    Mapas de latitud y longitud: la columna recorre la longitud y la fila 0 es el polo
    sur, como las coordenadas de la esfera de `paisaje.py`. El de color tiene forma
    `(ancho / 2, ancho, 4)`, con la altura del relieve en el canal alfa (la usan los
    shaders; sin ellos, no se ve). El de nubes, en gris, tiene la mitad de resolución; solo
    lo llevan los planetas con `nubes`. El ruido se calcula sobre la dirección de cada
    punto, así que no hay costura en el meridiano de cierre.
    """
    ancho = ancho_textura(planeta, divisor)
    color, altura, emisivo = _superficie(planeta, direcciones_mapa(ancho))
    rango = float(altura.max() - altura.min())
    altura = (altura - altura.min()) / rango if rango > 1e-6 else np.full_like(altura, 0.5)
    rgba = np.concatenate([color, altura[..., None]], axis=-1)
    nubes = textura_nubes(planeta, ancho // 2) if planeta.nubes > 0 else None
    return _bytes(rgba), None if emisivo is None else _bytes(emisivo), nubes


def textura_nubes(planeta: Planeta, ancho: int) -> Textura:
    """Nubes de `planeta` en gris, forma `(ancho / 2, ancho)`: 0 despejado, 255 cubierto.

    Ruido deformado en remolinos y algo estirado a lo largo de los paralelos.
    """
    d = direcciones_mapa(ancho)
    s = planeta.semilla * 97 + 500
    remolino = np.stack([fractal(d * 1.8 + np.float32(k * 3.1), s + k, 3) for k in range(3)], -1)
    p = (d + (remolino - 0.5) * np.float32(0.7)) * np.asarray((3.0, 3.0, 5.0), np.float32)
    ruido = fractal(p, s + 7, 5)
    # El ruido fractal se concentra cerca de 0,5: el umbral sale de su reparto real, así
    # la parte cubierta es la que pide `nubes`.
    umbral = float(np.quantile(ruido, 1.0 - planeta.nubes))
    cubierta = suave(ruido, umbral, umbral + 1.2 * float(ruido.std()))
    resultado: Textura = (cubierta * 255.0 + 0.5).astype(np.uint8)
    return resultado


def _superficie(planeta: Planeta, d: Campo) -> tuple[Campo, Campo, Campo | None]:
    """Color, altura (sin normalizar) y luz propia de cada punto de la superficie."""
    s = planeta.semilla * 97
    c0, c1, c2 = (np.asarray(c, dtype=np.float32) for c in planeta.colores)
    latitud = np.arcsin(np.clip(d[..., 2], -1.0, 1.0))
    emisivo: Campo | None = None
    altura: Campo
    if planeta.superficie is Superficie.GASEOSO:
        deformacion = fractal(d * 1.6, s, 3)
        desvio = (deformacion - 0.5) * 6.0
        # Bandas de anchos distintos: dos frecuencias que no son múltiplo una de otra.
        bandas = (
            0.5
            + 0.35 * np.sin(latitud * 13.0 + desvio)
            + 0.15 * np.sin(latitud * 31.0 + desvio * 1.7)
        )
        # Vetas finas a lo largo de los paralelos: ruido estirado en longitud.
        vetas = fractal(d * np.asarray((2.5, 2.5, 16.0), np.float32), s + 1)
        color = _mezcla(c0, c1, np.clip(0.15 + 0.7 * bandas + 0.35 * (vetas - 0.5), 0, 1))
        claro = suave(fractal(d * 3.0, s + 2), 0.55, 0.8) * 0.45
        color = _mezcla(color, c2, claro)
        # Una gran tormenta ovalada en el hemisferio sur.
        tormenta = _mancha(d, latitud=-0.42, longitud=1.3, ancho=0.18, alto=0.09)
        color = _mezcla(color, c2 * np.float32(0.9) + c1 * np.float32(0.1), tormenta * 0.85)
        # Sin relieve: un gigante gaseoso no tiene suelo.
        altura = np.zeros(d.shape[:-1], dtype=np.float32)
    elif planeta.superficie is Superficie.HELADO:
        base = fractal(d * 3.0, s)
        color = _mezcla(c0, c1, suave(base, 0.3, 0.75))
        grietas = _crestas(fractal(d * 5.0, s + 1), 0.95, 0.995)
        color = _mezcla(color, c2, grietas * 0.4)
        casquete = suave(np.abs(np.sin(latitud)), 0.82, 0.92)
        color = _mezcla(color, np.asarray((0.95, 0.97, 1.0), np.float32), casquete)
        altura = 0.6 * base - 0.5 * grietas + 0.15 * fractal(d * 12.0, s + 3)
    elif planeta.superficie is Superficie.VOLCANICO:
        base = fractal(d * 3.0, s)
        color = _mezcla(c0, c1, base)
        grietas = _crestas(fractal(d * 4.0, s + 1), 0.87, 0.975)
        color = _mezcla(color, c0 * np.float32(0.5), grietas)
        brillo = grietas * (0.55 + 0.45 * fractal(d * 9.0, s + 2))
        emisivo = brillo[..., None] * c2
        altura = base - 0.6 * grietas + 0.2 * fractal(d * 14.0, s + 3)
    else:
        base = fractal(d * 2.5, s)
        detalle = fractal(d * 8.0, s + 1)
        color = _mezcla(c0, c1, suave(base, 0.25, 0.75))
        altura = 0.6 * base + 0.25 * detalle
        if planeta.superficie is Superficie.DESIERTO:
            dunas = 0.5 + 0.5 * np.sin(latitud * 34.0 + base * 9.0)
            color = _mezcla(color, c2, dunas * detalle * 0.45)
            altura = altura + 0.12 * dunas * detalle
        color = color * (0.85 + 0.3 * detalle[..., None])
        numero = 60 if planeta.superficie is Superficie.ROCOSO else 25
        crateres = _crateres(d, np.random.default_rng(s), numero)
        color = color * crateres[..., None]
        # Fondo hundido y borde levantado: el relieve sigue a la luz de los cráteres.
        altura = altura + 1.6 * (crateres - 1.0)
    return color, altura, emisivo


def direcciones_mapa(ancho: int) -> Campo:
    """Dirección de cada punto del mapa de latitud y longitud; forma `(ancho / 2, ancho, 3)`."""
    alto = ancho // 2
    longitud = (np.arange(ancho, dtype=np.float32) + 0.5) / ancho * np.float32(2 * math.pi)
    latitud = (np.arange(alto, dtype=np.float32) + 0.5) / alto * np.float32(math.pi) - np.float32(
        math.pi / 2
    )
    lat, lon = np.meshgrid(latitud, longitud, indexing="ij")
    coseno = np.cos(lat)
    return np.stack([coseno * np.cos(lon), coseno * np.sin(lon), np.sin(lat)], axis=-1)


def textura_anillos(color: Color, semilla: int, ancho: int = 256) -> Textura:
    """Bandas de los anillos, de dentro a fuera, con su transparencia; forma `(1, ancho, 4)`."""
    azar = np.random.default_rng(semilla)
    r = np.linspace(0.0, 1.0, ancho, dtype=np.float32)
    densidad = np.zeros(ancho, dtype=np.float32)
    for _ in range(9):
        centro, anchura = azar.random(), azar.uniform(0.03, 0.14)
        densidad += azar.uniform(0.3, 1.0) * np.exp(-(((r - centro) / anchura) ** 2))
    # Una división oscura, y bordes que se desvanecen.
    densidad *= 1 - 0.85 * np.exp(-(((r - 0.62) / 0.025) ** 2))
    densidad *= np.clip(r / 0.05, 0, 1) * np.clip((1 - r) / 0.08, 0, 1)
    densidad = np.clip(densidad / max(float(densidad.max()), 1e-6), 0, 1)
    tono = 0.75 + 0.25 * np.sin(r * 40.0 + azar.random() * 6)
    rgb = np.asarray(color, np.float32)[None, :] * tono[:, None]
    imagen = np.concatenate([rgb, (0.85 * densidad)[:, None]], axis=-1)
    return _bytes(imagen)[None, ...]


def _mezcla(a: Campo, b: Campo, t: Campo | float) -> Campo:
    """Mezcla lineal de dos colores (o campos de color) según `t`."""
    peso = np.asarray(t, dtype=np.float32)
    if peso.ndim and peso.shape[-1:] != (3,):
        peso = peso[..., None]
    resultado: Campo = a + (b - a) * peso
    return resultado


def _crateres(d: Campo, azar: np.random.Generator, numero: int) -> Campo:
    """Factor de luz de los cráteres: fondo hundido y oscuro, y borde claro.

    Muchos pequeños y pocos grandes, en direcciones al azar.
    """
    factor = np.ones(d.shape[:-1], dtype=np.float32)
    for _ in range(numero):
        z = azar.uniform(-1, 1)
        angulo = azar.uniform(0, 2 * math.pi)
        r = math.sqrt(1 - z * z)
        centro = np.asarray((r * math.cos(angulo), r * math.sin(angulo), z), np.float32)
        radio = 0.02 + 0.16 * azar.random() ** 3
        distancia = np.arccos(np.clip(d @ centro, -1, 1))
        dentro = suave(np.float32(radio) - distancia, 0.0, radio * 0.35)
        borde = np.exp(-(((distancia - radio) / (radio * 0.18)) ** 2))
        factor *= 1 - 0.28 * dentro + 0.22 * borde
    return factor


def _crestas(ruido: Campo, a: float, b: float) -> Campo:
    """Líneas finas donde el ruido pasa por su valor medio: grietas, cráteres, vetas."""
    return suave(1.0 - np.abs(ruido - 0.5) * 2.0, a, b)


def _mancha(d: Campo, latitud: float, longitud: float, ancho: float, alto: float) -> Campo:
    """Óvalo suave centrado en (`latitud`, `longitud`), en radianes."""
    centro = np.asarray(
        (
            math.cos(latitud) * math.cos(longitud),
            math.cos(latitud) * math.sin(longitud),
            math.sin(latitud),
        ),
        dtype=np.float32,
    )
    lat = np.arcsin(np.clip(d[..., 2], -1, 1))
    cercania = np.clip(d @ centro, -1, 1)
    angulo = np.arccos(cercania)
    # Más ancho en longitud que en latitud.
    dlat = (lat - latitud) / alto
    dlon = np.sqrt(np.maximum(angulo**2 - (lat - latitud) ** 2, 0)) / ancho
    mancha: Campo = np.exp(-(dlat**2 + dlon**2))
    return mancha


def _bytes(color: Campo) -> Textura:
    resultado: Textura = (np.clip(color, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
    return resultado
