# Módulo entrada

- **Capa:** presentación
- **Cubre:** RF-46; RNF-02, RNF-03; RES-04

## Responsabilidad
Leer el teclado y el ratón y traducirlos a acciones del jugador, para que el resto del juego no dependa de teclas concretas.

## Estado que gestiona
- El estado de cada tecla usada: pulsada o no, y si se ha pulsado o soltado en este paso.
- La posición de la mira que marca el ratón, medida desde el centro de la pantalla en medias alturas de pantalla (de −1 abajo a +1 arriba en vertical).

## Acciones que ofrece

| Acción | Tecla | Tipo |
|---|---|---|
| Girar a la izquierda / derecha | Flecha izquierda / derecha, o A / D | mantenida |
| Girar hacia arriba / abajo | Flecha arriba / abajo, o W / S | mantenida |
| Apuntar y disparar | Barra espaciadora o botón izquierdo del ratón | mantenida; se informa también del momento en que se suelta |
| Pausa / volver | Esc | pulsación |
| Confirmar | Intro | pulsación |
| Navegar por menús | Flechas o W, A, S, D | pulsación, con repetición si se mantiene |
| Mover la mira | Ratón | posición; solo durante una oleada |

Las teclas de una misma acción son equivalentes: la acción está activa mientras cualquiera de ellas esté pulsada, y se suelta cuando se sueltan todas.

## Operaciones
- **Actualizar:** al principio de cada paso de simulación, toma el estado del teclado y la posición del ratón del motor.
- **Consultar:** estado de cada acción (mantenida, recién pulsada, recién soltada) y posición de la mira.

## Eventos
- Publica: ninguno. `flujo` consulta las acciones en cada paso.
- Escucha: ninguno.

## Depende de
El motor gráfico (lectura del teclado y del ratón).

## No hace
- No aplica reglas: no anula flechas opuestas (lo hace `vista`) ni bloquea por aturdimiento.
- No usa la rueda ni el botón derecho del ratón: el ratón solo mueve la mira y dispara con el botón izquierdo (RES-04).
- Si el ratón sale de la ventana, la mira se queda donde estaba.
- Si la ventana pierde el foco, informa todas las teclas como sueltas, para que no quede un giro o un apuntado atascado.
