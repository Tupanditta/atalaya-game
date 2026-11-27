"""Sonido de la partida: efectos, sonido posicional y sonido de fondo (`modulos/audio.md`).

- **Efectos:** disparo bláster, impacto, impacto en la estación, falta de energía, alarma
  de daño, aturdimiento, tono de la mira al apuntar, servos del giro de la cámara, salto
  hiperespacial y sonidos de los menús. Todos de registro grave.
- **Posicionales:** el motor de cada enemigo, su aviso de disparo, sus disparos y su
  explosión suenan desde su posición respecto a la cámara (RF-10). El oyente está en la
  estación y mira hacia donde mira la vista.
- **Fondo:** no hay música. El sonido de fondo de la oleada es la suma de los motores de
  todas las naves: cada uno suena más grave y más fuerte cuanto más cerca está. Debajo,
  un zumbido provisional de la estación, a la espera de definir su sonido propio.

Los sonidos se generan con numpy (`sintesis.py`) y se guardan como WAV en la caché de
usuario: desde el segundo arranque se cargan al momento. Si la caché no se puede
escribir, se guardan en un disco virtual en memoria.

**Sonidos propios:** cualquier sonido se puede sustituir por un archivo WAV u OGG de
`recursos/sonidos/`, indicándolo en `recursos/sonidos/sonidos.json` con su volumen y,
si se graba flojo, una ganancia que lo amplifica. Si un sonido posicional es un WAV
estéreo, se pasa a mono, que es lo que necesita el sonido 3D. Un archivo que falte o
una entrada mal escrita no impiden jugar: se avisa en el registro y suena el generado.

Al pausar la partida se detienen sus efectos y los motores; los sonidos de los menús
siguen sonando (CU-09).
"""

import json
import logging
import random
import wave
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from pathlib import Path

import numpy as np
import platformdirs
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    AudioManager,
    AudioSound,
    Filename,
    VirtualFileMountRamdisk,
    VirtualFileSystem,
)

from atalaya.logica.enemigos import Enemigos
from atalaya.logica.flujo import Flujo, Pantalla, SonidoMenu
from atalaya.logica.nucleo.bus import Bus, Evento
from atalaya.logica.nucleo.dominio import Vector3
from atalaya.logica.nucleo.eventos import (
    ApuntadoCambiado,
    AturdimientoIniciado,
    AvisoDisparo,
    DisparoRealizado,
    DisparoSinEnergia,
    EnemigoAlcanzado,
    EnemigoDestruido,
    EstacionDanada,
    EstacionDestruida,
    PartidaAbandonada,
    PartidaIniciada,
    PausaCambiada,
    ProyectilLanzado,
    SaltoIniciado,
)
from atalaya.logica.oleadas import Oleadas
from atalaya.logica.parametros import Parametros
from atalaya.logica.vista import Vista
from atalaya.presentacion.audio import sintesis

#: Carpeta del disco virtual para los sonidos si la caché no se puede escribir.
_CARPETA_VIRTUAL = "/atalaya-sonidos"

#: Volumen de cada efecto, de 0 a 1.
_VOLUMEN = {
    "disparo": 0.5,
    "disparo_enemigo": 0.7,
    "aviso": 0.65,
    "impacto": 0.55,
    "impacto_estacion": 0.95,
    "explosion": 1.0,
    "sin_energia": 0.55,
    "alarma": 0.3,
    "aturdimiento": 0.65,
    "giro_inicio": 0.3,
    "giro_fin": 0.3,
    "menu_mover": 0.35,
    "menu_confirmar": 0.45,
    "menu_error": 0.5,
    "salto": 0.85,
}

#: Sonidos que se pueden sustituir por uno propio: los efectos y los bucles.
NOMBRES_SONIDOS = frozenset({*_VOLUMEN, "motor", "apuntado", "zumbido"})

#: Copias de cada efecto que pueden sonar a la vez.
_COPIAS = {
    "aviso": 6,
    "explosion": 4,
    "impacto": 3,
    "disparo": 5,
    "disparo_enemigo": 4,
}

