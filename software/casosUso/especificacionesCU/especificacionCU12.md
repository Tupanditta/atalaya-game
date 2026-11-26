# CU-12. Salir del juego

## Identificación
- **Actor principal:** ACT-01
- **Actores secundarios:** ninguno
- **Objetivo:** Cerrar el juego.
- **Requisitos relacionados:** RF-34, RF-38, RNF-03, RN-25, RN-49, RES-04, RES-05, RES-06, RES-07

## Precondiciones
- El jugador está en el menú principal o en el menú de pausa.

## Disparador
El jugador elige «Salir del juego».

## Flujo principal
1. El jugador elige «Salir del juego» en el menú principal.
2. El sistema cierra el juego.

## Flujos alternativos y excepciones
### A1. Salir con una partida en curso (desde el paso 1)
1. El jugador elige «Salir del juego» en el menú de pausa.
2. El sistema pide confirmación con las opciones «Sí» y «No». «No» aparece seleccionada.
3. El jugador elige «Sí».
4. El sistema descarta la partida en curso y cierra el juego.

### A2. No confirmar la salida (desde el paso 3 de A1)
1. El jugador elige «No» o pulsa Esc.
2. El sistema vuelve al menú de pausa (CU-09). Finaliza.

## Reglas de presentación
- No se identifican reglas de presentación propias.

## Postcondiciones
- El juego está cerrado.
- El nivel desbloqueado guardado no cambia. La partida en curso, sus puntos y sus mejoras se pierden.

## Criterios de aceptación
- Desde el menú principal, «Salir del juego» cierra el juego sin pedir confirmación.
- Desde la pausa, «Salir del juego» pide confirmación.
- Al volver a abrir el juego tras salir, el nivel desbloqueado es el mismo que antes de salir.
