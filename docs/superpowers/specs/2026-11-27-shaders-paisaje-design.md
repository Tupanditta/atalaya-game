# Shaders para planetas, asteroides, estrellas y sol — diseño

Fecha: 2026-11-27 · Estado: pendiente de aprobación

## Intención

El propietario ve la escena "poco realista y muy simple". Quiere una **mejora visual
notoria** en planetas, asteroides, estrellas y sol, con shaders, **perdiendo la menor
fluidez posible**. Todo original y generado por código, como el resto de la ambientación.

## Objetivos

1. Planetas con luz por píxel, atmósfera dispersada, relieve, nubes y sombras de anillos.
2. Asteroides con forma orgánica, color variado y luz por píxel.
3. Cielo más natural: colores de estrella por temperatura, nebulosas más detalladas y
   estrellas brillantes que centellean.
4. Sol con deslumbramiento y destellos de lente.
5. Medir la fluidez como en F7 y no empeorarla de forma apreciable.

## No objetivos

- **Sin posproceso** (bloom, HDR, tonemapping de pantalla): opción B elegida por el
  propietario. Se descarta expresamente.
- No se tocan enemigos, efectos de combate, salto, HUD ni sonido.
- No se cambian qué planetas hay ni dónde están (`planetas.PAISAJES`), salvo añadir datos
  de nubes.

## Anti-objetivos (sería un fracaso aunque funcione)

- Tirones nuevos al empezar la partida, al saltar o al aparecer un fondo.
- Que el juego se cierre en un equipo sin shaders.
- Planetas o rocas que tapen enemigos o proyectiles (todo sigue más allá del radar).
- Arranque en frío notablemente más lento (el fondo 1 se genera al arrancar).

## Restricciones

- Panda3D 1.10.16, pipeline fijo hoy; numpy ya es dependencia.
- **GLSL 1.30** (OpenGL 3.0). Si el GSG no admite GLSL o un shader no compila, se usa el
  aspecto actual (respaldo), sin error para el jugador.
- Las texturas y cielos van a la caché de usuario: se suben `planetas.VERSION` y
  `cielo.VERSION` a 2.
- Los shaders deben respetar `color_scale`/`alpha_scale` (`p3d_ColorScale`): el salto
  apaga el nodo `espacio` con ellos.
- Fluidez de referencia (F7): mediana 1,4 ms, p99 6,5–7 ms. Límite: mediana ≤ 1,9 ms y
  p99 ≤ 8 ms, sin picos nuevos fuera de los ya conocidos.
- Reglas de `CLAUDE.md`: sin commits, sin subagentes, documentación de `software/`
  actualizada en cada cambio, `.md` de la raíz solo si lo pide el propietario.

## Enfoques considerados

| | Qué | A favor | En contra |
|---|---|---|---|
| A | Shaders por objeto + bloom | El salto visual mayor | Coste de pantalla completa (~1–2 ms GPU) |
| **B** | **Shaders por objeto, sin bloom** | **Mejora grande con poco riesgo de fluidez** | Los brillos no "sangran" luz |
| C | Solo texturas numpy, sin shaders | Coste casi nulo | Mejora poco notoria |

**Elegido: B** (propietario). Respaldo al aspecto actual si no hay shaders (aclarado: solo
falla sin controlador, en escritorio remoto o máquina virtual sin 3D).

## Diseño

### Módulo nuevo: `presentacion/escena/sombreado.py`

- Carga los programas GLSL (ficheros `.vert`/`.frag` en
  `presentacion/escena/shaders/`).
- `disponible(gsg) -> bool`: `gsg.get_supports_glsl()` y versión ≥ 1.30.
- Compila cada shader una vez; si falla, lo registra en el log y devuelve `None`. Quien
  lo usa cae al camino actual.
- El calentamiento del menú (`Calentamiento`) dibuja un planeta, una roca, la capa de
  estrellas y el sol una vez para que la compilación no dé un tirón en partida.

### 1. Planetas

**Texturas (numpy, `planetas.py`, versión 2):**
- Color RGBA: el canal **A guarda la altura** (cráteres, grietas, dunas, cordilleras). Sin
  textura nueva para el relieve; el respaldo ignora el alfa (sin transparencia).
- **Nubes** (nueva, solo planetas con atmósfera): mapa en gris, la mitad del ancho del de
  color. Tipo de nube según superficie: polvo fino (desierto), nubes densas (rocoso),
  bruma clara (helado), ceniza (volcánico). El gaseoso no lleva: ya tiene bandas.
- La de luz propia (volcánicos) se mantiene.

**Shader de superficie (una sola pasada; sustituye la esfera de lava):**
- Luz difusa por píxel con la línea de sombra suavizada y algo teñida de la atmósfera.
- Normal perturbada a partir de la altura (4 muestras de la textura vecinas).
- Nubes que giran a otra velocidad que el suelo y proyectan sombra (muestra desplazada
  hacia el sol).
