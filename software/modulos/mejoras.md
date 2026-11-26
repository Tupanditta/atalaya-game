# Módulo mejoras

- **Capa:** lógica
- **Cubre:** CU-11; RF-40, RF-41, RF-42, RF-43; RN-45, RN-46, RN-47, RN-48, RN-49

## Responsabilidad
Calcular los puntos de mejora de cada oleada y aplicar las reparaciones y mejoras que el jugador compra con ellos.

## Estado que gestiona
- Los puntos disponibles.
- El nivel actual de cada mejora: blindaje, batería y generador.
- Si está abierto el descanso, que es el único momento en que se puede comprar (RN-48).
- El resultado de la última oleada: tiempo, tiempo de referencia y puntos obtenidos.

## Operaciones
- **Reparar:** solo durante el descanso.
  - Si hay puntos suficientes y la integridad no está al máximo, descuenta el coste y publica ReparacionAplicada con la cantidad de reparación.
  - Si no, no hace nada y devuelve el motivo: sin puntos, integridad al máximo o fuera del descanso.
- **Mejorar una característica:** solo durante el descanso.
  - Si hay puntos suficientes y no está en el nivel máximo, descuenta el coste, sube el nivel y publica MejoraAplicada.
  - Si no, devuelve el motivo.
- **Consultar:**
  - puntos disponibles,
  - nivel y nivel máximo de cada mejora,
  - coste de cada opción,
  - qué opciones están disponibles,
  - resultado de la última oleada.

Para saber si la integridad está al máximo, `mejoras` guarda la integridad y la máxima que recibe con IntegridadCambiada.

## Reglas que aplica
Al recibir OleadaSuperada:
1. Calcula el tiempo de referencia con el número de enemigos de la oleada.
2. Da 3, 2 o 1 puntos según el tiempo de la oleada (RN-45).
3. Suma los puntos a los disponibles y publica PuntosObtenidos.

## Eventos
- Publica: PuntosObtenidos, ReparacionAplicada, MejoraAplicada.
- Escucha:
  - OleadaSuperada,
  - DescansoIniciado y DescansoTerminado, que abren y cierran la compra,
  - IntegridadCambiada,
  - PartidaIniciada, que deja los puntos y las mejoras a cero (RN-49).

## Depende de
nucleo, parametros.

## No hace
- No cambia la integridad ni la energía directamente: publica eventos y `estacion` y `armamento` aplican los efectos.
- No guarda nada en disco (RN-49).