#: Efectos que suenan desde la posición de su origen, con la distancia hasta la que se
#: oyen a todo volumen. La explosión no se atenúa con esta caída: su volumen lo decide
#: `volumen_explosion`, más alto cuanto más cerca.
_DISTANCIA_PLENA = {"aviso": 150.0, "disparo_enemigo": 200.0, "explosion": 5000.0}

#: Volumen de la explosión según la distancia: de todo el volumen a 150 u a un 15 % a
#: 1200 u, con un cambio suave entre medias.
DISTANCIAS_EXPLOSION = (150.0, 1200.0)
VOLUMEN_EXPLOSION = (1.0, 0.15)

#: Sonidos que suenan en 3D y necesitan archivos mono.
_EN_3D = {*_DISTANCIA_PLENA, "motor"}

#: Carpeta de los sonidos propios y archivo que dice cuáles se usan.
CARPETA_PROPIOS = Path(__file__).resolve().parents[3] / "recursos" / "sonidos"
_INDICE_PROPIOS = "sonidos.json"

#: Ganancia máxima de un sonido propio.
_GANANCIA_MAXIMA = 20.0

_registro = logging.getLogger(__name__)

#: Sonido de cada respuesta de un menú.
_SONIDO_MENU = {
    SonidoMenu.MOVER: "menu_mover",
    SonidoMenu.CONFIRMAR: "menu_confirmar",
    SonidoMenu.ERROR: "menu_error",
}

#: Sonido posicional: distancia máxima y factor de caída con la distancia.
_DISTANCIA_MAXIMA = 4000.0
_CAIDA = 1.0

#: Motores: como mucho, los enemigos activos a la vez (RN-43). Suenan a todo volumen
#: hasta `_DISTANCIA_PLENA_MOTOR` y, además, más graves y más fuertes cuanto más cerca.
_MOTORES = 6
_DISTANCIA_PLENA_MOTOR = 300.0
#: Distancias entre las que cambia el tono del motor, y su velocidad y volumen de cerca
#: y de lejos.
DISTANCIAS_MOTOR = (150.0, 1200.0)
VELOCIDAD_MOTOR = (0.68, 1.08)
VOLUMEN_MOTOR = (1.0, 0.3)
#: Variación de tono de cada nave, para que no suenen todas igual.
_VARIACION_MOTOR = 0.06

#: Tono de la mira: volumen y velocidad al empezar a apuntar y con la mira al mínimo.
_APUNTADO_VOLUMEN = (0.08, 0.22)
_APUNTADO_VELOCIDAD = (1.0, 1.8)

#: Variación de tono al azar de algunos efectos, para que no suenen siempre igual.
_VARIACION = {
    "disparo": 0.04,
    "explosion": 0.12,
    "impacto": 0.08,
    "impacto_estacion": 0.06,
    "disparo_enemigo": 0.06,
}

#: Tiempo mínimo entre dos arranques del giro, para no encadenarlos al tocar teclas.
_ENTRE_GIROS = 0.06

#: Fundido del zumbido de la estación, en segundos.
FUNDIDO = 1.5


@dataclass(frozen=True)
class EstadoSonido:
    """Lo que decide el volumen del zumbido de la estación."""

    pantalla: Pantalla
    #: Pantalla de la partida detenida si hay pausa; `None` si no la hay.
    pausada: Pantalla | None
    en_salto: bool


def volumen_estacion(estado: EstadoSonido) -> float:
    """Volumen del zumbido provisional de la estación en `estado`.

    Se oye en la partida y el descanso; más bajo en el salto, en pausa y en los menús.
    """
    if estado.pausada is not None:
        return 0.12
    if estado.pantalla is Pantalla.OLEADA_EN_CURSO:
        return 0.15 if estado.en_salto else 0.3
    if estado.pantalla is Pantalla.DESCANSO:
        return 0.3
    return 0.18


def tono_motor(distancia: float) -> tuple[float, float]:
    """Velocidad de reproducción y volumen del motor de una nave a `distancia`.

    Más cerca, más grave (velocidad menor) y más fuerte. Cambia de forma suave entre las
    distancias de `DISTANCIAS_MOTOR`.
    """
    cerca, lejos = DISTANCIAS_MOTOR
    k = min(1.0, max(0.0, (distancia - cerca) / (lejos - cerca)))
    k = k * k * (3 - 2 * k)
    velocidad = VELOCIDAD_MOTOR[0] + (VELOCIDAD_MOTOR[1] - VELOCIDAD_MOTOR[0]) * k
    volumen = VOLUMEN_MOTOR[0] + (VOLUMEN_MOTOR[1] - VOLUMEN_MOTOR[0]) * k
    return velocidad, volumen


