"""Pruebas de los sonidos generados y de las decisiones del audio.

No necesitan dispositivo de sonido: comprueban las muestras y las decisiones.
"""

import io
import wave
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest

from atalaya.logica.flujo import Pantalla
from atalaya.presentacion.audio import sintesis
from atalaya.presentacion.audio.audio import (
    CARPETA_PROPIOS,
    DISTANCIAS_EXPLOSION,
    DISTANCIAS_MOTOR,
    EstadoSonido,
    _Rutas,
    acercar,
    cargar_propios,
    evento_giro,
    preparar_propio,
    tono_motor,
    volumen_estacion,
    volumen_explosion,
)
from atalaya.presentacion.escena import salto

EFECTOS: dict[str, Callable[[], sintesis.Muestras]] = {
    "disparo": sintesis.disparo,
    "disparo_enemigo": sintesis.disparo_enemigo,
    "impacto": sintesis.impacto,
    "impacto_estacion": sintesis.impacto_estacion,
    "explosion": sintesis.explosion,
    "sin_energia": sintesis.sin_energia,
    "alarma": sintesis.alarma,
    "aturdimiento": sintesis.aturdimiento,
    "giro_inicio": sintesis.giro_inicio,
    "giro_fin": sintesis.giro_fin,
    "menu_mover": sintesis.menu_mover,
    "menu_confirmar": sintesis.menu_confirmar,
    "menu_error": sintesis.menu_error,
}

BUCLES: dict[str, Callable[[], sintesis.Muestras]] = {
    "motor": sintesis.motor,
    "zumbido": sintesis.zumbido,
    "apuntado": sintesis.apuntado,
}

#: Centro de gravedad del espectro de cada sonido como mucho, en Hz: registro grave.
GRAVE = {
    "explosion": 550,
    "impacto_estacion": 600,
    "motor": 700,
    "zumbido": 300,
    "disparo": 1700,
    "giro_inicio": 900,
    "giro_fin": 900,
}


def _centroide(muestras: sintesis.Muestras) -> float:
    espectro = np.abs(np.fft.rfft(muestras))
    frecuencias = np.fft.rfftfreq(len(muestras), 1 / sintesis.FRECUENCIA)
    return float((frecuencias * espectro).sum() / espectro.sum())


@pytest.mark.parametrize("nombre", sorted(EFECTOS))
def test_efectos_sin_saturar_y_terminan_en_silencio(nombre: str) -> None:
    muestras = EFECTOS[nombre]()
    assert 0 < len(muestras) < 3 * sintesis.FRECUENCIA
    assert np.max(np.abs(muestras)) <= 1.0
    assert np.max(np.abs(muestras)) > 0.3
    # Sin chasquido al final.
    assert abs(muestras[-1]) < 0.01


@pytest.mark.parametrize("nombre", sorted(GRAVE))
def test_sonidos_graves(nombre: str) -> None:
    generar = EFECTOS.get(nombre) or BUCLES[nombre]
    assert _centroide(generar()) < GRAVE[nombre]


@pytest.mark.parametrize("nombre", sorted(EFECTOS))
def test_ningun_efecto_agudo(nombre: str) -> None:
    """Ningún efecto tiene su centro por encima de 2 kHz."""
    assert _centroide(EFECTOS[nombre]()) < 2000


def test_explosion_dura_2_5_s() -> None:
    assert len(sintesis.explosion()) == round(2.5 * sintesis.FRECUENCIA)


@pytest.mark.parametrize("nombre", sorted(BUCLES))
def test_bucles_sin_salto_al_repetirse(nombre: str) -> None:
    """El paso del final al principio no es mayor que los pasos normales del sonido."""
    muestras = BUCLES[nombre]()
    pasos = np.abs(np.diff(muestras))
    union = abs(muestras[0] - muestras[-1])
    assert union <= np.percentile(pasos, 99.9) * 1.5
    assert np.max(np.abs(muestras)) <= 1.0


