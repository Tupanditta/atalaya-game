"""Mira del jugador (`interfaz.md`, «Mira»).

Cuatro arcos con una marca exterior en cada hueco y un punto central. Al apuntar, la
mira se encoge, pasa de **texto** a **acento**, gira 45° hasta quedar en aspa, los arcos
cierran sus huecos y las marcas se acercan; con la mira al mínimo aparece un rombo
alrededor del punto. Al disparar, un anillo se expande y se desvanece desde la mira.
Un contorno oscuro bajo cada trazo la hace legible sobre nebulosas brillantes.

Aturdida, la mira queda bloqueada: círculo discontinuo y punto, al 40 %, sin marcas.
"""

import math

from panda3d.core import NodePath

from atalaya.presentacion.hud.dibujo import (
    Color,
    Punto,
    arco,
    capa,
    cinta,
    circulo,
    color,
    mezclar,
    poligono,
)
from atalaya.presentacion.hud.estilo import ACENTO, ALTO_DISENO, ANCHO_DISENO, TEXTO

#: Orden de dibujo de las capas de la mira: sombra, brillo y trazo, de abajo a arriba.
ORDEN_SOMBRA = 6
ORDEN_BRILLO = 7
ORDEN_TRAZO = 8

#: Centro de la mira en coordenadas de diseño; el ratón la desplaza desde aquí.
CENTRO: Punto = (ANCHO_DISENO / 2, ALTO_DISENO / 2)

GROSOR = 2.0
#: Contorno oscuro bajo los trazos: más ancho que el trazo y semitransparente.
SOMBRA = color("#000000", 0.45)
GROSOR_SOMBRA = GROSOR + 2.5
#: Brillo suave al apuntar (`interfaz.md`, «Estilo»): crece con el progreso.
GROSOR_BRILLO = 8.0
OPACIDAD_BRILLO = 0.22
OPACIDAD_TRAZO = 0.95

#: Arcos: amplitud de cada uno con la mira normal y con la mira al mínimo, en grados.
ARCO_NORMAL = 56.0
ARCO_MINIMO = 74.0
#: Giro de la mira al mínimo.
GIRO_MAXIMO = 45.0
#: Marcas exteriores: separación del anillo y largo, con la mira normal y al mínimo.
SEPARACION_NORMAL, SEPARACION_MINIMA = 7.0, 3.0
LARGO_NORMAL, LARGO_MINIMO = 10.0, 7.0
#: Punto central y rombo de mira al mínimo.
RADIO_PUNTO = 2.5
RADIO_SOMBRA_PUNTO = 4.0
RADIO_ROMBO = 7.0
GROSOR_ROMBO = 1.5

#: Mira bloqueada por aturdimiento: trazo discontinuo y opacidad al 40 %.
OPACIDAD_ATURDIDA = 0.4
TRAZO_DISCONTINUO = 8.0
HUECO_DISCONTINUO = 6.0

#: Anillo de disparo: dura 0,18 s y se aleja 22 px de la mira.
DURACION_PULSO = 0.18
EXPANSION_PULSO = 22.0
OPACIDAD_PULSO = 0.8


