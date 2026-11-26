# CU-07. Superar oleada

## Identificación
- **Actor principal:** ACT-01
- **Actores secundarios:** ninguno
- **Objetivo:** Acabar con una oleada y avanzar en la partida.
- **Requisitos relacionados:** RF-09, RF-16, RF-17, RF-18, RF-19, RF-24, RF-26, RF-40, RF-43, RF-45, RN-06, RN-15, RN-16, RN-18, RN-19, RN-20, RN-21, RN-22, RN-25, RN-32, RN-43, RN-44, RN-45, RES-03, RES-05, RES-06, RES-07

## Precondiciones
- Hay una partida en curso con una oleada activa.

## Disparador
El jugador destruye al último enemigo de la oleada.

## Flujo principal
1. El jugador destruye al último enemigo de la oleada (CU-04).
2. El sistema da la oleada por superada y detiene el cronómetro de la oleada.
3. El sistema calcula los puntos de mejora según el tiempo de la oleada y los suma a los puntos disponibles.
4. El número de oleadas superadas es múltiplo de 5, y el sistema cambia el fondo espacial.
5. El sistema empieza el descanso, cuya duración depende del nivel de dificultad, y abre la pantalla de mejoras (CU-11). En ella se presentan la transmisión de radio, el tiempo de la oleada, los puntos obtenidos y la cuenta atrás.
6. Al terminar la cuenta atrás, o cuando el jugador elige continuar, el sistema cierra la pantalla de mejoras.
7. El sistema inicia la siguiente oleada, con una dificultad mayor o igual que la anterior. Sus enemigos aparecen lejos de la estación, de uno en uno, sin superar el máximo de enemigos activos.

## Flujos alternativos y excepciones
### A1. Sin cambio de fondo (desde el paso 4)
1. El número de oleadas superadas no es múltiplo de 5.
2. El sistema mantiene el fondo actual.
3. Vuelve al paso 5.

### A2. Oleada final (desde el paso 2)
1. La oleada superada es la oleada 50.
2. El sistema da la partida por ganada y detiene el juego. No hay descanso ni pantalla de mejoras.
3. Si el nivel siguiente al de la partida es mayor que el nivel más alto desbloqueado, el sistema lo guarda como nuevo nivel más alto desbloqueado.
4. El sistema indica la victoria y muestra el resumen de fin de partida.
5. El sistema ofrece al jugador subir el nivel de dificultad (CU-08) o volver a jugar en el mismo nivel (CU-01, A2).
6. Finaliza.

### A3. Oleada con entorno de baja visibilidad (desde el paso 7)
1. A la nueva oleada le corresponde un entorno de niebla o de destellos.
2. El sistema lo anuncia en la transmisión de radio del descanso y lo activa al empezar la oleada.
3. El entorno dura toda la oleada y se desactiva al superarla. Vuelve al paso 1 cuando se destruye al último enemigo.

## Reglas de presentación
- La música acompaña la intensidad de cada oleada (RF-18).
- La transmisión de radio se presenta como texto en pantalla acompañado de un sonido de radio.
- Durante la cuenta atrás se muestra el número de la oleada que viene.

## Postcondiciones
- La oleada superada se suma al recuento de oleadas superadas.
- Los puntos de mejora obtenidos se suman a los disponibles.
- Si no era la oleada final, hay una nueva oleada activa.
- Si era la oleada final, la partida queda ganada.

## Criterios de aceptación
- La siguiente oleada empieza solo cuando no queda ningún enemigo de la anterior y ha terminado el descanso, o el jugador ha elegido continuar.
- Durante el descanso no hay enemigos activos.
- Superar una oleada en un tiempo menor o igual que el de referencia da 3 puntos; en hasta el doble, 2 puntos; en más tiempo, 1 punto.
- Ningún enemigo aparece cerca de la estación.
- La nueva oleada no es más fácil que la anterior en número o tipo de enemigos.
- El fondo cambia al superar las oleadas 5, 10, 15… y solo entonces.
- Las oleadas 15, 18, 21… se juegan con niebla o destellos, alternando, y las demás no.
- Superar la oleada 50 da la partida por ganada y ofrece subir el nivel de dificultad.
- Tras ganar, el nivel desbloqueado se conserva al cerrar y volver a abrir el juego.
