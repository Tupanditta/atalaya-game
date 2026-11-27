"""Ventana y escena 3D (`modulos/escena.md`).

Versión de S6: ventana a pantalla completa, cámara orientada según `vista`, el fondo
actual de `entorno` entre los cinco cielos generados (RN-20), enemigos con el modelo y
el color de su tipo y la escala de su tamaño, el brillo de su motor y su destello de
aviso, proyectiles, disparo bláster desde dos cañones alternos, destello y chispas en
el impacto, explosión con onda expansiva y sacudida de la cámara, daño recibido
(temblor y tinte rojo) y temblor continuo por desestabilización. Entre dos fondos, la
animación del salto hiperespacial (`salto.py`). Cada fondo tiene su paisaje de
planetas, asteroides y polvo (`paisaje.py`), y el sol de ese fondo ilumina también a los
enemigos. Con la partida en pausa, la escena
queda congelada y oscurecida; sin partida en curso (menú principal y resumen), el fondo
gira muy despacio. Los entornos de baja visibilidad llegan en un sprint posterior.
"""

import math

from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    AmbientLight,
    CardMaker,
    DirectionalLight,
    GraphicsStateGuardianBase,
    NodePath,
    Quat,
    Texture,
    TransparencyAttrib,
    Vec3,
    WindowProperties,
    load_prc_file_data,
)

from atalaya.logica.enemigos import Enemigos, FaseAtaque, distancia_impacto
from atalaya.logica.entorno import EntornoEspacial
from atalaya.logica.nucleo.bus import Bus, Evento
from atalaya.logica.nucleo.dominio import Tamano, TipoEnemigo, Vector3
from atalaya.logica.nucleo.eventos import (
    DescansoIniciado,
    DisparoRealizado,
    EnemigoAlcanzado,
    EnemigoDestruido,
    EstacionDanada,
    EstacionDestruida,
    FondoCambiado,
    PartidaAbandonada,
    PartidaIniciada,
    PausaCambiada,
    SaltoIniciado,
)
from atalaya.logica.parametros import Parametros
from atalaya.logica.vista import Vista, interpolar
from atalaya.presentacion.escena.efectos import (
    Calentamiento,
    Chispas,
    DanoRecibido,
    Destello,
    Efecto,
    Explosion,
    Proyectil,
    Rayo,
    Sacudida,
    brillo,
    textura_anillo,
    textura_brillo,
)
from atalaya.presentacion.escena.fondo import Fondos, cubo_de_cielo
from atalaya.presentacion.escena.modelos import COLOR_TIPO, modelo_enemigo
from atalaya.presentacion.escena.paisaje import Paisaje
from atalaya.presentacion.escena.planetas import PAISAJES
from atalaya.presentacion.escena.salto import SaltoHiperespacial

#: Resolución si el sistema no informa de la de la pantalla (`design.md`, sección 6).
ANCHO = 1920
ALTO = 1080

#: Distancia del plano cercano de la cámara.
_PLANO_CERCANO = 0.5
#: Distancia del plano lejano: más allá del alcance del radar y de los planetas del
#: paisaje, con sus anillos.
_PLANO_LEJANO = 9000.0

#: Salida del disparo respecto a la cámara (derecha, delante, arriba). Si saliera del
#: centro de la cámara se vería como un punto; así se ve como una línea hacia el impacto.
#: Hay dos cañones, a izquierda y derecha, que disparan por turnos.
_SALIDA_RAYO: Vector3 = (0.35, 1.0, -0.45)

#: Brillo del motor de los enemigos: posición detrás del cuerpo y tamaño, en radios.
_POSICION_MOTOR = -0.8
_TAMANO_MOTOR = 0.55

#: Radio del modelo de un enemigo, en fracción del radio de su zona de impacto. La zona
#: de impacto es más amplia que la nave para que el disparo sea más certero (RN-06).
_ESCALA_MODELO = 0.5

#: Sacudida de la cámara por una explosión: grados por cada unidad de radio del enemigo
#: dividida por su distancia, y máximo.
_SACUDIDA_POR_RADIO = 6.0
_SACUDIDA_MAXIMA = 0.5

#: Eventos de la simulación que se convierten en efectos o limpian la escena.
_EVENTOS = (
    DisparoRealizado,
    EnemigoAlcanzado,
    EnemigoDestruido,
    EstacionDanada,
    PartidaIniciada,
    PartidaAbandonada,
    EstacionDestruida,
)

