"""Punto de entrada del juego: `python -m atalaya.arranque`.

Crea los módulos, les pasa sus dependencias y ejecuta el bucle del núcleo. Es el único
sitio donde se conocen todos los módulos (`modulos/README.md`).
"""

from dataclasses import dataclass

from atalaya.logica.armamento import Armamento
from atalaya.logica.enemigos import Enemigos
from atalaya.logica.estacion import Estacion
from atalaya.logica.flujo import Flujo
from atalaya.logica.nucleo import Etapa, Nucleo
from atalaya.logica.oleadas import Oleadas
from atalaya.logica.parametros import Parametros, cargar
from atalaya.logica.radar import Radar
from atalaya.logica.vista import Vista
from atalaya.presentacion.entrada import Entrada, FuenteRaton, FuenteTeclado


@dataclass(frozen=True)
class Juego:
    """Módulos del juego ya conectados entre sí."""

    nucleo: Nucleo
    entrada: Entrada
    flujo: Flujo
    vista: Vista
    armamento: Armamento
    enemigos: Enemigos
    oleadas: Oleadas
    estacion: Estacion
    radar: Radar


def montar(
    parametros: Parametros,
    teclado: FuenteTeclado,
    semilla: int | None = None,
    raton: FuenteRaton | None = None,
) -> Juego:
    """Crea los módulos en orden, inyecta sus dependencias y los registra en el núcleo."""
    nucleo = Nucleo(semilla)
    entrada = Entrada(teclado, raton)
    vista = Vista(nucleo.bus, parametros)
    armamento = Armamento(nucleo.bus, parametros, vista, nucleo.azar)
    enemigos = Enemigos(nucleo.bus, parametros, nucleo.azar)
    oleadas = Oleadas(nucleo.bus, parametros)
    estacion = Estacion(nucleo.bus, parametros)
    radar = Radar(parametros, vista, enemigos)
    flujo = Flujo(nucleo.bus, entrada, vista, armamento)
    nucleo.registrar(Etapa.ENTRADA, entrada)
    nucleo.registrar(Etapa.FLUJO, flujo)
    nucleo.registrar(Etapa.VISTA, vista)
    nucleo.registrar(Etapa.ARMAMENTO, armamento)
    nucleo.registrar(Etapa.ENEMIGOS, enemigos)
    nucleo.registrar(Etapa.OLEADAS, oleadas)
    # `estacion` aún no tiene nada que actualizar en cada paso: los efectos con duración
    # (aturdimiento y desestabilización) llegan en S4.
    return Juego(nucleo, entrada, flujo, vista, armamento, enemigos, oleadas, estacion, radar)


def main() -> None:
    """Abre la ventana y ejecuta el juego hasta que el jugador lo cierre."""
    # El motor solo se carga al arrancar de verdad, no al montar los módulos en las pruebas.
    from direct.task import Task
    from panda3d.core import ClockObject

    from atalaya.presentacion.audio import Audio
    from atalaya.presentacion.entrada.panda import FuenteRatonPanda, FuenteTecladoPanda
    from atalaya.presentacion.escena import Escena, crear_ventana
    from atalaya.presentacion.hud import Hud

    parametros = cargar()
    base = crear_ventana()
    juego = montar(parametros, FuenteTecladoPanda(base), raton=FuenteRatonPanda(base))
    escena = Escena(base, juego.nucleo.bus, juego.vista, juego.enemigos, parametros)
    hud = Hud(
        base,
        juego.nucleo.bus,
        parametros,
        juego.armamento,
        juego.vista,
        juego.radar,
        juego.estacion,
        juego.oleadas,
        juego.flujo,
    )
    Audio(base, juego.nucleo.bus, parametros)
    reloj = ClockObject.get_global_clock()

    def fotograma(tarea: Task.Task) -> int:
        nucleo = juego.nucleo
        nucleo.avanzar(reloj.get_dt())
        if juego.flujo.salir_solicitado:
            base.userExit()
        # En pausa no avanza la orientación: se dibuja el último paso, sin interpolar.
        escena.dibujar(1.0 if nucleo.en_pausa else nucleo.fraccion_paso, reloj.get_dt())
        hud.dibujar(reloj.get_dt())
        return Task.cont

    juego.flujo.iniciar_partida(nivel=1)
    base.taskMgr.add(fotograma, "atalaya-fotograma")
    base.run()


if __name__ == "__main__":
    main()
