# Módulo estacion

- **Capa:** lógica
- **Cubre:** CU-06; RF-08, RF-15; RN-02, RN-10, RN-11, RN-12, RN-13, RN-17, RN-46, RN-47 (blindaje)

## Responsabilidad
Mantener la integridad de la estación y los efectos que los ataques enemigos causan al jugador.

## Estado que gestiona
- La integridad actual y la integridad máxima, incluida la mejora de blindaje.
- El tiempo restante de aturdimiento.
- El tiempo restante de desestabilización.

## Operaciones
- **Actualizar:** descuenta el tiempo de aturdimiento y de desestabilización. Cuando cada uno llega a cero, publica su evento de fin.
- **Consultar:** integridad actual y máxima, si el jugador está aturdido, si está desestabilizado.

## Reglas que aplica al recibir ProyectilImpacta
1. Resta a la integridad el daño del tipo de enemigo, sin bajar de cero.
2. Si el tipo es desestabilizador, empieza o renueva la desestabilización con su duración completa.
3. Si el tipo es aturdidor, empieza o renueva el aturdimiento con su duración completa.
4. Publica EstacionDanada e IntegridadCambiada.
5. Si la integridad ha llegado a cero, publica EstacionDestruida una sola vez y deja de aplicar impactos.

## Eventos
- Publica:
  - EstacionDanada, IntegridadCambiada,
  - DesestabilizacionIniciada y DesestabilizacionTerminada,
  - AturdimientoIniciado y AturdimientoTerminado,
  - EstacionDestruida.
- Escucha:
  - ProyectilImpacta,
  - ReparacionAplicada (suma sin superar la máxima),
  - MejoraAplicada (blindaje: sube la máxima y la actual),
  - PartidaIniciada (todo a valores iniciales).

## Depende de
nucleo, parametros.

## No hace
- No decide cuándo se puede reparar: eso lo controla `mejoras`, que solo opera durante el descanso (RN-48).
- No bloquea el giro ni el disparo directamente; `vista` y `armamento` lo hacen al recibir los eventos de aturdimiento.
