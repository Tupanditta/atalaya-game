"""HUD de la partida (`modulos/hud.md`, `interfaz/interfaz.md`, sección 6).

Versión de S2: la mira y la barra de energía, con su parpadeo sin energía. El radar,
la integridad, la oleada y las pantallas llegan en sprints posteriores.
"""

import math

from direct.showbase.ShowBase import ShowBase
from panda3d.core import NodePath, TextNode

from atalaya.logica.armamento import Armamento
from atalaya.logica.nucleo.bus import Bus
from atalaya.logica.nucleo.eventos import DisparoSinEnergia, PartidaIniciada
from atalaya.logica.parametros import Parametros
from atalaya.presentacion.hud.dibujo import (
    Color,
    Texto,
    cargar_fuente,
    circulo,
    color,
    linea,
    mezclar,
    panel,
    poligono,
    rectangulo,
)

#: Medidas de diseño (`interfaz.md`, sección 2).
ANCHO_DISENO = 1920
ALTO_DISENO = 1080

TEXTO = color("#E6F1FF")
TEXTO_SECUNDARIO = color("#8AA0B8")
ACENTO = color("#2AD4FF")
PISTA = color("#1A2638")
AVISO = color("#FFB020")
FONDO_PANEL = color("#0A1220")

#: Barra de energía en el panel de estado de la estación (`interfaz/03-oleada.svg`).
#: En S2 el panel solo tiene la fila de energía; la de integridad llega en S3.
_BARRA_X, _BARRA_Y, _BARRA_ANCHO, _BARRA_ALTO = 1464, 1006, 384, 10
_PANEL_X, _PANEL_Y, _PANEL_ANCHO, _PANEL_ALTO = 1440, 962, 432, 70

#: Aviso sin energía: tres parpadeos en 0,6 s y el texto durante 1 s.
_PARPADEO = 0.6
_PARPADEOS = 3
_AVISO_TEXTO = 1.0
#: Constante de tiempo de la transición de la barra: llega al valor en unos 150 ms.
_TRANSICION = 0.05

#: Mira: grosor, separación y largo de las marcas, y radio del punto central.
_GROSOR_MIRA = 2
_SEPARACION_MARCAS = 10
_LARGO_MARCAS = 10
_RADIO_PUNTO = 3
_OPACIDAD_MIRA = 0.9


def radio_mira_en_pantalla(radio: float, campo_vision: float) -> float:
    """Radio de la mira en píxeles de diseño (`interfaz.md`, «Mira»)."""
    mitad = ALTO_DISENO / 2
    return mitad * math.tan(math.radians(radio)) / math.tan(math.radians(campo_vision) / 2)


