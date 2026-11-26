"""HUD de la partida (`modulos/hud.md`, `interfaz/interfaz.md`, sección 6).

Versión de S5: la mira, que sigue al ratón, el radar con el símbolo y el color de cada
tipo y tamaño, las barras de integridad y energía, el nivel, el panel de oleada, el
aviso de aturdimiento, la pantalla de mejoras del descanso (`mejoras.py`) y el resumen
mínimo de derrota. Las transmisiones y los menús llegan en sprints posteriores.

La mira desviada por desestabilización (RN-12) no se desplaza en la pantalla: `escena`
gira la imagen con el desvío de `vista`, así que la mira queda desviada respecto a la
escena justo hacia donde va el disparo.
"""

import math

from direct.showbase.ShowBase import ShowBase
from panda3d.core import CardMaker, NodePath, TextNode, TransparencyAttrib

from atalaya.logica.armamento import Armamento
from atalaya.logica.estacion import Estacion
from atalaya.logica.flujo import Flujo, Pantalla
from atalaya.logica.mejoras import Mejoras
from atalaya.logica.nucleo.bus import Bus
from atalaya.logica.nucleo.dominio import Tamano, TipoEnemigo
from atalaya.logica.nucleo.eventos import DisparoSinEnergia, PartidaIniciada
from atalaya.logica.oleadas import Oleadas
from atalaya.logica.parametros import Parametros
from atalaya.logica.radar import Altura, Contacto, Radar
from atalaya.logica.vista import Vista
from atalaya.presentacion.escena.efectos import textura_vineta
from atalaya.presentacion.hud.dibujo import (
    Color,
    Punto,
    Texto,
    capa,
    cargar_fuente,
    circulo,
    color,
    linea,
    mezclar,
    panel,
    poligono,
    rectangulo,
)
from atalaya.presentacion.hud.estilo import (
    ACENTO,
    ALTO_DISENO,
    ANCHO_DISENO,
    AVISO,
    FONDO_PANEL,
    PELIGRO,
    PISTA,
    TEXTO,
    TEXTO_SECUNDARIO,
    VELO,
    color_integridad,
)
from atalaya.presentacion.hud.mejoras import PantallaMejoras

#: Color de cada tipo de enemigo y de sus proyectiles (`interfaz.md`, sección 3).
COLOR_TIPO: dict[TipoEnemigo, Color] = {
    TipoEnemigo.SIN_EFECTO: color("#FF4D5E"),
    TipoEnemigo.DESESTABILIZADOR: color("#FFD23F"),
    TipoEnemigo.ATURDIDOR: color("#B36BFF"),
}

#: Orden de dibujo de cada capa del HUD (`dibujo.capa`): las mayores, encima.
_ORDEN_PISTA = 2
_ORDEN_RELLENO = 3
_ORDEN_MARCAS = 4
_ORDEN_CONTACTOS = 5
_ORDEN_MIRA = 6
_ORDEN_VELO = 60
_ORDEN_TEXTO_VELO = 70

#: Panel de estado de la estación (`interfaz/03-oleada.svg`).
_PANEL_X, _PANEL_Y, _PANEL_ANCHO, _PANEL_ALTO = 1440, 912, 432, 120
_BARRA_X, _BARRA_ANCHO, _BARRA_ALTO = 1464, 384, 10
_INTEGRIDAD_Y = 956
_ENERGIA_Y = 1006

#: Panel de oleada, centrado arriba.
_OLEADA_X, _OLEADA_Y, _OLEADA_ANCHO, _OLEADA_ALTO = 780, 32, 360, 80

#: Radar, abajo a la izquierda.
_RADAR_CENTRO: Punto = (210, 870)
_RADAR_RADIO = 150
#: Diámetro del contacto según el tamaño del enemigo, en píxeles de diseño.
_TAMANO_CONTACTO = {Tamano.PEQUENO: 8, Tamano.MEDIANO: 12, Tamano.GRANDE: 16}
_OPACIDAD_FUERA = 0.7
#: El contacto de un enemigo en aviso parpadea dos veces por segundo.
_PARPADEO_AVISO = 0.5
#: Lado de la marca de altura junto al contacto.
_MARCA_ALTURA = 6

