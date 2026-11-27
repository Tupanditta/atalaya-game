"""Menú principal, pausa con sus confirmaciones y resumen de fin de partida.

Ver `interfaz.md`, sección 7, y las maquetas `01-menuPrincipal.svg`, `07-pausa.svg` y
`09-victoria.svg`. Solo consultan a `flujo`: qué hace cada opción lo decide `flujo`.
"""

from panda3d.core import NodePath, TextFont, TextNode

import atalaya
from atalaya.logica.flujo import (
    Confirmacion,
    Flujo,
    OpcionConfirmacion,
    OpcionMenu,
    OpcionPausa,
    OpcionResumen,
    Pantalla,
)
from atalaya.logica.parametros import Parametros
from atalaya.presentacion.hud.componentes import (
    ALTO_OPCION,
    SELECCION,
    TAMANO_OPCION,
    PantallaMenu,
    ayudas,
    opcion,
)
from atalaya.presentacion.hud.dibujo import capa, color, linea, panel, rectangulo
from atalaya.presentacion.hud.estilo import (
    ACENTO,
    ALTO_DISENO,
    ANCHO_DISENO,
    PELIGRO,
    TEXTO,
    TEXTO_SECUNDARIO,
    VELO,
)

_CENTRO = ANCHO_DISENO / 2
_FONDO_PANEL = color("#0A1220", 0.9)

#: Menú principal: título a la izquierda y columna de opciones de 480 px desde y = 520.
_TITULO_X, _TITULO_Y = 160, 380
_OPCIONES_MENU_Y, _PASO_MENU, _ANCHO_MENU = 520, 80, 480
_TITULOS_MENU = {
    OpcionMenu.JUGAR: "JUGAR",
    OpcionMenu.MANUAL: "MANUAL",
    OpcionMenu.SALIR: "SALIR DEL JUEGO",
}

#: Pausa: panel centrado de 560 × 440 px.
_PAUSA_X, _PAUSA_Y, _PAUSA_ANCHO, _PAUSA_ALTO = 680, 250, 560, 440
_OPCIONES_PAUSA_Y, _PASO_PAUSA = 364, 72
_TITULOS_PAUSA = {
    OpcionPausa.CONTINUAR: "CONTINUAR",
    OpcionPausa.MANUAL: "MANUAL",
    OpcionPausa.ABANDONAR: "ABANDONAR PARTIDA",
    OpcionPausa.SALIR: "SALIR DEL JUEGO",
}

#: Confirmación: panel centrado de 640 × 260 px, encima del de pausa.
_CONFIRMACION_X, _CONFIRMACION_Y = 640, 410
_CONFIRMACION_ANCHO, _CONFIRMACION_ALTO = 640, 260
_VELO_CONFIRMACION = color("#000000", 0.35)
#: Opaco: el menú de pausa que queda debajo no debe leerse a través de la confirmación.
_FONDO_CONFIRMACION = color("#0A1220")
_BOTON_Y, _BOTON_ANCHO = 566, 276
_BOTONES_X = {OpcionConfirmacion.NO: 676, OpcionConfirmacion.SI: 968}
_TITULOS_CONFIRMACION = {OpcionConfirmacion.NO: "NO", OpcionConfirmacion.SI: "SÍ"}
_PREGUNTAS = {
    Confirmacion.ABANDONAR: "¿ABANDONAR LA PARTIDA?",
    Confirmacion.SALIR: "¿SALIR DEL JUEGO?",
}

#: Resumen: contenido centrado sin panel, con las opciones desde y = 580.
_OPCIONES_RESUMEN_X, _OPCIONES_RESUMEN_Y, _PASO_RESUMEN, _ANCHO_RESUMEN = 720, 580, 80, 480
_TITULOS_RESUMEN = {
    OpcionResumen.VOLVER_A_JUGAR: "VOLVER A JUGAR",
    OpcionResumen.MENU_PRINCIPAL: "MENÚ PRINCIPAL",
}

#: Orden de dibujo dentro de cada pantalla. En la pausa, todo el menú queda debajo del
#: velo y del panel de la confirmación.
_ORDEN_PANEL = 81
_ORDEN_SELECCION = 83
_ORDEN_TEXTO_PAUSA = 84
_ORDEN_VELO_CONFIRMACION = 85
_ORDEN_CONFIRMACION = 86
_ORDEN_BOTON = 88


