# CU-07. Superar oleada

## Identificación
- **Actor principal:** ACT-01
- **Actores secundarios:** ninguno
- **Objetivo:** Acabar con una oleada y avanzar en la partida.
- **Requisitos relacionados:** RF-09, RF-16, RF-17, RF-18, RF-19, RF-24, RN-06, RN-15, RN-16, RN-18, RN-19, RN-20, RN-21, RN-22, RN-25, RF-26, RES-03, RES-07, RES-05, RES-06

## Precondiciones
- Hay una partida en curso con una oleada activa.

## Disparador
El jugador destruye al último enemigo de la oleada.

## Flujo principal
1. El jugador destruye al último enemigo activo de la oleada (CU-04).
2. El sistema da la oleada por superada.
3. El sistema empieza el descanso entre oleadas, cuya duración depende del nivel de dificultad.
4. Durante el descanso, el sistema presenta una transmisión de radio que hace avanzar la historia.
5. El número de oleadas superadas es múltiplo de 5, y el sistema cambia el fondo espacial.
6. Al terminar el descanso, el sistema inicia la siguiente oleada, con una dificultad mayor o igual que la anterior.

## Flujos alternativos y excepciones
### A1. Sin cambio de fondo (desde el paso 5)
1. El número de oleadas superadas no es múltiplo de 5.
2. El sistema mantiene el fondo actual.
3. Vuelve al paso 6.

### A2. Oleada final (desde el paso 2)
1. La oleada superada es la oleada 50.
2. El sistema da la partida por ganada y detiene el juego.
3. Si el nivel siguiente al de la partida es mayor que el nivel más alto desbloqueado, el sistema lo guarda como nuevo nivel más alto desbloqueado.
4. El sistema indica la victoria y muestra el resumen de fin de partida.
5. El sistema ofrece al jugador subir el nivel de dificultad (CU-08) o volver a jugar en el mismo nivel (CU-01, A2).
6. Finaliza.

## Reglas de presentación
- La música acompaña la intensidad de cada oleada (RF-18, propuesto).
- Cómo se presenta el descanso, por ejemplo con una cuenta atrás, está [por definir].

## Postcondiciones
- La oleada superada se suma al recuento de oleadas superadas.
- Si no era la oleada final, hay una nueva oleada activa.
- Si era la oleada final, la partida queda ganada.

## Criterios de aceptación
- La siguiente oleada empieza solo cuando no queda ningún enemigo activo de la anterior y ha terminado el descanso.
- Durante el descanso no hay enemigos activos.
- Durante cada descanso se presenta una transmisión de radio.
- La nueva oleada no es más fácil que la anterior en número, tipo o velocidad de enemigos.
- El fondo cambia al superar las oleadas 5, 10, 15… y solo entonces.
- Superar la oleada 50 da la partida por ganada y ofrece subir el nivel de dificultad.
- Tras ganar, el nivel desbloqueado se conserva al cerrar y volver a abrir el juego.