#: Aviso sin energía: tres parpadeos en 0,6 s y el texto durante 1 s.
_PARPADEO = 0.6
_PARPADEOS = 3
_AVISO_TEXTO = 1.0
#: Constante de tiempo de la transición de las barras: llegan al valor en unos 150 ms.
_TRANSICION = 0.05

#: Mira: grosor, separación y largo de las marcas, y radio del punto central.
_GROSOR_MIRA = 2
_SEPARACION_MARCAS = 10
_LARGO_MARCAS = 10
_RADIO_PUNTO = 3
_OPACIDAD_MIRA = 0.9
#: Mira bloqueada por aturdimiento: trazo discontinuo y opacidad al 40 %.
_OPACIDAD_MIRA_ATURDIDA = 0.4
_TRAZO_DISCONTINUO = 8
_HUECO_DISCONTINUO = 6

#: Cartel de aturdimiento bajo el panel de oleada (`interfaz/05-aturdido.svg`).
_CARTEL_X, _CARTEL_Y, _CARTEL_ANCHO, _CARTEL_ALTO = 700, 128, 520, 56
#: Opacidad de la viñeta de aturdimiento en los bordes de la pantalla.
_OPACIDAD_VINETA_ATURDIDO = 0.3
#: Orden de dibujo de la viñeta: debajo del HUD, encima de la escena.
_ORDEN_VINETA = -5


def radio_mira_en_pantalla(radio: float, campo_vision: float) -> float:
    """Radio de la mira en píxeles de diseño (`interfaz.md`, «Mira»)."""
    mitad = ALTO_DISENO / 2
    return mitad * math.tan(math.radians(radio)) / math.tan(math.radians(campo_vision) / 2)


def posicion_en_radar(contacto: Contacto) -> Punto:
    """Punto del radar de un contacto: «adelante» arriba y ángulos en sentido horario."""
    cx, cy = _RADAR_CENTRO
    r = _RADAR_RADIO * contacto.distancia_relativa
    angulo = math.radians(contacto.angulo)
    return cx + r * math.sin(angulo), cy - r * math.cos(angulo)


def forma_contacto(tipo: TipoEnemigo, centro: Punto, lado: float) -> list[Punto]:
    """Círculo, triángulo o rombo según el tipo, para distinguirlo también sin color."""
    x, y = centro
    m = lado / 2
    if tipo is TipoEnemigo.DESESTABILIZADOR:
        return [(x, y - m), (x + m, y + m), (x - m, y + m)]
    if tipo is TipoEnemigo.ATURDIDOR:
        return [(x, y - m), (x + m, y), (x, y + m), (x - m, y)]
    return circulo(centro, m, 20)[:-1]


def texto_aturdimiento(restante: float) -> str:
    """Texto del cartel de aturdimiento con la cuenta atrás en décimas, con coma decimal.

    Se redondea hacia arriba: mientras dura el aturdimiento nunca muestra «0,0 s».
    """
    decimas = max(1, math.ceil(restante * 10 - 1e-9))
    return f"SISTEMAS ATURDIDOS · {decimas // 10},{decimas % 10} s"


def circulo_discontinuo(centro: Punto, radio: float) -> list[list[Punto]]:
    """Trazos de una circunferencia discontinua: 8 px de trazo y 6 px de hueco."""
    periodo = _TRAZO_DISCONTINUO + _HUECO_DISCONTINUO
    trazos = max(1, round(2 * math.pi * radio / periodo))
    fraccion = _TRAZO_DISCONTINUO / periodo
    cx, cy = centro
    resultado = []
    for k in range(trazos):
        inicio = 2 * math.pi * k / trazos
        fin = inicio + 2 * math.pi * fraccion / trazos
        puntos = [
            (
                cx + radio * math.cos(inicio + (fin - inicio) * i / 4),
                cy + radio * math.sin(inicio + (fin - inicio) * i / 4),
            )
            for i in range(5)
        ]
        resultado.append(puntos)
    return resultado


