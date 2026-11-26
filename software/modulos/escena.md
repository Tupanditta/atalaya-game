# Módulo escena

- **Capa:** presentación
- **Cubre:** RF-12, RF-13, RF-14, RF-17, RF-45; RNF-01; RES-03

## Responsabilidad
Dibujar el mundo en 3D desde la cámara del jugador, con sus efectos visuales.

## Qué dibuja
- **Cámara:** orientación y campo de visión de `vista`.
- **Fondo:** el fondo espacial actual de `entorno`, a distancia infinita. Al cambiar de fondo, hace un fundido de 2 s entre el anterior y el nuevo.
- **Enemigos:** un modelo sencillo por tipo, escalado según su tamaño, en la posición de `enemigos`. Durante el aviso de disparo, el enemigo emite un destello creciente del color de su tipo.
- **Proyectiles enemigos:** esferas luminosas del color del tipo, con una estela corta.
- **Rayo del disparo:** una línea luminosa de la estación al punto de impacto, que se desvanece en 0,1 s.
- **Impacto en un enemigo:** un destello breve en el punto de impacto.
- **Explosión:** partículas y un destello de luz donde se destruye un enemigo.
- **Daño recibido:** temblor breve de la cámara, de 0,3 s, solo visual, y un tinte rojo en los bordes de la pantalla (RF-14).
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
  - FondoCambiado, EntornoCambiado, DestelloAviso, DestelloInicio, DestelloFin,
  - PausaCambiada, PartidaIniciada, PartidaAbandonada, EstacionDestruida.

## Depende de
El motor gráfico; vista, enemigos, entorno y armamento (solo lectura).

## No hace
- No dibuja la mira, el radar, los indicadores ni los menús: lo hace `hud`.
- No cambia el estado de la lógica.