def volumen_explosion(distancia: float) -> float:
    """Volumen de una explosión a `distancia`: más alta cuanto más cerca."""
    cerca, lejos = DISTANCIAS_EXPLOSION
    k = min(1.0, max(0.0, (distancia - cerca) / (lejos - cerca)))
    k = k * k * (3 - 2 * k)
    return VOLUMEN_EXPLOSION[0] + (VOLUMEN_EXPLOSION[1] - VOLUMEN_EXPLOSION[0]) * k


@dataclass(frozen=True)
class SonidoPropio:
    """Archivo que sustituye a un sonido generado, con su volumen."""

    ruta: Path
    volumen: float
    #: Amplificación de las muestras: 1 deja el sonido como está; 5, cinco veces más.
    ganancia: float = 1.0


def cargar_propios(carpeta: Path = CARPETA_PROPIOS) -> dict[str, SonidoPropio]:
    """Sonidos propios de `carpeta/sonidos.json`, por nombre del sonido.

    Formato: `{"version": 1, "sonidos": {"explosion": {"archivo": "...", "volumen": 1,
    "ganancia": 5}}}`; el volumen (de 0 a 1) y la ganancia (de 0 a 20) son opcionales.
    Lo que no se puede usar se avisa en el registro y se ignora.
    """
    indice = carpeta / _INDICE_PROPIOS
    if not indice.is_file():
        return {}
    try:
        datos = json.loads(indice.read_text(encoding="utf-8"))
        entradas = datos["sonidos"] if datos.get("version") == 1 else None
        if not isinstance(entradas, dict):
            raise ValueError("falta la sección 'sonidos' o la versión no es 1")
    except (OSError, ValueError, KeyError, AttributeError) as error:
        _registro.warning("No se pueden leer los sonidos propios de %s: %s", indice, error)
        return {}
    propios: dict[str, SonidoPropio] = {}
    for nombre, entrada in entradas.items():
        if nombre not in NOMBRES_SONIDOS:
            _registro.warning("Sonido propio desconocido: %r", nombre)
            continue
        archivo = entrada.get("archivo") if isinstance(entrada, dict) else None
        volumen = entrada.get("volumen", _VOLUMEN.get(nombre, 1.0)) if archivo else None
        ruta = carpeta / str(archivo)
        if not archivo or not ruta.is_file():
            _registro.warning("No existe el archivo del sonido propio %r: %s", nombre, ruta)
            continue
        if not isinstance(volumen, int | float) or not 0 <= volumen <= 1:
            _registro.warning("Volumen no válido para el sonido propio %r: %r", nombre, volumen)
            continue
        ganancia = entrada.get("ganancia", 1.0)
        if not isinstance(ganancia, int | float) or not 0 < ganancia <= _GANANCIA_MAXIMA:
            _registro.warning("Ganancia no válida para el sonido propio %r: %r", nombre, ganancia)
            continue
        propios[nombre] = SonidoPropio(ruta, float(volumen), float(ganancia))
    return propios


def preparar_propio(origen: Path, destino: Path, mono: bool, ganancia: float) -> Path:
    """`origen` listo para sonar: en mono si `mono`, y amplificado por `ganancia`.

    Si no hace falta ningún cambio, o el archivo no es un WAV de 16 bits, se usa tal cual.
    Si no, se escribe la versión preparada en `destino`. La amplificación pasa por un
    limitador suave: los picos no se cortan de golpe, y los graves profundos ganan
    armónicos que los hacen audibles también en altavoces pequeños.
    """
    if origen.suffix.lower() != ".wav":
        return origen
    try:
        with wave.open(str(origen)) as archivo:
            canales = archivo.getnchannels()
            ancho = archivo.getsampwidth()
            frecuencia = archivo.getframerate()
            datos = archivo.readframes(archivo.getnframes())
    except (OSError, wave.Error, EOFError):
        return origen
    a_mono = mono and canales > 1
    if ancho != 2 or (not a_mono and ganancia == 1.0):
        return origen
    muestras = np.frombuffer(datos, dtype="<i2").reshape(-1, canales) / 32768.0
    if a_mono:
        muestras = muestras.mean(axis=1, keepdims=True)
    if ganancia != 1.0:
        muestras = np.tanh(muestras * ganancia)
    enteros = np.round(np.clip(muestras, -1.0, 1.0) * 32767).astype("<i2")
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(destino), "wb") as salida:
            salida.setnchannels(enteros.shape[1])
            salida.setsampwidth(2)
            salida.setframerate(frecuencia)
            salida.writeframes(enteros.tobytes())
    except OSError:
        return origen
    return destino


