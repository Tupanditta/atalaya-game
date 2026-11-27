"""Medidas de diseño y colores de la interfaz (`interfaz.md`, secciones 2 y 3)."""

from atalaya.logica.nucleo.dominio import TipoEnemigo
from atalaya.presentacion.hud.dibujo import Color, Punto, circulo, color

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

#: Color de cada tipo de enemigo y de sus proyectiles (`interfaz.md`, sección 3).
COLOR_TIPO: dict[TipoEnemigo, Color] = {
    TipoEnemigo.SIN_EFECTO: color("#FF4D5E"),
    TipoEnemigo.DESESTABILIZADOR: color("#FFD23F"),
    TipoEnemigo.ATURDIDOR: color("#B36BFF"),
}


def color_integridad(fraccion: float) -> Color:
    """Verde por encima del 50 %, ámbar entre el 25 % y el 50 %, rojo por debajo."""
    if fraccion > 0.5:
        return INTEGRIDAD_ALTA
    if fraccion >= 0.25:
        return AVISO
    return PELIGRO


def forma_contacto(tipo: TipoEnemigo, centro: Punto, lado: float) -> list[Punto]:
    """Círculo, triángulo o rombo según el tipo, para distinguirlo también sin color."""
    x, y = centro
    m = lado / 2
    if tipo is TipoEnemigo.DESESTABILIZADOR:
        return [(x, y - m), (x + m, y + m), (x - m, y + m)]
    if tipo is TipoEnemigo.ATURDIDOR:
        return [(x, y - m), (x + m, y), (x, y + m), (x - m, y)]
    return circulo(centro, m, 20)[:-1]


def cifra(valor: float) -> str:
    """Número sin ceros sobrantes y con coma decimal: 1,5; 10; 0,25."""
    return f"{valor:g}".replace(".", ",")
