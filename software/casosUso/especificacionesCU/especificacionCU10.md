# CU-10. Consultar el manual

## Identificación
- **Actor principal:** ACT-01
- **Actores secundarios:** ninguno
- **Objetivo:** Conocer los controles, los enemigos, los entornos y las mejoras del juego.
- **Requisitos relacionados:** RF-39, RNF-03, RN-06, RN-11, RN-12, RN-13, RN-14, RN-22, RN-44, RN-47, RES-04, RES-05, RES-06

## Precondiciones
- El jugador está en el menú principal o en el menú de pausa.

## Disparador
El jugador elige «Manual».

## Flujo principal
1. El jugador elige «Manual».
2. El sistema muestra el manual abierto por su primera sección. Las secciones son:
   - **Controles:** flechas para girar, barra espaciadora para apuntar (mantener) y disparar (soltar), Esc para pausar.
   - **Tipos de enemigo:** para cada tipo, su nombre, su símbolo y color en el radar, el daño que hace, su tiempo de recarga y su efecto.
   - **Tamaños de enemigo:** para cada tamaño, su vida, su velocidad y lo difícil que es de acertar.
   - **Entornos:** qué son la niebla y los destellos y cómo afectan a la visibilidad.
   - **Mejoras:** la reparación y cada mejora, con su efecto, su coste y su número máximo de niveles.
3. El jugador cambia de sección con las flechas izquierda y derecha.
4. El sistema muestra la sección elegida.
5. El jugador pulsa Esc.
6. El sistema cierra el manual y vuelve a la pantalla desde la que se abrió.

## Flujos alternativos y excepciones
### A1. Manual abierto desde la pausa (desde el paso 2)
1. Hay una partida en curso.
2. El sistema muestra la vida de los enemigos correspondiente al nivel de dificultad de la partida. Desde el menú principal muestra la del nivel 1.
3. Vuelve al paso 3.

## Reglas de presentación
- Todos los valores del manual salen de los mismos parámetros que usa el juego, de modo que el manual siempre coincide con el comportamiento real.
- La sección actual y el número total de secciones se muestran siempre, por ejemplo «2 / 5».

## Postcondiciones
- No modifica el estado del sistema.

## Criterios de aceptación
- El manual se puede abrir desde el menú principal y desde la pausa.
- El manual muestra los tres tipos y los tres tamaños de enemigo con valores iguales a los de los parámetros del juego.
- Abierto desde la pausa, la vida mostrada corresponde al nivel de dificultad de la partida.
- Esc cierra el manual y vuelve a la pantalla anterior.
- Mientras el manual está abierto desde la pausa, la partida sigue detenida.
