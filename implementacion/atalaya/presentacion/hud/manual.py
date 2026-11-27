"""Manual del juego (`interfaz.md`, «Manual»; `08-manual.svg`; CU-10).

Todas las cifras salen de `parametros`, así que el manual coincide siempre con el
comportamiento real. El contenido de cada sección lo calculan funciones sin motor
(`filas_controles`, `tarjetas_enemigos`…), que se pueden probar sin ventana; la clase
`PantallaManual` solo lo dibuja. La sección que se muestra la decide `flujo`.
"""

from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

from panda3d.core import NodePath, TextFont, TextNode

from atalaya.logica.flujo import Flujo, SeccionManual
from atalaya.logica.nucleo.dominio import Mejora, Tamano, TipoEnemigo
from atalaya.logica.parametros import Parametros
from atalaya.presentacion.hud.componentes import PantallaMenu, ayudas
from atalaya.presentacion.hud.dibujo import (
    Punto,
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
    COLOR_TIPO,
    TEXTO,
    TEXTO_SECUNDARIO,
    cifra,
    forma_contacto,
)

# --- contenido -----------------------------------------------------------------------

#: Nombre de cada pestaña, en el orden de `SeccionManual`.
PESTANAS = {
    SeccionManual.CONTROLES: "CONTROLES",
    SeccionManual.ENEMIGOS: "ENEMIGOS",
    SeccionManual.TAMANOS: "TAMAÑOS",
    SeccionManual.ENTORNOS: "ENTORNOS",
    SeccionManual.MEJORAS: "MEJORAS",
}

#: Título de cada sección, encima de su contenido.
TITULOS = {
    SeccionManual.CONTROLES: "CONTROLES",
    SeccionManual.ENEMIGOS: "TIPOS DE ENEMIGO",
    SeccionManual.TAMANOS: "TAMAÑOS DE ENEMIGO",
    SeccionManual.ENTORNOS: "ENTORNOS DE BAJA VISIBILIDAD",
    SeccionManual.MEJORAS: "MEJORAS Y REPARACIÓN",
}

_NOMBRES_TIPO = {
    TipoEnemigo.SIN_EFECTO: "SIN EFECTO",
    TipoEnemigo.DESESTABILIZADOR: "DESESTABILIZADOR",
    TipoEnemigo.ATURDIDOR: "ATURDIDOR",
}
_NOMBRES_TAMANO = {Tamano.PEQUENO: "PEQUEÑO", Tamano.MEDIANO: "MEDIANO", Tamano.GRANDE: "GRANDE"}
#: Dificultad para acertar, del enemigo con la zona de impacto más pequeña a la más grande.
_DIFICULTADES = ("difícil", "media", "fácil")
_NOMBRES_MEJORA = {
    Mejora.BLINDAJE: "BLINDAJE",
    Mejora.ESCUDO: "ESCUDO",
    Mejora.BATERIA: "BATERÍA",
    Mejora.GENERADOR: "GENERADOR",
}
_EFECTOS_MEJORA = {
    Mejora.BLINDAJE: "integridad máxima",
    Mejora.ESCUDO: "escudo máximo",
    Mejora.BATERIA: "energía máxima",
    Mejora.GENERADOR: "recarga de energía por segundo",
}


@dataclass(frozen=True, slots=True)
class Tarjeta:
    """Tarjeta del manual: un título y filas de etiqueta y valor.

    Un valor con un salto de línea ocupa dos renglones.
    """

    titulo: str
    filas: tuple[tuple[str, str], ...]


def _puntos(n: int) -> str:
    return "1 punto" if n == 1 else f"{n} puntos"


def filas_controles(p: Parametros) -> list[tuple[str, str]]:
    """Teclas y acciones (CU-10, «Controles»)."""
    j = p.jugador
    return [
        ("Flechas o W A S D", "Girar la vista"),
        ("Ratón", "Mover la mira por la pantalla"),
        ("Espacio o clic (mantener)", "Apuntar: la mira se reduce y la vista se acerca"),
        ("Soltar", f"Disparar; cada disparo gasta {cifra(j.coste_disparo)} de energía"),
        ("Esc", "Pausar la partida"),
        ("Intro", "Elegir una opción en los menús"),
    ]