class PantallaMenuPrincipal(PantallaMenu):
    """Título, «Jugar», «Manual» y «Salir del juego» sobre el fondo que gira."""

    def __init__(self, raiz: NodePath, fuente: TextFont | None, flujo: Flujo) -> None:
        super().__init__(raiz, fuente)
        self._flujo = flujo

    def _clave(self) -> object:
        return self._flujo.seleccion_menu

    def _construir(self, padre: NodePath) -> None:
        # El título y las opciones van anclados a la izquierda; las ayudas, centradas.
        self._texto(padre, _TITULO_X, _TITULO_Y, 140, "ATALAYA", TEXTO)
        self._texto(padre, _TITULO_X + 6, _TITULO_Y + 50, 20, "ÚLTIMA GUARDIA DE LA RED", ACENTO)
        seleccionada = self._flujo.seleccion_menu
        for i, opcion_menu in enumerate(self._flujo.opciones_menu):
            y = _OPCIONES_MENU_Y + _PASO_MENU * i
            titulo = _TITULOS_MENU[opcion_menu]
            opcion(
                padre, self._fuente, _TITULO_X, y, _ANCHO_MENU, titulo,
                opcion_menu is seleccionada, _ORDEN_SELECCION,
            )  # fmt: skip
        teclas = [("↑↓", "Navegar"), ("Intro", "Confirmar")]
        ayudas(padre, self._fuente, self._dx + _CENTRO, teclas, self._escala)
        version = f"v{atalaya.__version__}"
        self._texto(
            padre, self._ancho - 48, ALTO_DISENO - 48, 14, version, TEXTO_SECUNDARIO,
            TextNode.A_right,
        )  # fmt: skip


class PantallaPausa(PantallaMenu):
    """Menú de pausa y, encima, la confirmación de abandonar o salir (CU-09, CU-12)."""

    def __init__(self, raiz: NodePath, fuente: TextFont | None, flujo: Flujo) -> None:
        super().__init__(raiz, fuente)
        self._flujo = flujo

    def _clave(self) -> object:
        f = self._flujo
        confirmando = f.pantalla is Pantalla.CONFIRMACION
        return (f.seleccion_pausa, confirmando, f.confirmacion, f.seleccion_confirmacion)

    def _construir(self, padre: NodePath) -> None:
        marco = padre.attach_new_node("pausa")
        marco.set_x(self._dx)
        e = self._escala
        panel(
            marco, _PAUSA_X, _PAUSA_Y, _PAUSA_ANCHO, _PAUSA_ALTO, e,
            relleno=_FONDO_PANEL, orden=_ORDEN_PANEL,
        )  # fmt: skip
        self._texto(
            marco, _CENTRO, _PAUSA_Y + 72, 48, "PAUSA", TEXTO, TextNode.A_center,
            _ORDEN_TEXTO_PAUSA,
        )  # fmt: skip
        confirmando = self._flujo.pantalla is Pantalla.CONFIRMACION
        seleccionada = None if confirmando else self._flujo.seleccion_pausa
        for i, opcion_pausa in enumerate(self._flujo.opciones_pausa):
            y = _OPCIONES_PAUSA_Y + _PASO_PAUSA * i
            titulo = _TITULOS_PAUSA[opcion_pausa]
            opcion(
                marco, self._fuente, _PAUSA_X + 24, y, _PAUSA_ANCHO - 48, titulo,
                opcion_pausa is seleccionada, _ORDEN_SELECCION,
                orden_texto=_ORDEN_TEXTO_PAUSA,
            )  # fmt: skip
        if confirmando:
            self._construir_confirmacion(padre, marco)
            teclas = [("←→", "Elegir"), ("Intro", "Confirmar"), ("Esc", "Cancelar")]
        else:
            teclas = [("↑↓", "Navegar"), ("Intro", "Confirmar"), ("Esc", "Continuar")]
        ayudas(marco, self._fuente, _CENTRO, teclas, e)

    def _construir_confirmacion(self, padre: NodePath, marco: NodePath) -> None:
        velo = capa(padre, "velo-confirmacion", _ORDEN_VELO_CONFIRMACION)
        rectangulo(velo, 0, 0, self._ancho, ALTO_DISENO, _VELO_CONFIRMACION)
        caja = capa(marco, "confirmacion", _ORDEN_CONFIRMACION)
        x, y = _CONFIRMACION_X, _CONFIRMACION_Y
        panel(
            caja, x, y, _CONFIRMACION_ANCHO, _CONFIRMACION_ALTO, self._escala,
            relleno=_FONDO_CONFIRMACION, orden=_ORDEN_CONFIRMACION,
        )  # fmt: skip
        pregunta = _PREGUNTAS[self._flujo.confirmacion]
        self._texto(caja, _CENTRO, y + 64, 36, pregunta, TEXTO, TextNode.A_center)
        aviso = "Se perderán los puntos y las mejoras de esta partida."
        self._texto(caja, _CENTRO, y + 104, 20, aviso, TEXTO_SECUNDARIO, TextNode.A_center)
        seleccionada = self._flujo.seleccion_confirmacion
        for boton, bx in _BOTONES_X.items():
            elegido = boton is seleccionada
            fondo = capa(caja, "boton", _ORDEN_BOTON)
            if elegido:
                rectangulo(fondo, bx, _BOTON_Y, _BOTON_ANCHO, ALTO_OPCION, SELECCION)
            borde = ACENTO if elegido else color("#8AA0B8", 0.4)
            esquinas = [
                (bx, _BOTON_Y),
                (bx + _BOTON_ANCHO, _BOTON_Y),
                (bx + _BOTON_ANCHO, _BOTON_Y + ALTO_OPCION),
                (bx, _BOTON_Y + ALTO_OPCION),
                (bx, _BOTON_Y),
            ]
            linea(fondo, esquinas, borde, 1, self._escala)
            tono = TEXTO if elegido else TEXTO_SECUNDARIO
            titulo = _TITULOS_CONFIRMACION[boton]
            self._texto(
                caja, bx + _BOTON_ANCHO / 2, _BOTON_Y + 43, TAMANO_OPCION, titulo, tono,
                TextNode.A_center,
            )  # fmt: skip


