# CU-04. Disparar

## Identificación
- **Actor principal:** ACT-01
- **Actores secundarios:** ninguno
- **Objetivo:** Dañar o destruir a un enemigo.
- **Requisitos relacionados:** RF-05, RF-06, RF-11, RF-12, RF-13, RNF-01, RNF-02, RNF-03, RNF-05, RF-28, RN-03, RN-04, RN-05, RN-06, RN-07, RN-12, RN-13, RN-22, RN-23, RES-03, RES-04, RES-05, RES-06

## Precondiciones
- Hay una partida en curso.

## Disparador
El jugador pulsa la barra espaciadora.

## Flujo principal
1. El jugador pulsa la barra espaciadora.
2. El sistema comprueba que el jugador no está aturdido y que la energía disponible cubre el coste del disparo.
3. El sistema descuenta el coste del disparo de la energía y actualiza la barra de energía.
4. El sistema lanza el disparo hacia la posición de la mira, con su efecto visual y sonoro. El disparo alcanza al instante el punto de la mira, sin tiempo de viaje.
5. En ese punto hay un enemigo, y el sistema reduce su vida.
6. La vida del enemigo llega a cero: el sistema lo destruye, muestra la explosión con su sonido y lo retira del radar.

## Flujos alternativos y excepciones
### A1. Energía insuficiente (desde el paso 2)
1. La energía disponible no cubre el coste del disparo.
2. El sistema no dispara y avisa al jugador con un efecto visual y sonoro.
3. Finaliza.

### A2. Jugador aturdido (desde el paso 2)
1. El jugador está aturdido.
2. El sistema no dispara y no descuenta energía.
3. Finaliza.

### A3. Disparo fallido (desde el paso 5)
1. El disparo no alcanza a ningún enemigo.
2. Finaliza. La energía gastada no se recupera.

### A4. Enemigo dañado (desde el paso 6)
1. La vida del enemigo sigue por encima de cero.
2. El sistema muestra que el enemigo ha recibido el impacto.
3. Finaliza.

## Reglas de presentación
- El disparo se ve como un rayo que va de la estación al punto de impacto y desaparece enseguida.
- El rayo y el impacto aparecen en el primer fotograma tras la pulsación.
- Cada pulsación es un disparo. Mantener pulsada la barra espaciadora no dispara en ráfaga.
- Se puede disparar mientras se gira la vista.
- La energía sigue recargándose después de disparar.

## Postcondiciones
- La energía queda reducida en el coste del disparo.
- Si el disparo acierta, el enemigo pierde vida o queda destruido.

## Criterios de aceptación
- Con energía suficiente, pulsar la barra espaciadora dispara hacia la mira y reduce la energía.
- Con energía insuficiente, pulsarla no dispara, no cambia la energía y muestra el aviso.
- Aturdido, pulsarla no dispara ni cambia la energía.
- Mantener pulsada la barra espaciadora produce un solo disparo.
- Un enemigo cuya vida llega a cero explota y desaparece del radar.
- Un enemigo grande necesita más impactos que uno pequeño para ser destruido.
- Un mismo tipo de enemigo necesita más impactos en un nivel de dificultad mayor.
- El impacto se produce en el punto de la mira en el momento de la pulsación, aunque el enemigo se mueva justo después.