def notas_controles(p: Parametros) -> list[str]:
    j = p.jugador
    return [
        f"La energía máxima es {cifra(j.energia_maxima)} y se recarga a "
        f"{cifra(j.recarga_energia)} por segundo.",
        f"La mira llega a su tamaño mínimo en {cifra(j.tiempo_apuntado)} s de apuntado.",
    ]


def _efecto_tipo(p: Parametros, tipo: TipoEnemigo) -> str:
    """Efecto del tipo con su duración, del escudo lleno al vacío (RN-51)."""
    minima = cifra(round(p.duracion_efecto(tipo, 1.0), 2))
    maxima = cifra(p.duracion_efecto(tipo, 0.0))
    if tipo is TipoEnemigo.DESESTABILIZADOR:
        return f"pantalla y mira\ntiemblan {minima} a {maxima} s"
    if tipo is TipoEnemigo.ATURDIDOR:
        return f"no puedes girar ni\ndisparar {minima} a {maxima} s"
    return "ninguno"


def tarjetas_enemigos(p: Parametros) -> list[tuple[TipoEnemigo, Tarjeta]]:
    """Daño, recarga, primera oleada y efecto de cada tipo (RN-11 a RN-14, RN-16)."""
    desde = {
        TipoEnemigo.SIN_EFECTO: 1,
        TipoEnemigo.DESESTABILIZADOR: p.oleadas.oleada_desestabilizadores,
        TipoEnemigo.ATURDIDOR: p.oleadas.oleada_aturdidores,
    }
    tarjetas = []
    for tipo in TipoEnemigo:
        datos = p.tipos.de(tipo)
        filas = (
            ("Daño", cifra(datos.dano)),
            ("Recarga", f"{cifra(datos.recarga)} s"),
            ("Aparece desde", f"oleada {desde[tipo]}"),
            ("Efecto", _efecto_tipo(p, tipo)),
        )
        tarjetas.append((tipo, Tarjeta(_NOMBRES_TIPO[tipo], filas)))
    return tarjetas


def notas_enemigos(p: Parametros) -> list[str]:
    aviso = cifra(p.ataques.duracion_aviso)
    return [
        f"Todos los enemigos avisan con un destello y un sonido de carga {aviso} s "
        "antes de disparar.",
        "Si los destruyes durante el aviso, no llegan a disparar.",
        _nota_escudo(p),
    ]


def _nota_escudo(p: Parametros) -> str:
    """Cómo cambia el escudo la duración de los efectos (RN-51)."""
    j = p.jugador
    desestabilizacion = cifra(p.tipos.desestabilizador.duracion_efecto)
    aturdimiento = cifra(p.tipos.aturdidor.duracion_efecto)
    desgaste = cifra(p.tipos.desestabilizador.desgaste_escudo)
    return (
        f"El escudo acorta los efectos: al {cifra(j.umbral_escudo)} % duran "
        f"{desestabilizacion} s y {aturdimiento} s. Cada impacto con efecto gasta {desgaste}."
    )


def tarjetas_tamanos(p: Parametros, nivel: int) -> list[tuple[Tamano, Tarjeta]]:
    """Vida en el nivel `nivel`, velocidad y dificultad para acertar (RN-06, RN-22)."""
    por_radio = sorted(Tamano, key=lambda t: p.tamanos.de(t).radio_impacto)
    tarjetas = []
    for tamano in Tamano:
        datos = p.tamanos.de(tamano)
        dificultad = _DIFICULTADES[min(por_radio.index(tamano), len(_DIFICULTADES) - 1)]
        filas = (
            ("Vida", cifra(round(p.vida_enemigo(tamano, nivel), 2))),
            ("Velocidad", f"{cifra(datos.velocidad_maxima)} u/s"),
            ("Zona de impacto", f"{cifra(datos.radio_impacto)} u"),
            ("Para acertar", dificultad),
        )
        tarjetas.append((tamano, Tarjeta(_NOMBRES_TAMANO[tamano], filas)))
    return tarjetas


def notas_tamanos(p: Parametros, nivel: int) -> list[str]:
    incremento = cifra(round(p.nivel.incremento_vida * 100, 2))
    return [
        f"Vida en el nivel {nivel}. Cada disparo que acierta quita "
        f"{cifra(p.jugador.dano_disparo)} de vida.",
        f"Cada nivel de dificultad suma un {incremento} % de la vida del nivel 1.",
    ]