- Especular solo en hielo.
- Luz propia de la lava más visible en la cara de noche.
- Sombra de los anillos sobre el planeta: intersección analítica del rayo hacia el sol con
  el plano de los anillos, leyendo su densidad.

**Atmósfera (sustituye la tarjeta del halo):** cáscara esférica a 1,04 radios, caras
traseras, aditiva. Brillo de borde (Fresnel) por el lado de día, que vira al anaranjado
cerca de la línea de sombra y se apaga de noche.

**Anillos:** shader propio con la sombra del planeta sobre ellos (intersección
rayo–esfera) y luz más fuerte vista a contraluz.

### 2. Asteroides

- `_roca` pasa a numpy: icosaedro subdividido 3 veces, desplazado con `ruido.fractal`, con
  **normales suaves** y color por vértice (vetas y oscurecimiento en las hendiduras como
  oclusión aproximada). 8 variantes por campo en lugar de 5.
- Siguen unidas con `flatten_strong` en 6 grupos: mismo número de llamadas de dibujo.
- Shader: luz por píxel con el sol del fondo, luz de contorno tenue y un poco de ruido de
  detalle según la posición del objeto.

### 3. Estrellas y nebulosas (`cielo.py`, versión 2)

- Color de cada estrella por **temperatura** (rojizas, amarillas, blancas, azuladas), con
  más frías que calientes; los temas cálidos/fríos sesgan el reparto.
- Brillos con ley de potencias (pocas brillantes, muchas tenues).
- Nebulosas a 512 px por cara (hoy 256) y una octava más; filamentos más marcados.
- **Capa de estrellas que centellean:** las ~1500 más brillantes salen del cubo y se
  dibujan como una sola geometría de puntos con shader (tamaño según brillo, centelleo
  sutil con fase propia por estrella). Va en el bin `background` justo después del cubo y
  bajo el nodo `espacio`.

### 4. Sol

- En los fondos con sol (1, 3 y 4): tarjeta enfrentada a la cámara en su dirección con
  shader de deslumbramiento (núcleo, halo y seis rayos finos).
- Destellos de lente: 4–5 círculos tenues en `render2d` a lo largo de la línea
  sol–centro de pantalla, solo con el sol en el campo de visión.
- Se atenúan si un planeta tapa el sol (comprobación angular en CPU, pocos planetas).
- Los fondos 2 y 5 no tienen sol: no hay deslumbramiento.

### Respaldo

Si `sombreado.disponible` es falso o un shader no compila, cada parte usa su código actual
(esfera con textura y lava, tarjeta de halo, anillos sin sombra, rocas con luz fija, sin
deslumbramiento). Las texturas v2 sirven igual (la altura en el alfa no se ve). Como las
estrellas brillantes ya no están en el cubo, la capa de centelleo se dibuja en el respaldo
con puntos fijos del pipeline fijo (la textura `brillo` actual), sin centelleo.

El tiempo de generación en frío del fondo 1 no puede pasar de 1,5 veces el actual (se mide
antes de empezar la fase 3).

## Fases (se valida con capturas antes y después de cada una)

1. Planetas: texturas v2, nubes, shaders de superficie, atmósfera y anillos, y respaldo.
2. Asteroides.
3. Estrellas y nebulosas.
4. Sol.
5. Medición de fluidez (método F7: fuera de pantalla, con escena, HUD y audio reales) y
   del tiempo de generación en frío del fondo 1.

## Pruebas

- Las 623 actuales en verde.
- Nuevas: forma y rango de las texturas v2 (alfa de altura, nubes); geometría de las
  rocas (normales unitarias, sin triángulos degenerados); estrellas de la capa de
  centelleo fuera del cubo; elección del respaldo cuando `disponible` es falso o la
  compilación falla.
- Compilación real de los shaders solo si hay GSG con GLSL (si no, la prueba se omite).

## Documentación

`software/design.md` (sección 6) y `software/modulos/escena.md`, en cada fase.

## Decisiones tomadas por mí (revisables)

- GLSL 1.30 y respaldo al aspecto actual.
- Altura en el alfa en vez de un mapa de normales aparte (menos caché y memoria).
- Nubes solo en planetas con atmósfera; ninguna en el gaseoso.
- Especular solo en hielo.
- Límite de fluidez: mediana ≤ 1,9 ms, p99 ≤ 8 ms.
- 1500 estrellas en la capa de centelleo, 8 variantes de roca, nebulosas a 512 px.
- Orden de fases: planetas, asteroides, estrellas, sol, medición.

## Para quien lo construya

Constantes visuales exactas (colores, intensidades, velocidades de nubes, tamaño de los
destellos), la forma concreta de las fórmulas de dispersión y el reparto en ficheros de los
shaders.
