"""Efectos de sonido de la partida (`modulos/audio.md`).

Versión mínima, sin sonido posicional: disparo, aviso, impacto, explosión, falta de
energía y alarma de daño (S3), aturdimiento (S4) y los sonidos de los menús: mover,
confirmar y error (S5). Al pausar la partida se detienen todos los sonidos de partida;
los de los menús siguen sonando (S6). Los sonidos se generan al arrancar (`sintesis.py`)
y se guardan en un disco virtual en memoria, así que no hay archivos de sonido en disco.
El sonido posicional, la radio y la música llegan en sprints posteriores.
"""

from collections.abc import Callable
from functools import partial

from direct.showbase.ShowBase import ShowBase
from panda3d.core import AudioSound, Filename, VirtualFileMountRamdisk, VirtualFileSystem

from atalaya.logica.flujo import Flujo, SonidoMenu
from atalaya.logica.nucleo.bus import Bus, Evento
from atalaya.logica.nucleo.eventos import (
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
)
from atalaya.logica.parametros import Parametros
from atalaya.presentacion.audio import sintesis

#: Carpeta del disco virtual donde se guardan los sonidos generados.
_CARPETA = "/atalaya-sonidos"

#: Volumen de cada sonido, de 0 a 1.
_VOLUMEN = {
    "disparo": 0.5,
    "aviso": 0.6,
    "impacto": 0.6,
    "explosion": 0.8,
    "sin_energia": 0.6,
    "alarma": 0.55,
    "aturdimiento": 0.7,
    "menu_mover": 0.4,
    "menu_confirmar": 0.5,
    "menu_error": 0.55,
}

#: Sonido de cada respuesta de un menú.
_SONIDO_MENU = {
    SonidoMenu.MOVER: "menu_mover",
    SonidoMenu.CONFIRMAR: "menu_confirmar",
    SonidoMenu.ERROR: "menu_error",
}

#: Copias de cada sonido que pueden sonar a la vez (varios enemigos avisan a la vez).
_COPIAS = {"aviso": 6, "explosion": 3, "impacto": 3, "disparo": 3}


class Audio:
    """Reproduce un efecto de sonido por cada evento de la partida que lo tiene."""

    def __init__(self, base: ShowBase, bus: Bus, parametros: Parametros, flujo: Flujo) -> None:
        self._flujo = flujo
        self._sonidos_menu = {s: flujo.sonidos_menu(s) for s in SonidoMenu}
        generadores: dict[str, Callable[[], list[float]]] = {
            "disparo": sintesis.disparo,
            "aviso": lambda: sintesis.aviso(parametros.ataques.duracion_aviso),
            "impacto": sintesis.impacto,
            "explosion": sintesis.explosion,
            "sin_energia": sintesis.sin_energia,
            "alarma": sintesis.alarma,
            "aturdimiento": sintesis.aturdimiento,
            "menu_mover": sintesis.menu_mover,
            "menu_confirmar": sintesis.menu_confirmar,
            "menu_error": sintesis.menu_error,
        }
        vfs = VirtualFileSystem.get_global_ptr()
        if not vfs.is_directory(Filename(_CARPETA)):
            vfs.mount(VirtualFileMountRamdisk(), _CARPETA, 0)
        self._sonidos: dict[str, list[AudioSound]] = {}
        self._siguiente: dict[str, int] = {}
        for nombre, generar in generadores.items():
            ruta = Filename(f"{_CARPETA}/{nombre}.wav")
            vfs.write_file(ruta, sintesis.a_wav(generar()), False)
            copias = []
            for _ in range(_COPIAS.get(nombre, 1)):
                sonido = base.loader.load_sfx(ruta)
                sonido.set_volume(_VOLUMEN[nombre])
                copias.append(sonido)
            self._sonidos[nombre] = copias
            self._siguiente[nombre] = 0
        reacciones: list[tuple[type[Evento], str]] = [
            (DisparoRealizado, "disparo"),
            (AvisoDisparo, "aviso"),
            (EnemigoAlcanzado, "impacto"),
            (EnemigoDestruido, "explosion"),
            (DisparoSinEnergia, "sin_energia"),
            (EstacionDanada, "alarma"),
            (AturdimientoIniciado, "aturdimiento"),
        ]
        for tipo, nombre in reacciones:
            bus.suscribir(tipo, partial(self._al_evento, nombre))
        for tipo in (PartidaIniciada, PartidaAbandonada, EstacionDestruida):
            bus.suscribir(tipo, self._callar_avisos)
        bus.suscribir(PausaCambiada, self._al_cambiar_pausa)

    def actualizar(self) -> None:
        """Una vez por fotograma: suena cada respuesta de los menús desde el anterior."""
        for sonido, nombre in _SONIDO_MENU.items():
            veces = self._flujo.sonidos_menu(sonido)
            if veces != self._sonidos_menu[sonido]:
                self._sonidos_menu[sonido] = veces
                self._sonar(nombre)

    def _al_evento(self, nombre: str, evento: Evento) -> None:
        self._sonar(nombre)

    def _sonar(self, nombre: str) -> None:
        """Reproduce la siguiente copia libre del sonido, o la más antigua si no hay."""
        copias = self._sonidos[nombre]
        indice = self._siguiente[nombre]
        self._siguiente[nombre] = (indice + 1) % len(copias)
        copias[indice].play()

    def _al_cambiar_pausa(self, evento: PausaCambiada) -> None:
        """En pausa no suena ningún efecto de la partida (CU-09); los menús, sí."""
        if not evento.activa:
            return
        menu = set(_SONIDO_MENU.values())
        for nombre, copias in self._sonidos.items():
            if nombre not in menu:
                for sonido in copias:
                    sonido.stop()

    def _callar_avisos(self, evento: Evento) -> None:
        """Al empezar o terminar la partida no queda ningún aviso sonando."""
        for sonido in self._sonidos["aviso"]:
            sonido.stop()