def textos_entornos(p: Parametros) -> list[tuple[str, list[str]]]:
    """Qué son la niebla y los destellos y cómo afectan a la visibilidad (RN-44)."""
    e = p.entornos
    return [
        (
            "NIEBLA",
            [
                "Una nube de polvo cósmico difumina a los enemigos",
                "y a sus proyectiles según la distancia.",
                f"Se ven bien hasta {cifra(e.niebla_visibilidad_completa)} u y desaparecen",
                f"a partir de {cifra(e.niebla_invisible)} u.",
            ],
        ),
        (
            "DESTELLOS",
            [
                "Una estrella cercana lanza llamaradas que deslumbran",
                f"la pantalla durante {cifra(e.destellos_deslumbramiento)} s, una cada "
                f"{cifra(e.destellos_intervalo_minimo)} a {cifra(e.destellos_intervalo_maximo)} s.",
                f"Antes de cada una, un resplandor avisa durante {cifra(e.destellos_aviso)} s.",
            ],
        ),
    ]


def notas_entornos(p: Parametros) -> list[str]:
    e = p.entornos
    return [
        f"Desde la oleada {e.primera_oleada}, una de cada {e.intervalo_oleadas} oleadas "
        "tiene entorno: niebla y destellos, por turnos.",
        "Los enemigos no cambian; el radar y los indicadores siguen igual.",
    ]


def filas_mejoras(p: Parametros) -> list[tuple[str, str, str, str]]:
    """Nombre, efecto, coste y niveles de cada opción del descanso (RN-46, RN-47, RN-51).

    En el mismo orden que la pantalla de mejoras: la regeneración, tras el blindaje.
    """
    m = p.mejoras
    filas = [
        (
            "REPARAR",
            f"+{cifra(m.cantidad_reparacion)} integridad, sin pasar del máximo",
            _puntos(m.coste_reparacion),
            "sin límite",
        )
    ]
    for mejora in Mejora:
        datos = m.de(mejora)
        efecto = f"+{cifra(datos.efecto)} {_EFECTOS_MEJORA[mejora]} por nivel"
        filas.append(
            (_NOMBRES_MEJORA[mejora], efecto, _puntos(datos.coste), str(datos.niveles_maximos))
        )
    regenerar = (
        "REGENERAR ESCUDO",
        f"+{cifra(m.cantidad_regeneracion)} escudo, sin pasar del máximo",
        _puntos(m.coste_regeneracion),
        "sin límite",
    )
    filas.insert(2, regenerar)
    return filas


def notas_mejoras(p: Parametros) -> list[str]:
    m = p.mejoras
    return [
        f"Al superar una oleada ganas {_puntos(m.puntos_rapido)} si tardas como mucho el "
        f"tiempo de referencia, {m.puntos_medio} si tardas hasta {cifra(m.factor_tiempo_medio)} "
        f"veces ese tiempo y {m.puntos_lento} si tardas más.",
        f"Tiempo de referencia: {cifra(m.tiempo_referencia_base)} s más "
        f"{cifra(m.tiempo_referencia_por_enemigo)} s por enemigo. "
        "Puntos y mejoras duran solo una partida.",
    ]


# --- dibujo --------------------------------------------------------------------------

#: Panel centrado de 1440 × 840 px.
_PANEL_X, _PANEL_Y, _PANEL_ANCHO, _PANEL_ALTO = 240, 120, 1440, 840
_IZQUIERDA, _DERECHA = 288, 1632
_FONDO_PANEL = color("#0A1220", 0.88)
_VELO = color("#000000", 0.45)
_FONDO_TARJETA = color("#0F1A2C")
_BORDE_TARJETA = color("#2AD4FF", 0.2)
_PESTANA_Y, _TAMANO_PESTANA, _SEPARACION_PESTANAS = 192, 22, 60
_TITULO_Y = 288
_TARJETA_Y, _TARJETA_ALTO = 320, 440
_NOTAS_Y = 830

_ORDEN_PANEL = 81
_ORDEN_TARJETA = 83
_ORDEN_DIBUJO = 85


