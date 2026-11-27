"""Fondos espaciales: cubos de cielo y texturas de planetas (`design.md`, sección 6; RN-20).

Los cinco cielos se generan con numpy en `cielo.py`, y las texturas de sus planetas en
`planetas.py`. Aquí se guardan en la caché de usuario, para que desde el segundo
arranque se carguen al momento, y se convierten en texturas del motor.

Fluidez: el fondo 1 se prepara al arrancar (unos segundos la primera vez; después sale
de la caché). Los demás se generan en un proceso aparte, que no compite con el juego
por el intérprete, y un hilo los lee de la caché y los deja en el formato del motor. Al
cambiar de fondo solo queda crear la textura.
"""

import multiprocessing
import os
import threading
import zipfile
from pathlib import Path

import numpy as np
import platformdirs
from numpy.typing import NDArray
from panda3d.core import (
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexArrayFormat,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    InternalName,
    NodePath,
    SamplerState,
    Texture,
)

from atalaya.presentacion.escena import cielo, planetas
from atalaya.presentacion.escena.cielo import LADO_CARA, Caras

#: Texturas de un planeta: color con la altura, luz propia y nubes (`planetas.Texturas`).
TexturasPlaneta = planetas.Texturas
#: Las mismas, ya como texturas del motor.
TexturasMotor = tuple[Texture, Texture | None, Texture | None]

#: Número de fondos distintos (RN-20).
FONDOS = len(cielo.TEMAS)

#: Cada cuánto mira el hilo si el proceso ya ha dejado un cielo en la caché, en segundos.
_ESPERA_CACHE = 0.2


def carpeta_cache() -> Path:
    """Carpeta de la caché de cielos generados, propia de cada sistema."""
    return Path(platformdirs.user_cache_dir("atalaya", appauthor=False)) / "cielos"


def ruta_cache(indice: int, lado: int, carpeta: Path) -> Path:
    """Archivo de la caché del cielo `indice`; cambia con la versión del generador."""
    return carpeta / f"cielo-{indice}-v{cielo.VERSION}-{lado}.npz"


def ruta_planetas(indice: int, carpeta: Path, divisor: int = 1) -> Path:
    """Archivo de la caché de los planetas del fondo `indice`, a su resolución."""
    ancho = planetas.ANCHO_GRANDE // divisor
    return carpeta / f"planetas-{indice}-v{planetas.VERSION}-{ancho}.npz"


def _guardar(ruta: Path, **matrices: NDArray[np.uint8]) -> None:
    """Escribe `matrices` en `ruta` de una vez; si no se puede, la caché se queda sin él."""
    temporal = ruta.with_name(f"{ruta.stem}-{os.getpid()}-{threading.get_ident()}.tmp")
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with temporal.open("wb") as archivo:
            np.savez_compressed(archivo, **matrices)  # type: ignore[arg-type]
        # El cambio de nombre es atómico: nunca queda en la caché un archivo a medias.
        os.replace(temporal, ruta)
    except OSError:
        temporal.unlink(missing_ok=True)


def leer_cache(indice: int, lado: int, carpeta: Path) -> Caras | None:
    """Caras del cielo `indice` guardadas en la caché, o `None` si no están o no valen."""
    try:
        with np.load(ruta_cache(indice, lado, carpeta)) as datos:
            caras: Caras = datos["caras"]
    except (OSError, ValueError, KeyError, zipfile.BadZipFile):
        return None
    if caras.shape != (6, lado, lado, 3) or caras.dtype != np.uint8:
        return None
    return caras


def cargar_caras(indice: int, lado: int = LADO_CARA, carpeta: Path | None = None) -> Caras:
    """Caras del cielo `indice`: de la caché si están, o generadas y guardadas en ella.

    La caché es solo una ayuda: si no se puede leer o escribir, el cielo se genera igual.
    """
    carpeta = carpeta_cache() if carpeta is None else carpeta
    caras = leer_cache(indice, lado, carpeta)
    if caras is not None:
        return caras
    caras = cielo.generar(indice, lado)
    _guardar(ruta_cache(indice, lado, carpeta), caras=caras)
    return caras


