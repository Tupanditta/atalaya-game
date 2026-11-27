"""Pantalla de mejoras del descanso (`interfaz.md`, «Pantalla de mejoras»; CU-11).

Panel centrado sobre la escena con el resultado de la oleada, los puntos disponibles, la
integridad, las opciones con su coste y su nivel, y la cuenta atrás del descanso. El
hueco de la transmisión de radio queda vacío hasta S8. Solo consulta a la lógica: qué
hace cada opción lo decide `flujo`.
"""

import math

from panda3d.core import NodePath, TextFont, TextNode

from atalaya.logica.estacion import Estacion
from atalaya.logica.flujo import MEJORA_DE_OPCION, Flujo, OpcionDescanso
from atalaya.logica.mejoras import Mejoras, Motivo
from atalaya.logica.nucleo.dominio import Mejora
from atalaya.logica.oleadas import Oleadas
from atalaya.presentacion.hud.componentes import parpadeo_encendido
from atalaya.presentacion.hud.dibujo import (
    Color,
    Texto,
    ancho_texto,
    capa,
    circulo,
    color,
    linea,
    panel,
    poligono,
    rectangulo,
)
from atalaya.presentacion.hud.estilo import (
    ACENTO,
    ALTO_DISENO,
    ANCHO_DISENO,
    AVISO,
    PISTA,
    TEXTO,
    TEXTO_SECUNDARIO,
    color_integridad,
)

#: Orden de dibujo: encima del HUD de la partida, que queda atenuado debajo.
_ORDEN_VELO = 60
_ORDEN_PANEL = 61
_ORDEN_SELECCION = 63
_ORDEN_CONTENIDO = 64
_ORDEN_TEXTO = 70

#: Oscurecimiento de la escena del descanso (`06-mejoras.svg`).
_VELO = color("#000000", 0.4)
_FONDO_PANEL = color("#0A1220", 0.85)

#: Panel centrado de 1280 × 760 px.
_PANEL_X, _PANEL_Y, _PANEL_ANCHO, _PANEL_ALTO = 320, 160, 1280, 760
_IZQUIERDA = 368
_DERECHA = 1552

#: Barra de integridad de la columna izquierda.
_BARRA_X, _BARRA_Y, _BARRA_ANCHO, _BARRA_ALTO = 368, 764, 480, 10

#: Opciones de la columna derecha: borde superior de cada fila y su alto.
_OPCION_X, _OPCION_ANCHO, _OPCION_ALTO = 912, 640, 88
_FILAS = {
    OpcionDescanso.REPARAR: 322,
    OpcionDescanso.BLINDAJE: 422,
    OpcionDescanso.BATERIA: 522,
    OpcionDescanso.GENERADOR: 622,
    OpcionDescanso.CONTINUAR: 742,
}
_TITULOS = {
    OpcionDescanso.REPARAR: "REPARAR",
    OpcionDescanso.BLINDAJE: "BLINDAJE",
    OpcionDescanso.BATERIA: "BATERÍA",
    OpcionDescanso.GENERADOR: "GENERADOR",
    OpcionDescanso.CONTINUAR: "CONTINUAR",
}
#: Efecto de cada nivel de mejora; la cifra sale de `parametros`.
_EFECTOS = {
    Mejora.BLINDAJE: "integridad máxima",
    Mejora.BATERIA: "energía máxima",
    Mejora.GENERADOR: "recarga de energía por segundo",
}
#: Opción no disponible: opacidad al 40 %.
_OPACIDAD_NO_DISPONIBLE = 0.4
#: Indicador de niveles: puntos de 10 px separados 18 px.
_NIVELES_X, _RADIO_NIVEL, _PASO_NIVEL = 1300, 5, 18

#: La cuenta atrás pasa a aviso con 5 s o menos.
_CUENTA_ATRAS_AVISO = 5.0
#: Aparición: fundido y desplazamiento vertical de 16 px en 200 ms (`interfaz.md`, sección 8).
_APARICION = 0.2
_DESPLAZAMIENTO = 16