def evento_giro(anterior: tuple[int, int], actual: tuple[int, int]) -> str | None:
    """Sonido del giro de la cámara al pasar de `anterior` a `actual`, o `None`.

    Arranque al empezar a girar o al cambiar de dirección; parada al dejar de girar.
    """
    if actual == anterior:
        return None
    if actual == (0, 0):
        return "giro_fin"
    return "giro_inicio"


def acercar(actual: float, objetivo: float, dt: float, fundido: float = FUNDIDO) -> float:
    """Volumen que va de `actual` a `objetivo` como mucho a razón de 1 cada `fundido` s."""
    paso = dt / fundido
    if actual < objetivo:
        return min(objetivo, actual + paso)
    return max(objetivo, actual - paso)


def carpeta_cache() -> Path:
    """Carpeta de la caché de sonidos generados."""
    return Path(platformdirs.user_cache_dir("atalaya", appauthor=False)) / "sonidos"


class Audio:
    """Reproduce efectos, sonido posicional y el sonido de fondo de la partida."""

    def __init__(
        self,
        base: ShowBase,
        bus: Bus,
        parametros: Parametros,
        flujo: Flujo,
        vista: Vista,
        enemigos: Enemigos,
        oleadas: Oleadas,
        carpeta: Path | None = None,
        carpeta_propios: Path = CARPETA_PROPIOS,
    ) -> None:
        self._base = base
        self._flujo = flujo
        self._vista = vista
        self._enemigos = enemigos
        self._oleadas = oleadas
        # Azar solo para variar el tono de los efectos: no forma parte de la simulación.
        self._azar = random.Random()
        self._gestor: AudioManager = base.sfxManagerList[0]
        self._gestor.audio_3d_set_drop_off_factor(_CAIDA)
        self._sonidos_menu = {s: flujo.sonidos_menu(s) for s in SonidoMenu}
        self._rutas = _Rutas(carpeta_cache() if carpeta is None else carpeta)
        self._propios = cargar_propios(carpeta_propios)
        a = parametros.ataques.duracion_aviso
        s = parametros.oleadas.duracion_salto
        generadores: dict[str, tuple[str, Callable[[], sintesis.Muestras]]] = {
            "disparo": ("disparo", sintesis.disparo),
            "disparo_enemigo": ("disparo_enemigo", sintesis.disparo_enemigo),
            "aviso": (f"aviso-{a:g}", lambda: sintesis.aviso(a)),
            "impacto": ("impacto", sintesis.impacto),
            "impacto_estacion": ("impacto_estacion", sintesis.impacto_estacion),
            "explosion": ("explosion", sintesis.explosion),
            "sin_energia": ("sin_energia", sintesis.sin_energia),
            "alarma": ("alarma", sintesis.alarma),
            "aturdimiento": ("aturdimiento", sintesis.aturdimiento),
            "giro_inicio": ("giro_inicio", sintesis.giro_inicio),
            "giro_fin": ("giro_fin", sintesis.giro_fin),
            "menu_mover": ("menu_mover", sintesis.menu_mover),
            "menu_confirmar": ("menu_confirmar", sintesis.menu_confirmar),
            "menu_error": ("menu_error", sintesis.menu_error),
            "salto": (f"salto-{s:g}", lambda: sintesis.salto(s)),
        }
        self._sonidos: dict[str, list[AudioSound]] = {}
        self._siguiente: dict[str, int] = {}
        self._volumen: dict[str, float] = {}
        for nombre, (archivo, generar) in generadores.items():
            ruta = self._ruta(nombre, archivo, generar)
            self._volumen[nombre] = self._volumen_de(nombre)
            copias = []
            for _ in range(_COPIAS.get(nombre, 1)):
                sonido = self._cargar(ruta, self._volumen[nombre])
                if nombre in _DISTANCIA_PLENA:
                    sonido.set_3d_min_distance(_DISTANCIA_PLENA[nombre])
                    sonido.set_3d_max_distance(_DISTANCIA_MAXIMA)
                copias.append(sonido)
            self._sonidos[nombre] = copias
            self._siguiente[nombre] = 0
        ruta_motor = self._ruta("motor", "motor", sintesis.motor)
        self._motores = [self._bucle(ruta_motor, 0.0, posicional=True) for _ in range(_MOTORES)]
        self._motor_de: dict[int, int] = {}
        self._variacion_de: dict[int, float] = {}
        self._apuntado = self._bucle(self._ruta("apuntado", "apuntado", sintesis.apuntado), 0.0)
        self._progreso_apuntado = 0.0
        self._estacion_sonido = self._bucle(self._ruta("zumbido", "zumbido", sintesis.zumbido), 0.0)
        self._volumen_estacion = 0.0
        self._giro_anterior = (0, 0)
        self._desde_giro = 1.0
        self._en_pausa = False
        bus.suscribir(DisparoRealizado, self._al_disparar)
        bus.suscribir(AvisoDisparo, self._al_avisar)
        bus.suscribir(ProyectilLanzado, self._al_lanzar)
        bus.suscribir(EnemigoDestruido, self._al_destruir)
        bus.suscribir(ApuntadoCambiado, self._al_apuntar)
        sencillos: list[tuple[type[Evento], str]] = [
            (EnemigoAlcanzado, "impacto"),
            (DisparoSinEnergia, "sin_energia"),
            (EstacionDanada, "impacto_estacion"),
            (EstacionDanada, "alarma"),
            (AturdimientoIniciado, "aturdimiento"),
            (SaltoIniciado, "salto"),
        ]
        for tipo, nombre in sencillos:
            bus.suscribir(tipo, partial(self._al_evento, nombre))
        for tipo in (PartidaIniciada, PartidaAbandonada, EstacionDestruida):
            bus.suscribir(tipo, self._callar_partida)
        bus.suscribir(PausaCambiada, self._al_cambiar_pausa)

    # --- cada fotograma ----------------------------------------------------------------

    def actualizar(self, dt: float) -> None:
        """Menús, oyente, motores, giro de la cámara, tono de la mira y zumbido."""
        for sonido, nombre in _SONIDO_MENU.items():
            veces = self._flujo.sonidos_menu(sonido)
            if veces != self._sonidos_menu[sonido]:
                self._sonidos_menu[sonido] = veces
                self._sonar(nombre)
        self._colocar_oyente()
        self._mover_motores()
        self._sonar_giro(dt)
        self._sonar_apuntado()
        self._sonar_estacion(dt)

    def _colocar_oyente(self) -> None:
        """El oyente está en la estación y mira hacia donde mira la vista."""
        delante = self._vista.adelante
        arriba = self._vista.orientacion.rotar((0.0, 0.0, 1.0))
        self._gestor.audio_3d_set_listener_attributes(0, 0, 0, 0, 0, 0, *delante, *arriba)

    def _mover_motores(self) -> None:
        """Un motor sonando en la posición de cada enemigo activo, salvo en pausa.

        Su tono y su volumen dependen de la distancia: la suma de todos es el fondo.
        """
        activos = {} if self._en_pausa else {e.id: e.posicion for e in self._enemigos.activos}
        for id in [i for i in self._motor_de if i not in activos]:
            self._motores[self._motor_de.pop(id)].stop()
            self._variacion_de.pop(id, None)
        libres = [i for i in range(_MOTORES) if i not in self._motor_de.values()]
        for id, posicion in activos.items():
            nuevo = id not in self._motor_de
            if nuevo:
                if not libres:
                    continue
                self._motor_de[id] = libres.pop()
                self._variacion_de[id] = 1 + self._azar.uniform(-_VARIACION_MOTOR, _VARIACION_MOTOR)
            motor = self._motores[self._motor_de[id]]
            x, y, z = posicion
            velocidad, volumen = tono_motor((x * x + y * y + z * z) ** 0.5)
            motor.set_play_rate(velocidad * self._variacion_de[id])
            motor.set_volume(volumen)
            _colocar(motor, posicion)
            if nuevo:
                motor.play()

    def _sonar_giro(self, dt: float) -> None:
        """Servo al empezar a girar la cámara o cambiar de dirección, y al parar."""
        if self._en_pausa:
            return
        self._desde_giro += dt
        oleada = self._flujo.pantalla is Pantalla.OLEADA_EN_CURSO
        giro = self._vista.giro if oleada else (0, 0)
        sonido = evento_giro(self._giro_anterior, giro)
        self._giro_anterior = giro
        if sonido == "giro_inicio":
            if self._desde_giro < _ENTRE_GIROS:
                return
            self._desde_giro = 0.0
        if sonido is not None:
            self._sonar(sonido)

    def _sonar_apuntado(self) -> None:
        """Tono que sube con el apuntado; calla sin apuntar o en pausa."""
        progreso = 0.0 if self._en_pausa else self._progreso_apuntado
        if progreso <= 0.0:
            if self._apuntado.status() == AudioSound.PLAYING:
                self._apuntado.stop()
            return
        bajo, alto = _APUNTADO_VOLUMEN
        lento, rapido = _APUNTADO_VELOCIDAD
        self._apuntado.set_volume(bajo + (alto - bajo) * progreso)
        self._apuntado.set_play_rate(lento + (rapido - lento) * progreso)
        if self._apuntado.status() != AudioSound.PLAYING:
            self._apuntado.play()

    def _sonar_estacion(self, dt: float) -> None:
        """Zumbido provisional de la estación, con fundidos según el momento."""
        estado = EstadoSonido(
            pantalla=self._flujo.pantalla,
            pausada=self._flujo.pantalla_pausada,
            en_salto=self._oleadas.en_salto,
        )
        self._volumen_estacion = acercar(self._volumen_estacion, volumen_estacion(estado), dt)
        sonido = self._estacion_sonido
        sonido.set_volume(self._volumen_estacion)
        sonando = sonido.status() == AudioSound.PLAYING
        if self._volumen_estacion > 0 and not sonando:
            sonido.play()
        elif self._volumen_estacion == 0 and sonando:
            sonido.stop()

    # --- eventos -------------------------------------------------------------------------

    def _al_evento(self, nombre: str, evento: Evento) -> None:
        self._sonar(nombre)

    def _al_disparar(self, evento: DisparoRealizado) -> None:
        self._progreso_apuntado = 0.0
        self._sonar("disparo")

    def _al_apuntar(self, evento: ApuntadoCambiado) -> None:
        self._progreso_apuntado = evento.progreso

    def _al_avisar(self, evento: AvisoDisparo) -> None:
        enemigo = self._enemigos.enemigo(evento.id_enemigo)
        self._sonar("aviso", None if enemigo is None else enemigo.posicion)

    def _al_lanzar(self, evento: ProyectilLanzado) -> None:
        posicion = next((p.posicion for p in self._enemigos.proyectiles if p.id == evento.id), None)
        self._sonar("disparo_enemigo", posicion)

    def _al_destruir(self, evento: EnemigoDestruido) -> None:
        self._sonar("explosion", evento.posicion)

    def _al_cambiar_pausa(self, evento: PausaCambiada) -> None:
        """En pausa no suena ningún efecto de la partida (CU-09); los menús, sí."""
        self._en_pausa = evento.activa
        if evento.activa:
            self._callar_efectos()
            self._mover_motores()

    def _callar_partida(self, evento: Evento) -> None:
        """Al empezar o terminar la partida no queda sonando nada de la anterior."""
        self._progreso_apuntado = 0.0
        for sonido in self._sonidos["aviso"]:
            sonido.stop()
        for indice in self._motor_de.values():
            self._motores[indice].stop()
        self._motor_de.clear()

    # --- internos ------------------------------------------------------------------------

    def _sonar(self, nombre: str, posicion: Vector3 | None = None) -> None:
        """Reproduce la siguiente copia del efecto, en `posicion` si es posicional."""
        copias = self._sonidos[nombre]
        indice = self._siguiente[nombre]
        self._siguiente[nombre] = (indice + 1) % len(copias)
        sonido = copias[indice]
        if nombre in _DISTANCIA_PLENA:
            _colocar(sonido, posicion or (0.0, 0.0, 0.0))
        if nombre == "explosion":
            x, y, z = posicion or (0.0, 0.0, 0.0)
            distancia = (x * x + y * y + z * z) ** 0.5
            sonido.set_volume(self._volumen[nombre] * volumen_explosion(distancia))
        variacion = _VARIACION.get(nombre, 0.0)
        sonido.set_play_rate(1.0 + self._azar.uniform(-variacion, variacion))
        sonido.play()

    def _ruta(
        self, nombre: str, archivo: str, generar: Callable[[], sintesis.Muestras]
    ) -> Filename:
        """El sonido propio de `nombre` si lo hay; si no, el generado."""
        propio = self._propios.get(nombre)
        if propio is None:
            return self._rutas.ruta(archivo, generar)
        mono = nombre in _EN_3D
        nombre_preparado = (
            f"propio-{propio.ruta.stem}-g{propio.ganancia:g}{'-mono' if mono else ''}.wav"
        )
        ruta = preparar_propio(
            propio.ruta, self._rutas.carpeta / nombre_preparado, mono, propio.ganancia
        )
        return Filename.from_os_specific(str(ruta))

    def _volumen_de(self, nombre: str) -> float:
        propio = self._propios.get(nombre)
        return _VOLUMEN[nombre] if propio is None else propio.volumen

    def _callar_efectos(self) -> None:
        menu = set(_SONIDO_MENU.values())
        for nombre, copias in self._sonidos.items():
            if nombre not in menu:
                for sonido in copias:
                    sonido.stop()
        self._apuntado.stop()

    def _cargar(self, ruta: Filename, volumen: float) -> AudioSound:
        sonido: AudioSound = self._base.loader.load_sfx(ruta)
        sonido.set_volume(volumen)
        return sonido

    def _bucle(self, ruta: Filename, volumen: float, posicional: bool = False) -> AudioSound:
        sonido = self._cargar(ruta, volumen)
        sonido.set_loop(True)
        if posicional:
            sonido.set_3d_min_distance(_DISTANCIA_PLENA_MOTOR)
            sonido.set_3d_max_distance(_DISTANCIA_MAXIMA)
        return sonido