def suavizar(t: float) -> float:
    """Curva suave entre 0 y 1: arranca y llega despacio."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def arcos_mira(radio: float, progreso: float) -> list[list[Punto]]:
    """Los cuatro arcos del anillo: en diagonal con la mira normal y en cruz al mínimo."""
    p = suavizar(progreso)
    amplitud = ARCO_NORMAL + (ARCO_MINIMO - ARCO_NORMAL) * p
    giro = GIRO_MAXIMO * p
    return [
        arco(CENTRO, radio, centro - amplitud / 2, centro + amplitud / 2, 16)
        for centro in (45 + giro + 90 * k for k in range(4))
    ]


def marcas_mira(radio: float, progreso: float) -> list[list[Punto]]:
    """Las cuatro marcas exteriores, en los huecos entre arcos."""
    p = suavizar(progreso)
    separacion = SEPARACION_NORMAL + (SEPARACION_MINIMA - SEPARACION_NORMAL) * p
    largo = LARGO_NORMAL + (LARGO_MINIMO - LARGO_NORMAL) * p
    giro = GIRO_MAXIMO * p
    cx, cy = CENTRO
    marcas = []
    for k in range(4):
        angulo = math.radians(giro + 90 * k)
        dx, dy = math.sin(angulo), -math.cos(angulo)
        dentro, fuera = radio + separacion, radio + separacion + largo
        marcas.append([(cx + dx * dentro, cy + dy * dentro), (cx + dx * fuera, cy + dy * fuera)])
    return marcas


def trazos_discontinuos(radio: float) -> list[list[Punto]]:
    """Trazos de una circunferencia discontinua: 8 px de trazo y 6 px de hueco."""
    periodo = TRAZO_DISCONTINUO + HUECO_DISCONTINUO
    trazos = max(1, round(2 * math.pi * radio / periodo))
    amplitud = 360 * TRAZO_DISCONTINUO / periodo / trazos
    return [
        arco(CENTRO, radio, 360 * k / trazos, 360 * k / trazos + amplitud, 4) for k in range(trazos)
    ]


def rombo(radio: float) -> list[Punto]:
    cx, cy = CENTRO
    return [(cx, cy - radio), (cx + radio, cy), (cx, cy + radio), (cx - radio, cy)]


def _con_opacidad(tono: Color, opacidad: float) -> Color:
    return (tono[0], tono[1], tono[2], tono[3] * opacidad)


class Mira:
    """Dibuja la mira y el anillo de disparo, y los mueve a donde marca el ratón."""

    def __init__(self, padre: NodePath) -> None:
        self._raiz = padre.attach_new_node("mira")
        self._forma: NodePath | None = None
        self._clave: tuple[float, float, bool] | None = None
        self._pulso: NodePath | None = None
        self._desde_disparo = math.inf
        self._radio = 0.0
        self._tono = TEXTO

    def olvidar(self) -> None:
        """Obliga a reconstruirla, por ejemplo tras cambiar la escala."""
        self._clave = None

    def disparo(self) -> None:
        """Empieza el anillo de disparo."""
        self._desde_disparo = 0.0

    def reiniciar(self) -> None:
        """Sin anillo de disparo pendiente, por ejemplo al empezar una partida."""
        self._desde_disparo = math.inf

    def dibujar(
        self,
        radio: float,
        progreso: float,
        aturdida: bool,
        posicion: Punto,
        visible: bool,
        dt: float,
    ) -> None:
        """`radio` en píxeles de diseño; `posicion`, desplazamiento desde el centro."""
        self._desde_disparo += dt
        self._raiz.set_pos(posicion[0], 0, posicion[1])
        if not visible:
            self._raiz.hide()
            return
        self._raiz.show()
        clave = (round(radio, 2), round(progreso, 3), aturdida)
        if clave != self._clave or self._forma is None:
            self._clave = clave
            self._radio = radio
            self._tono = mezclar(TEXTO, ACENTO, progreso)
            if self._forma is not None:
                self._forma.remove_node()
            self._forma = self._raiz.attach_new_node("forma")
            if aturdida:
                self._dibujar_aturdida(self._forma)
            else:
                self._dibujar_normal(self._forma, progreso)
        self._dibujar_pulso(aturdida)

    # --- formas ----------------------------------------------------------------------

    def _dibujar_normal(self, padre: NodePath, progreso: float) -> None:
        sombra = capa(padre, "sombra", ORDEN_SOMBRA)
        brillo = capa(padre, "brillo", ORDEN_BRILLO)
        trazo = capa(padre, "trazo", ORDEN_TRAZO)
        tono = _con_opacidad(self._tono, OPACIDAD_TRAZO)
        resplandor = _con_opacidad(ACENTO, OPACIDAD_BRILLO * suavizar(progreso))
        for puntos in [*arcos_mira(self._radio, progreso), *marcas_mira(self._radio, progreso)]:
            cinta(sombra, puntos, GROSOR_SOMBRA, SOMBRA)
            if progreso > 0:
                cinta(brillo, puntos, GROSOR_BRILLO, resplandor)
            cinta(trazo, puntos, GROSOR, tono)
        poligono(sombra, circulo(CENTRO, RADIO_SOMBRA_PUNTO, 16)[:-1], SOMBRA)
        poligono(trazo, circulo(CENTRO, RADIO_PUNTO, 16)[:-1], self._tono)
        if progreso >= 1:
            # Mira al mínimo: el rombo indica que el disparo está listo.
            cinta(sombra, rombo(RADIO_ROMBO), GROSOR_ROMBO + 2, SOMBRA, cerrada=True)
            cinta(brillo, rombo(RADIO_ROMBO), GROSOR_BRILLO / 2, resplandor, cerrada=True)
            cinta(trazo, rombo(RADIO_ROMBO), GROSOR_ROMBO, ACENTO, cerrada=True)

    def _dibujar_aturdida(self, padre: NodePath) -> None:
        """Mira bloqueada (`interfaz/05-aturdido.svg`): discontinua, sin marcas, al 40 %."""
        sombra = capa(padre, "sombra", ORDEN_SOMBRA)
        trazo = capa(padre, "trazo", ORDEN_TRAZO)
        tono = _con_opacidad(self._tono, OPACIDAD_ATURDIDA)
        oscuro = _con_opacidad(SOMBRA, OPACIDAD_ATURDIDA)
        for puntos in trazos_discontinuos(self._radio):
            cinta(sombra, puntos, GROSOR_SOMBRA, oscuro)
            cinta(trazo, puntos, GROSOR, tono)
        poligono(trazo, circulo(CENTRO, RADIO_PUNTO, 16)[:-1], tono)

    def _dibujar_pulso(self, aturdida: bool) -> None:
        """Anillo que se aleja de la mira y se desvanece tras cada disparo."""
        if self._pulso is not None:
            self._pulso.remove_node()
            self._pulso = None
        t = self._desde_disparo / DURACION_PULSO
        if t >= 1 or aturdida:
            return
        avance = 1 - (1 - t) ** 2
        radio = self._radio + EXPANSION_PULSO * avance
        self._pulso = capa(self._raiz, "pulso", ORDEN_BRILLO)
        tono = _con_opacidad(ACENTO, OPACIDAD_PULSO * (1 - t))
        cinta(self._pulso, circulo(CENTRO, radio, 48)[:-1], GROSOR * (1 - 0.5 * t), tono, True)
