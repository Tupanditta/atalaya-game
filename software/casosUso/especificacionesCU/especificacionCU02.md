# CU-02. Girar la vista

## Identificación
- **Actor principal:** ACT-01
- **Actores secundarios:** ninguno
- **Objetivo:** Orientar la vista hacia la dirección que quiere vigilar y colocar la mira sobre el objetivo al que quiere disparar.
- **Requisitos relacionados:** RF-02, RF-03, RF-21, RF-33, RF-46, RNF-01, RNF-02, RNF-03, RNF-04, RN-01, RN-12, RN-13, RN-26, RN-29, RN-33, RN-39, RN-40, RN-41, RES-02, RES-04, RES-05, RES-06

## Precondiciones
- Hay una partida en curso.

## Disparador
El jugador pulsa una flecha del teclado o su tecla equivalente (W, A, S o D). En este caso de uso, «flecha» incluye siempre su tecla equivalente.

## Flujo principal
1. El jugador mantiene pulsada una flecha: izquierda o derecha para girar en horizontal, arriba o abajo para girar en vertical.
2. El sistema gira la vista en ese sentido respecto a la propia cámara, de forma continua, mientras la flecha siga pulsada, sin mover la posición de la estación. La mira conserva su posición en la pantalla, así que gira con la vista.
3. El jugador suelta la flecha.
4. El sistema detiene el giro y mantiene la orientación alcanzada.

## Flujos alternativos y excepciones
### A1. Giro combinado (desde el paso 1)
1. El jugador mantiene pulsadas a la vez una flecha lateral y una vertical (por ejemplo, arriba y derecha).
2. El sistema gira la vista en horizontal y en vertical al mismo tiempo, en diagonal.
3. Si el jugador suelta una de las dos flechas, el sistema sigue girando solo en el sentido de la que sigue pulsada, sin detenerse ni saltar.
4. Vuelve al paso 3.

### A2. Flechas opuestas (desde el paso 1)
1. El jugador pulsa a la vez dos flechas opuestas de un mismo eje (izquierda y derecha, o arriba y abajo).
2. El sistema no gira la vista en ese eje.
3. Si además hay una flecha pulsada en el otro eje, el sistema gira la vista solo en ese otro eje (por ejemplo, con arriba, izquierda y derecha, solo hacia arriba).
4. Si están pulsadas las cuatro flechas, el sistema no gira la vista.
5. Cuando el jugador suelta una de las flechas opuestas, el sistema gira en el sentido de la que sigue pulsada. Vuelve al paso 2 del flujo principal.

### A3. Pantalla desestabilizada (desde el paso 2)
1. El jugador está bajo el efecto de un ataque desestabilizador.
2. El sistema hace temblar la pantalla y la mira, que se desvía de la posición donde la tiene el jugador. El giro sigue respondiendo a las flechas.
3. Cuando termina el efecto, la mira vuelve a esa posición y la pantalla deja de temblar. Vuelve al paso 2.

### A4. Jugador aturdido (desde el paso 1)
1. El jugador está aturdido.
2. El sistema ignora las flechas y mantiene la orientación actual.
3. Cuando termina el aturdimiento, vuelve al paso 1.

### A5. Mover la mira con el ratón (en cualquier momento de la oleada)
1. El jugador mueve el ratón.
2. El sistema desplaza la mira por la pantalla siguiendo el ratón, sin girar la vista. La mira no sale de la pantalla.
3. El disparo sale hacia el punto de la escena que hay bajo la mira (CU-04). Vuelve al paso en que estaba.

## Reglas de presentación
- El radar se actualiza con la nueva orientación mientras la vista gira.
- La velocidad de giro es la fijada en los parámetros iniciales de `reglasNegocio.md`, y se reduce con el zoom (RN-40).

## Postcondiciones
- La vista queda orientada en la dirección elegida. La posición de la estación no cambia.

## Criterios de aceptación
- Mantener pulsada una flecha gira la vista en ese sentido; soltarla detiene el giro.
- La mira sigue al ratón por la pantalla y nunca sale de ella; mover el ratón no gira la vista.
- Al girar la vista con las flechas, la mira conserva su posición en la pantalla.
- Durante la desestabilización, la mira y la pantalla tiemblan; al terminar el efecto, la mira vuelve a la posición que marca el ratón.
- El giro no tiene tope ni en horizontal ni en vertical: se puede dar la vuelta completa en ambos ejes y en ambos sentidos.
- Pulsar una flecha lateral y una vertical a la vez gira la vista en diagonal.
- El giro es continuo, sin saltos, también al pulsar o soltar la segunda flecha.
- Con izquierda y derecha pulsadas a la vez, la vista no gira en horizontal; con arriba y abajo, no gira en vertical.
- Con arriba, izquierda y derecha pulsadas, la vista solo gira hacia arriba.
- Con las cuatro flechas pulsadas, la vista no gira.
- Girar nunca desplaza la posición de la estación.
- Con zoom, la vista gira más despacio que sin zoom.
- Tras una vuelta vertical completa, la vista vuelve a la orientación inicial.
- Tras media vuelta vertical, la flecha derecha sigue girando la imagen hacia la derecha de la pantalla.
- Mientras el jugador está aturdido, las flechas no tienen efecto.
