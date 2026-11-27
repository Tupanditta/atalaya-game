"""Cartel de inicio de oleada (`interfaz.md`, «Movimiento»).

Al empezar cada oleada aparece en el centro, por encima de la mira, `OLEADA 12` en
grande y debajo un subtítulo: el sector y su nombre al llegar a un fondo nuevo, o los
hostiles que vienen. Dos líneas se abren desde el centro, el texto se enciende con un
parpadeo, se mantiene y se desvanece. No bloquea nada: se puede disparar mientras dura.
"""

from panda3d.core import NodePath, TextFont, TextNode

from atalaya.presentacion.hud.componentes import parpadeo_encendido
from atalaya.presentacion.hud.dibujo import Texto, capa, rectangulo
from atalaya.presentacion.hud.estilo import ACENTO, ANCHO_DISENO, TEXTO_SECUNDARIO

#: Tiempos del cartel, en segundos: apertura de las líneas, tiempo visible y desvanecido.
APERTURA = 0.35
DURACION = 2.6
DESVANECIDO = 0.5

#: Posición y tamaños, en píxeles de diseño.
_Y_TITULO = 330
_Y_SUBTITULO = 372
_Y_LINEAS = 344
_TAMANO_TITULO = 72
_TAMANO_SUBTITULO = 22
_ANCHO_LINEAS = 300
_ORDEN = 60


class CartelOleada:
    """Cartel animado del inicio de cada oleada."""

    def __init__(
        self, padre: NodePath, fuente_titulo: TextFont | None, fuente: TextFont | None
    ) -> None:
        centro = ANCHO_DISENO / 2
        self._raiz = capa(padre, "cartel-oleada", _ORDEN)
        self._titulo = Texto(
            self._raiz, fuente_titulo, centro, _Y_TITULO, _TAMANO_TITULO, TextNode.A_center, _ORDEN
        )
        self._subtitulo = Texto(
            self._raiz, fuente, centro, _Y_SUBTITULO, _TAMANO_SUBTITULO, TextNode.A_center, _ORDEN
        )
        # Líneas a izquierda y derecha del subtítulo, que se abren desde el centro.
        self._lineas = []
        for lado in (-1, 1):
            pivote = self._raiz.attach_new_node("linea")
            pivote.set_pos(centro + lado * 12, 0, -_Y_LINEAS)
            inicio = 0 if lado > 0 else -_ANCHO_LINEAS
            rectangulo(pivote, inicio, 0, _ANCHO_LINEAS, 2, ACENTO)
            self._lineas.append(pivote)
        self._tiempo = DURACION
        self._raiz.hide()

    @property
    def visible(self) -> bool:
        return self._tiempo < DURACION

    def mostrar(self, titulo: str, subtitulo: str) -> None:
        """Empieza el cartel con estos textos."""
        self._titulo.mostrar(titulo, ACENTO)
        self._subtitulo.mostrar(subtitulo, TEXTO_SECUNDARIO)
        self._tiempo = 0.0

    def ocultar(self) -> None:
        self._tiempo = DURACION

    def dibujar(self, dt: float, permitido: bool) -> None:
        """Avanza la animación; `permitido` es falso fuera de la oleada (menús, pausa)."""
        self._tiempo = min(DURACION, self._tiempo + dt)
        if not permitido or not self.visible:
            self._raiz.hide()
            return
        self._raiz.show()
        t = self._tiempo
        apertura = min(1.0, t / APERTURA)
        apertura = 1 - (1 - apertura) ** 3
        for linea in self._lineas:
            linea.set_sx(max(1e-3, apertura))
        desvanecido = min(1.0, (DURACION - t) / DESVANECIDO)
        self._raiz.set_alpha_scale(parpadeo_encendido(t) * desvanecido)
        # El título se acerca un poco mientras aparece.
        self._titulo.escalar(1.06 - 0.06 * apertura)
