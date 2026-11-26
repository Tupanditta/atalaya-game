"""S0-T17: `parametros.json` coincide con «Parámetros iniciales» de `reglasNegocio.md`.

La prueba lee las tablas del documento, extrae las cifras de cada fila (sin la
columna de etiqueta ni la de regla) y las compara con las cifras que se esperan a
partir de los parámetros cargados. Toda fila del documento debe tener su entrada en
`ESPERADO` y viceversa, de modo que un parámetro nuevo obliga a actualizar la prueba.
"""

import re
from collections.abc import Callable
from pathlib import Path

import pytest

from atalaya.logica.parametros import Parametros

REGLAS = Path(__file__).resolve().parents[3] / "software" / "reglasNegocio.md"

_CIFRA = re.compile(r"\d+(?:,\d+)?")

Esperado = Callable[[Parametros], list[float]]

ESPERADO: dict[tuple[str, str], Esperado] = {
    # Jugador y estación
    ("Jugador y estación", "Energía máxima"): lambda p: [p.jugador.energia_maxima],
    ("Jugador y estación", "Coste de un disparo"): lambda p: [p.jugador.coste_disparo],
    ("Jugador y estación", "Recarga de energía"): lambda p: [p.jugador.recarga_energia],
    ("Jugador y estación", "Integridad máxima"): lambda p: [p.jugador.integridad_maxima],
    ("Jugador y estación", "Daño de un disparo del jugador"): lambda p: [p.jugador.dano_disparo],
    ("Jugador y estación", "Velocidad de giro sin zoom"): lambda p: [p.jugador.velocidad_giro],
    ("Jugador y estación", "Campo de visión sin zoom"): lambda p: [p.jugador.campo_vision_normal],
    ("Jugador y estación", "Campo de visión con zoom máximo"): lambda p: [
        p.jugador.campo_vision_zoom
    ],
    ("Jugador y estación", "Tamaño normal de la mira (radio del círculo)"): lambda p: [
        p.jugador.mira_normal
    ],
    ("Jugador y estación", "Tamaño mínimo de la mira"): lambda p: [p.jugador.mira_minima],
    ("Jugador y estación", "Tiempo para llegar al tamaño mínimo"): lambda p: [
        p.jugador.tiempo_apuntado
    ],
    ("Jugador y estación", "Tiempo de vuelta de la mira y el zoom a su estado normal"): lambda p: [
        p.jugador.tiempo_vuelta_mira
    ],
    # Enemigos por tamaño
    **{
        ("Enemigos por tamaño", etiqueta): (
            lambda p, n=nombre: [
                getattr(p.tamanos, n).vida,
                getattr(p.tamanos, n).velocidad_maxima,
                getattr(p.tamanos, n).aceleracion_maxima,
                getattr(p.tamanos, n).radio_impacto,
            ]
        )
        for etiqueta, nombre in [
            ("Pequeño", "pequeno"),
            ("Mediano", "mediano"),
            ("Grande", "grande"),
        ]
    },
    # Enemigos por tipo
    ("Enemigos por tipo", "Sin efecto especial"): lambda p: [
        p.tipos.sin_efecto.dano,
        p.tipos.sin_efecto.recarga,
    ],
    ("Enemigos por tipo", "Desestabilizador"): lambda p: [
        p.tipos.desestabilizador.dano,
        p.tipos.desestabilizador.recarga,
        p.tipos.desestabilizador.duracion_efecto,
    ],
    ("Enemigos por tipo", "Aturdidor"): lambda p: [
        p.tipos.aturdidor.dano,
        p.tipos.aturdidor.recarga,
        p.tipos.aturdidor.duracion_efecto,
    ],
    # Ataques y distancias
    ("Ataques y distancias", "Duración del aviso de disparo"): lambda p: [p.ataques.duracion_aviso],
    ("Ataques y distancias", "Velocidad de los proyectiles enemigos"): lambda p: [
        p.ataques.velocidad_proyectil
    ],
    ("Ataques y distancias", "Distancia de aparición"): lambda p: [
        p.ataques.distancia_aparicion_minima,
        p.ataques.distancia_aparicion_maxima,
    ],
    ("Ataques y distancias", "Distancia máxima"): lambda p: [p.ataques.distancia_maxima],
    ("Ataques y distancias", "Alcance de disparo enemigo"): lambda p: [p.ataques.alcance_disparo],
    ("Ataques y distancias", "Distancia mínima"): lambda p: [p.ataques.distancia_minima],
    ("Ataques y distancias", "Alcance del radar"): lambda p: [p.ataques.alcance_radar],
    (
        "Ataques y distancias",
        "Distancia de llegada al destino "
        "(a menos de esta distancia, el enemigo elige otro destino)",
    ): lambda p: [p.ataques.distancia_llegada],
    ("Ataques y distancias", "Desestabilización: desvío máximo de la mira respecto al centro"): (
        lambda p: [p.ataques.desvio_maximo]
    ),
    ("Ataques y distancias", "Desestabilización: velocidad máxima del desvío"): lambda p: [
        p.ataques.velocidad_desvio
    ],
    ("Ataques y distancias", "Enemigos activos a la vez"): lambda p: [
        p.ataques.enemigos_activos_maximos
    ],
    ("Ataques y distancias", "Ritmo de aparición"): lambda p: [p.ataques.intervalo_aparicion],
    # Composición de las oleadas («3 + parte entera de n / 2»)
    ("Composición de las oleadas", "Enemigos por oleada"): lambda p: [
        p.oleadas.enemigos_base,
        p.oleadas.divisor_enemigos,
    ],
    ("Composición de las oleadas", "Tamaños"): lambda p: [1],
    ("Composición de las oleadas", "Desestabilizadores"): lambda p: [
        p.oleadas.oleada_desestabilizadores
    ],
    ("Composición de las oleadas", "Aturdidores"): lambda p: [p.oleadas.oleada_aturdidores],
    # «como máximo un tercio de la oleada»: se comprueba aparte, en palabras.
    ("Composición de las oleadas", "Enemigos con efecto especial"): lambda p: [],
    ("Composición de las oleadas", "Fondos distintos"): lambda p: [
        p.oleadas.fondos,
        p.oleadas.oleadas_por_fondo,
    ],
    # Entornos de baja visibilidad
    ("Entornos de baja visibilidad", "Oleadas con entorno"): lambda p: [
        p.entornos.primera_oleada,
        p.entornos.primera_oleada,
        p.entornos.primera_oleada + p.entornos.intervalo_oleadas,
        p.entornos.primera_oleada + 2 * p.entornos.intervalo_oleadas,
    ],
    ("Entornos de baja visibilidad", "Niebla: visibilidad completa"): lambda p: [
        p.entornos.niebla_visibilidad_completa
    ],
    ("Entornos de baja visibilidad", "Niebla: invisible"): lambda p: [p.entornos.niebla_invisible],
    ("Entornos de baja visibilidad", "Destellos: intervalo"): lambda p: [
        p.entornos.destellos_intervalo_minimo,
        p.entornos.destellos_intervalo_maximo,
    ],
    ("Entornos de baja visibilidad", "Destellos: aviso previo"): lambda p: [
        p.entornos.destellos_aviso
    ],
    ("Entornos de baja visibilidad", "Destellos: deslumbramiento"): lambda p: [
        p.entornos.destellos_deslumbramiento
    ],
    # Mejoras y reparación
    ("Mejoras y reparación", "Tiempo de referencia de una oleada"): lambda p: [
        p.mejoras.tiempo_referencia_base,
        p.mejoras.tiempo_referencia_por_enemigo,
    ],
    ("Mejoras y reparación", "Puntos por oleada"): lambda p: [
        p.mejoras.puntos_rapido,
        p.mejoras.puntos_medio,
        p.mejoras.puntos_lento,
    ],
    ("Mejoras y reparación", "Reparación"): lambda p: [
        p.mejoras.coste_reparacion,
        p.mejoras.cantidad_reparacion,
    ],
    ("Mejoras y reparación", "Blindaje"): lambda p: [
        p.mejoras.blindaje.efecto,
        p.mejoras.blindaje.efecto,
        p.mejoras.blindaje.niveles_maximos,
        p.mejoras.blindaje.coste,
    ],
    ("Mejoras y reparación", "Batería"): lambda p: [
        p.mejoras.bateria.efecto,
        p.mejoras.bateria.niveles_maximos,
        p.mejoras.bateria.coste,
    ],
    ("Mejoras y reparación", "Generador"): lambda p: [
        p.mejoras.generador.efecto,
        p.mejoras.generador.niveles_maximos,
        p.mejoras.generador.coste,
    ],
    # Nivel de dificultad
    ("Nivel de dificultad", "Vida de los enemigos"): lambda p: [
        1,
        1,
        p.nivel.incremento_vida,
        1,
    ],
    ("Nivel de dificultad", "Descanso entre oleadas"): lambda p: [
        p.nivel.descanso_minimo,
        p.nivel.descanso_variable,
        p.nivel.factor_descanso,
        1,
    ],
}


