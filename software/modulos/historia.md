# Módulo historia

- **Capa:** lógica
- **Cubre:** RF-16; CU-01 (paso 6), CU-07 (paso 5)

## Responsabilidad
Elegir qué transmisión de radio corresponde a cada momento de la partida.

## Estado que gestiona
- Los textos de las transmisiones, cargados de un archivo de datos del juego.
- La transmisión actual.

## Contenido de las transmisiones
El archivo de datos tiene una transmisión para cada momento:
- inicio de la partida,
- descanso tras cada una de las oleadas 1 a 49,
- victoria,
- derrota.

Las transmisiones de los descansos previos a una oleada con niebla o destellos avisan de ese entorno. Los textos siguen la historia de `contexto.md`. Para el primer prototipo basta con textos provisionales; un momento sin texto propio usa uno genérico.

## Operaciones
- **Consultar la transmisión actual:** texto y momento.

## Reglas que aplica
- Al recibir PartidaIniciada, publica TransmisionDisponible con la transmisión de inicio.
- Al recibir OleadaSuperada, publica la transmisión del descanso que corresponde a esa oleada.
- Al recibir PartidaGanada o EstacionDestruida, publica la de victoria o la de derrota.

## Eventos
- Publica: TransmisionDisponible.
- Escucha: PartidaIniciada, OleadaSuperada, PartidaGanada, EstacionDestruida.

## Depende de
nucleo, parametros.

## No hace
- No muestra el texto ni reproduce el sonido de radio: lo hacen `hud` y `audio`.
