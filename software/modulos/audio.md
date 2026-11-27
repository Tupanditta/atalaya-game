# Módulo audio

- **Capa:** presentación
- **Cubre:** RF-10, RF-11, RF-12, RF-13, RF-14, RF-16, RF-18; RN-34

## Responsabilidad
Reproducir los efectos de sonido, el sonido posicional de los enemigos, la radio y la música.

## Sonidos
Todos de registro grave.
- **Posicionales:** se oyen desde la dirección de su origen respecto a la cámara, y más bajos cuanto más lejos (RF-10).
  - Motor de cada enemigo: un rugido grave con un aullido, en bucle. Cuanto más cerca está la nave, más grave y más fuerte suena: de 150 u a 1200 u pasa de 0,68 a 1,08 veces su velocidad y de todo el volumen a un 30 %, y además se atenúa con la distancia a partir de 300 u. Cada nave tiene un tono algo distinto.
  - Aviso de disparo: un sonido de carga claro (RN-34). Se oye igual con niebla o destellos.
  - Disparo de un enemigo.
  - Explosión: más alta cuanto más cerca, de todo el volumen a 150 u a un 15 % a 1200 u, con un cambio suave entre medias. Suena desde su dirección.
- **No posicionales:**
  - disparo propio: un bláster de chirrido descendente con ecos y un golpe grave que le da cuerpo,
  - reducción de la mira (un tono que sube mientras se apunta),
  - impacto en un enemigo,
  - impacto de un proyectil en la estación: golpe sordo en el casco, quejido metálico y traqueteo, con la alarma de daño (RF-14) más baja detrás,
  - falta de energía (RF-11),
  - aturdimiento,
  - giro de la cámara: un servo que arranca al empezar a girar o al cambiar de dirección, y otro que se detiene al dejar de girar. El mismo para las cuatro direcciones,
  - sonido de radio al empezar una transmisión,
  - sonidos de los menús: mover, confirmar, error. Suenan cuando `flujo` indica que el jugador ha movido la selección, ha elegido una opción o ha elegido una opción no disponible,
  - salto hiperespacial: carga, estampido, rumor del túnel y salida, con las fases de su animación.
- Algunos efectos (disparos, impactos, explosión) varían un poco de tono cada vez, para que no suenen siempre igual.
- **Sonidos propios:** cualquier sonido se puede sustituir por un archivo WAV u OGG de `implementacion/recursos/sonidos/`, indicándolo en `sonidos.json` de esa carpeta: `{"version": 1, "sonidos": {"explosion": {"archivo": "...", "volumen": 1.0, "ganancia": 5}}}`. El volumen (de 0 a 1) y la ganancia (de 0 a 20) son opcionales. La ganancia amplifica las muestras de un archivo grabado flojo, con un limitador suave para que los picos no se corten de golpe; la explosión usa ganancia 5. Los nombres que se pueden sustituir son los de los efectos y los bucles: disparo, disparo_enemigo, aviso, impacto, impacto_estacion, explosion, sin_energia, alarma, aturdimiento, giro_inicio, giro_fin, menu_mover, menu_confirmar, menu_error, salto, motor, apuntado y zumbido. Un WAV estéreo en un sonido posicional se pasa a mono. Un archivo que falte o una entrada mal escrita se avisan en el registro y suena el generado. Ahora son propios el disparo y la explosión (ver `recursos/CREDITOS.md`).
- **Sonido de fondo (RF-18):** no hay música. Durante la oleada, el fondo es la suma de los motores de todas las naves, que crece en intensidad cuanto más cerca están. Debajo suena un zumbido grave de la estación, provisional hasta definir su sonido propio; se oye más bajo en el salto, en pausa y en los menús, con fundidos de 1,5 s.

## Operaciones
- **Actualizar:** una vez por fotograma.
  - Coloca al oyente con la orientación de `vista`.
  - Mueve los sonidos posicionales a la posición de cada enemigo y proyectil.

## Eventos
- Publica: ninguno.
- Escucha:
  - PausaCambiada: con la partida en pausa, detiene los sonidos de partida (también los motores y el tono de la mira) y deja la música en calma a volumen bajo.
  - ApuntadoCambiado, DisparoRealizado, DisparoSinEnergia,
  - EnemigoAparecido, AvisoDisparo, ProyectilLanzado, EnemigoAlcanzado, EnemigoDestruido,
  - EstacionDanada, AturdimientoIniciado, EstacionDestruida,
  - OleadaIniciada, OleadaSuperada, PartidaGanada,
  - EntornoCambiado, DestelloAviso, DestelloInicio,
  - SaltoIniciado,
  - TransmisionDisponible, PartidaIniciada, PartidaAbandonada.
- Consulta en cada fotograma: la pantalla de `flujo`, los enemigos activos, el giro de `vista` y si hay salto en `oleadas`.

## Depende de
El motor de audio; vista, enemigos, oleadas y flujo (solo lectura).

## No hace
- No decide cuándo ocurre nada: solo reacciona a eventos.
