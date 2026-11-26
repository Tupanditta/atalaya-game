"""Pruebas del azar con semilla (Sprint 0)."""

from atalaya.logica.nucleo import Azar, Nucleo, semilla_nueva


def _secuencia(azar: Azar) -> list[float]:
    return [azar.aleatorio() for _ in range(20)]


def test_s0_t08_misma_semilla_misma_secuencia() -> None:
    """S0-T08 azar con semilla: la misma semilla repite la secuencia; otra la cambia."""
    assert _secuencia(Azar(42)) == _secuencia(Azar(42))
    assert _secuencia(Azar(42)) != _secuencia(Azar(43))


def test_reiniciar_azar_del_nucleo() -> None:
    """Reiniciar el azar con la misma semilla vuelve a dar la misma secuencia."""
    nucleo = Nucleo(semilla=7)
    assert nucleo.azar.semilla == 7
    primera = _secuencia(nucleo.azar)
    nucleo.reiniciar_azar(7)
    assert _secuencia(nucleo.azar) == primera


def test_semilla_nueva_por_partida() -> None:
    """Cada partida empieza con una semilla nueva."""
    nucleo = Nucleo()
    semillas = {nucleo.azar.semilla}
    for _ in range(5):
        nucleo.reiniciar_azar()
        semillas.add(nucleo.azar.semilla)
    assert len(semillas) == 6
    assert semilla_nueva() >= 0


def test_operaciones_de_azar() -> None:
    """Las operaciones del azar devuelven valores en sus rangos y son reproducibles."""
    azar = Azar(3)
    for _ in range(100):
        assert 0.0 <= azar.aleatorio() < 1.0
        assert 2.0 <= azar.uniforme(2.0, 5.0) <= 5.0
        assert 1 <= azar.entero(1, 3) <= 3
    lista_a = list(range(10))
    lista_b = list(range(10))
    Azar(9).barajar(lista_a)
    Azar(9).barajar(lista_b)
    assert lista_a == lista_b
    assert sorted(lista_a) == list(range(10))
    assert Azar(5).elegir(["x", "y", "z"]) == Azar(5).elegir(["x", "y", "z"])
