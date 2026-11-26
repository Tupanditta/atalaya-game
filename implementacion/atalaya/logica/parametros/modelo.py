"""Grupos de parámetros del juego y valores derivados.

Los grupos siguen la sección «Parámetros iniciales» de `reglasNegocio.md`.
Todos son inmutables: los parámetros no cambian durante la partida.
"""

from dataclasses import dataclass

from atalaya.logica.nucleo.dominio import Entorno, Mejora, Tamano, TipoEnemigo


@dataclass(frozen=True, slots=True)
class Jugador:
    """Jugador y estación. Ángulos en grados, tiempos en segundos."""

    energia_maxima: float
    coste_disparo: float
    #: Energía recargada por segundo.
    recarga_energia: float
    integridad_maxima: float
    #: Puntos de vida que quita un disparo del jugador.
    dano_disparo: float
    #: Grados por segundo en cada eje, sin zoom.
    velocidad_giro: float
    campo_vision_normal: float
    campo_vision_zoom: float
    #: Radio de dispersión de la mira, en grados.
    mira_normal: float
    mira_minima: float
    #: Tiempo para que la mira llegue al tamaño mínimo.
    tiempo_apuntado: float
    #: Tiempo de vuelta de la mira y el zoom a su estado normal.
    tiempo_vuelta_mira: float


@dataclass(frozen=True, slots=True)
class DatosTamano:
    """Datos de un tamaño de enemigo (RN-06). Vida en el nivel 1."""

    vida: float
    velocidad_maxima: float
    aceleracion_maxima: float
    radio_impacto: float


@dataclass(frozen=True, slots=True)
class Tamanos:
    pequeno: DatosTamano
    mediano: DatosTamano
    grande: DatosTamano

    def de(self, tamano: Tamano) -> DatosTamano:
        """Datos del tamaño `tamano`."""
        datos: DatosTamano = getattr(self, tamano.value)
        return datos


@dataclass(frozen=True, slots=True)
class DatosTipo:
    """Datos de un tipo de enemigo (RN-11, RN-12, RN-13, RN-14)."""

    #: Daño a la integridad de cada proyectil.
    dano: float
    #: Tiempo de recarga entre ataques.
    recarga: float
    #: Duración del temblor o del aturdimiento; 0 si el tipo no tiene efecto.
    duracion_efecto: float


@dataclass(frozen=True, slots=True)
class Tipos:
    sin_efecto: DatosTipo
    desestabilizador: DatosTipo
    aturdidor: DatosTipo

    def de(self, tipo: TipoEnemigo) -> DatosTipo:
        """Datos del tipo `tipo`."""
        datos: DatosTipo = getattr(self, tipo.value)
        return datos


@dataclass(frozen=True, slots=True)
class Ataques:
    """Ataques y distancias. Distancias en unidades del mundo."""

    duracion_aviso: float
    velocidad_proyectil: float
    distancia_aparicion_minima: float
    distancia_aparicion_maxima: float
    distancia_maxima: float
    alcance_disparo: float
    distancia_minima: float
    alcance_radar: float
    distancia_llegada: float
    #: Desvío máximo de la mira respecto al centro por desestabilización, en grados.
    desvio_maximo: float
    #: Velocidad máxima del desvío, en grados por segundo.
    velocidad_desvio: float
    enemigos_activos_maximos: int
    #: Segundos entre apariciones, mientras haya hueco.
    intervalo_aparicion: float


@dataclass(frozen=True, slots=True)
class Oleadas:
    """Composición de las oleadas."""

    numero_oleadas: int
    #: Enemigos por oleada = enemigos_base + parte entera de n / divisor_enemigos.
    enemigos_base: int
    divisor_enemigos: int
    oleada_desestabilizadores: int
    oleada_aturdidores: int
    #: Enemigos con efecto especial: como máximo parte entera de enemigos / divisor_efecto.
    divisor_efecto: int
    fondos: int
    oleadas_por_fondo: int


@dataclass(frozen=True, slots=True)
class Entornos:
    """Entornos de baja visibilidad (RN-44)."""

    primera_oleada: int
    intervalo_oleadas: int
    niebla_visibilidad_completa: float
    niebla_invisible: float
    destellos_intervalo_minimo: float
    destellos_intervalo_maximo: float
    destellos_aviso: float
    destellos_deslumbramiento: float


