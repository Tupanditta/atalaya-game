"""Pruebas de la turbulencia al recibir daño: 0,2 s, cámara y mira (sin ventana)."""

from panda3d.core import NodePath

from atalaya.presentacion.escena.efectos import (
    DURACION_DANO,
    DURACION_TURBULENCIA,
    DanoRecibido,
    turbulencia,
)

PASO = 1 / 60


def test_turbulencia_de_0_2_s_en_la_camara() -> None:
    """La cámara tiembla 0,2 s; el tinte rojo sigue algo más."""
    assert DURACION_TURBULENCIA == 0.2
    assert DURACION_DANO > DURACION_TURBULENCIA
    camara = NodePath("camara")
    dano = DanoRecibido(NodePath("render2d"))
    dano.recibir()
    giros = []
    for _ in range(round(DURACION_DANO / PASO)):
        camara.set_hpr(0, 0, 0)
        dano.avanzar(PASO, camara)
        giros.append(camara.get_hpr().length())
    tiembla = [g > 1e-6 for g in giros]
    pasos_turbulencia = round(DURACION_TURBULENCIA / PASO)
    assert any(tiembla[: pasos_turbulencia - 1])
    assert not any(tiembla[pasos_turbulencia + 1 :])


def test_turbulencia_se_apaga_con_la_fuerza() -> None:
    assert turbulencia(0.37, 0.0) == (0.0, 0.0)
    fuerte = turbulencia(0.37, 1.0)
    debil = turbulencia(0.37, 0.25)
    assert abs(debil[0]) == abs(fuerte[0]) * 0.25
    # Otra fase: otro temblor, para la mira.
    assert turbulencia(0.37, 1.0, fase=3.7) != fuerte
