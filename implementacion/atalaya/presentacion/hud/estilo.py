"""Medidas de diseño y colores de la interfaz (`interfaz.md`, secciones 2 y 3)."""

from atalaya.presentacion.hud.dibujo import Color, color

#: Medidas de diseño (`interfaz.md`, sección 2).
ANCHO_DISENO = 1920
ALTO_DISENO = 1080

TEXTO = color("#E6F1FF")
TEXTO_SECUNDARIO = color("#8AA0B8")
ACENTO = color("#2AD4FF")
PISTA = color("#1A2638")
AVISO = color("#FFB020")
PELIGRO = color("#FF4D5E")
INTEGRIDAD_ALTA = color("#3DDC84")
FONDO_PANEL = color("#0A1220")
VELO = color("#000000", 0.55)


def color_integridad(fraccion: float) -> Color:
    """Verde por encima del 50 %, ámbar entre el 25 % y el 50 %, rojo por debajo."""
    if fraccion > 0.5:
        return INTEGRIDAD_ALTA
    if fraccion >= 0.25:
        return AVISO
    return PELIGRO