def leer_planetas(indice: int, carpeta: Path, divisor: int = 1) -> list[TexturasPlaneta] | None:
    """Texturas de los planetas del fondo `indice` en la caché, o `None` si no valen."""
    especificaciones = planetas.PAISAJES[indice - 1].planetas
    try:
        with np.load(ruta_planetas(indice, carpeta, divisor)) as datos:
            leidas: list[TexturasPlaneta] = []
            for i, planeta in enumerate(especificaciones):
                color: NDArray[np.uint8] = datos[f"color{i}"]
                emisivo, nubes = (
                    datos[f"{clave}{i}"] if f"{clave}{i}" in datos.files else None
                    for clave in ("emisivo", "nubes")
                )
                ancho = planetas.ancho_textura(planeta, divisor)
                if color.shape != (ancho // 2, ancho, 4) or color.dtype != np.uint8:
                    return None
                if (nubes is None) != (planeta.nubes <= 0):
                    return None
                leidas.append((color, emisivo, nubes))
            guardadas = sum(1 + sum(t is not None for t in resto) for _, *resto in leidas)
            if len(datos.files) != guardadas:
                return None
    except (OSError, ValueError, KeyError, zipfile.BadZipFile):
        return None
    return leidas


def cargar_planetas(
    indice: int, carpeta: Path | None = None, divisor: int = 1
) -> list[TexturasPlaneta]:
    """Texturas de los planetas del fondo `indice`: de la caché o generadas y guardadas."""
    carpeta = carpeta_cache() if carpeta is None else carpeta
    leidas = leer_planetas(indice, carpeta, divisor)
    if leidas is not None:
        return leidas
    generadas = planetas.generar_texturas(indice, divisor)
    matrices: dict[str, NDArray[np.uint8]] = {}
    for i, (color, emisivo, nubes) in enumerate(generadas):
        matrices[f"color{i}"] = color
        if emisivo is not None:
            matrices[f"emisivo{i}"] = emisivo
        if nubes is not None:
            matrices[f"nubes{i}"] = nubes
    _guardar(ruta_planetas(indice, carpeta, divisor), **matrices)
    return generadas


def _en_cache(indice: int, lado: int, carpeta: Path, divisor: int) -> bool:
    return (
        ruta_cache(indice, lado, carpeta).exists()
        and ruta_planetas(indice, carpeta, divisor).exists()
    )


def _generar_en_cache(indices: list[int], lado: int, carpeta: Path, divisor: int) -> None:
    """Proceso aparte: genera los cielos y planetas de `indices` y los deja en la caché."""
    for indice in indices:
        cargar_caras(indice, lado, carpeta)
        cargar_planetas(indice, carpeta, divisor)


def datos_motor(caras: Caras) -> NDArray[np.uint8]:
    """Bytes de las caras en el orden del motor: colores en BGR.

    Las filas van tal cual: la fila i de cada cara es la coordenada t de los mapas
    cúbicos de OpenGL, que el motor usa sin cambios. Cargar las caras como imágenes
    (`PNMImage`) las invertiría de arriba abajo y descuadraría las caras entre sí.
    """
    return np.ascontiguousarray(caras[..., ::-1])


def textura_cielo(caras: Caras, nombre: str = "fondo") -> Texture:
    """Mapa cúbico del motor con las seis caras de `caras`."""
    return _textura(datos_motor(caras), nombre)


def textura_planeta(imagen: NDArray[np.uint8], nombre: str = "planeta") -> Texture:
    """Textura del motor con un mapa de latitud y longitud de `planetas.py`.

    RGB, RGBA (el alfa es la altura) o gris (nubes). La fila 0 del mapa es el polo sur,
    que es también la fila de abajo para el motor.
    """
    if imagen.ndim == 2:
        datos, formato = np.ascontiguousarray(imagen), Texture.F_luminance
    elif imagen.shape[-1] == 4:
        datos, formato = np.ascontiguousarray(imagen[..., [2, 1, 0, 3]]), Texture.F_rgba
    else:
        datos, formato = np.ascontiguousarray(imagen[..., ::-1]), Texture.F_rgb
    textura = Texture(nombre)
    textura.setup_2d_texture(datos.shape[1], datos.shape[0], Texture.T_unsigned_byte, formato)
    textura.set_ram_image(datos.data)
    textura.set_minfilter(SamplerState.FT_linear_mipmap_linear)
    textura.set_magfilter(SamplerState.FT_linear)
    # Da la vuelta en longitud; en latitud, los polos no se repiten.
    textura.set_wrap_u(SamplerState.WM_repeat)
    textura.set_wrap_v(SamplerState.WM_clamp)
    return textura


def texturas_motor(texturas: TexturasPlaneta, nombre: str = "") -> TexturasMotor:
    """Las texturas de un planeta (`planetas.texturas_planeta`) como texturas del motor."""
    color, emisivo, nubes = texturas
    return (
        textura_planeta(color, f"planeta-{nombre}"),
        None if emisivo is None else textura_planeta(emisivo, f"lava-{nombre}"),
        None if nubes is None else textura_planeta(nubes, f"nubes-{nombre}"),
    )


def _textura(datos: NDArray[np.uint8], nombre: str) -> Texture:
    textura = Texture(nombre)
    textura.setup_cube_map(datos.shape[1], Texture.T_unsigned_byte, Texture.F_rgb)
    textura.set_ram_image(datos.data)
    textura.set_minfilter(SamplerState.FT_linear)
    textura.set_magfilter(SamplerState.FT_linear)
    textura.set_wrap_u(SamplerState.WM_clamp)
    textura.set_wrap_v(SamplerState.WM_clamp)
    return textura


class Fondos:
    """Texturas de los cinco fondos, con sus planetas, preparadas sin parar el juego.

    El fondo 1 está listo al crear el objeto. Los que faltan en la caché se generan en
    un proceso aparte; un hilo los va leyendo de la caché en orden. Si se pide un fondo
    antes de tenerlo, se espera a que llegue.
    """

    def __init__(
        self,
        lado: int = LADO_CARA,
        carpeta: Path | None = None,
        proceso: bool = True,
        divisor_planetas: int = 1,
    ) -> None:
        self._lado = lado
        self._divisor = divisor_planetas
        self._carpeta = carpeta_cache() if carpeta is None else carpeta
        self._datos: dict[int, NDArray[np.uint8]] = {
            1: datos_motor(cargar_caras(1, lado, self._carpeta))
        }
        self._planetas: dict[int, list[TexturasPlaneta]] = {
            1: cargar_planetas(1, self._carpeta, divisor_planetas)
        }
        self._listos = {i: threading.Event() for i in range(1, FONDOS + 1)}
        self._listos[1].set()
        self._texturas: dict[int, Texture] = {}
        self._texturas_planetas: dict[int, list[TexturasMotor]] = {}
        faltan = [
            i
            for i in range(2, FONDOS + 1)
            if not _en_cache(i, lado, self._carpeta, divisor_planetas)
        ]
        self._proceso: multiprocessing.process.BaseProcess | None = None
        if faltan and proceso:
            # El proceso muere con el juego: si se cierra a medias, no hay que esperarlo.
            contexto = multiprocessing.get_context("spawn")
            self._proceso = contexto.Process(
                target=_generar_en_cache,
                args=(faltan, lado, self._carpeta, divisor_planetas),
                name="atalaya-cielos",
                daemon=True,
            )
            self._proceso.start()
        self._hilo = threading.Thread(target=self._leer_resto, name="atalaya-fondos", daemon=True)
        self._hilo.start()

    def textura(self, indice: int) -> Texture:
        """Textura del fondo `indice`, de 1 a 5."""
        if not 1 <= indice <= FONDOS:
            raise ValueError(f"El fondo {indice} no existe: van de 1 a {FONDOS}")
        textura = self._texturas.get(indice)
        if textura is None:
            self._listos[indice].wait()
            textura = _textura(self._datos.pop(indice), f"fondo-{indice}")
            self._texturas[indice] = textura
        return textura

    def texturas_planetas(self, indice: int) -> list[TexturasMotor]:
        """Texturas de color, de luz propia y de nubes de cada planeta del fondo `indice`."""
        if not 1 <= indice <= FONDOS:
            raise ValueError(f"El fondo {indice} no existe: van de 1 a {FONDOS}")
        texturas = self._texturas_planetas.get(indice)
        if texturas is None:
            self._listos[indice].wait()
            texturas = [
                texturas_motor(t, f"{indice}-{i}") for i, t in enumerate(self._planetas.pop(indice))
            ]
            self._texturas_planetas[indice] = texturas
        return texturas

    def esperar(self, tiempo: float | None = None) -> bool:
        """Espera a tener todos los fondos. Devuelve si están todos."""
        self._hilo.join(tiempo)
        return not self._hilo.is_alive()

    def _leer_resto(self) -> None:
        """Lee cada fondo de la caché en cuanto el proceso lo deja allí.

        Si el proceso termina sin dejarlo (no se pudo escribir la caché), se genera aquí.
        """
        for indice in range(2, FONDOS + 1):
            while (
                self._proceso is not None
                and self._proceso.is_alive()
                and not _en_cache(indice, self._lado, self._carpeta, self._divisor)
            ):
                threading.Event().wait(_ESPERA_CACHE)
            caras = cargar_caras(indice, self._lado, self._carpeta)
            self._datos[indice] = datos_motor(caras)
            self._planetas[indice] = cargar_planetas(indice, self._carpeta, self._divisor)
            self._listos[indice].set()


def cubo_de_cielo(textura: Texture) -> NodePath:
    """Cubo centrado en el origen con `textura` como mapa cúbico.

    Se dibuja el primero, sin prueba ni escritura de profundidad, así que siempre queda
    detrás de todo lo demás, como si estuviera a distancia infinita.
    """
    columnas = GeomVertexArrayFormat()
    columnas.add_column(InternalName.get_vertex(), 3, Geom.NT_float32, Geom.C_point)
    # Coordenadas de textura en 3D: la dirección desde el centro del cubo.
    columnas.add_column(InternalName.get_texcoord(), 3, Geom.NT_float32, Geom.C_texcoord)
    formato = GeomVertexFormat.register_format(GeomVertexFormat(columnas))
    datos = GeomVertexData("fondo", formato, Geom.UH_static)
    vertices = GeomVertexWriter(datos, "vertex")
    coordenadas = GeomVertexWriter(datos, "texcoord")
    esquinas = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    for esquina in esquinas:
        vertices.add_data3(*esquina)
        coordenadas.add_data3(*esquina)
    triangulos = GeomTriangles(Geom.UH_static)
    # Cada cara del cubo: cuatro esquinas que comparten una coordenada.
    for eje in range(3):
        for signo in (-1, 1):
            cara = [i for i, e in enumerate(esquinas) if e[eje] == signo]
            a, b, c, d = cara
            triangulos.add_vertices(a, b, d)
            triangulos.add_vertices(a, d, c)
    geom = Geom(datos)
    geom.add_primitive(triangulos)
    nodo = GeomNode("fondo")
    nodo.add_geom(geom)
    cubo = NodePath(nodo)
    cubo.set_texture(textura)
    cubo.set_two_sided(True)
    cubo.set_light_off()
    cubo.set_bin("background", 0)
    cubo.set_depth_test(False)
    cubo.set_depth_write(False)
    cubo.set_scale(10)
    return cubo