class PantallaResumen(PantallaMenu):
    """Resumen de derrota: oleadas superadas, nivel y opciones (RF-19, RF-20).

    La victoria y «Subir nivel» llegan en S7.
    """

    def __init__(
        self, raiz: NodePath, fuente: TextFont | None, flujo: Flujo, parametros: Parametros
    ) -> None:
        super().__init__(raiz, fuente)
        self._flujo = flujo
        self._parametros = parametros

    def _fondo(self, nodo: NodePath) -> None:
        rectangulo(nodo, 0, 0, self._ancho, ALTO_DISENO, VELO)

    def _clave(self) -> object:
        f = self._flujo
        return (f.seleccion_resumen, f.oleadas_superadas, f.nivel)

    def _construir(self, padre: NodePath) -> None:
        marco = padre.attach_new_node("resumen")
        marco.set_x(self._dx)
        a_centro = TextNode.A_center
        self._texto(marco, _CENTRO, 330, 96, "ESTACIÓN PERDIDA", PELIGRO, a_centro)
        self._texto(marco, _CENTRO, 392, 24, "La Atalaya ha caído.", TEXTO, a_centro)
        total = self._parametros.oleadas.numero_oleadas
        datos = [
            (840, "OLEADAS SUPERADAS", f"{self._flujo.oleadas_superadas} / {total}"),
            (1080, "NIVEL", str(self._flujo.nivel)),
        ]
        for x, etiqueta, valor in datos:
            self._texto(marco, x, 468, 16, etiqueta, TEXTO_SECUNDARIO, a_centro)
            self._texto(marco, x, 510, 36, valor, TEXTO, a_centro)
        seleccionada = self._flujo.seleccion_resumen
        for i, opcion_resumen in enumerate(self._flujo.opciones_resumen):
            y = _OPCIONES_RESUMEN_Y + _PASO_RESUMEN * i
            titulo = _TITULOS_RESUMEN[opcion_resumen]
            opcion(
                marco, self._fuente, _OPCIONES_RESUMEN_X, y, _ANCHO_RESUMEN, titulo,
                opcion_resumen is seleccionada, _ORDEN_SELECCION,
            )  # fmt: skip
        teclas = [("↑↓", "Navegar"), ("Intro", "Confirmar")]
        ayudas(marco, self._fuente, _CENTRO, teclas, self._escala)
