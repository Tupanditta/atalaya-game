# Módulo radar

- **Capa:** lógica
- **Cubre:** CU-05; RF-07, RF-22, RF-23, RF-31; RN-09, RN-30, RN-41

## Responsabilidad
Traducir la posición de cada enemigo a lo que muestra el radar, siempre respecto a la cámara.

## Estado que gestiona
Ninguno propio. Cada consulta se calcula con el estado actual de `vista` y `enemigos`.

## Operaciones
**Consultar contactos:** devuelve, para cada enemigo activo:
- **Ángulo en el radar:** la dirección del enemigo proyectada sobre el plano horizontal de la cámara (el que forman sus ejes «adelante» y «derecha»). El 0 corresponde a «adelante», que se dibuja arriba en el radar.
- **Distancia relativa:** su distancia a la estación dividida por el alcance del radar, de 0 a 1.
- **Altura:** «por encima», «a la misma altura» o «por debajo», según el ángulo del enemigo respecto al plano horizontal de la cámara. Se considera «a la misma altura» si ese ángulo es menor de 15°.
- **Tipo y tamaño**, copiados del enemigo.
- **En campo de visión:** si el enemigo cae dentro del campo de visión actual de la cámara.

**Consultar el sector de visión:** el ángulo de apertura del campo de visión actual, para dibujarlo en el radar.

## Eventos
- Publica: ninguno.
- Escucha: ninguno.

## Depende de
nucleo, parametros, vista (orientación y campo de visión), enemigos (lista de enemigos activos).

## No hace
- No dibuja el radar: lo hace `hud`.
- No oculta enemigos por la niebla ni por los destellos (RN-09).