def formato_tiempo(segundos: float) -> str:
    """Tiempo en minutos y segundos, `MM:SS`, sin redondear hacia arriba."""
    total = max(0, math.floor(segundos + 1e-9))
    return f"{total // 60:02d}:{total % 60:02d}"


def texto_puntos(puntos: int) -> str:
    """`1 PUNTO` o `N PUNTOS`."""
    return "1 PUNTO" if puntos == 1 else f"{puntos} PUNTOS"


def texto_cuenta_atras(restante: float) -> str:
    """Segundos que faltan, redondeados hacia arriba: nunca muestra «0 s» antes de acabar."""
    return f"{max(0, math.ceil(restante - 1e-9))} s"


def texto_coste(coste: int, motivo: Motivo | None) -> str:
    """Coste de una opción, o por qué no se puede comprar (`interfaz.md`)."""
    if motivo is Motivo.SIN_PUNTOS:
        return "SIN PUNTOS"
    if motivo in (Motivo.NIVEL_MAXIMO, Motivo.INTEGRIDAD_MAXIMA):
        return "COMPLETO"
    return texto_puntos(coste)


class PantallaMejoras:
    """Dibuja la pantalla de mejoras mientras dura el descanso."""

    def __init__(
        self,
        raiz: NodePath,
        fuente: TextFont | None,
        mejoras: Mejoras,
        estacion: Estacion,
        oleadas: Oleadas,
        flujo: Flujo,
    ) -> None:
        self._raiz = raiz
        self._fuente = fuente
        self._mejoras = mejoras
        self._estacion = estacion
        self._oleadas = oleadas
        self._flujo = flujo
        self._nodo: NodePath | None = None
        self._marco: NodePath | None = None
        self._contenido: NodePath | None = None
        self._clave: tuple[object, ...] | None = None
        self._cuenta_atras: Texto | None = None
        self._abierta = 0.0
        self._escala = 1.0

    def olvidar(self) -> None:
        """Obliga a reconstruirla, por ejemplo tras cambiar la escala de la pantalla."""
        if self._nodo is not None:
            self._nodo.remove_node()
        self._nodo = None
        self._clave = None

    def dibujar(self, visible: bool, escala: float, ancho_diseno: float, dt: float) -> None:
        """Muestra u oculta la pantalla y la pone al día con el estado de la lógica."""
        if not visible:
            self.olvidar()
            return
        if self._nodo is None:
            self._escala = escala
            self._crear(ancho_diseno)
        assert self._marco is not None
        assert self._cuenta_atras is not None
        self._abierta += dt
        avance = min(1.0, self._abierta / _APARICION)
        self._marco.set_alpha_scale(avance * parpadeo_encendido(self._abierta))
        self._marco.set_z(-_DESPLAZAMIENTO * (1 - avance))
        restante = self._oleadas.tiempo_descanso
        tono = AVISO if restante <= _CUENTA_ATRAS_AVISO else ACENTO
        self._cuenta_atras.mostrar(texto_cuenta_atras(restante), tono)
        clave = self._clave_actual()
        if clave != self._clave:
            self._clave = clave
            self._crear_contenido()

    # --- construcción ----------------------------------------------------------------

    def _crear(self, ancho_diseno: float) -> None:
        """Velo, panel y textos fijos; el contenido que cambia va aparte."""
        self._abierta = 0.0
        self._nodo = capa(self._raiz, "mejoras", _ORDEN_VELO)
        rectangulo(self._nodo, 0, 0, ancho_diseno, ALTO_DISENO, _VELO)
        self._marco = self._nodo.attach_new_node("marco")
        self._marco.set_x((ancho_diseno - ANCHO_DISENO) / 2)
        m, e = self._marco, self._escala
        x, y, ancho, alto = _PANEL_X, _PANEL_Y, _PANEL_ANCHO, _PANEL_ALTO
        panel(m, x, y, ancho, alto, e, relleno=_FONDO_PANEL, orden=_ORDEN_PANEL)
        lineas = capa(m, "lineas", _ORDEN_CONTENIDO)
        linea(lineas, [(_IZQUIERDA, 290), (_DERECHA, 290)], color("#2AD4FF", 0.25), 1, e)
        linea(lineas, [(880, 320), (880, 860)], color("#2AD4FF", 0.15), 1, e)
        linea(lineas, [(912, 736), (_DERECHA, 736)], color("#2AD4FF", 0.15), 1, e)
        a_derecha, a_centro = TextNode.A_right, TextNode.A_center
        self._texto(m, _DERECHA, 214, 16, "SIGUIENTE OLEADA EN", TEXTO_SECUNDARIO, a_derecha)
        self._cuenta_atras = Texto(m, self._fuente, _DERECHA, 262, 48, a_derecha, _ORDEN_TEXTO)
        self._texto(m, _IZQUIERDA, 496, 16, "RESULTADO", TEXTO_SECUNDARIO)
        self._texto(m, _IZQUIERDA, 596, 16, "PUNTOS DISPONIBLES", TEXTO_SECUNDARIO)
        self._texto(m, _IZQUIERDA, 752, 16, "INTEGRIDAD", TEXTO_SECUNDARIO)
        pista = capa(m, "pista", _ORDEN_CONTENIDO)
        rectangulo(pista, _BARRA_X, _BARRA_Y, _BARRA_ANCHO, _BARRA_ALTO, PISTA)
        ayudas = "↑↓  Navegar   ·   Intro  Comprar   ·   Esc  Pausa"
        self._texto(m, ANCHO_DISENO / 2, 1029, 16, ayudas, TEXTO_SECUNDARIO, a_centro)
        self._contenido = None
        self._clave = None

    def _clave_actual(self) -> tuple[object, ...]:
        """Todo lo que cambia el contenido; si no cambia, no se reconstruye."""
        m = self._mejoras
        return (
            self._flujo.seleccion_descanso,
            m.puntos,
            m.resultado,
            tuple(m.nivel(mejora) for mejora in Mejora),
            m.motivo_reparar(),
            tuple(m.motivo_mejorar(mejora) for mejora in Mejora),
            math.ceil(self._estacion.integridad - 1e-9),
            self._estacion.integridad_maxima,
            self._oleadas.numero,
        )

    def _crear_contenido(self) -> None:
        assert self._marco is not None
        if self._contenido is not None:
            self._contenido.remove_node()
        self._contenido = self._marco.attach_new_node("contenido")
        c = self._contenido
        resultado = self._mejoras.resultado
        numero = resultado.numero if resultado is not None else self._oleadas.numero
        self._texto(c, _IZQUIERDA, 250, 48, f"OLEADA {numero} SUPERADA", TEXTO)
        if resultado is not None:
            tiempos = (
                f"Tiempo {formato_tiempo(resultado.tiempo)} · "
                f"Referencia {formato_tiempo(resultado.tiempo_referencia)} · "
            )
            self._texto(c, _IZQUIERDA, 528, 20, tiempos, TEXTO)
            x = _IZQUIERDA + ancho_texto(self._fuente, tiempos, 20)
            puntos = "+1 punto" if resultado.puntos == 1 else f"+{resultado.puntos} puntos"
            self._texto(c, x, 528, 20, puntos, ACENTO)
        self._texto(c, _IZQUIERDA, 676, 72, str(self._mejoras.puntos), ACENTO)
        self._dibujar_integridad(c)
        for opcion in self._flujo.opciones_descanso:
            self._dibujar_opcion(c, opcion)

    def _dibujar_integridad(self, padre: NodePath) -> None:
        integridad = self._estacion.integridad
        maxima = self._estacion.integridad_maxima
        valor = f"{math.ceil(integridad - 1e-9)} / {maxima:g}"
        self._texto(padre, _BARRA_X + _BARRA_ANCHO, 752, 20, valor, TEXTO, TextNode.A_right)
        fraccion = max(0.0, min(1.0, integridad / maxima))
        if fraccion > 0:
            relleno = capa(padre, "integridad", _ORDEN_CONTENIDO + 1)
            ancho = fraccion * _BARRA_ANCHO
            tono = color_integridad(fraccion)
            rectangulo(relleno, _BARRA_X, _BARRA_Y, ancho, _BARRA_ALTO, tono)

    def _dibujar_opcion(self, padre: NodePath, opcion: OpcionDescanso) -> None:
        """Una fila: título, efecto, indicador de niveles y coste (`interfaz.md`)."""
        y = _FILAS[opcion]
        seleccionada = opcion is self._flujo.seleccion_descanso
        fila = padre.attach_new_node(opcion.value)
        if seleccionada:
            fondo = capa(fila, "seleccion", _ORDEN_SELECCION)
            rectangulo(fondo, _OPCION_X, y, _OPCION_ANCHO, _OPCION_ALTO, color("#2AD4FF", 0.14))
            rectangulo(fondo, _OPCION_X, y, 4, _OPCION_ALTO, ACENTO)
            marca = "\N{SINGLE RIGHT-POINTING ANGLE QUOTATION MARK}"
            self._texto(fila, _DERECHA - 12, y + 52, 32, marca, TEXTO, TextNode.A_right)
        titulo = TEXTO if seleccionada else TEXTO_SECUNDARIO
        self._texto(fila, 940, y + 40, 32, _TITULOS[opcion], titulo)
        m = self._mejoras
        motivo: Motivo | None
        if opcion is OpcionDescanso.CONTINUAR:
            siguiente = self._oleadas.numero + 1
            self._texto(
                fila, 940, y + 70, 18, f"Empezar ya la oleada {siguiente}", TEXTO_SECUNDARIO
            )
            return
        if opcion is OpcionDescanso.REPARAR:
            efecto = f"+{m.cantidad_reparacion:g} integridad"
            coste, motivo = m.coste_reparacion, m.motivo_reparar()
        else:
            mejora = MEJORA_DE_OPCION[opcion]
            efecto = f"+{m.efecto(mejora):g} {_EFECTOS[mejora]}"
            coste, motivo = m.coste(mejora), m.motivo_mejorar(mejora)
            self._dibujar_niveles(fila, y + 44, m.nivel(mejora), m.nivel_maximo(mejora))
        self._texto(fila, 940, y + 70, 18, efecto, TEXTO_SECUNDARIO)
        tono_coste = ACENTO if seleccionada else TEXTO_SECUNDARIO
        coste_x = _DERECHA - 40
        self._texto(
            fila, coste_x, y + 50, 22, texto_coste(coste, motivo), tono_coste, TextNode.A_right
        )
        if motivo is not None:
            fila.set_alpha_scale(_OPACIDAD_NO_DISPONIBLE)

    def _dibujar_niveles(self, padre: NodePath, y: float, nivel: int, maximo: int) -> None:
        """Puntos rellenos para los niveles comprados y huecos para los que faltan."""
        nodo = capa(padre, "niveles", _ORDEN_CONTENIDO)
        for k in range(maximo):
            centro = (_NIVELES_X + _PASO_NIVEL * k, y)
            if k < nivel:
                poligono(nodo, circulo(centro, _RADIO_NIVEL, 20)[:-1], ACENTO)
            else:
                linea(nodo, circulo(centro, _RADIO_NIVEL, 20), ACENTO, 1, self._escala)

    def _texto(
        self,
        padre: NodePath,
        x: float,
        y: float,
        tamano: float,
        contenido: str,
        tono: Color,
        alineacion: int = TextNode.A_left,
    ) -> None:
        Texto(padre, self._fuente, x, y, tamano, alineacion, _ORDEN_TEXTO).mostrar(contenido, tono)
