"""Punto de entrada del juego: `python -m atalaya.arranque`.

Crea los módulos, les pasa sus dependencias y ejecuta el bucle del núcleo. Es el único
sitio donde se conocen todos los módulos (`modulos/README.md`).
"""

from dataclasses import dataclass

from atalaya.logica.flujo import Flujo
from atalaya.logica.nucleo import Etapa, Nucleo
from atalaya.logica.parametros import Parametros, cargar
from atalaya.logica.vista import Vista
from atalaya.presentacion.entrada import Entrada, FuenteTeclado


@dataclass(frozen=True)
class Juego:
    """Módulos del juego ya conectados entre sí."""

    nucleo: Nucleo
    entrada: Entrada
    flujo: Flujo
    vista: Vista


def montar(parametros: Parametros, teclado: FuenteTeclado, semilla: int | None = None) -> Juego:
    """Crea los módulos en orden, inyecta sus dependencias y los registra en el núcleo."""
    nucleo = Nucleo(semilla)
    entrada = Entrada(teclado)
    vista = Vista(nucleo.bus, parametros)
    flujo = Flujo(nucleo.bus, entrada, vista)
    nucleo.registrar(Etapa.ENTRADA, entrada)
    nucleo.registrar(Etapa.FLUJO, flujo)
    nucleo.registrar(Etapa.VISTA, vista)
    return Juego(nucleo, entrada, flujo, vista)


def main() -> None:
    """Abre la ventana y ejecuta el juego hasta que el jugador lo cierre."""
    # El motor solo se carga al arrancar de verdad, no al montar los módulos en las pruebas.
    from direct.task import Task
    from panda3d.core import ClockObject

    from atalaya.presentacion.entrada.panda import FuenteTecladoPanda
    from atalaya.presentacion.escena import Escena, crear_ventana

    parametros = cargar()
    base = crear_ventana()
    juego = montar(parametros, FuenteTecladoPanda(base))
    escena = Escena(base, juego.vista)
    reloj = ClockObject.get_global_clock()

    def fotograma(tarea: Task.Task) -> int:
        nucleo = juego.nucleo
        nucleo.avanzar(reloj.get_dt())
        if juego.flujo.salir_solicitado:
            base.userExit()
        # En pausa no avanza la orientación: se dibuja el último paso, sin interpolar.
        escena.dibujar(1.0 if nucleo.en_pausa else nucleo.fraccion_paso)
        return Task.cont

    juego.flujo.iniciar_partida(nivel=1)
    base.taskMgr.add(fotograma, "atalaya-fotograma")
    base.run()


if __name__ == "__main__":
    main()