#: Destello de aviso de disparo, en radios del enemigo: crece durante el aviso (RN-34).
_AVISO_TAMANO_INICIAL = 1.5
_AVISO_TAMANO_FINAL = 6.0

#: Velo de pausa: negro al 55 % que se oscurece en 150 ms (`interfaz.md`, secciones 3 y 8).
_OPACIDAD_VELO = 0.55
_APARICION_VELO = 0.15
#: Orden de dibujo del velo en `render2d`: encima de los tintes de la escena y debajo del HUD.
_ORDEN_VELO = -4

#: Giro del fondo sin partida en curso, en grados por segundo: «muy despacio».
_GIRO_MENU = 1.5


def crear_ventana() -> ShowBase:
    """Abre la ventana del juego a pantalla completa con la resolución nativa de la pantalla.

    Cursor oculto: la mira del HUD hace de cursor (RES-04). La cámara adapta el campo de
    visión horizontal a la proporción de la pantalla, así que cualquier resolución se ve
    sin deformar.
    """
    load_prc_file_data(
        "atalaya",
        """
        window-title Atalaya
        sync-video true
        cursor-hidden true
        show-frame-rate-meter false
        """,
    )
    base = ShowBase(windowType="none")
    base.makeDefaultPipe()
    ancho, alto = base.pipe.get_display_width(), base.pipe.get_display_height()
    if ancho <= 0 or alto <= 0:
        ancho, alto = ANCHO, ALTO
    propiedades = WindowProperties.get_default()
    propiedades.set_size(ancho, alto)
    propiedades.set_fullscreen(True)
    base.openDefaultWindow(props=propiedades)
    base.disable_mouse()
    base.set_background_color(0, 0, 0, 1)
    return base


