# Catálogo de casos de uso

## Actores
| ID | Nombre | Descripción |
|---|---|---|
| ACT-01 | Jugador | Persona que controla al artillero de la estación |
| ACT-02 | Enemigo | Nave hostil, controlada por el juego, que ataca la estación |

## Casos de uso
| ID | Título | Actores | Objetivo |
|---|---|---|---|
| CU-01 | Iniciar partida | ACT-01 | Que el jugador empiece una partida nueva |
| CU-02 | Girar la vista | ACT-01 | Que el jugador oriente la vista y la mira hacia la dirección que quiere vigilar o el objetivo al que quiere disparar |
| CU-03 | Apuntar (eliminado) | — | Integrado en CU-02: se apunta girando la vista y moviendo la mira con el ratón |
| CU-04 | Disparar | ACT-01 | Que el jugador dañe o destruya a un enemigo |
| CU-05 | Localizar enemigos | ACT-01 | Que el jugador sepa dónde están los enemigos, incluidos los que están fuera de la vista |
| CU-06 | Atacar la estación | ACT-02, ACT-01 | Que un enemigo dañe la estación o dificulte el control del jugador |
| CU-07 | Superar oleada | ACT-01 | Que el jugador acabe con una oleada y avance en la partida |
| CU-08 | Subir el nivel de dificultad | ACT-01 | Que el jugador juegue una partida más difícil tras ganar una |
| CU-09 | Pausar la partida | ACT-01 | Que el jugador detenga la partida y decida si seguir, consultar el manual, abandonar o salir |
| CU-10 | Consultar el manual | ACT-01 | Que el jugador conozca los controles, los enemigos, los entornos y las mejoras |
| CU-11 | Mejorar y reparar la estación | ACT-01 | Que el jugador gaste sus puntos de mejora entre oleadas |
| CU-12 | Salir del juego | ACT-01 | Que el jugador cierre el juego |
