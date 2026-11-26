"""Ventana y escena 3D (`modulos/escena.md`).

Versión de S2: ventana a pantalla completa, cámara orientada según `vista`, fondo 1,
enemigos, rayo del disparo, destello de impacto y explosión básica. Los proyectiles,
el daño recibido, los entornos y los cambios de fondo llegan en sprints posteriores.
"""

import math

from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    AmbientLight,
    DirectionalLight,
    NodePath,
    Quat,
    Vec3,
    WindowProperties,
    load_prc_file_data,
)

from atalaya.logica.enemigos import Enemigos, distancia_impacto
from atalaya.logica.nucleo.bus import Bus, Evento
from atalaya.logica.nucleo.dominio import Tamano, Vector3
from atalaya.logica.nucleo.eventos import (
    DisparoRealizado,
    EnemigoAlcanzado,
    EnemigoDestruido,
    EstacionDestruida,
    PartidaAbandonada,
    PartidaIniciada,
)
from atalaya.logica.parametros import Parametros
from atalaya.logica.vista import Vista, interpolar
from atalaya.presentacion.escena.efectos import (
    Destello,
    Efecto,
    Explosion,
    Rayo,
    textura_brillo,
)
from atalaya.presentacion.escena.fondo import cubo_de_cielo, textura_fondo
from atalaya.presentacion.escena.modelos import modelo_enemigo

#: Resolución si el sistema no informa de la de la pantalla (`design.md`, sección 6).
ANCHO = 1920
ALTO = 1080

#: Distancia del plano cercano de la cámara.
_PLANO_CERCANO = 0.5
#: Distancia del plano lejano: más allá del alcance del radar.
_PLANO_LEJANO = 5000.0

#: Salida del rayo respecto a la cámara (derecha, delante, arriba). Si saliera del centro
#: de la cámara se vería como un punto; así se ve como una línea hacia el impacto.
_SALIDA_RAYO: Vector3 = (0.35, 1.0, -0.45)

#: Eventos de la simulación que se convierten en efectos o limpian la escena.
_EVENTOS = (
    DisparoRealizado,
    EnemigoAlcanzado,
    EnemigoDestruido,
    PartidaIniciada,
    PartidaAbandonada,
    EstacionDestruida,
)


def crear_ventana() -> ShowBase:
    """Abre la ventana del juego a pantalla completa con la resolución nativa de la pantalla.

    Sin ratón (RES-04). La cámara adapta el campo de visión horizontal a la proporción
    de la pantalla, así que cualquier resolución se ve sin deformar.
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
        parametros: Parametros,
    ) -> None:
        self._base = base
        self._vista = vista
        self._enemigos = enemigos
        self._parametros = parametros
        base.camLens.set_near_far(_PLANO_CERCANO, _PLANO_LEJANO)
        self._fondo = cubo_de_cielo(textura_fondo(1))
        self._fondo.reparent_to(base.render)
        self._mundo = base.render.attach_new_node("mundo")
        self._iluminar()
        self._brillo = textura_brillo()
        self._modelos: dict[int, NodePath] = {}
        self._tamanos: dict[int, Tamano] = {}
        self._efectos: list[Efecto] = []
        self._eventos: list[Evento] = []
        for tipo in _EVENTOS:
            bus.suscribir(tipo, self._anotar)

    def _anotar(self, evento: Evento) -> None:
        """Guarda el evento para convertirlo en efectos en el siguiente fotograma."""
        self._eventos.append(evento)

    def dibujar(self, fraccion: float, dt: float) -> None:
        """Dibuja un fotograma interpolando entre los dos últimos pasos de simulación.

        `fraccion` es la parte del paso siguiente ya transcurrida, entre 0 y 1; `dt` es
        el tiempo real desde el fotograma anterior, para animar los efectos.
        """
        v = self._vista
        q = interpolar(v.orientacion_anterior, v.orientacion, fraccion)
        # Panda3D usa la misma convención de ejes que la lógica (x derecha, y delante,
        # z arriba), así que el cuaternión se pasa tal cual.
        self._base.camera.set_quat(Quat(q.w, q.x, q.y, q.z))
        self._ajustar_lente(v.campo_vision)
        # Los efectos nuevos aparecen en este mismo fotograma (RNF-05).
        self._procesar_eventos()
        self._colocar_enemigos(fraccion)
        self._efectos = [e for e in self._efectos if e.avanzar(dt)]

    # --- enemigos --------------------------------------------------------------------

    def _iluminar(self) -> None:
        ambiente = AmbientLight("ambiente")
        ambiente.set_color((0.35, 0.38, 0.45, 1))
        sol = DirectionalLight("sol")
        sol.set_color((0.9, 0.88, 0.85, 1))
        nodo_sol = self._mundo.attach_new_node(sol)
        nodo_sol.set_hpr(30, -40, 0)
        self._mundo.set_light(self._mundo.attach_new_node(ambiente))
        self._mundo.set_light(nodo_sol)

    def _colocar_enemigos(self, fraccion: float) -> None:
        """Crea, mueve y borra los modelos para que coincidan con los enemigos activos."""
        activos = {e.id: e for e in self._enemigos.activos}
        for id in [i for i in self._modelos if i not in activos]:
            self._modelos.pop(id).remove_node()
            self._tamanos.pop(id, None)
        for id, enemigo in activos.items():
            modelo = self._modelos.get(id)
            if modelo is None:
                modelo = modelo_enemigo(enemigo.tipo, self._radio(enemigo.tamano))
                modelo.reparent_to(self._mundo)
                self._modelos[id] = modelo
                self._tamanos[id] = enemigo.tamano
            a, b = Vec3(*enemigo.posicion_anterior), Vec3(*enemigo.posicion)
            posicion = a + (b - a) * fraccion
            modelo.set_pos(posicion)
            velocidad = Vec3(*enemigo.velocidad)
            if velocidad.length() > 1e-3:
                modelo.look_at(posicion + velocidad, Vec3(0, 0, 1))

    def _radio(self, tamano: Tamano) -> float:
        return self._parametros.tamanos.de(tamano).radio_impacto

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
                if disparo is not None:
                    impacto = self._punto_impacto(disparo, evento.posicion, tamano)
                self._efectos.append(
                    Explosion(
                        self._mundo, self._brillo, Vec3(*evento.posicion), self._radio(tamano)
                    )
                )
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
        salida = Vec3(*self._vista.orientacion.rotar(_SALIDA_RAYO))
        if impacto is None:
            # Sin impacto, el rayo se pierde a la distancia máxima de los enemigos.
            fin = Vec3(*disparo.direccion) * self._parametros.ataques.distancia_maxima
        else:
            fin, radio = impacto
            self._efectos.append(Destello(self._mundo, self._brillo, fin, radio * 0.8))
        self._efectos.append(Rayo(self._mundo, salida, fin))

    def _limpiar(self) -> None:
        for modelo in self._modelos.values():
            modelo.remove_node()
        self._modelos.clear()
        self._tamanos.clear()
        for efecto in self._efectos:
            efecto.avanzar(math.inf)
        self._efectos.clear()

    def _ajustar_lente(self, vertical: float) -> None:
        """Campo de visión vertical en grados; el horizontal sale de la proporción."""
        proporcion = self._base.get_aspect_ratio()
        horizontal = math.degrees(2 * math.atan(math.tan(math.radians(vertical) / 2) * proporcion))
        self._base.camLens.set_fov(horizontal, vertical)
