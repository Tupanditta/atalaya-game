# Módulo progreso

- **Capa:** lógica (con acceso a disco a través de un puerto de almacenamiento)
- **Cubre:** CU-01 (A4), CU-07 (A2), CU-12; RF-26; RN-21, RN-25; RES-07; `basesDatos/especificacion.md`

## Responsabilidad
Leer y guardar el nivel de dificultad más alto desbloqueado, según `basesDatos/especificacion.md`.

## Estado que gestiona
- El nivel más alto desbloqueado en memoria.

## Operaciones
- **Cargar al arrancar:** lee el archivo de progreso.
  - Si falta, está dañado o el valor no es válido, usa el nivel 1 sin bloquear el juego.
- **Consultar:** nivel más alto desbloqueado.

## Reglas que aplica
Al recibir PartidaGanada con el nivel N:
1. Si N + 1 es mayor que el nivel guardado, lo guarda como nuevo nivel más alto desbloqueado. La escritura es atómica: archivo temporal y después renombrado.
2. Si la escritura falla, mantiene el valor en memoria y lo registra en el registro de errores, sin interrumpir el juego.

## Puerto de almacenamiento
`progreso` no accede al disco directamente. Usa un puerto con dos operaciones:
- leer texto,
- escribir texto de forma atómica.

En el juego, el puerto escribe en la carpeta de datos de usuario. En las pruebas, se sustituye por un almacenamiento en memoria.

## Eventos
- Publica: ninguno.
- Escucha: PartidaGanada.

## Depende de
nucleo, puerto de almacenamiento.

## No hace
- No guarda el estado de una partida, ni puntos ni mejoras (RN-49).
- No envía datos fuera del equipo (RES-07).
