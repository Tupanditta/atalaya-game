# Módulo entrada

- **Capa:** presentación
- **Cubre:** RNF-02, RNF-03; RES-04

## Responsabilidad
Leer el teclado y traducirlo a acciones del jugador, para que el resto del juego no dependa de teclas concretas.

## Estado que gestiona
- El estado de cada tecla usada: pulsada o no, y si se ha pulsado o soltado en este paso.

## Acciones que ofrece

| Acción | Tecla | Tipo |
|---|---|---|
| Girar a la izquierda / derecha | Flecha izquierda / derecha | mantenida |
| Girar hacia arriba / abajo | Flecha arriba / abajo | mantenida |
| Apuntar y disparar | Barra espaciadora | mantenida; se informa también del momento en que se suelta |
| Pausa / volver | Esc | pulsación |
| Confirmar | Intro | pulsación |
| Navegar por menús | Flechas | pulsación, con repetición si se mantiene |

## Operaciones
- **Actualizar:** al principio de cada paso de simulación, toma el estado del teclado del motor.
- **Consultar:** estado de cada acción (mantenida, recién pulsada, recién soltada).

## Eventos
- Publica: ninguno. `flujo` consulta las acciones en cada paso.
- Escucha: ninguno.

## Depende de
El motor gráfico (lectura del teclado).

## No hace
- No aplica reglas: no anula flechas opuestas (lo hace `vista`) ni bloquea por aturdimiento.
- No usa el ratón (RES-04).
- Si la ventana pierde el foco, informa todas las teclas como sueltas, para que no quede un giro o un apuntado atascado.
