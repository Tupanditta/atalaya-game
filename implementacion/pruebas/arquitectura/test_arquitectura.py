"""Pruebas de arquitectura de la capa lógica (Sprint 0).

Analizan las importaciones de cada archivo de `atalaya/logica` sin ejecutarlo.
"""

import ast
import re
from collections.abc import Iterator
from pathlib import Path

import pytest

import atalaya.logica

LOGICA = Path(atalaya.logica.__file__).resolve().parent
MODULOS_README = Path(__file__).resolve().parents[3] / "software" / "modulos" / "README.md"

#: Consultas permitidas entre módulos lógicos (`modulos/README.md`, «Dependencias permitidas»).
#: `flujo` también consulta a `entrada`, pero es de presentación: lo recibe inyectado.
DEPENDENCIAS: dict[str, set[str]] = {
    "flujo": {"vista", "armamento", "mejoras", "oleadas", "progreso"},
    "armamento": {"vista"},
    "radar": {"vista", "enemigos"},
}

#: Todos los módulos pueden usar estos dos. `nucleo` no depende de nada.
COMUNES = {"nucleo", "parametros"}

#: Módulos que solo puede usar `nucleo`: reloj del sistema y azar global.
RELOJ_Y_AZAR = {"time", "datetime", "random", "secrets"}

#: Paquetes del motor gráfico.
MOTOR = {"panda3d", "direct", "pandac"}


def _archivos() -> Iterator[Path]:
    yield from sorted(LOGICA.rglob("*.py"))


def _modulo_de(archivo: Path) -> str:
    """Nombre del módulo lógico al que pertenece `archivo` (primer nivel bajo `logica`)."""
    return archivo.relative_to(LOGICA).parts[0]


def _base(archivo: Path, nodo: ast.ImportFrom) -> str:
    """Nombre absoluto del módulo de un `from ... import`, también si es relativo."""
    if nodo.level == 0:
        assert nodo.module is not None
        return nodo.module
    # El paquete de `a/b/c.py` y de `a/b/__init__.py` es `a.b`.
    paquete = ["atalaya", "logica", *archivo.relative_to(LOGICA).with_suffix("").parts][:-1]
    paquete = paquete[: len(paquete) - (nodo.level - 1)]
    return ".".join([*paquete, *([nodo.module] if nodo.module else [])])


def _importaciones(archivo: Path) -> Iterator[str]:
    """Nombres absolutos de los módulos que importa `archivo`."""
    arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                yield alias.name
        elif isinstance(nodo, ast.ImportFrom):
            base = _base(archivo, nodo)
            yield base
            for alias in nodo.names:
                yield f"{base}.{alias.name}"


def _modulos_logicos_documentados() -> set[str]:
    texto = MODULOS_README.read_text(encoding="utf-8")
    return set(re.findall(r"^\| (\w+) \| lógica \|", texto, flags=re.MULTILINE))


def test_hay_archivos_que_analizar() -> None:
    """El análisis encuentra el código de la capa lógica."""
    assert any(_modulo_de(a) == "nucleo" for a in _archivos())


def test_subpaquetes_de_la_capa_logica() -> None:
    """Hay un subpaquete por módulo lógico de `modulos/README.md` y ninguno más."""
    subpaquetes = {d.name for d in LOGICA.iterdir() if (d / "__init__.py").is_file()}
    documentados = _modulos_logicos_documentados()
    assert len(documentados) == 13
    assert subpaquetes == documentados


@pytest.mark.parametrize(
    "archivo", list(_archivos()), ids=lambda a: a.relative_to(LOGICA).as_posix()
)
def test_s0_t18_capas(archivo: Path) -> None:
    """S0-T18 arquitectura, capas: ningún módulo lógico importa Panda3D ni la presentación."""
    for nombre in _importaciones(archivo):
        raiz = nombre.split(".")[0]
        assert raiz not in MOTOR, f"{archivo.name} importa el motor: {nombre}"
        assert not nombre.startswith("atalaya.presentacion"), (
            f"{archivo.name} importa la presentación: {nombre}"
        )


@pytest.mark.parametrize(
    "archivo", list(_archivos()), ids=lambda a: a.relative_to(LOGICA).as_posix()
)
def test_s0_t19_dependencias(archivo: Path) -> None:
    """S0-T19 arquitectura, dependencias: solo las de la tabla, más nucleo y parametros."""
    propio = _modulo_de(archivo)
    if propio == "nucleo":
        permitidos = {"nucleo"}
    else:
        permitidos = {propio} | COMUNES | DEPENDENCIAS.get(propio, set())
    for nombre in _importaciones(archivo):
        partes = nombre.split(".")
        if partes[:2] != ["atalaya", "logica"] or len(partes) < 3:
            continue
        assert partes[2] in permitidos, f"{propio} no puede depender de {partes[2]} ({nombre})"


@pytest.mark.parametrize(
    "archivo", list(_archivos()), ids=lambda a: a.relative_to(LOGICA).as_posix()
)
def test_s0_t20_tiempo_y_azar_solo_en_nucleo(archivo: Path) -> None:
    """S0-T20: ningún módulo salvo nucleo usa time, datetime ni random."""
    if _modulo_de(archivo) == "nucleo":
        return
    for nombre in _importaciones(archivo):
        assert nombre.split(".")[0] not in RELOJ_Y_AZAR, f"{archivo.name} importa {nombre}"


def test_analisis_detecta_importaciones_prohibidas(tmp_path: Path) -> None:
    """El análisis reconoce importaciones absolutas y relativas."""
    archivo = tmp_path / "prueba.py"
    archivo.write_text(
        "import time\nfrom random import random\nimport panda3d.core\n"
        "from atalaya.presentacion import hud\n",
        encoding="utf-8",
    )
    nombres = set(_importaciones(archivo))
    assert {"time", "random", "panda3d.core", "atalaya.presentacion.hud"} <= nombres


def test_analisis_resuelve_importaciones_relativas() -> None:
    """Una importación relativa se resuelve respecto al paquete del archivo."""
    nodos = ast.parse("from ..enemigos import a\nfrom . import b\n").body
    for archivo in (LOGICA / "vista" / "giro.py", LOGICA / "vista" / "__init__.py"):
        assert [_base(archivo, n) for n in nodos if isinstance(n, ast.ImportFrom)] == [
            "atalaya.logica.enemigos",
            "atalaya.logica.vista",
        ]
