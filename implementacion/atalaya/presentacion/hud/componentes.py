"""Componentes de las pantallas de menú (`interfaz.md`, secciones 5 y 8).

- `opcion`: opción de menú seleccionada, no seleccionada o no disponible.
- `ayudas`: barra de teclas centrada a 48 px del borde inferior.
- `PantallaMenu`: base de las pantallas de menú. Se construye al abrirse con un fundido y
  un desplazamiento vertical, y solo se reconstruye cuando cambia lo que muestra.
"""

from collections.abc import Sequence

from panda3d.core import NodePath, TextFont, TextNode

from atalaya.presentacion.hud.dibujo import (
    Color,
    Texto,
    ancho_texto,
    capa,
    color,
    linea,
    rectangulo,
)
from atalaya.presentacion.hud.estilo import ACENTO, ANCHO_DISENO, TEXTO, TEXTO_SECUNDARIO

#: Alto de una opción de menú y relleno del texto (`interfaz.md`, «Opción de menú»).
ALTO_OPCION = 64
_RELLENO_OPCION = 28
#: Línea base del texto dentro de la opción, como en las maquetas.
_BASE_OPCION = 43
TAMANO_OPCION = 32
#: Opción no disponible: opacidad al 40 %.
OPACIDAD_NO_DISPONIBLE = 0.4
SELECCION = color("#2AD4FF", 0.14)
MARCA_SELECCION = "\N{SINGLE RIGHT-POINTING ANGLE QUOTATION MARK}"

#: Barra de ayudas: teclas de 30 px de alto con su línea base a 1029 px.
_AYUDAS_Y = 1008
_AYUDAS_BASE = 1029
_TECLA_ALTO = 30
_TECLA_ANCHO_MINIMO = 40
_TAMANO_AYUDA = 16
_SEPARACION = 20

#: Aparición: fundido y desplazamiento vertical de 16 px en 200 ms (`interfaz.md`, sección 8).
_APARICION = 0.2
_DESPLAZAMIENTO = 16

#: Orden de dibujo del texto de los menús: encima de sus paneles.
ORDEN_TEXTO = 90


def texto(
    padre: NodePath,
    fuente: TextFont | None,
    x: float,
    y: float,
    tamano: float,
    contenido: str,
    tono: Color,
    alineacion: int = TextNode.A_left,
    orden: int = ORDEN_TEXTO,
) -> None:
    """Texto fijo con la línea base en (x, y)."""
    Texto(padre, fuente, x, y, tamano, alineacion, orden).mostrar(contenido, tono)


def opcion(
    padre: NodePath,
    fuente: TextFont | None,
    x: float,
    y: float,
    ancho: float,
    titulo: str,
    seleccionada: bool,
    orden: int,
    disponible: bool = True,
    orden_texto: int = ORDEN_TEXTO,
) -> NodePath:
    """Opción de menú de 64 px de alto con su borde superior en `y`.

    `orden` es el orden de dibujo del fondo de la selección y `orden_texto`, el del texto.
    """
    nodo = padre.attach_new_node("opcion")
    if seleccionada:
        fondo = capa(nodo, "seleccion", orden)
        rectangulo(fondo, x, y, ancho, ALTO_OPCION, SELECCION)
        rectangulo(fondo, x, y, 4, ALTO_OPCION, ACENTO)
        base = y + _BASE_OPCION
        texto(
            nodo, fuente, x + ancho - _RELLENO_OPCION, base, TAMANO_OPCION, MARCA_SELECCION,
            ACENTO, TextNode.A_right, orden_texto,
        )  # fmt: skip
    tono = TEXTO if seleccionada else TEXTO_SECUNDARIO
    texto(
        nodo, fuente, x + _RELLENO_OPCION, y + _BASE_OPCION, TAMANO_OPCION, titulo, tono,
        orden=orden_texto,
    )  # fmt: skip
    if not disponible:
        nodo.set_alpha_scale(OPACIDAD_NO_DISPONIBLE)
    return nodo


