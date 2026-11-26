# CU-06. Atacar la estación

## Identificación
- **Actor principal:** ACT-02
- **Actores secundarios:** ACT-01
- **Objetivo:** Dañar la estación o dificultar el control del jugador.
- **Requisitos relacionados:** RF-08, RF-14, RF-15, RF-19, RF-20, RNF-01, RN-10, RN-11, RN-12, RN-13, RN-14, RN-17, RN-29, RN-30, RN-31, RN-33, RN-34, RN-35, RN-36, RN-38, RN-42, RN-43, RN-48, RES-05, RES-06

## Precondiciones
- Hay una partida en curso.
- El enemigo está activo y en condiciones de atacar.

## Disparador
El enemigo está dentro de su alcance de disparo y ha terminado su tiempo de recarga.

## Flujo principal
1. El enemigo, mientras se mueve dentro de su alcance de disparo, muestra el aviso de disparo: un destello y un sonido de carga durante el tiempo de aviso fijado en los parámetros.
2. El enemigo dispara un proyectil visible hacia la estación.
3. El proyectil viaja hacia la estación. Cuanto más lejos está el enemigo, más tarda en llegar.
4. El proyectil alcanza la estación y el sistema reduce su integridad.
5. El sistema avisa al jugador con un temblor breve de la pantalla y una alarma.
6. El sistema actualiza el indicador de integridad.
7. El enemigo espera su tiempo de recarga antes de volver a atacar.

## Flujos alternativos y excepciones
### A1. Ataque desestabilizador (desde el paso 4)
1. El proyectil es de un desestabilizador.
2. El sistema reduce la integridad menos que con un ataque sin efecto especial.
3. El sistema hace temblar la pantalla y la mira durante el tiempo fijado en los parámetros.
4. Vuelve al paso 6.

### A2. Ataque aturdidor (desde el paso 4)
1. El proyectil es de un aturdidor.
2. El sistema reduce la integridad de la estación.
3. El sistema aturde al jugador durante el tiempo fijado en los parámetros: no puede girar ni disparar, y se le indica que está aturdido. Si estaba apuntando con la mira reducida, la mira y el zoom vuelven a su estado normal (CU-04, A4).
4. Al terminar el aturdimiento, el sistema devuelve el control al jugador.
5. El enemigo espera un tiempo de recarga mayor que el de un enemigo sin efecto especial. Finaliza.

### A3. La estación cae (desde el paso 4)
1. La integridad de la estación llega a cero.
2. El sistema termina la partida y detiene a todos los enemigos y proyectiles.
3. El sistema muestra el resumen de fin de partida con el número de oleadas superadas y la opción de volver a jugar (CU-01, A2).
4. Finaliza.

### A4. Enemigo destruido durante el aviso (desde el paso 1)
1. El jugador destruye al enemigo mientras muestra el aviso de disparo (CU-04).
2. El enemigo no llega a disparar. Finaliza.

### A5. Enemigo destruido con el proyectil en vuelo (desde el paso 3)
1. El jugador destruye al enemigo después de que haya disparado.
2. El proyectil sigue su camino. Vuelve al paso 4.

## Reglas de presentación
- El aviso de disparo debe oírse siempre con claridad, también cuando la niebla o un destello impiden verlo.
- Los proyectiles enemigos son visibles durante todo su recorrido.
- El efecto de daño recibido (paso 5) debe distinguirse del temblor de la desestabilización.
- Los proyectiles de cada tipo de enemigo tienen un color propio, el mismo que el símbolo de ese tipo en el radar.
- Los valores de daño, recarga, aviso y duración de los efectos están en los parámetros iniciales de `reglasNegocio.md`.

## Postcondiciones
- La integridad de la estación queda reducida, o el jugador queda desestabilizado o aturdido.
- Si la integridad llega a cero, la partida queda terminada.

## Criterios de aceptación
- Todo disparo enemigo va precedido de un aviso visible y audible.
- Destruir a un enemigo durante su aviso impide su disparo.
- Un proyectil ya lanzado alcanza la estación aunque su enemigo haya sido destruido.
- Un proyectil disparado desde más lejos tarda más en llegar.
- Cada proyectil que alcanza la estación reduce la integridad y lo muestra el indicador.
- Un ataque desestabilizador reduce menos la integridad que uno sin efecto especial y hace temblar la pantalla y la mira.
- Un ataque aturdidor reduce la integridad.
- Durante el aturdimiento el jugador no puede girar ni disparar, y se le indica que está aturdido.
- Un aturdidor tarda más en volver a atacar que un enemigo sin efecto especial.
- Ningún enemigo choca con la estación, por mucho que se acerque.
- Ningún enemigo dispara desde más lejos que su alcance de disparo.
- Nunca hay más enemigos activos a la vez que el máximo fijado.
- Durante la oleada no se puede reparar la estación: la integridad solo se recupera en la pantalla de mejoras.
- Los enemigos se acercan y se alejan mientras atacan, sin cambios de dirección bruscos.
- Cuando la integridad llega a cero, la partida termina y se muestra el resumen con las oleadas superadas.
