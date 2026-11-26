# Módulo audio

- **Capa:** presentación
- **Cubre:** RF-10, RF-11, RF-12, RF-13, RF-14, RF-16, RF-18; RN-34

## Responsabilidad
Reproducir los efectos de sonido, el sonido posicional de los enemigos, la radio y la música.

## Sonidos
- **Posicionales:** se oyen desde la dirección de su origen respecto a la cámara, y más bajos cuanto más lejos (RF-10).
  - Motor de cada enemigo: un zumbido continuo y suave.
  - Aviso de disparo: un sonido de carga claro (RN-34). Se oye igual con niebla o destellos.
  - Proyectil en vuelo y explosión.
- **No posicionales:**
  - disparo propio,
  - reducción de la mira (un tono que sube mientras se apunta),
  - impacto en un enemigo,
  - falta de energía (RF-11),
  - alarma de daño (RF-14),
  - aturdimiento,
  - sonido de radio al empezar una transmisión,
  - sonidos de los menús: mover, confirmar, error.
- **Música (RF-18):** tres pistas.
  - Calma: menús y descansos.
  - Combate: oleada en curso.
  - Crítica: integridad por debajo del 25 %.

  El cambio de pista es un fundido de 2 s.

## Operaciones
- **Actualizar:** una vez por fotograma.
  - Coloca al oyente con la orientación de `vista`.
  - Mueve los sonidos posicionales a la posición de cada enemigo y proyectil.

## Eventos
- Publica: ninguno.
- Escucha:
  - PausaCambiada: con la partida en pausa, detiene los sonidos de partida y deja la música en calma a volumen bajo.
  - ApuntadoCambiado, DisparoRealizado, DisparoSinEnergia,
  - EnemigoAparecido, AvisoDisparo, ProyectilLanzado, EnemigoAlcanzado, EnemigoDestruido,
  - EstacionDanada, AturdimientoIniciado, EstacionDestruida,
  - OleadaIniciada, OleadaSuperada, PartidaGanada,
  - EntornoCambiado, DestelloAviso, DestelloInicio,
  - TransmisionDisponible, PartidaIniciada, PartidaAbandonada.

## Depende de
El motor de audio; vista y enemigos (solo lectura).

## No hace
- No decide cuándo ocurre nada: solo reacciona a eventos.
