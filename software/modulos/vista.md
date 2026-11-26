# Módulo vista

- **Capa:** lógica
- **Cubre:** CU-02; RF-02, RF-03, RF-21, RF-28, RF-33; RNF-04; RN-01, RN-12, RN-13, RN-26, RN-39, RN-40, RN-41

## Responsabilidad
Mantener hacia dónde mira el jugador y cuánto zoom tiene, y calcular la dirección real de la mira, que incluye el desvío por desestabilización.

## Estado que gestiona
- La orientación de la cámara, sin «arriba» fijo del espacio (RN-41).
- El campo de visión actual, entre el normal y el de zoom máximo.
- El desvío actual de la mira por desestabilización.
- Si el giro está bloqueado por aturdimiento.

## Operaciones
- **Recibir ejes de giro:** horizontal y vertical, cada uno con valor −1, 0 o +1.
  - Dos flechas opuestas del mismo eje dan 0 (RN-26).
  - Si el jugador está aturdido, ambos ejes valen 0 (RN-13).
- **Actualizar:**
  - Gira la cámara en sus propios ejes. La velocidad es la de giro sin zoom multiplicada por el campo de visión actual dividido por el normal (RN-40).
  - Ajusta el campo de visión al progreso de apuntado (RN-39).
  - Actualiza el desvío de la mira mientras dura la desestabilización: ruido suave y continuo, no saltos.
- **Consultar:**
  - orientación,
  - campo de visión,
  - dirección de la mira (el centro de la vista más el desvío),
  - ejes de la cámara (adelante, arriba, derecha).

## Eventos
- Publica: ninguno.
- Escucha:
  - ApuntadoCambiado,
  - DesestabilizacionIniciada y DesestabilizacionTerminada,
  - AturdimientoIniciado y AturdimientoTerminado,
  - PartidaIniciada, que restablece la orientación inicial y el campo de visión normal.

## Depende de
nucleo, parametros.

## No hace
- No mueve la posición de la estación: solo existe la orientación (RN-01).
- No aplica el temblor breve por daño recibido (RF-14): ese temblor es solo visual y lo hace `escena`.
- No decide cuándo se apunta ni cuánto se reduce la mira; eso lo hace `armamento`.