@dataclass(frozen=True, slots=True)
class DatosMejora:
    """Datos de una mejora de la estación (RN-47)."""

    efecto: float
    niveles_maximos: int
    coste: int


@dataclass(frozen=True, slots=True)
class Mejoras:
    """Mejoras y reparación (RN-45, RN-46, RN-47)."""

    #: Tiempo de referencia = base + por_enemigo × enemigos de la oleada.
    tiempo_referencia_base: float
    tiempo_referencia_por_enemigo: float
    #: Puntos si el tiempo es menor o igual que el de referencia.
    puntos_rapido: int
    #: Puntos si el tiempo es menor o igual que el de referencia × factor_tiempo_medio.
    puntos_medio: int
    puntos_lento: int
    factor_tiempo_medio: float
    coste_reparacion: int
    cantidad_reparacion: float
    blindaje: DatosMejora
    bateria: DatosMejora
    generador: DatosMejora

    def de(self, mejora: Mejora) -> DatosMejora:
        """Datos de la mejora `mejora`."""
        datos: DatosMejora = getattr(self, mejora.value)
        return datos


@dataclass(frozen=True, slots=True)
class Nivel:
    """Efecto del nivel de dificultad (RN-22)."""

    #: Vida = vida en nivel 1 × (1 + incremento_vida × (nivel − 1)).
    incremento_vida: float
    #: Descanso = descanso_minimo + descanso_variable × factor_descanso^(nivel − 1).
    descanso_minimo: float
    descanso_variable: float
    factor_descanso: float


@dataclass(frozen=True, slots=True)
class Composicion:
    """Composición de una oleada (RN-16)."""

    numero_enemigos: int
    tipos_permitidos: frozenset[TipoEnemigo]
    maximo_con_efecto: int


@dataclass(frozen=True, slots=True)
class Parametros:
    """Todos los parámetros del juego, de solo lectura."""

    jugador: Jugador
    tamanos: Tamanos
    tipos: Tipos
    ataques: Ataques
    oleadas: Oleadas
    entornos: Entornos
    mejoras: Mejoras
    nivel: Nivel

    def vida_enemigo(self, tamano: Tamano, nivel: int) -> float:
        """Vida de un enemigo de `tamano` en el nivel de dificultad `nivel` (RN-22)."""
        _comprobar_nivel(nivel)
        return self.tamanos.de(tamano).vida * (1 + self.nivel.incremento_vida * (nivel - 1))

    def duracion_descanso(self, nivel: int) -> float:
        """Duración del descanso entre oleadas en el nivel `nivel` (RN-18, RN-22)."""
        _comprobar_nivel(nivel)
        n = self.nivel
        return n.descanso_minimo + n.descanso_variable * n.factor_descanso ** (nivel - 1)

    def composicion_oleada(self, numero: int) -> Composicion:
        """Número de enemigos y tipos permitidos en la oleada `numero` (RN-16)."""
        self._comprobar_oleada(numero)
        o = self.oleadas
        enemigos = o.enemigos_base + numero // o.divisor_enemigos
        tipos = {TipoEnemigo.SIN_EFECTO}
        if numero >= o.oleada_desestabilizadores:
            tipos.add(TipoEnemigo.DESESTABILIZADOR)
        if numero >= o.oleada_aturdidores:
            tipos.add(TipoEnemigo.ATURDIDOR)
        maximo_con_efecto = enemigos // o.divisor_efecto if len(tipos) > 1 else 0
        return Composicion(enemigos, frozenset(tipos), maximo_con_efecto)

    def entorno_oleada(self, numero: int) -> Entorno:
        """Entorno de la oleada `numero`: alterna niebla y destellos, empezando por la niebla."""
        self._comprobar_oleada(numero)
        e = self.entornos
        desde_primera = numero - e.primera_oleada
        if desde_primera < 0 or desde_primera % e.intervalo_oleadas != 0:
            return Entorno.NINGUNO
        orden = desde_primera // e.intervalo_oleadas
        return Entorno.NIEBLA if orden % 2 == 0 else Entorno.DESTELLOS

    def _comprobar_oleada(self, numero: int) -> None:
        if not 1 <= numero <= self.oleadas.numero_oleadas:
            raise ValueError(
                f"La oleada {numero} no existe: van de 1 a {self.oleadas.numero_oleadas}"
            )


def _comprobar_nivel(nivel: int) -> None:
    if nivel < 1:
        raise ValueError(f"El nivel de dificultad {nivel} no existe: empiezan en 1")