class Hud:
    """Dibuja encima de la escena la mira y los indicadores de la partida."""

    def __init__(
        self, base: ShowBase, bus: Bus, parametros: Parametros, armamento: Armamento
    ) -> None:
        self._base = base
        self._jugador = parametros.jugador
        self._armamento = armamento
        self._fuente = cargar_fuente(base)
        self._raiz = base.pixel2d.attach_new_node("hud")
        self._escala = 0.0
        self._centro = self._raiz.attach_new_node("centro")
        self._derecha = self._raiz.attach_new_node("derecha")
        self._mira: NodePath | None = None
        self._clave_mira: tuple[float, Color] | None = None
        self._energia_mostrada = armamento.energia
        self._desde_sin_energia = math.inf
        self._barra: NodePath | None = None
        self._clave_barra: tuple[float, Color] | None = None
        self._estaticos: NodePath | None = None
        self._textos: dict[str, Texto] = {}
        bus.suscribir(DisparoSinEnergia, self._al_disparar_sin_energia)
        bus.suscribir(PartidaIniciada, self._al_iniciar_partida)

    def dibujar(self, dt: float) -> None:
        """Actualiza el HUD una vez por fotograma consultando a `armamento`."""
        self._ajustar_escala()
        self._desde_sin_energia += dt
        self._dibujar_mira()
        self._dibujar_energia(dt)

    # --- escala y anclajes -----------------------------------------------------------

    def _ajustar_escala(self) -> None:
        """Escala por alto ÷ 1080 y separa los anclajes en pantallas más anchas que 16:9."""
        ventana = self._base.win
        ancho, alto = ventana.get_x_size(), ventana.get_y_size()
        escala = alto / ALTO_DISENO
        if escala == self._escala or escala <= 0:
            return
        self._escala = escala
        self._raiz.set_scale(escala)
        ancho_diseno = ancho / escala
        self._centro.set_x((ancho_diseno - ANCHO_DISENO) / 2)
        self._derecha.set_x(ancho_diseno - ANCHO_DISENO)
        self._crear_estaticos()
        self._clave_mira = None
        self._clave_barra = None

    def _crear_estaticos(self) -> None:
        if self._estaticos is not None:
            self._estaticos.remove_node()
        self._estaticos = self._derecha.attach_new_node("estaticos")
        panel(self._estaticos, _PANEL_X, _PANEL_Y, _PANEL_ANCHO, _PANEL_ALTO, self._escala)
        rectangulo(self._estaticos, _BARRA_X, _BARRA_Y, _BARRA_ANCHO, _BARRA_ALTO, PISTA)
        # Los textos cuelgan de los elementos fijos: se borran con ellos al cambiar la escala.
        fijos, fuente, derecha = self._estaticos, self._fuente, TextNode.A_right
        self._textos = {
            "etiqueta": Texto(fijos, fuente, _BARRA_X, 996, 16),
            "valor": Texto(fijos, fuente, _BARRA_X + _BARRA_ANCHO, 996, 20, derecha),
            "aviso": Texto(fijos, fuente, _BARRA_X, _PANEL_Y - 12, 16),
        }

    # --- mira ------------------------------------------------------------------------

    def _dibujar_mira(self) -> None:
        j = self._jugador
        progreso = self._armamento.progreso_apuntado
        campo = j.campo_vision_normal + (j.campo_vision_zoom - j.campo_vision_normal) * progreso
        radio = radio_mira_en_pantalla(self._armamento.radio_mira, campo)
        tono = mezclar(TEXTO, ACENTO, progreso)
        clave = (round(radio, 2), tono)
        if clave == self._clave_mira:
            return
        self._clave_mira = clave
        if self._mira is not None:
            self._mira.remove_node()
        self._mira = self._centro.attach_new_node("mira")
        trazo = (*tono[:3], _OPACIDAD_MIRA)
        cx, cy = ANCHO_DISENO / 2, ALTO_DISENO / 2
        linea(self._mira, circulo((cx, cy), radio), trazo, _GROSOR_MIRA, self._escala)
        dentro, fuera = radio + _SEPARACION_MARCAS, radio + _SEPARACION_MARCAS + _LARGO_MARCAS
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            marca = [(cx + dx * dentro, cy + dy * dentro), (cx + dx * fuera, cy + dy * fuera)]
            linea(self._mira, marca, trazo, _GROSOR_MIRA, self._escala)
        poligono(self._mira, circulo((cx, cy), _RADIO_PUNTO, 16)[:-1], tono)

    # --- energía ---------------------------------------------------------------------

    def _dibujar_energia(self, dt: float) -> None:
        actual = self._armamento.energia
        maxima = self._armamento.energia_maxima
        self._energia_mostrada += (actual - self._energia_mostrada) * (
            1 - math.exp(-dt / _TRANSICION)
        )
        relleno = AVISO if self._parpadeo_encendido() else ACENTO
        fraccion = max(0.0, min(1.0, self._energia_mostrada / maxima))
        clave = (round(fraccion * _BARRA_ANCHO, 1), relleno)
        if clave != self._clave_barra:
            self._clave_barra = clave
            if self._barra is not None:
                self._barra.remove_node()
            self._barra = self._derecha.attach_new_node("barra-energia")
            if fraccion > 0:
                rectangulo(
                    self._barra, _BARRA_X, _BARRA_Y, fraccion * _BARRA_ANCHO, _BARRA_ALTO, relleno
                )
            # Una marca cada «coste de un disparo», para contar los disparos que quedan.
            coste = self._jugador.coste_disparo
            for k in range(1, math.ceil(maxima / coste)):
                x = _BARRA_X + _BARRA_ANCHO * k * coste / maxima
                rectangulo(self._barra, x - 1, _BARRA_Y, 2, _BARRA_ALTO, FONDO_PANEL)
        self._textos["etiqueta"].mostrar("ENERGÍA", TEXTO_SECUNDARIO)
        self._textos["valor"].mostrar(f"{math.floor(actual + 1e-9)} / {maxima:g}", TEXTO)
        if self._desde_sin_energia < _AVISO_TEXTO:
            self._textos["aviso"].mostrar("SIN ENERGÍA", AVISO)
        else:
            self._textos["aviso"].ocultar()

    def _parpadeo_encendido(self) -> bool:
        t = self._desde_sin_energia
        if t >= _PARPADEO:
            return False
        periodo = _PARPADEO / _PARPADEOS
        return (t % periodo) < periodo / 2

    # --- eventos ---------------------------------------------------------------------

    def _al_disparar_sin_energia(self, evento: DisparoSinEnergia) -> None:
        self._desde_sin_energia = 0.0

    def _al_iniciar_partida(self, evento: PartidaIniciada) -> None:
        self._desde_sin_energia = math.inf
        self._energia_mostrada = self._armamento.energia_maxima
