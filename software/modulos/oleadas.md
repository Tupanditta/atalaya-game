# Módulo oleadas

- **Capa:** lógica
- **Cubre:** CU-07; RF-09, RF-24; RN-15, RN-16, RN-18, RN-19, RN-22, RN-43

## Responsabilidad
Organizar la partida en oleadas: qué enemigos tiene cada una, cuándo aparecen, cuándo termina la oleada, el descanso y la victoria.

## Estado que gestiona
- El número de la oleada actual (1 a 50) y el nivel de dificultad.
- La lista de enemigos pendientes de aparecer en la oleada: tipo, tamaño y vida según el nivel.
- El número de enemigos activos y el tiempo hasta la siguiente aparición.
- El cronómetro de la oleada: desde que aparece el primer enemigo hasta que se destruye el último.
- La fase: oleada en curso o descanso, y el tiempo restante de descanso.

## Composición de una oleada
Usa los cálculos de `parametros`:
- número de enemigos según el número de oleada,
- tamaños al azar,
- desestabilizadores desde la oleada 5 y aturdidores desde la 10, sin superar un tercio de la oleada.

El orden de aparición se baraja con el azar del núcleo.

## Operaciones
- **Actualizar:**
  - Durante la oleada, cada 2 s, si hay menos enemigos activos que el máximo y quedan pendientes, publica SolicitudAparicion con el siguiente (RN-43).
  - Durante el descanso, descuenta el tiempo. Al llegar a cero, publica DescansoTerminado e inicia la siguiente oleada.
- **Consultar:**
  - número de oleada,
  - enemigos restantes,
  - cronómetro,
  - fase y tiempo restante de descanso.

## Reglas que aplica
1. Al recibir EnemigoDestruido, resta uno a los activos. Si no quedan activos ni pendientes, la oleada está superada (RN-15).
   - Si era la oleada 50, publica PartidaGanada (RN-19).
   - Si no, publica OleadaSuperada con el tiempo de la oleada, y después DescansoIniciado con la duración del descanso del nivel (RN-18, RN-22).
2. Al recibir TerminarDescansoSolicitado, termina el descanso en ese momento.
3. Al iniciar una oleada, publica OleadaIniciada con su número y el entorno que le corresponde, que obtiene de `parametros` a partir del número de oleada.

## Eventos
- Publica: OleadaIniciada, SolicitudAparicion, OleadaSuperada, DescansoIniciado, DescansoTerminado, PartidaGanada.
- Escucha:
  - PartidaIniciada, que empieza la oleada 1 con el nivel recibido,
  - EnemigoDestruido, TerminarDescansoSolicitado,
  - PartidaAbandonada y EstacionDestruida, que detienen las oleadas.

## Depende de
nucleo, parametros.

## No hace
- No mueve enemigos ni sabe dónde están.
- No calcula puntos de mejora: publica el tiempo y `mejoras` hace el cálculo.
