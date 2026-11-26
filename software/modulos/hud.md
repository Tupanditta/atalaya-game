# Módulo hud

- **Capa:** presentación
- **Cubre:** CU-01, CU-05, CU-08 a CU-12 (presentación); RF-06, RF-07, RF-08, RF-11, RF-15, RF-16, RF-19, RF-22, RF-23, RF-24, RF-31, RF-46, RF-34, RF-39, RF-40, RF-43

## Responsabilidad
Dibujar todo lo que va encima de la escena 3D: la mira, los indicadores, el radar, las transmisiones, los menús y las pantallas.

## Durante una oleada
- **Mira:** círculo con el tamaño de `armamento`, en la posición de la pantalla que marca `vista` (el ratón), desplazado por el desvío de `vista` durante la desestabilización.
- **Radar:** contactos de `radar` con su símbolo, color, tamaño y marca de altura, y el sector del campo de visión.
- **Energía:** barra con la energía actual y máxima. Parpadea al recibir DisparoSinEnergia.
- **Integridad:** barra con la integridad actual y máxima, y el nivel de dificultad al lado.
- **Oleada:** número de oleada y enemigos restantes.
- **Aturdimiento:** un aviso visible mientras dura (RF-15).
- El radar y los indicadores no cambian de tamaño con el zoom y no se ven afectados por la niebla ni por los destellos.

## Pantallas
- **Menú principal:** Jugar, Manual, Salir del juego.
- **Selección de nivel:** niveles disponibles, con el seleccionado resaltado.
- **Pantalla de mejoras:** según CU-11; incluye la transmisión de radio y la cuenta atrás.
- **Pausa y confirmaciones:** según CU-09 y CU-12.
- **Manual:** según CU-10, con valores tomados de `parametros`.
- **Resumen de fin de partida:** victoria o derrota, oleadas superadas, nivel y opciones según CU-07 y CU-08.
- **Transmisión de inicio:** texto superpuesto al empezar la partida, que desaparece a los 6 s.

## Operaciones
- **Dibujar:** una vez por fotograma, consultando el estado de la lógica.

## Eventos
- Publica: ninguno.
- Escucha:
  - PausaCambiada,
  - DisparoSinEnergia, EnergiaCambiada, IntegridadCambiada,
  - AturdimientoIniciado, AturdimientoTerminado,
  - DesestabilizacionIniciada, DesestabilizacionTerminada,
  - OleadaIniciada, DescansoIniciado, PuntosObtenidos, MejoraAplicada,
  - TransmisionDisponible, PartidaIniciada.

## Depende de
El motor gráfico; vista, radar, armamento, estacion, oleadas, mejoras, historia, flujo, progreso y parametros (solo lectura).

## No hace
- No decide qué pantalla toca ni qué hace cada opción: lo decide `flujo`.
- La disposición exacta de los elementos y su estilo se especifican en `interfaz/`.