def ayudas(
    padre: NodePath,
    fuente: TextFont | None,
    centro: float,
    teclas: Sequence[tuple[str, str]],
    escala: float,
) -> None:
    """Fila de teclas y acciones centrada en `centro` (`interfaz.md`, «Barra de ayudas»)."""
    piezas: list[tuple[str, float, float]] = []
    for tecla, accion in teclas:
        ancho_tecla = max(_TECLA_ANCHO_MINIMO, ancho_texto(fuente, tecla, _TAMANO_AYUDA) + 20)
        ancho_accion = ancho_texto(fuente, accion, _TAMANO_AYUDA)
        piezas.append((tecla, ancho_tecla, ancho_accion))
    separador = ancho_texto(fuente, "·", _TAMANO_AYUDA)
    total = sum(t + 10 + a for _, t, a in piezas)
    total += (len(piezas) - 1) * (2 * _SEPARACION + separador)
    x = centro - total / 2
    for i, ((tecla, ancho_tecla, ancho_accion), (_, accion)) in enumerate(
        zip(piezas, teclas, strict=True)
    ):
        if i > 0:
            texto(
                padre, fuente, x + _SEPARACION, _AYUDAS_BASE, _TAMANO_AYUDA, "·",
                TEXTO_SECUNDARIO,
            )  # fmt: skip
            x += 2 * _SEPARACION + separador
        borde = [
            (x, _AYUDAS_Y),
            (x + ancho_tecla, _AYUDAS_Y),
            (x + ancho_tecla, _AYUDAS_Y + _TECLA_ALTO),
            (x, _AYUDAS_Y + _TECLA_ALTO),
            (x, _AYUDAS_Y),
        ]
        marco = linea(padre, borde, TEXTO_SECUNDARIO, 1, escala)
        marco.set_bin("fixed", ORDEN_TEXTO)
        texto(
            padre, fuente, x + ancho_tecla / 2, _AYUDAS_BASE, _TAMANO_AYUDA, tecla,
            TEXTO_SECUNDARIO, TextNode.A_center,
        )  # fmt: skip
        texto(
            padre, fuente, x + ancho_tecla + 10, _AYUDAS_BASE, _TAMANO_AYUDA, accion,
            TEXTO_SECUNDARIO,
        )  # fmt: skip
        x += ancho_tecla + 10 + ancho_accion


class PantallaMenu:
    """Base de las pantallas de menú del HUD.

    Las subclases dicen qué muestran (`_clave`) y cómo se dibuja (`_construir`). El
    contenido se dibuja en coordenadas de diseño; `self._dx` desplaza lo centrado en
    pantallas más anchas que 16:9 y `self._ancho` es el ancho de diseño de la pantalla.
    """

    #: Orden de dibujo de la pantalla: encima del HUD de la partida.
    ORDEN = 80

    def __init__(self, raiz: NodePath, fuente: TextFont | None, animar: bool = True) -> None:
        self._raiz = raiz
        self._fuente = fuente
        self._animar = animar
        self._nodo: NodePath | None = None
        self._marco: NodePath | None = None
        self._contenido: NodePath | None = None
        self._clave_dibujada: object = None
        self._abierta = 0.0
        self._escala = 1.0
        self._ancho = float(ANCHO_DISENO)
        self._dx = 0.0

    def olvidar(self) -> None:
        """La quita de la pantalla; la próxima vez que se muestre se vuelve a construir."""
        if self._nodo is not None:
            self._nodo.remove_node()
        self._nodo = None
        self._marco = None
        self._contenido = None
        self._clave_dibujada = None

    def dibujar(self, visible: bool, escala: float, ancho_diseno: float, dt: float) -> None:
        """Muestra u oculta la pantalla y la pone al día con el estado de la lógica."""
        if not visible:
            self.olvidar()
            return
        if self._nodo is None:
            self._escala = escala
            self._ancho = ancho_diseno
            self._dx = (ancho_diseno - ANCHO_DISENO) / 2
            self._abierta = 0.0
            self._nodo = capa(self._raiz, type(self).__name__, self.ORDEN)
            self._fondo(self._nodo)
            self._marco = self._nodo.attach_new_node("marco")
        assert self._marco is not None
        self._abierta += dt
        if self._animar:
            avance = min(1.0, self._abierta / _APARICION)
            self._marco.set_alpha_scale(avance)
            self._marco.set_z(-_DESPLAZAMIENTO * (1 - avance))
        clave = self._clave()
        if clave != self._clave_dibujada or self._contenido is None:
            self._clave_dibujada = clave
            if self._contenido is not None:
                self._contenido.remove_node()
            self._contenido = self._marco.attach_new_node("contenido")
            self._construir(self._contenido)
        self._actualizar(dt)

    # --- para las subclases ------------------------------------------------------------

    def _fondo(self, nodo: NodePath) -> None:
        """Lo que no se anima al abrir, como un velo a pantalla completa."""

    def _clave(self) -> object:
        """Todo lo que cambia el contenido; si no cambia, no se reconstruye."""
        return None

    def _construir(self, padre: NodePath) -> None:
        """Dibuja el contenido de la pantalla."""
        raise NotImplementedError

    def _actualizar(self, dt: float) -> None:
        """Cambios de cada fotograma que no obligan a reconstruir."""

    def _texto(
        self,
        padre: NodePath,
        x: float,
        y: float,
        tamano: float,
        contenido: str,
        tono: Color,
        alineacion: int = TextNode.A_left,
        orden: int = ORDEN_TEXTO,
    ) -> None:
        texto(padre, self._fuente, x, y, tamano, contenido, tono, alineacion, orden)