class _Barra:
    """Barra con transición suave que solo se reconstruye cuando cambia."""

    def __init__(self, padre: NodePath, y: float) -> None:
        self._padre = padre
        self._y = y
        self._nodo: NodePath | None = None
        self._clave: tuple[float, Color, int] | None = None
        self.mostrada: float | None = None

    def olvidar(self) -> None:
        """Obliga a reconstruirla, por ejemplo tras cambiar la escala."""
        self._clave = None

    def dibujar(self, actual: float, maxima: float, relleno: Color, marcas: int, dt: float) -> None:
        if self.mostrada is None:
            self.mostrada = actual
        self.mostrada += (actual - self.mostrada) * (1 - math.exp(-dt / _TRANSICION))
        fraccion = max(0.0, min(1.0, self.mostrada / maxima))
        clave = (round(fraccion * _BARRA_ANCHO, 1), relleno, marcas)
        if clave == self._clave:
            return
        self._clave = clave
        if self._nodo is not None:
            self._nodo.remove_node()
        self._nodo = capa(self._padre, "barra", _ORDEN_RELLENO)
        if fraccion > 0:
            rectangulo(self._nodo, _BARRA_X, self._y, fraccion * _BARRA_ANCHO, _BARRA_ALTO, relleno)
        for k in range(1, marcas):
            x = _BARRA_X + _BARRA_ANCHO * k / marcas
            marca = rectangulo(self._nodo, x - 1, self._y, 2, _BARRA_ALTO, FONDO_PANEL)
            marca.set_bin("fixed", _ORDEN_MARCAS)


