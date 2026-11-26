# Módulo nucleo

- **Capa:** lógica
- **Cubre:** RNF-01, RNF-02, RN-50

## Responsabilidad
Dar a todos los módulos un tiempo común, un canal de eventos y una fuente de azar, sin saber nada del juego.

## Estado que gestiona
- El reloj del juego: tiempo acumulado y si está en pausa.
- La lista de suscriptores de cada evento.
- El generador de números al azar de la partida y su semilla.

## Operaciones
- **Avanzar:** recibe el tiempo real transcurrido desde el fotograma anterior y ejecuta tantos pasos de simulación de duración fija (1/60 s) como quepan, en el orden de actualización de `README.md`.
- **Pausar / reanudar el reloj:** con el reloj en pausa no se ejecutan pasos de simulación de la partida.
- **Publicar un evento** y **suscribirse a un tipo de evento.**
- **Reiniciar el azar** con una semilla. Cada partida empieza con una semilla nueva. Las pruebas usan una semilla fija para obtener siempre el mismo resultado.

## Eventos
- Publica: ninguno.
- Escucha: ninguno.

## Depende de
Nada.

## No hace
- No conoce ningún módulo concreto ni ninguna regla del juego.
- No dibuja ni lee el teclado.
- Si un fotograma tarda mucho, no ejecuta más de 5 pasos seguidos; descarta el resto para no bloquear el juego.
