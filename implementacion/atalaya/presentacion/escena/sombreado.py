"""Shaders GLSL del paisaje, con respaldo al pipeline fijo (`design.md`, sección 6).

Los programas son cadenas de texto en módulos propios (`planetas_glsl.py`...): así viajan
con el paquete sin datos aparte. Aquí se compilan una sola vez contra la tarjeta gráfica,
al crear la escena. Si no hay GLSL 1.30 o un programa no compila, `programa` devuelve
`None` y quien lo pide dibuja como antes de los shaders: el juego nunca se cierra por eso.

Compilar al crear la escena, y no al dibujar por primera vez, evita además un tirón en
mitad de la partida.
"""

from direct.directnotify.DirectNotifyGlobal import directNotify
from panda3d.core import GraphicsStateGuardianBase, Shader

from atalaya.presentacion.escena import asteroides_glsl, estrellas_glsl, planetas_glsl, sol_glsl

#: Versión mínima de GLSL que usan los programas (OpenGL 3.0).
VERSION_GLSL = (1, 30)

#: Programas conocidos: nombre, código del vértice y del fragmento.
PROGRAMAS: dict[str, tuple[str, str]] = {
    **planetas_glsl.PROGRAMAS,
    **asteroides_glsl.PROGRAMAS,
    **estrellas_glsl.PROGRAMAS,
    **sol_glsl.PROGRAMAS,
}

_aviso = directNotify.newCategory("sombreado")


class Sombreado:
    """Programas compilados para la tarjeta gráfica `gsg`; sin ella, ninguno."""

    def __init__(
        self,
        gsg: GraphicsStateGuardianBase | None,
        programas: dict[str, tuple[str, str]] | None = None,
    ) -> None:
        self._programas: dict[str, Shader] = {}
        self.activo = gsg is not None and _admite_glsl(gsg)
        if gsg is None or not self.activo:
            return
        for nombre, (vertice, fragmento) in (PROGRAMAS if programas is None else programas).items():
            shader = Shader.make(Shader.SL_GLSL, vertice, fragmento)
            if shader is None or shader.prepare_now(gsg.get_prepared_objects(), gsg) is None:
                _aviso.warning(f"El shader {nombre} no compila: se dibuja sin él")
                continue
            self._programas[nombre] = shader

    def programa(self, nombre: str) -> Shader | None:
        """El programa `nombre` ya compilado, o `None` si no se puede usar."""
        return self._programas.get(nombre)


def _admite_glsl(gsg: GraphicsStateGuardianBase) -> bool:
    if not gsg.get_supports_glsl():
        return False
    version = (gsg.get_driver_shader_version_major(), gsg.get_driver_shader_version_minor())
    # Algunos controladores no informan de la versión (−1): se intenta compilar igual.
    return version[0] < 0 or version >= VERSION_GLSL