class Hud:
    """Dibuja encima de la escena la mira, el radar y los indicadores de la partida."""

    def __init__(
        self,
        base: ShowBase,
        bus: Bus,
        parametros: Parametros,
        armamento: Armamento,
        vista: Vista,
        radar: Radar,
        estacion: Estacion,
        oleadas: Oleadas,
        mejoras: Mejoras,
        flujo: Flujo,
    ) -> None:
        self._base = base
        self._parametros = parametros
        self._jugador = parametros.jugador
        self._armamento = armamento
        self._vista = vista
        self._radar = radar
        self._estacion = estacion
        self._oleadas = oleadas
        self._flujo = flujo
        self._fuente = cargar_fuente(base)
        self._raiz = base.pixel2d.attach_new_node("hud")
        self._escala = 0.0
        self._ancho_diseno = float(ANCHO_DISENO)
        self._izquierda = self._raiz.attach_new_node("izquierda")
        self._centro = self._raiz.attach_new_node("centro")
        self._derecha = self._raiz.attach_new_node("derecha")
        self._tiempo = 0.0
        self._mira: NodePath | None = None
        self._clave_mira: tuple[float, Color, bool] | None = None
        self._cartel: NodePath | None = None
        self._vineta = self._crear_vineta()
        self._sector: NodePath | None = None
        self._clave_sector: float | None = None
        self._contactos: NodePath | None = None
        self._velo: NodePath | None = None
        self._desde_sin_energia = math.inf
        self._energia = _Barra(self._derecha, _ENERGIA_Y)
        self._integridad = _Barra(self._derecha, _INTEGRIDAD_Y)
        self._estaticos: list[NodePath] = []
        self._textos: dict[str, Texto] = {}
        self._pantalla_mejoras = PantallaMejoras(
            self._raiz, self._fuente, mejoras, estacion, oleadas, flujo
        )
        bus.suscribir(DisparoSinEnergia, self._al_disparar_sin_energia)
        bus.suscribir(PartidaIniciada, self._al_iniciar_partida)

    def dibujar(self, dt: float) -> None:
        """Actualiza el HUD una vez por fotograma consultando el estado de la lógica."""
        self._ajustar_escala()
        self._tiempo += dt
        self._desde_sin_energia += dt
        pantalla = self._flujo.pantalla
        derrota = pantalla is Pantalla.RESUMEN
        descanso = pantalla is Pantalla.DESCANSO
        aturdido = self._estacion.aturdido and not derrota
        # En el descanso no se apunta: la mira solo se ve durante la oleada.
        self._dibujar_mira(visible=not (derrota or descanso), aturdida=aturdido)
        self._dibujar_radar()
        self._dibujar_estado(dt)
        self._dibujar_oleada()
        self._dibujar_aturdimiento(aturdido)
        self._pantalla_mejoras.dibujar(descanso, self._escala, self._ancho_diseno, dt)
        self._dibujar_resumen(derrota)

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
        self._ancho_diseno = ancho / escala
        self._centro.set_x((self._ancho_diseno - ANCHO_DISENO) / 2)
        self._derecha.set_x(self._ancho_diseno - ANCHO_DISENO)
        self._crear_estaticos()
        self._clave_mira = None
        self._clave_sector = None
        self._energia.olvidar()
        self._integridad.olvidar()
        self._pantalla_mejoras.olvidar()
        if self._velo is not None:
            self._velo.remove_node()
            self._velo = None

    def _crear_estaticos(self) -> None:
        """Paneles, pistas, el fondo del radar y los textos; cuelgan de nodos fijos."""
        for nodo in self._estaticos:
            nodo.remove_node()
        derecha = capa(self._derecha, "estaticos", _ORDEN_PISTA)
        centro = capa(self._centro, "estaticos", _ORDEN_PISTA)
        izquierda = capa(self._izquierda, "estaticos", _ORDEN_PISTA)
        self._estaticos = [derecha, centro, izquierda]
        e = self._escala
        panel(derecha, _PANEL_X, _PANEL_Y, _PANEL_ANCHO, _PANEL_ALTO, e)
        for y in (_INTEGRIDAD_Y, _ENERGIA_Y):
            rectangulo(derecha, _BARRA_X, y, _BARRA_ANCHO, _BARRA_ALTO, PISTA)
        panel(centro, _OLEADA_X, _OLEADA_Y, _OLEADA_ANCHO, _OLEADA_ALTO, e)
        self._crear_fondo_radar(izquierda)
        self._cartel = centro.attach_new_node("cartel-aturdimiento")
        atenuado = color("#0A1220", 0.85)
        aturdidor = COLOR_TIPO[TipoEnemigo.ATURDIDOR]
        x, y, ancho, alto = _CARTEL_X, _CARTEL_Y, _CARTEL_ANCHO, _CARTEL_ALTO
        panel(self._cartel, x, y, ancho, alto, e, relleno=atenuado, borde=aturdidor)
        self._cartel.hide()
        f, a_derecha, a_centro = self._fuente, TextNode.A_right, TextNode.A_center
        fin_barra = _BARRA_X + _BARRA_ANCHO
        mitad_barra = _BARRA_X + _BARRA_ANCHO / 2
        self._textos = {
            "integridad": Texto(derecha, f, _BARRA_X, _INTEGRIDAD_Y - 10, 16),
            "integridad_valor": Texto(derecha, f, fin_barra, _INTEGRIDAD_Y - 10, 20, a_derecha),
            "energia": Texto(derecha, f, _BARRA_X, _ENERGIA_Y - 10, 16),
            "energia_valor": Texto(derecha, f, fin_barra, _ENERGIA_Y - 10, 20, a_derecha),
            # Sobre la barra de energía, entre su etiqueta y su valor.
            "sin_energia": Texto(derecha, f, mitad_barra, _ENERGIA_Y - 10, 16, a_centro),
            "nivel": Texto(derecha, f, _PANEL_X + _PANEL_ANCHO, _PANEL_Y - 14, 16, a_derecha),
            "oleada": Texto(centro, f, ANCHO_DISENO / 2, 72, 30, a_centro),
            "restantes": Texto(centro, f, ANCHO_DISENO / 2, 98, 16, a_centro),
            "radar": Texto(izquierda, f, 60, 702, 16),
            "aturdimiento": Texto(self._cartel, f, ANCHO_DISENO / 2, 164, 24, a_centro),
        }
        cx, cy = _RADAR_CENTRO
        alcance = self._parametros.ataques.alcance_radar
        for k in (1, 2):
            texto = Texto(izquierda, f, cx + 4, cy - _RADAR_RADIO * k / 3 - 2, 11)
            texto.mostrar(f"{alcance * k / 3:g}", TEXTO_SECUNDARIO)
        self._textos["radar"].mostrar("RADAR", TEXTO_SECUNDARIO)
        self._textos["integridad"].mostrar("INTEGRIDAD", TEXTO_SECUNDARIO)
        self._textos["energia"].mostrar("ENERGÍA", TEXTO_SECUNDARIO)

    def _crear_fondo_radar(self, padre: NodePath) -> None:
        cx, cy = _RADAR_CENTRO
        fondo = poligono(padre, circulo(_RADAR_CENTRO, _RADAR_RADIO)[:-1], color("#0A1220", 0.78))
        fondo.set_bin("fixed", 0)
        lineas = capa(padre, "anillos", 1)
        e = self._escala
        linea(lineas, circulo(_RADAR_CENTRO, _RADAR_RADIO), color("#2AD4FF", 0.35), 1, e)
        for k in (1, 2):
            anillo = circulo(_RADAR_CENTRO, _RADAR_RADIO * k / 3)
            linea(lineas, anillo, color("#2AD4FF", 0.2), 1, e)
        cruz = capa(padre, "estacion", _ORDEN_CONTACTOS)
        linea(cruz, [(cx - 5, cy), (cx + 5, cy)], ACENTO, 2, e)
        linea(cruz, [(cx, cy - 5), (cx, cy + 5)], ACENTO, 2, e)

    # --- mira ------------------------------------------------------------------------

    def _dibujar_mira(self, visible: bool, aturdida: bool) -> None:
        j = self._jugador
        progreso = self._armamento.progreso_apuntado
        campo = j.campo_vision_normal + (j.campo_vision_zoom - j.campo_vision_normal) * progreso
        radio = radio_mira_en_pantalla(self._armamento.radio_mira, campo)
        tono = mezclar(TEXTO, ACENTO, progreso)
        clave = (round(radio, 2), tono, aturdida)
        if clave != self._clave_mira or self._mira is None:
            self._clave_mira = clave
            if self._mira is not None:
                self._mira.remove_node()
            self._mira = capa(self._centro, "mira", _ORDEN_MIRA)
            cx, cy = ANCHO_DISENO / 2, ALTO_DISENO / 2
            e = self._escala
            if aturdida:
                # Mira bloqueada (`interfaz/05-aturdido.svg`): círculo discontinuo y punto,
                # sin marcas exteriores, todo al 40 %.
                trazo = (*tono[:3], _OPACIDAD_MIRA_ATURDIDA)
                for trazo_circulo in circulo_discontinuo((cx, cy), radio):
                    linea(self._mira, trazo_circulo, trazo, _GROSOR_MIRA, e)
                poligono(self._mira, circulo((cx, cy), _RADIO_PUNTO, 16)[:-1], trazo)
            else:
                trazo = (*tono[:3], _OPACIDAD_MIRA)
                linea(self._mira, circulo((cx, cy), radio), trazo, _GROSOR_MIRA, e)
                dentro = radio + _SEPARACION_MARCAS
                fuera = dentro + _LARGO_MARCAS
                for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                    marca = [
                        (cx + dx * dentro, cy + dy * dentro),
                        (cx + dx * fuera, cy + dy * fuera),
                    ]
                    linea(self._mira, marca, trazo, _GROSOR_MIRA, e)
                poligono(self._mira, circulo((cx, cy), _RADIO_PUNTO, 16)[:-1], tono)
        # La mira está donde la ha puesto el ratón: `puntero` va en medias alturas desde el
        # centro, con la y hacia arriba, y el HUD dibuja con la y de diseño hacia abajo.
        x, y = self._vista.puntero
        mitad = ALTO_DISENO / 2
        self._mira.set_pos(x * mitad, 0, y * mitad)
        if visible:
            self._mira.show()
        else:
            self._mira.hide()

    # --- radar -----------------------------------------------------------------------

    def _dibujar_radar(self) -> None:
        self._dibujar_sector(self._radar.sector_vision)
        if self._contactos is not None:
            self._contactos.remove_node()
        self._contactos = capa(self._izquierda, "contactos", _ORDEN_CONTACTOS)
        apagado = (self._tiempo % _PARPADEO_AVISO) >= _PARPADEO_AVISO / 2
        for contacto in self._radar.contactos:
            self._dibujar_contacto(self._contactos, contacto, apagado)

    def _dibujar_sector(self, apertura: float) -> None:
        """Sector del campo de visión, abierto hacia arriba; se estrecha con el zoom."""
        clave = round(apertura, 2)
        if clave == self._clave_sector:
            return
        self._clave_sector = clave
        if self._sector is not None:
            self._sector.remove_node()
        self._sector = capa(self._izquierda, "sector", _ORDEN_PISTA)
        cx, cy = _RADAR_CENTRO
        mitad = math.radians(apertura / 2)
        lados = 24
        arco = [
            (
                cx + _RADAR_RADIO * math.sin(-mitad + 2 * mitad * i / lados),
                cy - _RADAR_RADIO * math.cos(-mitad + 2 * mitad * i / lados),
            )
            for i in range(lados + 1)
        ]
        poligono(self._sector, [_RADAR_CENTRO, *arco], color("#2AD4FF", 0.10))

    def _dibujar_contacto(self, padre: NodePath, contacto: Contacto, apagado: bool) -> None:
        x, y = posicion_en_radar(contacto)
        lado = _TAMANO_CONTACTO[contacto.tamano]
        nodo = padre.attach_new_node("contacto")
        forma = forma_contacto(contacto.tipo, (x, y), lado)
        poligono(nodo, forma, COLOR_TIPO[contacto.tipo])
        if contacto.en_campo_vision:
            linea(nodo, [*forma, forma[0]], TEXTO, 1, self._escala)
        else:
            nodo.set_alpha_scale(_OPACIDAD_FUERA)
        if contacto.altura is not Altura.MISMA:
            mx, m = x + lado / 2 + 5, _MARCA_ALTURA / 2
            if contacto.altura is Altura.POR_ENCIMA:
                my = y - lado / 2
                marca = [(mx, my - m), (mx + m, my + m), (mx - m, my + m)]
            else:
                my = y + lado / 2
                marca = [(mx - m, my - m), (mx + m, my - m), (mx, my + m)]
            poligono(nodo, marca, TEXTO)
        if contacto.en_aviso and apagado:
            nodo.set_alpha_scale(0.15)

    # --- estado de la estación -------------------------------------------------------

    def _dibujar_estado(self, dt: float) -> None:
        integridad = self._estacion.integridad
        maxima = self._estacion.integridad_maxima
        tono = color_integridad(integridad / maxima)
        self._integridad.dibujar(integridad, maxima, tono, 0, dt)
        valor = f"{math.ceil(integridad - 1e-9)} / {maxima:g}"
        self._textos["integridad_valor"].mostrar(valor, TEXTO)
        self._textos["nivel"].mostrar(f"NIVEL {self._flujo.nivel}", ACENTO)

        energia = self._armamento.energia
        energia_maxima = self._armamento.energia_maxima
        relleno = AVISO if self._parpadeo_encendido() else ACENTO
        # Una marca cada «coste de un disparo», para contar los disparos que quedan.
        marcas = math.ceil(energia_maxima / self._jugador.coste_disparo)
        self._energia.dibujar(energia, energia_maxima, relleno, marcas, dt)
        valor_energia = f"{math.floor(energia + 1e-9)} / {energia_maxima:g}"
        self._textos["energia_valor"].mostrar(valor_energia, TEXTO)
        if self._desde_sin_energia < _AVISO_TEXTO:
            self._textos["sin_energia"].mostrar("SIN ENERGÍA", AVISO)
        else:
            self._textos["sin_energia"].ocultar()

    def _parpadeo_encendido(self) -> bool:
        t = self._desde_sin_energia
        if t >= _PARPADEO:
            return False
        periodo = _PARPADEO / _PARPADEOS
        return (t % periodo) < periodo / 2

    # --- oleada ----------------------------------------------------------------------

    def _dibujar_oleada(self) -> None:
        total = self._parametros.oleadas.numero_oleadas
        numero = max(1, self._oleadas.numero)
        self._textos["oleada"].mostrar(f"OLEADA {numero} / {total}", TEXTO)
        restantes = self._oleadas.restantes
        texto = "1 ENEMIGO RESTANTE" if restantes == 1 else f"{restantes} ENEMIGOS RESTANTES"
        self._textos["restantes"].mostrar(texto, TEXTO_SECUNDARIO)

    # --- aturdimiento -----------------------------------------------------------------

    def _crear_vineta(self) -> NodePath:
        """Viñeta del color del aturdidor en los bordes, a pantalla completa (RF-15)."""
        tarjeta = CardMaker("vineta-aturdimiento")
        tarjeta.set_frame(-1, 1, -1, 1)
        vineta = self._base.render2d.attach_new_node(tarjeta.generate())
        vineta.set_texture(textura_vineta())
        vineta.set_color(*COLOR_TIPO[TipoEnemigo.ATURDIDOR][:3], _OPACIDAD_VINETA_ATURDIDO)
        vineta.set_transparency(TransparencyAttrib.M_alpha)
        vineta.set_depth_test(False)
        vineta.set_depth_write(False)
        vineta.set_bin("fixed", _ORDEN_VINETA)
        vineta.hide()
        return vineta

    def _dibujar_aturdimiento(self, aturdido: bool) -> None:
        """Cartel con la cuenta atrás y viñeta mientras dura el aturdimiento (RF-15)."""
        if self._cartel is None:
            return
        if not aturdido:
            self._cartel.hide()
            self._vineta.hide()
            return
        self._cartel.show()
        self._vineta.show()
        texto = texto_aturdimiento(self._estacion.tiempo_aturdimiento)
        self._textos["aturdimiento"].mostrar(texto, COLOR_TIPO[TipoEnemigo.ATURDIDOR])

    # --- resumen de derrota ----------------------------------------------------------

    def _dibujar_resumen(self, visible: bool) -> None:
        """Resumen mínimo de derrota (`interfaz.md`, «Fin de partida»), sin menú todavía."""
        if not visible:
            if self._velo is not None:
                self._velo.remove_node()
                self._velo = None
            return
        if self._velo is not None:
            return
        self._velo = capa(self._raiz, "resumen", _ORDEN_VELO)
        rectangulo(self._velo, 0, 0, self._ancho_diseno, ALTO_DISENO, VELO)
        textos = self._velo.attach_new_node("textos")
        textos.set_x((self._ancho_diseno - ANCHO_DISENO) / 2)
        f, centro, x = self._fuente, TextNode.A_center, ANCHO_DISENO / 2
        o = _ORDEN_TEXTO_VELO
        total = self._parametros.oleadas.numero_oleadas
        lineas = [
            (440, 96, "ESTACIÓN PERDIDA", PELIGRO),
            (500, 24, "La Atalaya ha caído.", TEXTO),
            (580, 22, f"OLEADAS SUPERADAS  {self._flujo.oleadas_superadas} / {total}", TEXTO),
            (620, 22, f"NIVEL  {self._flujo.nivel}", TEXTO),
            (1032, 16, "Intro  Volver a jugar   ·   Esc  Salir del juego", TEXTO_SECUNDARIO),
        ]
        for y, tamano, contenido, tono in lineas:
            Texto(textos, f, x, y, tamano, centro, o).mostrar(contenido, tono)

    # --- eventos ---------------------------------------------------------------------

    def _al_disparar_sin_energia(self, evento: DisparoSinEnergia) -> None:
        self._desde_sin_energia = 0.0

    def _al_iniciar_partida(self, evento: PartidaIniciada) -> None:
        self._desde_sin_energia = math.inf
        self._energia.mostrada = None
        self._integridad.mostrada = None
