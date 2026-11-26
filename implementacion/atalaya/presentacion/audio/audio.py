"""Efectos de sonido de la partida (`modulos/audio.md`).

Versión mínima de S3, sin sonido posicional: disparo, aviso, impacto, explosión, falta
de energía y alarma de daño. Los sonidos se generan al arrancar (`sintesis.py`) y se
guardan en un disco virtual en memoria, así que no hay archivos de sonido en disco.
El sonido posicional, la radio y la música llegan en sprints posteriores.
"""

from collections.abc import Callable
from functools import partial

from direct.showbase.ShowBase import ShowBase
from panda3d.core import AudioSound, Filename, VirtualFileMountRamdisk, VirtualFileSystem

from atalaya.logica.nucleo.bus import Bus, Evento
from atalaya.logica.nucleo.eventos import (
    AvisoDisparo,
    DisparoRealizado,
    DisparoSinEnergia,
    EnemigoAlcanzado,
    EnemigoDestruido,
    EstacionDanada,
    EstacionDestruida,
    PartidaAbandonada,
    PartidaIniciada,
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
}

#: Copias de cada sonido que pueden sonar a la vez (varios enemigos avisan a la vez).
_COPIAS = {"aviso": 6, "explosion": 3, "impacto": 3, "disparo": 3}


class Audio:
    """Reproduce un efecto de sonido por cada evento de la partida que lo tiene."""

    def __init__(self, base: ShowBase, bus: Bus, parametros: Parametros) -> None:
        generadores: dict[str, Callable[[], list[float]]] = {
            "disparo": sintesis.disparo,
            "aviso": lambda: sintesis.aviso(parametros.ataques.duracion_aviso),
            "impacto": sintesis.impacto,
            "explosion": sintesis.explosion,
            "sin_energia": sintesis.sin_energia,
            "alarma": sintesis.alarma,
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
        ]
        for tipo, nombre in reacciones:
            bus.suscribir(tipo, partial(self._al_evento, nombre))
        for tipo in (PartidaIniciada, PartidaAbandonada, EstacionDestruida):
            bus.suscribir(tipo, self._callar_avisos)

    def _al_evento(self, nombre: str, evento: Evento) -> None:
        self._sonar(nombre)

    def _sonar(self, nombre: str) -> None:
        """Reproduce la siguiente copia libre del sonido, o la más antigua si no hay."""
        copias = self._sonidos[nombre]
        indice = self._siguiente[nombre]
        self._siguiente[nombre] = (indice + 1) % len(copias)
        copias[indice].play()

    def _callar_avisos(self, evento: Evento) -> None:
        """Al empezar o terminar la partida no queda ningún aviso sonando."""
        for sonido in self._sonidos["aviso"]:
            sonido.stop()
