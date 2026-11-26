# CU-04. Disparar

## Identificación
- **Actor principal:** ACT-01
- **Actores secundarios:** ninguno
- **Objetivo:** Dañar o destruir a un enemigo.
- **Requisitos relacionados:** RF-05, RF-06, RF-11, RF-12, RF-13, RF-28, RF-32, RF-33, RNF-01, RNF-02, RNF-03, RNF-05, RN-03, RN-04, RN-05, RN-06, RN-07, RN-12, RN-13, RN-22, RN-23, RN-29, RN-37, RN-38, RN-39, RN-40, RES-03, RES-04, RES-05, RES-06

## Precondiciones
- Hay una partida en curso.

## Disparador
El jugador pulsa la barra espaciadora.

## Flujo principal
1. El jugador pulsa la barra espaciadora y la mantiene pulsada.
2. El sistema reduce la mira y acerca la imagen (zoom) de forma continua.
3. El jugador gira la vista para mantener al enemigo dentro de la mira (CU-02). Cuanto mayor es el zoom, más lento es el giro.
4. La mira llega a su tamaño mínimo. El sistema deja de reducirla y mantiene el zoom máximo.
5. El jugador suelta la barra espaciadora.
6. El sistema comprueba que el jugador no está aturdido y que la energía disponible cubre el coste del disparo.
7. El sistema descuenta el coste del disparo de la energía y actualiza la barra de energía.
8. El sistema elige al azar un punto dentro de la mira, tal como está en ese momento, y lanza el disparo hacia él con su efecto visual y sonoro. El disparo alcanza ese punto al instante.
9. El sistema devuelve la mira y el zoom a su estado normal de forma suave.
10. En el punto de impacto hay un enemigo, y el sistema reduce su vida.
11. La vida del enemigo llega a cero: el sistema lo destruye, muestra la explosión con su sonido y lo retira del radar.

## Flujos alternativos y excepciones
### A1. Soltar antes del tamaño mínimo (desde el paso 3)
1. El jugador suelta la barra espaciadora antes de que la mira llegue a su tamaño mínimo. Un toque corto deja la mira casi en su tamaño normal.
2. El sistema usa el tamaño de mira alcanzado en ese momento. Vuelve al paso 6.

### A2. Energía insuficiente (desde el paso 6)
1. La energía disponible no cubre el coste del disparo.
2. El sistema no dispara y avisa al jugador con un efecto visual y sonoro.
3. El sistema devuelve la mira y el zoom a su estado normal. Finaliza.

### A3. Jugador aturdido al pulsar (desde el paso 1)
1. El jugador está aturdido.
2. El sistema no reduce la mira, no aplica zoom y no dispara al soltar. Finaliza.

### A4. Aturdido mientras apunta (desde los pasos 2 a 4)
1. El jugador queda aturdido con la barra pulsada.
2. El sistema devuelve la mira y el zoom a su estado normal y cancela el disparo.
3. Para volver a apuntar, el jugador debe soltar la barra y pulsarla de nuevo cuando termine el aturdimiento. Finaliza.

### A5. Disparo fallido (desde el paso 10)
1. En el punto de impacto no hay ningún enemigo.
2. Finaliza. La energía gastada no se recupera.

### A6. Enemigo dañado (desde el paso 11)
1. La vida del enemigo sigue por encima de cero.
2. El sistema muestra que el enemigo ha recibido el impacto.
3. Finaliza.

## Reglas de presentación
- La mira es un círculo cuyo tamaño muestra la zona donde puede caer el disparo.
- La reducción de la mira y el zoom son continuos, sin saltos.
- El radar, la barra de energía y la integridad no cambian de tamaño con el zoom.
- El disparo se ve como un rayo que va de la estación al punto de impacto y desaparece enseguida.
- El rayo y el impacto aparecen en el primer fotograma tras soltar la barra espaciadora.
- Mientras se mantiene la barra pulsada no se gasta energía, y la energía sigue recargándose.
- Cada pulsación produce como mucho un disparo. Mantener pulsada la barra no dispara en ráfaga.
- Se puede apuntar y disparar mientras se gira la vista.

## Postcondiciones
- La energía queda reducida en el coste del disparo.
- La mira y el zoom vuelven a su estado normal.
- Si el disparo acierta, el enemigo pierde vida o queda destruido.

## Criterios de aceptación
- Mantener pulsada la barra espaciadora reduce la mira y acerca la imagen hasta el tamaño mínimo, y no más.
- El disparo sale al soltar la barra, no al pulsarla.
- El punto de impacto siempre cae dentro de la mira, tal como está al soltar.
- Con la mira al mínimo, los disparos caen más agrupados que con la mira normal.
- Con zoom, el giro es más lento que sin zoom.
- Tras el disparo, la mira y el zoom vuelven a su estado normal.
- Con energía insuficiente, soltar la barra no dispara, no cambia la energía y muestra el aviso.
- Aturdido, no se puede reducir la mira ni disparar. Si el aturdimiento llega mientras se apunta, la mira y el zoom vuelven a su estado normal y no hay disparo.
- Un enemigo cuya vida llega a cero explota y desaparece del radar.
- Un enemigo grande necesita más impactos que uno pequeño para ser destruido.
- Un mismo tipo de enemigo necesita más impactos en un nivel de dificultad mayor.
