# CU-01. Iniciar partida

## Identificación
- **Actor principal:** ACT-01
- **Actores secundarios:** ninguno
- **Objetivo:** Empezar una partida nueva.
- **Requisitos relacionados:** RF-01, RF-06, RF-07, RF-08, RF-09, RF-16, RF-18, RF-20, RF-27, RF-34, RNF-03, RN-02, RN-24, RN-25, RN-32, RN-49, RES-01, RES-04, RES-05, RES-06, RES-07

## Precondiciones
- El juego está abierto en el menú principal y no hay una partida en curso.

## Disparador
El jugador elige «Jugar» en el menú principal.

## Flujo principal
1. El jugador elige «Jugar» en el menú principal.
2. El sistema muestra los niveles de dificultad disponibles, del 1 al nivel más alto desbloqueado, con el más alto ya seleccionado.
3. El jugador elige un nivel o acepta el seleccionado.
4. El sistema fija el nivel elegido y pone la energía y la integridad de la estación al máximo.
5. El sistema muestra la vista desde la estación con la mira, el radar, la barra de energía y la integridad de la estación.
6. El sistema presenta la transmisión de radio inicial de la historia.
7. El sistema inicia la primera oleada de enemigos, que aparecen lejos de la estación.

## Flujos alternativos y excepciones
### A1. Solo hay un nivel disponible (desde el paso 2)
1. El nivel más alto desbloqueado es 1.
2. El sistema no pide elegir nivel y fija el nivel 1.
3. Vuelve al paso 4.

### A2. Volver a jugar (desde el paso 1)
1. El jugador elige volver a jugar en el resumen de fin de partida.
2. El sistema descarta el estado de la partida anterior y mantiene su nivel de dificultad, sin pedir elegir nivel.
3. Vuelve al paso 4.

### A3. Partida en un nivel superior (desde el paso 1)
1. El jugador ha elegido subir el nivel de dificultad tras ganar una partida (CU-08).
2. El sistema descarta el estado de la partida anterior y fija el nuevo nivel, sin pedir elegir nivel.
3. Vuelve al paso 4.

### A4. Dato guardado ilegible (desde el paso 2)
1. El nivel más alto desbloqueado no existe o no se puede leer.
2. El sistema toma el nivel 1 como nivel más alto desbloqueado, sin mostrar un error que bloquee el juego (ver `basesDatos/especificacion.md`).
3. Continúa en A1.

### A5. Volver al menú (desde el paso 3)
1. El jugador pulsa Esc en la selección de nivel.
2. El sistema vuelve al menú principal sin empezar la partida. Finaliza.

## Reglas de presentación
- La mira, el radar, la barra de energía y la integridad de la estación son visibles durante toda la partida.
- La mira está en el centro de la pantalla. El radar, la barra de energía, la integridad y el nivel de dificultad se colocan en los bordes, sin tapar el centro. La disposición exacta se especifica en `interfaz/`.

## Postcondiciones
- Hay una partida en curso en el nivel elegido, con la primera oleada activa y la energía y la integridad al máximo.

## Criterios de aceptación
- Al empezar una partida, la energía y la integridad se muestran al máximo.
- Al empezar una partida, la mira, el radar, la barra de energía y la integridad son visibles.
- Antes de la primera oleada se presenta la transmisión de radio inicial.
- La primera vez que se abre el juego, la partida empieza en el nivel 1 sin pedir elegir nivel.
- La partida empieza sin puntos de mejora ni mejoras.
- En la selección de nivel, el nivel se cambia con las flechas, se confirma con Intro y Esc vuelve al menú principal.
- Con varios niveles desbloqueados, solo se ofrecen niveles del 1 al más alto desbloqueado, y el más alto aparece seleccionado.
- Al volver a jugar desde el resumen, la partida nueva conserva solo el nivel de dificultad de la anterior.
- Si el dato guardado está dañado, el juego arranca en el nivel 1 sin bloquearse.