def test_sonido_del_salto_sigue_a_la_animacion() -> None:
    """Dura lo que el salto y tiene las mismas fases que su animación."""
    assert sintesis.FASES_SALTO == (
        salto._FIN_CARGA,
        salto._FIN_ARRANQUE,
        salto._FIN_TUNEL,
        salto._FIN_SALIDA,
    )
    muestras = sintesis.salto(4.0)
    assert len(muestras) == 4 * sintesis.FRECUENCIA
    # El estampido del arranque es lo más fuerte del primer tercio.
    tercio = muestras[: len(muestras) // 3]
    pico = np.argmax(np.abs(tercio)) / sintesis.FRECUENCIA
    assert 4.0 * 0.28 < pico < 4.0 * 0.33


def test_aviso_dura_lo_que_el_aviso() -> None:
    assert len(sintesis.aviso(1.0)) == sintesis.FRECUENCIA


def test_wav_mono_16_bits() -> None:
    datos = sintesis.a_wav(sintesis.menu_mover())
    with wave.open(io.BytesIO(datos)) as archivo:
        assert archivo.getnchannels() == 1
        assert archivo.getsampwidth() == 2
        assert archivo.getframerate() == sintesis.FRECUENCIA


# --- motores, giro y estación ----------------------------------------------------------


def test_motor_mas_grave_y_fuerte_de_cerca() -> None:
    """Cuanto más cerca la nave, más grave (velocidad menor) y más fuerte."""
    distancias = [50, *range(150, 1300, 50), 3000]
    tonos = [tono_motor(d) for d in distancias]
    velocidades = [v for v, _ in tonos]
    volumenes = [v for _, v in tonos]
    assert velocidades == sorted(velocidades)
    assert volumenes == sorted(volumenes, reverse=True)
    cerca, lejos = DISTANCIAS_MOTOR
    assert tono_motor(cerca)[0] < 0.75
    assert tono_motor(cerca)[1] == pytest.approx(1.0)
    assert tono_motor(lejos)[0] > 1.0


def test_sonidos_del_giro() -> None:
    """Arranque al empezar o cambiar de dirección; parada al soltar; nada si no cambia."""
    assert evento_giro((0, 0), (1, 0)) == "giro_inicio"
    assert evento_giro((1, 0), (1, 0)) is None
    assert evento_giro((1, 0), (-1, 0)) == "giro_inicio"
    assert evento_giro((1, 0), (1, 1)) == "giro_inicio"
    assert evento_giro((0, 1), (0, 0)) == "giro_fin"
    assert evento_giro((0, 0), (0, 0)) is None


def test_zumbido_de_la_estacion() -> None:
    def volumen(pantalla: Pantalla, pausada: Pantalla | None = None, salto: bool = False) -> float:
        return volumen_estacion(EstadoSonido(pantalla, pausada, salto))

    oleada = volumen(Pantalla.OLEADA_EN_CURSO)
    assert oleada > volumen(Pantalla.OLEADA_EN_CURSO, salto=True) > 0
    assert oleada > volumen(Pantalla.PAUSA, pausada=Pantalla.OLEADA_EN_CURSO) > 0
    assert volumen(Pantalla.MENU_PRINCIPAL) > 0


def test_fundido() -> None:
    volumen = 0.0
    for _ in range(45):
        volumen = acercar(volumen, 1.0, 1 / 60)
    assert volumen == pytest.approx(0.5)
    for _ in range(200):
        volumen = acercar(volumen, 0.0, 1 / 60)
    assert volumen == 0.0


# --- caché -----------------------------------------------------------------------------


def test_cache_de_sonidos(tmp_path: Path) -> None:
    """La primera vez se genera y se guarda; la segunda se usa el archivo."""
    llamadas: list[int] = []

    def generar() -> sintesis.Muestras:
        llamadas.append(1)
        return sintesis.menu_mover()

    rutas = _Rutas(tmp_path)
    primera = rutas.ruta("pitido", generar)
    segunda = _Rutas(tmp_path).ruta("pitido", generar)
    assert primera == segunda
    assert llamadas == [1]
    assert (tmp_path / f"pitido-v{sintesis.VERSION}.wav").is_file()


def test_sin_cache_en_memoria(tmp_path: Path) -> None:
    archivo = tmp_path / "ocupado"
    archivo.write_text("x")
    ruta = _Rutas(archivo / "sonidos").ruta("pitido", sintesis.menu_mover)
    assert ruta.get_fullpath().startswith("/atalaya-sonidos/")


# --- explosión y sonidos propios -------------------------------------------------------


def test_explosion_mas_alta_cuanto_mas_cerca() -> None:
    volumenes = [volumen_explosion(d) for d in range(0, 2000, 50)]
    assert volumenes == sorted(volumenes, reverse=True)
    cerca, lejos = DISTANCIAS_EXPLOSION
    assert volumen_explosion(cerca) == pytest.approx(1.0)
    assert volumen_explosion(lejos) < 0.2
    assert volumen_explosion(500) > volumen_explosion(900)


def test_sonidos_propios_del_proyecto() -> None:
    """Los sonidos propios del proyecto apuntan a archivos que existen."""
    propios = cargar_propios(CARPETA_PROPIOS)
    assert set(propios) == {"disparo", "explosion"}
    assert all(p.ruta.is_file() for p in propios.values())


def _wav(ruta: Path, canales: int) -> None:
    datos = (np.sin(np.arange(2205) * 0.1) * 8000).astype("<i2")
    with wave.open(str(ruta), "wb") as archivo:
        archivo.setnchannels(canales)
        archivo.setsampwidth(2)
        archivo.setframerate(22050)
        archivo.writeframes(np.repeat(datos, canales).tobytes())


def test_sonidos_propios_mal_indicados_se_ignoran(tmp_path: Path) -> None:
    _wav(tmp_path / "bueno.wav", 1)
    (tmp_path / "sonidos.json").write_text(
        """{"version": 1, "sonidos": {
            "explosion": {"archivo": "bueno.wav", "volumen": 0.8},
            "disparo": {"archivo": "no-existe.wav"},
            "impacto": {"archivo": "bueno.wav", "volumen": 3},
            "inventado": {"archivo": "bueno.wav"},
            "motor": {"archivo": "bueno.wav"}
        }}""",
        encoding="utf-8",
    )
    propios = cargar_propios(tmp_path)
    assert set(propios) == {"explosion", "motor"}
    assert propios["explosion"].volumen == 0.8
    # Sin volumen, el del sonido generado.
    assert 0 < propios["motor"].volumen <= 1


def test_indice_de_sonidos_propios_estropeado(tmp_path: Path) -> None:
    (tmp_path / "sonidos.json").write_text("{esto no es json", encoding="utf-8")
    assert cargar_propios(tmp_path) == {}
    assert cargar_propios(tmp_path / "no-existe") == {}


def test_estereo_a_mono_para_el_sonido_3d(tmp_path: Path) -> None:
    _wav(tmp_path / "estereo.wav", 2)
    _wav(tmp_path / "mono.wav", 1)
    sin_cambios = preparar_propio(tmp_path / "mono.wav", tmp_path / "x.wav", True, 1.0)
    assert sin_cambios == tmp_path / "mono.wav"
    convertido = preparar_propio(
        tmp_path / "estereo.wav", tmp_path / "cache" / "estereo-mono.wav", True, 1.0
    )
    with wave.open(str(convertido)) as archivo:
        assert archivo.getnchannels() == 1
        assert archivo.getnframes() == 2205


def _nivel(ruta: Path) -> tuple[float, float]:
    with wave.open(str(ruta)) as archivo:
        x = np.frombuffer(archivo.readframes(archivo.getnframes()), "<i2") / 32768.0
    return float(np.abs(x).max()), float(np.sqrt((x**2).mean()))


def test_ganancia_amplifica_sin_saturar(tmp_path: Path) -> None:
    """Con ganancia 5 el sonido suena mucho más fuerte y sus picos no pasan del máximo."""
    _wav(tmp_path / "flojo.wav", 1)
    amplificado = preparar_propio(tmp_path / "flojo.wav", tmp_path / "fuerte.wav", True, 5.0)
    _, rms_antes = _nivel(tmp_path / "flojo.wav")
    pico, rms = _nivel(amplificado)
    assert rms > 2.5 * rms_antes
    assert pico <= 1.0


def test_explosion_del_proyecto_amplificada() -> None:
    assert cargar_propios(CARPETA_PROPIOS)["explosion"].ganancia == 5
