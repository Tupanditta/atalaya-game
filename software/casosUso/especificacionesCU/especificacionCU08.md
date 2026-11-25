# CU-08. Subir el nivel de dificultad

## Identificación
- **Actor principal:** ACT-01
- **Actores secundarios:** ninguno
- **Objetivo:** Jugar una partida nueva más difícil tras haber ganado una.
- **Requisitos relacionados:** RF-25, RF-26, RN-21, RN-22, RN-25, RES-05, RES-06

## Precondiciones
- El jugador acaba de ganar una partida (CU-07, A2).

## Disparador
El jugador elige subir el nivel de dificultad en el resumen de victoria.

## Flujo principal
1. El jugador elige subir el nivel de dificultad.
2. El sistema fija el nivel de dificultad en el siguiente al de la partida ganada.
3. El sistema aumenta la resistencia de todos los enemigos respecto al nivel anterior.
4. El sistema reduce el tiempo de descanso entre oleadas respecto al nivel anterior.
5. El sistema inicia una partida nueva en ese nivel (CU-01, A3).

## Flujos alternativos y excepciones
No se identifican flujos alternativos o excepciones. No hay nivel máximo: siempre se puede subir al siguiente tras ganar.

## Reglas de presentación
- El sistema muestra el nivel de dificultad de la partida. Dónde y cómo está [por definir].

## Postcondiciones
- Hay una partida nueva en curso en el nivel de dificultad siguiente.

## Criterios de aceptación
- Solo se puede subir de nivel tras ganar una partida.
- Siempre se puede subir de nivel tras ganar, sea cual sea el nivel actual.
- En el nivel nuevo, todos los enemigos necesitan más impactos que en el anterior.
- En el nivel nuevo, el descanso entre oleadas es más corto que en el anterior.
- Subir de nivel no cambia nada más: número, tipo, tamaño y velocidad de los enemigos, coste y recarga de energía e integridad de la estación siguen igual que en el nivel anterior.