def _cifras(texto: str) -> list[float]:
    return [float(c.replace(",", ".")) for c in _CIFRA.findall(texto)]


def _seccion_parametros() -> list[str]:
    lineas = REGLAS.read_text(encoding="utf-8").splitlines()
    inicio = lineas.index("## Parámetros iniciales")
    return lineas[inicio + 1 :]


def _filas_documento() -> dict[tuple[str, str], list[float]]:
    """Devuelve las cifras de cada fila de las tablas, por (sección, etiqueta)."""
    filas: dict[tuple[str, str], list[float]] = {}
    seccion = ""
    cabecera: list[str] | None = None
    for linea in _seccion_parametros():
        if linea.startswith("## "):
            break
        if linea.startswith("### "):
            seccion = linea[4:].strip()
            continue
        if not linea.startswith("|"):
            cabecera = None
            continue
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if cabecera is None:
            cabecera = celdas
            continue
        if set("".join(celdas)) <= set("-: "):
            continue
        valores = [
            c for c, titulo in zip(celdas[1:], cabecera[1:], strict=True) if titulo != "Regla"
        ]
        filas[(seccion, celdas[0])] = _cifras(" ".join(valores))
    return filas


def test_s0_t17_todas_las_filas_tienen_comprobacion() -> None:
    """S0-T17: cada fila del documento tiene su comprobación y no sobra ninguna."""
    assert set(_filas_documento()) == set(ESPERADO)


@pytest.mark.parametrize("clave", sorted(ESPERADO), ids=" / ".join)
def test_s0_t17_coherencia_de_datos(parametros: Parametros, clave: tuple[str, str]) -> None:
    """S0-T17 coherencia de datos: cada fila coincide con `parametros.json`."""
    documento = _filas_documento()[clave]
    assert documento == pytest.approx(ESPERADO[clave](parametros))


def test_s0_t17_valores_en_texto(parametros: Parametros) -> None:
    """S0-T17: valores escritos en el texto de la sección, no en cifras de tabla."""
    texto = "\n".join(_seccion_parametros())
    oleadas = re.search(r"n es el número de la oleada \(de 1 a (\d+)\)", texto)
    assert oleadas is not None
    assert int(oleadas.group(1)) == parametros.oleadas.numero_oleadas
    assert "como máximo un tercio de la oleada" in texto
    assert parametros.oleadas.divisor_efecto == 3
    assert "una de cada tres" in texto
    assert parametros.entornos.intervalo_oleadas == 3
    assert "menor o igual que el doble" in texto
    assert parametros.mejoras.factor_tiempo_medio == 2
