# CU-06. Atacar la estación

## Identificación
- **Actor principal:** ACT-02
- **Actores secundarios:** ACT-01
- **Objetivo:** Dañar la estación o dificultar el control del jugador.
- **Requisitos relacionados:** RF-08, RF-14, RF-15, RF-19, RF-20, RNF-01, RN-10, RN-11, RN-12, RN-13, RN-14, RN-17, RES-05, RES-06

## Precondiciones
- Hay una partida en curso.
- El enemigo está activo y en condiciones de atacar.

## Disparador
El enemigo lanza un ataque contra la estación.

## Flujo principal
1. El enemigo lanza un ataque que alcanza la estación.
2. El sistema reduce la integridad de la estación.
3. El sistema avisa al jugador con un temblor breve de la pantalla y una alarma.
4. El sistema actualiza el indicador de integridad.
5. El enemigo espera su tiempo de recarga antes de volver a atacar.

## Flujos alternativos y excepciones
### A1. Ataque desestabilizador (desde el paso 2)
1. El enemigo es un desestabilizador.
2. El sistema reduce la integridad menos que con un ataque sin efecto especial.
3. El sistema hace temblar la pantalla y la mira durante un tiempo [por definir].
4. Vuelve al paso 4.

### A2. Ataque aturdidor (desde el paso 2)
1. El enemigo es un aturdidor.
2. El sistema reduce la integridad de la estación.
3. El sistema aturde al jugador durante un tiempo [por definir]: no puede girar ni disparar, y se le indica que está aturdido.
4. Al terminar el aturdimiento, el sistema devuelve el control al jugador.
5. El enemigo espera un tiempo de recarga mayor que el de un enemigo sin efecto especial. Finaliza.

### A3. La estación cae (desde el paso 2)
1. La integridad de la estación llega a cero.
2. El sistema termina la partida y detiene a todos los enemigos.
3. El sistema muestra el resumen de fin de partida con el número de oleadas superadas y la opción de volver a jugar (CU-01, A2).
4. Finaliza.

### A4. Enemigo destruido antes de atacar (desde el paso 1)
1. El jugador destruye al enemigo antes de que su ataque alcance la estación (CU-04).
2. El ataque no se produce. Finaliza.

## Reglas de presentación
- El efecto de daño recibido (paso 3) debe distinguirse del temblor de la desestabilización.

## Postcondiciones
- La integridad de la estación queda reducida, o el jugador queda desestabilizado o aturdido.
- Si la integridad llega a cero, la partida queda terminada.

## Criterios de aceptación
- Cada ataque que alcanza la estación reduce la integridad y lo muestra el indicador.
- Un ataque desestabilizador reduce menos la integridad que uno sin efecto especial y hace temblar la pantalla y la mira.
- Un ataque aturdidor reduce la integridad.
- Durante el aturdimiento el jugador no puede girar ni disparar, y se le indica que está aturdido.
- Un aturdidor tarda más en volver a atacar que un enemigo sin efecto especial.
- Cuando la integridad llega a cero, la partida termina y se muestra el resumen con las oleadas superadas.
