# Módulo entorno

- **Capa:** lógica
- **Cubre:** CU-07 (A1, A3); RF-17, RF-45; RN-20, RN-44

## Responsabilidad
Decidir qué fondo espacial se ve y si la oleada tiene niebla o destellos, y calcular cuánto se ve cada cosa en cada momento.

## Estado que gestiona
- El índice del fondo actual, de 1 a 10.
- El entorno de la oleada actual: ninguno, niebla o destellos.
- En los destellos, la fase actual (calma, aviso o deslumbramiento) y el tiempo restante de esa fase.

## Operaciones
- **Actualizar:** en los destellos, avanza las fases. Al terminar la calma (un intervalo al azar entre 12 y 20 s) empieza el aviso; al terminar el aviso empieza el deslumbramiento; al terminar este vuelve la calma.
- **Consultar:**
  - fondo actual,
  - entorno actual,
  - **visibilidad a una distancia** (de 0 a 1, según la niebla),
  - **intensidad del deslumbramiento** (de 0 a 1, según la fase del destello).

## Reglas que aplica
- Al recibir OleadaSuperada, si el número de la oleada es múltiplo de 5, pasa al fondo siguiente y publica FondoCambiado (RN-20).
- Al recibir OleadaIniciada, activa el entorno indicado y publica EntornoCambiado. Al recibir OleadaSuperada, lo desactiva.
- En la niebla, la visibilidad es 1 hasta la distancia de visibilidad completa, baja de forma continua y es 0 desde la distancia de invisibilidad.

## Eventos
- Publica: FondoCambiado, EntornoCambiado, DestelloAviso, DestelloInicio, DestelloFin.
- Escucha:
  - OleadaIniciada, OleadaSuperada,
  - PartidaIniciada, que pone el fondo 1 y quita el entorno,
  - PartidaAbandonada y EstacionDestruida, que quitan el entorno.

## Depende de
nucleo (azar), parametros.

## No hace
- No dibuja nada: `escena` usa sus consultas para aplicar la niebla, el deslumbramiento y el fondo.
- No cambia el comportamiento de los enemigos ni del radar (RN-09, RN-44).
