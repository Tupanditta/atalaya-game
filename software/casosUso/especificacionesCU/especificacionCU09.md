# CU-09. Pausar la partida

## Identificación
- **Actor principal:** ACT-01
- **Actores secundarios:** ninguno
- **Objetivo:** Detener la partida un momento y decidir si seguir, consultar el manual, abandonar o salir.
- **Requisitos relacionados:** RF-35, RF-36, RF-37, RF-38, RF-39, RNF-03, RN-04, RN-38, RN-50, RES-04, RES-05, RES-06

## Precondiciones
- Hay una partida en curso, durante una oleada o durante el descanso.

## Disparador
El jugador pulsa Esc.

## Flujo principal
1. El jugador pulsa Esc.
2. El sistema detiene el tiempo del juego y muestra el menú de pausa con las opciones «Continuar», «Manual», «Abandonar partida» y «Salir del juego». «Continuar» aparece seleccionada.
3. El jugador elige «Continuar».
4. El sistema cierra el menú de pausa y reanuda el tiempo del juego en el mismo punto en que se detuvo.

## Flujos alternativos y excepciones
### A1. Apuntando al pausar (desde el paso 1)
1. El jugador tenía la barra espaciadora pulsada y la mira reducida.
2. El sistema cancela el apuntado sin disparar y devuelve la mira y el zoom a su estado normal.
3. Vuelve al paso 2.

### A2. Esc en el menú de pausa (desde el paso 3)
1. El jugador pulsa Esc otra vez.
2. Vuelve al paso 4.

### A3. Consultar el manual (desde el paso 3)
1. El jugador elige «Manual».
2. El sistema muestra el manual (CU-10).
3. Al salir del manual, vuelve al paso 2.

### A4. Abandonar la partida (desde el paso 3)
1. El jugador elige «Abandonar partida».
2. El sistema pide confirmación con las opciones «Sí» y «No». «No» aparece seleccionada.
3. El jugador elige «Sí».
4. El sistema descarta la partida en curso sin cambiar el nivel desbloqueado y muestra el menú principal. Finaliza.

### A5. No confirmar el abandono (desde el paso 3 de A4)
1. El jugador elige «No» o pulsa Esc.
2. Vuelve al paso 2.

### A6. Salir del juego (desde el paso 3)
1. El jugador elige «Salir del juego».
2. Deriva a CU-12.

## Reglas de presentación
- El menú de pausa se muestra encima de la escena detenida, que sigue visible y oscurecida.
- Las opciones se recorren con las flechas arriba y abajo y se eligen con Intro.
- Durante la pausa no suena la música de combate ni ningún efecto de la partida.

## Postcondiciones
- Si el jugador continúa, la partida sigue exactamente como estaba.
- Si abandona, no hay partida en curso y el juego está en el menú principal.

## Criterios de aceptación
- Al pulsar Esc durante una oleada o un descanso, todo se detiene: enemigos, proyectiles, energía, efectos, cronómetro y cuenta atrás.
- Al continuar, los enemigos, los proyectiles y la energía están exactamente donde se quedaron.
- Pausar con la mira reducida no produce ningún disparo.
- Abandonar exige confirmación y no cambia el nivel desbloqueado.
