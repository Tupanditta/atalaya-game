# Módulo flujo

- **Capa:** lógica
- **Cubre:** CU-01, CU-07 (paso 6), CU-08, CU-09, CU-10, CU-11, CU-12; RF-01, RF-19, RF-20, RF-24, RF-25, RF-27, RF-34 a RF-39, RF-44; RN-24, RN-48, RN-50

## Responsabilidad
Saber en qué pantalla está el juego y decidir qué hace cada acción del jugador en esa pantalla.

## Estado que gestiona
- La pantalla actual:
  - menú principal,
  - selección de nivel,
  - oleada en curso,
  - descanso (pantalla de mejoras),
  - pausa,
  - manual,
  - confirmación,
  - resumen de fin de partida.
- La pantalla anterior, para volver desde el manual o desde una confirmación.
- La opción seleccionada en el menú visible.
- El nivel de la partida en curso.

## Transiciones

| Desde | Acción o evento | Hacia |
|---|---|---|
| menú principal | Jugar | selección de nivel (o partida directamente si solo existe el nivel 1) |
| menú principal | Manual | manual |
| menú principal | Salir del juego | cierre del juego |
| selección de nivel | Intro | oleada en curso (publica PartidaIniciada) |
| selección de nivel | Esc | menú principal |
| oleada en curso / descanso | Esc | pausa (pausa el reloj) |
| pausa | Continuar o Esc | pantalla anterior (reanuda el reloj) |
| pausa | Manual | manual |
| pausa | Abandonar / Salir del juego | confirmación |
| confirmación | Sí | menú principal o cierre, según lo confirmado |
| confirmación | No o Esc | pausa |
| manual | Esc | pantalla anterior |
| oleada en curso | DescansoIniciado | descanso |
| descanso | Continuar | publica TerminarDescansoSolicitado |
| descanso | DescansoTerminado | oleada en curso |
| oleada en curso | EstacionDestruida o PartidaGanada | resumen de fin de partida |
| resumen | Volver a jugar | oleada en curso, con el mismo nivel |
| resumen | Subir nivel (solo tras victoria) | oleada en curso, con el nivel siguiente |
| resumen | Menú principal | menú principal |

## Operaciones
- **Actualizar:** lee las acciones de `entrada`.
  - Durante una oleada, entrega los ejes de giro a `vista` y el estado de la barra espaciadora a `armamento`.
  - En los menús, mueve la selección o ejecuta la opción elegida.
- En la pantalla de mejoras, ejecuta en `mejoras` la opción elegida (reparar o mejorar).
- Al pausar con la barra espaciadora pulsada, ordena a `armamento` cancelar el apuntado.
- **Consultar:** pantalla actual, opción seleccionada y cuántas veces ha tocado cada sonido de menú (mover, confirmar, error), que `audio` usa para sonar.

## Eventos
- Publica: PartidaIniciada, PartidaAbandonada, PausaCambiada, TerminarDescansoSolicitado.
- Escucha: DescansoIniciado, DescansoTerminado, EstacionDestruida, PartidaGanada, OleadaSuperada.

## Depende de
nucleo (reloj y eventos), parametros, entrada, vista, armamento, mejoras, oleadas, progreso.

## No hace
- No aplica reglas de juego: no calcula daño, puntos ni energía.
- No dibuja las pantallas; `hud` las dibuja consultando a `flujo`.
