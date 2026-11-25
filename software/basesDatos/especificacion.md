# Datos guardados

El juego solo conserva un dato entre sesiones: el nivel de dificultad más alto desbloqueado (RN-25, RF-26). El estado de una partida (energía, integridad, oleada, enemigos) no se guarda: cada partida empieza desde cero (RN-02).

No se usa un sistema de base de datos. Para un único dato basta con un archivo.

## Dato guardado

| Dato | Clave en el archivo | Descripción | Valores | Valor inicial |
|---|---|---|---|---|
| Nivel más alto desbloqueado | `nivel_desbloqueado` | Nivel de dificultad más alto al que el jugador puede jugar | Número entero, mayor o igual que 1, sin máximo | 1 |

## Almacenamiento

- **Formato:** JSON, codificado en UTF-8.
- **Nombre del archivo:** `progreso.json`.
- **Ubicación:** carpeta `Atalaya` dentro de la carpeta de datos de usuario del sistema operativo (en Windows, `%APPDATA%\Atalaya\`). Nunca dentro del repositorio ni de la carpeta de instalación.
- **Ejemplo de contenido:**

```json
{
  "version": 1,
  "nivel_desbloqueado": 3
}
```

- `version` indica la versión del formato, para poder ampliarlo en el futuro sin romper archivos antiguos.
- Los datos no salen del equipo del jugador (RES-07).

## Lectura

- El dato se lee al abrir el juego.
- Si el archivo no existe (primera vez que se abre el juego), se toma el valor inicial y no se crea el archivo hasta la primera escritura.
- Si el archivo está dañado, no es JSON válido, o `nivel_desbloqueado` falta o no es un entero mayor o igual que 1, se toma el valor inicial. El juego no muestra un error que lo bloquee (CU-01, A4).
- Un archivo dañado no se borra al leerlo. Se sobrescribe en la siguiente escritura.

## Escritura

- El dato se escribe al ganar una partida, solo si el nivel desbloqueado es mayor que el guardado (CU-07, A2).
- El dato nunca disminuye.
- La escritura es atómica: se escribe un archivo temporal en la misma carpeta y después se renombra sobre `progreso.json`. Así, si el juego se cierra a mitad de la escritura, el archivo anterior queda intacto.
- Si la escritura falla, la partida continúa con normalidad y el nivel desbloqueado se mantiene en memoria hasta cerrar el juego.

## Ampliación

Este archivo se ampliará si más adelante se decide guardar más datos, por ejemplo récords o progreso de la historia.
