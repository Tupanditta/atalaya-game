# Módulo escena

- **Capa:** presentación
- **Cubre:** RF-12, RF-13, RF-14, RF-17, RF-45; RNF-01; RES-03

## Responsabilidad
Dibujar el mundo en 3D desde la cámara del jugador, con sus efectos visuales.

## Qué dibuja
- **Cámara:** orientación y campo de visión de `vista`.
- **Fondo:** el fondo espacial actual de `entorno`, a distancia infinita: estrellas, nebulosas y polvo galáctico, distintos en cada uno de los 5 fondos. Cada fondo tiene además su paisaje 3D, siempre más lejos que el alcance del radar para no tapar enemigos ni proyectiles: planetas iluminados por el sol del fondo, con atmósfera, lunas, anillos o lava, un cinturón de asteroides que orbita despacio y polvo que deriva cerca de la estación. Al recibir SaltoIniciado hace la animación del salto hiperespacial, igual en los 4 cambios, y al terminar queda puesto el fondo nuevo.
- **Enemigos:** un modelo sencillo por tipo, escalado según su tamaño, en la posición de `enemigos`. Durante el aviso de disparo, el enemigo emite un destello creciente del color de su tipo.
- **Brillo del motor:** un resplandor del color del tipo detrás de cada enemigo, con un leve parpadeo.
- **Proyectiles enemigos:** esferas luminosas del color del tipo, con una estela de dardo bláster: halo del color del tipo y núcleo blanco.
- **Disparo bláster:** sale por turnos de dos cañones, a izquierda y derecha, con un fogonazo. El haz, de núcleo blanco y halo de color, se alarga del cañón al punto de impacto en 0,1 s como mucho; su cola lo sigue y el haz se apaga.
- **Impacto en un enemigo:** un destello breve y chispas en el punto de impacto, cuando llega el disparo.
- **Explosión:** fogonazo, bola de fuego, onda expansiva en anillo del color del tipo, chispas y restos que giran con una brasa encendida. Sacude un poco la cámara, más cuanto más grande y cercano es el enemigo.
- **Salto hiperespacial:** las estrellas se estiran en estelas, un destello da paso a un túnel azul que tiembla, y al salir aparece el cielo nuevo. El campo de visión se abre durante el salto. Dura lo que el salto de `oleadas` y se congela en la pausa.
- **Daño recibido:** turbulencia de la nave: una sacudida fuerte de la cámara durante 0,2 s, solo visual, y un tinte rojo en los bordes de la pantalla de 0,3 s (RF-14). La mira tiembla a la vez (`hud`).
- **Desestabilización:** temblor continuo de la imagen, que coincide con el desvío de la mira de `vista` (RN-12).
- **Niebla:** a cada enemigo y proyectil se le aplica la visibilidad de `entorno` según su distancia. El fondo también se atenúa.
- **Destellos:** un velo blanco a pantalla completa con la intensidad del deslumbramiento de `entorno`. Durante el aviso crece suavemente.
- **Pausa:** la escena queda congelada y oscurecida.

## Operaciones
- **Dibujar:** una vez por fotograma. Consulta el estado de la lógica e interpola posiciones y orientación entre los dos últimos pasos de simulación, para que el movimiento sea suave aunque la frecuencia de pantalla no sea 60 Hz.

## Eventos
- Publica: ninguno.
- Escucha:
  - DisparoRealizado, EnemigoAparecido, EnemigoAlcanzado, EnemigoDestruido,
  - AvisoDisparo, ProyectilLanzado,
  - EstacionDanada, DesestabilizacionIniciada, DesestabilizacionTerminada,
  - FondoCambiado, SaltoIniciado, EntornoCambiado, DestelloAviso, DestelloInicio, DestelloFin,
  - PausaCambiada, PartidaIniciada, PartidaAbandonada, EstacionDestruida.

## Depende de
El motor gráfico; vista, enemigos, entorno y armamento (solo lectura).

## No hace
- No dibuja la mira, el radar, los indicadores ni los menús: lo hace `hud`.
- No cambia el estado de la lógica.
