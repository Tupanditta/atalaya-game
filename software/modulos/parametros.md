# Módulo parametros

- **Capa:** lógica
- **Cubre:** sección «Parámetros iniciales» de `reglasNegocio.md`; CU-10

## Responsabilidad
Cargar al arrancar el archivo de parámetros del juego, comprobar que es correcto y ofrecer sus valores a todos los módulos.

## Estado que gestiona
Todos los valores de «Parámetros iniciales», agrupados como en `reglasNegocio.md`:
- jugador y estación,
- enemigos por tamaño y por tipo,
- ataques y distancias,
- composición de oleadas,
- entornos,
- mejoras y reparación,
- nivel de dificultad.

## Operaciones
- **Cargar:** lee el archivo de parámetros y comprueba que están todos los valores, que tienen el tipo correcto y que respetan las relaciones entre ellos. Por ejemplo:
  - la distancia mínima es menor que el alcance de disparo,
  - la distancia mínima es menor que la distancia de pasada, y esta, menor que el alcance de disparo,
  - el alcance de disparo es menor que la distancia máxima,
  - la distancia máxima es menor que el alcance del radar,
  - el tamaño mínimo de la mira es menor que el normal.
- **Consultar un grupo de valores:** devuelve valores de solo lectura.
- **Calcular valores derivados por nivel:** vida de un enemigo según tamaño y nivel; duración del descanso según nivel.
- **Calcular la composición de una oleada:** número de enemigos y tipos permitidos según su número.
- **Calcular el entorno de una oleada:** ninguno, niebla o destellos, según su número.

## Eventos
- Publica: ninguno.
- Escucha: ninguno.

## Depende de
Nada.

## No hace
- No permite cambiar valores durante la partida.
- Si el archivo de parámetros falta o es incorrecto, el juego no arranca y muestra qué valor falla. A diferencia del progreso guardado, los parámetros forman parte del juego instalado, así que un error es un fallo de instalación.