class PantallaManual(PantallaMenu):
    """Panel con las pestañas de las secciones y el contenido de la actual."""

    def __init__(
        self, raiz: NodePath, fuente: TextFont | None, flujo: Flujo, parametros: Parametros
    ) -> None:
        super().__init__(raiz, fuente)
        self._flujo = flujo
        self._parametros = parametros

    def _fondo(self, nodo: NodePath) -> None:
        # Desde la pausa, `escena` ya oscurece la partida detenida.
        if self._flujo.pantalla_pausada is None:
            rectangulo(nodo, 0, 0, self._ancho, ALTO_DISENO, _VELO)

    def _clave(self) -> object:
        return (self._flujo.seccion_manual, self._flujo.nivel_manual)

    def _construir(self, padre: NodePath) -> None:
        marco = padre.attach_new_node("manual")
        marco.set_x(self._dx)
        e = self._escala
        panel(
            marco, _PANEL_X, _PANEL_Y, _PANEL_ANCHO, _PANEL_ALTO, e,
            relleno=_FONDO_PANEL, orden=_ORDEN_PANEL,
        )  # fmt: skip
        self._pestanas(marco)
        seccion = self._flujo.seccion_manual
        self._texto(marco, _IZQUIERDA, _TITULO_Y, 16, TITULOS[seccion], TEXTO_SECUNDARIO)
        p, nivel = self._parametros, self._flujo.nivel_manual
        if seccion is SeccionManual.CONTROLES:
            self._controles(marco)
            notas = notas_controles(p)
        elif seccion is SeccionManual.ENEMIGOS:
            for i, (tipo, tarjeta) in enumerate(tarjetas_enemigos(p)):
                self._tarjeta(marco, i, tarjeta, partial(self._simbolo_tipo, tipo=tipo))
            notas = notas_enemigos(p)
        elif seccion is SeccionManual.TAMANOS:
            for i, (tamano, tarjeta) in enumerate(tarjetas_tamanos(p, nivel)):
                self._tarjeta(marco, i, tarjeta, partial(self._simbolo_tamano, tamano=tamano))
            notas = notas_tamanos(p, nivel)
        elif seccion is SeccionManual.ENTORNOS:
            self._entornos(marco)
            notas = notas_entornos(p)
        else:
            self._mejoras(marco)
            notas = notas_mejoras(p)
        for k, nota in enumerate(notas):
            self._texto(marco, _IZQUIERDA, _NOTAS_Y + 32 * k, 20, nota, TEXTO_SECUNDARIO)
        ayudas(marco, self._fuente, ANCHO_DISENO / 2, [("←→", "Sección"), ("Esc", "Volver")], e)

    def _pestanas(self, padre: NodePath) -> None:
        """Pestañas en una fila con la actual subrayada, y la posición a la derecha."""
        secciones = self._flujo.secciones_manual
        actual = self._flujo.seccion_manual
        x = float(_IZQUIERDA)
        subrayado = capa(padre, "subrayado", _ORDEN_DIBUJO)
        for seccion in secciones:
            nombre = PESTANAS[seccion]
            ancho = ancho_texto(self._fuente, nombre, _TAMANO_PESTANA)
            elegida = seccion is actual
            tono = ACENTO if elegida else TEXTO_SECUNDARIO
            self._texto(padre, x, _PESTANA_Y, _TAMANO_PESTANA, nombre, tono)
            if elegida:
                rectangulo(subrayado, x, _PESTANA_Y + 12, ancho, 3, ACENTO)
            x += ancho + _SEPARACION_PESTANAS
        posicion = f"{secciones.index(actual) + 1} / {len(secciones)}"
        self._texto(
            padre, _DERECHA, _PESTANA_Y, _TAMANO_PESTANA, posicion, TEXTO_SECUNDARIO,
            TextNode.A_right,
        )  # fmt: skip
        separador = capa(padre, "separador", _ORDEN_DIBUJO)
        linea(separador, [(_IZQUIERDA, 230), (_DERECHA, 230)], color("#2AD4FF", 0.25), 1,
              self._escala)  # fmt: skip

    def _caja(self, padre: NodePath, x: float, y: float, ancho: float, alto: float) -> None:
        panel(
            padre, x, y, ancho, alto, self._escala, relleno=_FONDO_TARJETA,
            borde=_BORDE_TARJETA, orden=_ORDEN_TARJETA,
        )  # fmt: skip

    def _tarjeta(
        self,
        padre: NodePath,
        indice: int,
        tarjeta: Tarjeta,
        simbolo: Callable[[NodePath, Punto], None],
    ) -> None:
        """Una de tres tarjetas en fila: símbolo, título y filas de etiqueta y valor."""
        ancho, hueco = 416.0, 48.0
        x = _IZQUIERDA + indice * (ancho + hueco)
        self._caja(padre, x, _TARJETA_Y, ancho, _TARJETA_ALTO)
        centro = x + ancho / 2
        dibujo = capa(padre, "simbolo", _ORDEN_DIBUJO)
        simbolo(dibujo, (centro, 410.0))
        a_centro = TextNode.A_center
        self._texto(padre, centro, 470, 14, "Símbolo en el radar", TEXTO_SECUNDARIO, a_centro)
        self._texto(padre, centro, 520, 32, tarjeta.titulo, TEXTO, a_centro)
        y = 584.0
        for etiqueta, valor in tarjeta.filas:
            self._texto(padre, x + 32, y, 20, etiqueta, TEXTO_SECUNDARIO)
            for renglon in valor.split("\n"):
                self._texto(padre, x + ancho - 32, y, 20, renglon, TEXTO, TextNode.A_right)
                y += 28
            y += 10

    def _simbolo_tipo(self, padre: NodePath, centro: Punto, tipo: TipoEnemigo) -> None:
        poligono(padre, forma_contacto(tipo, centro, 44), COLOR_TIPO[tipo])

    def _simbolo_tamano(self, padre: NodePath, centro: Punto, tamano: Tamano) -> None:
        # El contacto del radar mide 8, 12 o 16 px; aquí se dibuja al triple.
        lado = {Tamano.PEQUENO: 8, Tamano.MEDIANO: 12, Tamano.GRANDE: 16}[tamano] * 3
        poligono(padre, circulo(centro, lado / 2, 32)[:-1], TEXTO)

    def _controles(self, padre: NodePath) -> None:
        """Tabla de teclas y acciones."""
        for k, (tecla, accion) in enumerate(filas_controles(self._parametros)):
            y = 340 + 64 * k
            self._caja(padre, _IZQUIERDA, y, 400, 48)
            self._texto(padre, _IZQUIERDA + 24, y + 32, 22, tecla, ACENTO)
            self._texto(padre, _IZQUIERDA + 440, y + 32, 22, accion, TEXTO)

    def _entornos(self, padre: NodePath) -> None:
        """Niebla y destellos, uno al lado del otro."""
        ancho, hueco = 648.0, 48.0
        for i, (titulo, renglones) in enumerate(textos_entornos(self._parametros)):
            x = _IZQUIERDA + i * (ancho + hueco)
            self._caja(padre, x, _TARJETA_Y, ancho, 300)
            self._texto(padre, x + 32, _TARJETA_Y + 64, 32, titulo, TEXTO)
            for k, renglon in enumerate(renglones):
                self._texto(padre, x + 32, _TARJETA_Y + 120 + 34 * k, 20, renglon, TEXTO)

    def _mejoras(self, padre: NodePath) -> None:
        """Tabla con el efecto, el coste y los niveles de cada opción."""
        columnas = (_IZQUIERDA + 24, _IZQUIERDA + 280, _IZQUIERDA + 1040, _IZQUIERDA + 1220)
        for x, cabecera in zip(columnas, ("OPCIÓN", "EFECTO", "COSTE", "NIVELES"), strict=True):
            self._texto(padre, x, 352, 16, cabecera, TEXTO_SECUNDARIO)
        # Seis filas de 58 px cada 70 px: la última acaba antes de las notas.
        for k, fila in enumerate(filas_mejoras(self._parametros)):
            y = 376 + 70 * k
            self._caja(padre, _IZQUIERDA, y, _DERECHA - _IZQUIERDA, 58)
            for i, (x, valor) in enumerate(zip(columnas, fila, strict=True)):
                tono = TEXTO if i == 0 else TEXTO_SECUNDARIO if i == 1 else ACENTO
                self._texto(padre, x, y + 37, 24 if i == 0 else 20, valor, tono)