class Escena:
    """Dibuja el mundo desde la cámara del jugador."""

    def __init__(
        self,
        base: ShowBase,
        bus: Bus,
        vista: Vista,
        enemigos: Enemigos,
        entorno: EntornoEspacial,
        parametros: Parametros,
    ) -> None:
        self._base = base
        self._vista = vista
        self._enemigos = enemigos
        self._parametros = parametros
        base.camLens.set_near_far(_PLANO_CERCANO, _PLANO_LEJANO)
        self._entorno = entorno
        self._fondos = Fondos()
        # Espacio: el cielo y el paisaje del fondo, que el salto apaga y cambia juntos.
        self._espacio = base.render.attach_new_node("espacio")
        self._fondo = cubo_de_cielo(self._fondos.textura(entorno.fondo))
        self._fondo.reparent_to(self._espacio)
        self._mundo = base.render.attach_new_node("mundo")
        self._sol = self._iluminar()
        self._brillo = textura_brillo()
        self._anillo = textura_anillo()
        self._paisaje = Paisaje(self._espacio, self._brillo)
        self._poner_fondo(entorno.fondo)
        self._salto = SaltoHiperespacial(base.camera, base.render2d, self._espacio, self._brillo)
        self._modelos: dict[int, NodePath] = {}
        self._avisos: dict[int, NodePath] = {}
        self._motores: dict[int, NodePath] = {}
        self._tamanos: dict[int, Tamano] = {}
        self._tipos: dict[int, TipoEnemigo] = {}
        self._canon = 1.0
        self._sacudida = Sacudida()
        self._tiempo = 0.0
        self._proyectiles: dict[int, Proyectil] = {}
        self._dano = DanoRecibido(base.render2d)
        self._efectos: list[Efecto] = []
        self._eventos: list[Evento] = []
        self._velo = self._crear_velo()
        self._en_pausa = False
        self._velo_mostrado = 0.0
        self._en_partida = False
        self._rumbo_menu = 0.0
        self._cabeceo_menu = 0.0
        # Texturas y geometría de los efectos y del salto, ya en la tarjeta gráfica: la
        # primera explosión o el primer salto no dan un tirón.
        self._preparar(self._brillo, self._anillo)
        gsg = self._gsg()
        if gsg is not None:
            self._salto.preparar(gsg)
        self._calentar()
        for tipo in _EVENTOS:
            bus.suscribir(tipo, self._anotar)
        bus.suscribir(PausaCambiada, self._al_cambiar_pausa)
        bus.suscribir(DescansoIniciado, self._al_iniciar_descanso)
        bus.suscribir(SaltoIniciado, self._al_iniciar_salto)
        bus.suscribir(FondoCambiado, self._al_cambiar_fondo)
        bus.suscribir(PartidaIniciada, self._al_iniciar_partida)
        bus.suscribir(PartidaAbandonada, self._al_terminar_partida)
        bus.suscribir(EstacionDestruida, self._al_terminar_partida)

    def _anotar(self, evento: Evento) -> None:
        """Guarda el evento para convertirlo en efectos en el siguiente fotograma."""
        self._eventos.append(evento)

    def dibujar(self, fraccion: float, dt: float) -> None:
        """Dibuja un fotograma interpolando entre los dos últimos pasos de simulación.

        `fraccion` es la parte del paso siguiente ya transcurrida, entre 0 y 1; `dt` es
        el tiempo real desde el fotograma anterior, para animar los efectos.
        """
        self._mostrar_velo(dt)
        # En pausa todo queda congelado: los efectos no avanzan.
        dt_escena = 0.0 if self._en_pausa else dt
        self._tiempo += dt_escena
        v = self._vista
        if self._en_partida:
            q = interpolar(v.orientacion_anterior, v.orientacion, fraccion)
            # Panda3D usa la misma convención de ejes que la lógica (x derecha, y delante,
            # z arriba), así que el cuaternión se pasa tal cual.
            self._base.camera.set_quat(Quat(q.w, q.x, q.y, q.z))
            self._temblar(v.desvio)
        else:
            self._rumbo_menu = (self._rumbo_menu - _GIRO_MENU * dt) % 360
            self._base.camera.set_hpr(self._rumbo_menu, self._cabeceo_menu, 0)
        # Los efectos nuevos aparecen en este mismo fotograma (RNF-05).
        self._procesar_eventos()
        self._paisaje.avanzar(dt_escena)
        self._salto.avanzar(dt_escena, self._base.camera)
        self._ajustar_lente(v.campo_vision + self._salto.apertura)
        self._dano.avanzar(dt_escena, self._base.camera)
        self._sacudida.avanzar(dt_escena, self._base.camera)
        self._colocar_enemigos(fraccion)
        self._colocar_proyectiles(fraccion)
        self._efectos = [e for e in self._efectos if e.avanzar(dt_escena)]

    # --- pausa y menú ----------------------------------------------------------------

    def _crear_velo(self) -> NodePath:
        """Velo negro a pantalla completa que oscurece la escena en pausa."""
        tarjeta = CardMaker("velo-pausa")
        tarjeta.set_frame(-1, 1, -1, 1)
        velo = self._base.render2d.attach_new_node(tarjeta.generate())
        velo.set_color(0, 0, 0, 1)
        velo.set_transparency(TransparencyAttrib.M_alpha)
        velo.set_depth_test(False)
        velo.set_depth_write(False)
        velo.set_bin("fixed", _ORDEN_VELO)
        velo.hide()
        return velo

    def _mostrar_velo(self, dt: float) -> None:
        """Oscurece la escena en 150 ms al pausar; al reanudar, el velo se quita."""
        if not self._en_pausa:
            self._velo_mostrado = 0.0
            self._velo.hide()
            return
        self._velo_mostrado = min(1.0, self._velo_mostrado + dt / _APARICION_VELO)
        self._velo.show()
        self._velo.set_alpha_scale(_OPACIDAD_VELO * self._velo_mostrado)

    def _al_cambiar_pausa(self, evento: PausaCambiada) -> None:
        self._en_pausa = evento.activa

    def _al_iniciar_partida(self, evento: PartidaIniciada) -> None:
        self._en_partida = True

    def _al_terminar_partida(self, evento: Evento) -> None:
        """Sin partida, el fondo gira despacio desde donde miraba la cámara."""
        self._en_partida = False
        self._rumbo_menu = self._base.camera.get_h()
        self._cabeceo_menu = self._base.camera.get_p()

    # --- fondo -----------------------------------------------------------------------

    def _gsg(self) -> GraphicsStateGuardianBase | None:
        return self._base.win.get_gsg() if self._base.win is not None else None

    def _preparar(self, *texturas: Texture) -> None:
        """Sube las texturas a la tarjeta gráfica antes de que se usen."""
        gsg = self._gsg()
        if gsg is not None:
            for textura in texturas:
                textura.prepare(gsg.get_prepared_objects())

    def _preparar_fondo(self, indice: int) -> None:
        """Crea el cielo y el paisaje del fondo `indice` y los sube a la tarjeta gráfica."""
        self._preparar(self._fondos.textura(indice))
        self._paisaje.preparar(indice, self._fondos.texturas_planetas(indice), self._gsg())

    def _poner_fondo(self, indice: int) -> None:
        """Muestra el cielo y el paisaje del fondo `indice`, con la luz de su sol."""
        self._fondo.set_texture(self._fondos.textura(indice), 1)
        self._paisaje.mostrar(indice, self._fondos.texturas_planetas(indice))
        paisaje = PAISAJES[indice - 1]
        # Los enemigos se iluminan desde el mismo sol que los planetas.
        self._sol.node().set_color((*(0.9 * c for c in paisaje.luz_color), 1.0))
        self._sol.look_at(-Vec3(*paisaje.luz_direccion))

    def _al_iniciar_descanso(self, evento: DescansoIniciado) -> None:
        """Si tras este descanso hay salto, prepara ya el cielo y el paisaje de destino.

        Crearlos y subirlos a la tarjeta gráfica cuesta algún fotograma; así pasa tras la
        pantalla de mejoras y no en mitad del salto.
        """
        anterior = evento.siguiente_oleada - 1
        if 1 <= anterior <= self._parametros.oleadas.numero_oleadas and (
            self._parametros.hay_salto_tras(anterior)
        ):
            self._preparar_fondo(self._parametros.fondo_oleada(evento.siguiente_oleada))

    def _al_iniciar_salto(self, evento: SaltoIniciado) -> None:
        """Empieza la animación del salto; el fondo se cambia a mitad del túnel, sin verse."""
        self._preparar_fondo(evento.fondo)
        self._salto.iniciar(evento.duracion, lambda: self._poner_fondo(evento.fondo))

    def _al_cambiar_fondo(self, evento: FondoCambiado) -> None:
        self._poner_fondo(evento.indice)

    def _cancelar_salto(self) -> None:
        """Un salto interrumpido deja el fondo en que sigue la partida."""
        if self._salto.activo:
            self._salto.cancelar()
            self._poner_fondo(self._entorno.fondo)

    # --- enemigos --------------------------------------------------------------------

    def _iluminar(self) -> NodePath:
        """Luz ambiente y sol de los enemigos; el sol se orienta según el fondo."""
        ambiente = AmbientLight("ambiente")
        ambiente.set_color((0.35, 0.38, 0.45, 1))
        sol = DirectionalLight("sol")
        sol.set_color((0.9, 0.88, 0.85, 1))
        nodo_sol = self._mundo.attach_new_node(sol)
        nodo_sol.set_hpr(30, -40, 0)
        self._mundo.set_light(self._mundo.attach_new_node(ambiente))
        self._mundo.set_light(nodo_sol)
        return nodo_sol

    def _colocar_enemigos(self, fraccion: float) -> None:
        """Crea, mueve y borra los modelos para que coincidan con los enemigos activos."""
        activos = {e.id: e for e in self._enemigos.activos}
        for id in [i for i in self._modelos if i not in activos]:
            self._modelos.pop(id).remove_node()
            self._avisos.pop(id, None)
            self._motores.pop(id, None)
            self._tamanos.pop(id, None)
            self._tipos.pop(id, None)
        for id, enemigo in activos.items():
            modelo = self._modelos.get(id)
            if modelo is None:
                modelo = modelo_enemigo(enemigo.tipo, self._radio(enemigo.tamano))
                modelo.reparent_to(self._mundo)
                self._modelos[id] = modelo
                self._avisos[id] = brillo(modelo, self._brillo, COLOR_TIPO[enemigo.tipo])
                motor = brillo(modelo, self._brillo, COLOR_TIPO[enemigo.tipo])
                motor.set_pos(0, _POSICION_MOTOR, 0)
                self._motores[id] = motor
                self._tamanos[id] = enemigo.tamano
                self._tipos[id] = enemigo.tipo
            # El motor parpadea un poco, cada enemigo a su ritmo.
            parpadeo = 0.85 + 0.15 * math.sin(self._tiempo * 37.0 + id * 1.7)
            self._motores[id].set_scale(_TAMANO_MOTOR * parpadeo)
            a, b = Vec3(*enemigo.posicion_anterior), Vec3(*enemigo.posicion)
            posicion = a + (b - a) * fraccion
            modelo.set_pos(posicion)
            velocidad = Vec3(*enemigo.velocidad)
            if velocidad.length() > 1e-3:
                modelo.look_at(posicion + velocidad, Vec3(0, 0, 1))
            self._mostrar_aviso(self._avisos[id], enemigo.fase, enemigo.tiempo_fase)

    def _mostrar_aviso(self, aviso: NodePath, fase: FaseAtaque, restante: float) -> None:
        """Destello creciente del color del tipo mientras dura el aviso de disparo."""
        if fase is not FaseAtaque.AVISO:
            aviso.hide()
            return
        duracion = self._parametros.ataques.duracion_aviso
        progreso = min(1.0, max(0.0, 1 - restante / duracion))
        aviso.show()
        tamano = _AVISO_TAMANO_INICIAL + (_AVISO_TAMANO_FINAL - _AVISO_TAMANO_INICIAL) * progreso
        aviso.set_scale(tamano)
        aviso.set_alpha_scale(0.25 + 0.75 * progreso)

    def _colocar_proyectiles(self, fraccion: float) -> None:
        """Crea, mueve y borra los proyectiles para que coincidan con los que vuelan."""
        en_vuelo = {p.id: p for p in self._enemigos.proyectiles}
        for id in [i for i in self._proyectiles if i not in en_vuelo]:
            self._proyectiles.pop(id).quitar()
        for id, proyectil in en_vuelo.items():
            dibujo = self._proyectiles.get(id)
            if dibujo is None:
                dibujo = Proyectil(self._mundo, self._brillo, COLOR_TIPO[proyectil.tipo_enemigo])
                self._proyectiles[id] = dibujo
            a, b = Vec3(*proyectil.posicion_anterior), Vec3(*proyectil.posicion)
            dibujo.colocar(a + (b - a) * fraccion, Vec3(*proyectil.velocidad))

    def _radio(self, tamano: Tamano) -> float:
        """Radio del modelo del enemigo, con el que se dibujan la nave y sus efectos."""
        return self._parametros.tamanos.de(tamano).radio_impacto * _ESCALA_MODELO

    # --- efectos ---------------------------------------------------------------------

    def _procesar_eventos(self) -> None:
        """Convierte los eventos de la simulación en efectos.

        En el bus, cada DisparoRealizado va seguido del impacto que haya causado, que
        `enemigos` publica en el mismo paso.
        """
        eventos, self._eventos = self._eventos, []
        disparo: DisparoRealizado | None = None
        impacto: tuple[Vec3, float] | None = None
        for evento in eventos:
            if isinstance(evento, DisparoRealizado):
                self._lanzar_rayo(disparo, impacto)
                disparo, impacto = evento, None
            elif isinstance(evento, EnemigoAlcanzado):
                enemigo = self._enemigos.enemigo(evento.id)
                if disparo is not None and enemigo is not None:
                    impacto = self._punto_impacto(disparo, enemigo.posicion, enemigo.tamano)
            elif isinstance(evento, EnemigoDestruido):
                tamano = self._tamanos.get(evento.id, Tamano.MEDIANO)
                tipo = self._tipos.get(evento.id, TipoEnemigo.SIN_EFECTO)
                if disparo is not None:
                    impacto = self._punto_impacto(disparo, evento.posicion, tamano)
                self._explotar(Vec3(*evento.posicion), self._radio(tamano), tipo)
            elif isinstance(evento, EstacionDanada):
                self._dano.recibir()
            else:
                self._limpiar()
                disparo, impacto = None, None
        self._lanzar_rayo(disparo, impacto)

    def _punto_impacto(
        self, disparo: DisparoRealizado, centro: Vector3, tamano: Tamano
    ) -> tuple[Vec3, float]:
        """Punto donde el disparo entra en la zona de impacto, y el radio de esta."""
        radio = self._radio(tamano)
        distancia = distancia_impacto(disparo.origen, disparo.direccion, centro, radio)
        if distancia is None:
            # El enemigo se ha movido desde el disparo: se usa su punto más cercano al rayo.
            relativo = Vec3(*centro) - Vec3(*disparo.origen)
            distancia = max(0.0, relativo.dot(Vec3(*disparo.direccion)))
        return Vec3(*disparo.origen) + Vec3(*disparo.direccion) * distancia, radio

    def _lanzar_rayo(
        self, disparo: DisparoRealizado | None, impacto: tuple[Vec3, float] | None
    ) -> None:
        if disparo is None:
            return
        derecha, delante, arriba = _SALIDA_RAYO
        self._canon = -self._canon
        salida = Vec3(*self._vista.orientacion.rotar((derecha * self._canon, delante, arriba)))
        if impacto is None:
            # Sin impacto, el disparo se pierde a la distancia máxima de los enemigos.
            fin = Vec3(*disparo.direccion) * self._parametros.ataques.distancia_maxima
            self._efectos.append(Rayo(self._mundo, self._brillo, salida, fin))
            return
        fin, radio = impacto
        rayo = Rayo(self._mundo, self._brillo, salida, fin)
        self._efectos.append(rayo)
        # El destello y las chispas esperan a que llegue el disparo.
        retraso = rayo.duracion_vuelo
        self._efectos.append(Destello(self._mundo, self._brillo, fin, radio * 0.8, retraso))
        self._efectos.append(Chispas(self._mundo, self._brillo, fin, radio, retraso=retraso))

    def _calentar(self) -> None:
        """Dibuja una vez cada efecto, lejos y diminuto, para que el primero real no tarde."""
        lejos = Vec3(0, _PLANO_LEJANO * 0.8, 0)
        proyectil = Proyectil(self._mundo, self._brillo, COLOR_TIPO[TipoEnemigo.SIN_EFECTO])
        proyectil.colocar(lejos, Vec3(0, -1, 0))
        motor = brillo(self._mundo, self._brillo, COLOR_TIPO[TipoEnemigo.SIN_EFECTO])
        motor.set_pos(lejos)
        efectos: list[Efecto] = [
            Explosion(self._mundo, self._brillo, self._anillo, lejos, 0.01),
            Chispas(self._mundo, self._brillo, lejos, 0.01),
            Rayo(self._mundo, self._brillo, lejos, lejos + Vec3(0, 1, 0)),
            Destello(self._mundo, self._brillo, lejos, 0.01),
        ]
        self._efectos.append(Calentamiento(efectos, [proyectil.nodo, motor]))

    def _explotar(self, punto: Vec3, radio: float, tipo: TipoEnemigo) -> None:
        """Explosión del color del tipo y sacudida de la cámara según tamaño y distancia."""
        self._efectos.append(
            Explosion(self._mundo, self._brillo, self._anillo, punto, radio, COLOR_TIPO[tipo])
        )
        distancia = max(punto.length(), 1.0)
        self._sacudida.sacudir(min(_SACUDIDA_MAXIMA, _SACUDIDA_POR_RADIO * radio / distancia))

    def _limpiar(self) -> None:
        self._cancelar_salto()
        for modelo in self._modelos.values():
            modelo.remove_node()
        self._modelos.clear()
        self._avisos.clear()
        self._motores.clear()
        self._tamanos.clear()
        self._tipos.clear()
        for proyectil in self._proyectiles.values():
            proyectil.quitar()
        self._proyectiles.clear()
        # El daño recibido no se corta: el último impacto también se ve al caer la estación.
        for efecto in self._efectos:
            efecto.avanzar(math.inf)
        self._efectos.clear()

    def _temblar(self, desvio: tuple[float, float]) -> None:
        """Temblor continuo de la imagen por desestabilización (RN-12).

        La cámara de la escena se gira justo el desvío de la mira de `vista`: la mira del
        HUD, que sigue en el punto del ratón, queda sobre la escena desviada y señala
        hacia donde va el disparo. Solo es visual; la orientación de `vista` no cambia.
        """
        derecha, arriba = desvio
        if derecha or arriba:
            # En Panda3D, el rumbo positivo gira a la izquierda y el cabeceo, hacia arriba.
            self._base.camera.set_hpr(self._base.camera, -derecha, arriba, 0)

    def _ajustar_lente(self, vertical: float) -> None:
        """Campo de visión vertical en grados; el horizontal sale de la proporción."""
        proporcion = self._base.get_aspect_ratio()
        horizontal = math.degrees(2 * math.atan(math.tan(math.radians(vertical) / 2) * proporcion))
        self._base.camLens.set_fov(horizontal, vertical)