def _colocar(sonido: AudioSound, posicion: Vector3) -> None:
    sonido.set_3d_attributes(*posicion, 0.0, 0.0, 0.0)


class _Rutas:
    """Archivo WAV de cada sonido: de la caché, o generado y guardado en ella."""

    def __init__(self, carpeta: Path) -> None:
        self._carpeta = carpeta
        self._virtual = False

    @property
    def carpeta(self) -> Path:
        return self._carpeta

    def ruta(self, nombre: str, generar: Callable[[], sintesis.Muestras]) -> Filename:
        archivo = self._carpeta / f"{nombre}-v{sintesis.VERSION}.wav"
        if archivo.is_file():
            return Filename.from_os_specific(str(archivo))
        datos = sintesis.a_wav(generar())
        try:
            self._carpeta.mkdir(parents=True, exist_ok=True)
            temporal = archivo.with_suffix(".tmp")
            temporal.write_bytes(datos)
            temporal.replace(archivo)
            return Filename.from_os_specific(str(archivo))
        except OSError:
            return self._en_memoria(nombre, datos)

    def _en_memoria(self, nombre: str, datos: bytes) -> Filename:
        """Sin caché donde escribir, el sonido se guarda en un disco virtual en memoria."""
        vfs = VirtualFileSystem.get_global_ptr()
        if not self._virtual and not vfs.is_directory(Filename(_CARPETA_VIRTUAL)):
            vfs.mount(VirtualFileMountRamdisk(), _CARPETA_VIRTUAL, 0)
        self._virtual = True
        ruta = Filename(f"{_CARPETA_VIRTUAL}/{nombre}.wav")
        vfs.write_file(ruta, datos, False)
        return ruta
