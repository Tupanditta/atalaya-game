# Interfaz

Especificación visual de la interfaz: estilo, colores, tipografía, componentes y disposición de cada pantalla. Las maquetas SVG de esta carpeta muestran el resultado esperado. Si una maqueta y este documento no coinciden, prevalece este documento.

Lo que se muestra en cada pantalla lo fijan los casos de uso y `modulos/hud.md`. Este documento fija cómo se muestra.

## 1. Estilo

Interfaz moderna de ciencia ficción, limpia y legible:
- Paneles oscuros semitransparentes sobre la escena, con bordes finos de color acento y dos esquinas recortadas (arriba a la izquierda y abajo a la derecha).
- Sin texturas ni degradados recargados. Un brillo suave solo en los elementos activos.
- Textos de títulos y cifras en mayúsculas con algo de espaciado entre letras.
- La escena 3D siempre visible: ningún panel de partida ocupa el centro de la pantalla.

## 2. Medidas y escala

- Todas las medidas están en píxeles para una pantalla de **1920 × 1080**.
- Con otra resolución, todo se escala por el factor *alto de la pantalla ÷ 1080*.
- Cada elemento se ancla a su esquina o borde. En pantallas más anchas que 16:9, los elementos anclados a la izquierda y a la derecha se separan, y los centrados siguen centrados.
- Margen de seguridad: **48 px** desde cada borde.

## 3. Colores

| Nombre | Valor | Uso |
|---|---|---|
| fondo-panel | `#0A1220` al 78 % | Fondo de paneles |
| borde-panel | `#2AD4FF` al 35 % | Borde de paneles, anillos del radar |
| acento | `#2AD4FF` | Selección, energía, mira reducida, títulos de sección |
| texto | `#E6F1FF` | Texto principal, mira normal |
| texto-secundario | `#8AA0B8` | Etiquetas y ayudas |
| pista | `#1A2638` | Fondo de las barras |
| integridad-alta | `#3DDC84` | Integridad por encima del 50 % |
| aviso | `#FFB020` | Integridad entre 25 % y 50 %; energía insuficiente |
| peligro | `#FF4D5E` | Integridad por debajo del 25 %; daño recibido; derrota |
| enemigo-normal | `#FF4D5E` | Enemigo sin efecto especial y sus proyectiles |
| enemigo-desestabilizador | `#FFD23F` | Desestabilizador y sus proyectiles |
| enemigo-aturdidor | `#B36BFF` | Aturdidor, sus proyectiles y el aviso de aturdimiento |
| velo-pausa | `#000000` al 55 % | Oscurecimiento de la escena en pausa |

Los tipos de enemigo se distinguen siempre por **forma y color a la vez**, para que se reconozcan también con daltonismo.

## 4. Tipografía

| Uso | Fuente | Tamaño | Peso |
|---|---|---|---|
| Título del juego | Rajdhani | 140 px, espaciado 24 px | Bold |
| Títulos de pantalla | Rajdhani | 48 px, espaciado 6 px | Bold |
| Opciones de menú | Rajdhani | 32 px, espaciado 3 px | SemiBold |
| Cifras del HUD | Rajdhani | 30 px | SemiBold |
| Etiquetas del HUD | Rajdhani | 16 px, espaciado 3 px | SemiBold |
| Textos largos (transmisiones, manual) | Inter | 20 px, interlineado 1,4 | Regular |
| Ayudas de teclas | Inter | 16 px | Medium |

Las dos fuentes tienen licencia libre (SIL Open Font License) y se incluyen en `implementacion/recursos/fuentes/`.

## 5. Componentes

### Panel
- Fondo **fondo-panel** y borde de 1 px **borde-panel**.
- Esquinas superior izquierda e inferior derecha recortadas en diagonal, 12 px.
- Relleno interior de 24 px.

### Opción de menú
- 64 px de alto; texto alineado a la izquierda con 24 px de relleno.
- **Seleccionada:** fondo **acento** al 14 %, barra vertical de 4 px **acento** a la izquierda, texto **texto** y el signo «›» a la derecha.
- **No seleccionada:** sin fondo, texto **texto-secundario**.
- **No disponible:** opacidad al 40 %.
- Cambiar de opción tiene una transición de 120 ms.

### Barra
- 10 px de alto, fondo **pista** y relleno del color del dato.
- El valor cambia con una transición de 150 ms.
- Encima, la etiqueta a la izquierda y el valor numérico (`actual / máximo`) a la derecha.

### Tecla
- Rectángulo con borde de 1 px **texto-secundario**, esquinas redondeadas de 4 px y la tecla dentro: `↑↓`, `Intro`, `Esc`, `Espacio`.
- Va seguido de la acción en **texto-secundario**.

### Barra de ayudas
- Fila de teclas centrada a 48 px del borde inferior en todas las pantallas de menú.
- Por ejemplo: `↑↓ Navegar · Intro Confirmar · Esc Volver`.

### Indicador de niveles
- Cinco puntos de 10 px: rellenos **acento** para los niveles comprados y huecos para los que faltan.

## 6. HUD de la partida

Ver `03-oleada.svg`, `04-apuntando.svg` y `05-aturdido.svg`.

### Mira (sigue al ratón)
- **Forma:** anillo de cuatro arcos de 2 px, con una marca exterior de 10 px en cada hueco y un punto central de 5 px de diámetro. Con la mira normal, los arcos ocupan 56° cada uno, centrados en las diagonales, y las marcas quedan arriba, abajo, a la izquierda y a la derecha, a 7 px del anillo.
- **Contorno:** cada trazo y el punto llevan debajo un contorno negro al 45 %, 2,5 px más ancho, para que se lean sobre las nebulosas brillantes.
- **Al apuntar,** de forma continua y suavizada según el progreso de apuntado:
  - toda la mira gira hasta 45°,
  - los arcos se alargan hasta 74° y cierran los huecos,
  - las marcas se acercan al anillo (a 3 px) y se acortan (a 7 px),
  - aparece un brillo suave **acento** de 8 px bajo los trazos, hasta el 22 %.
- **Mira al mínimo:** un rombo **acento** de 1,5 px y 7 px de semidiagonal rodea el punto central: el disparo está listo.
- **Disparo:** un anillo **acento** sale de la mira, se aleja 22 px y se desvanece en 0,18 s.
- Empieza centrada en (960, 540) y se mueve con el ratón por toda la pantalla; no sale de ella. Sustituye al cursor, que no se muestra.
- **Radio en pantalla** = 540 × tan(radio de la mira) ÷ tan(campo de visión ÷ 2). Con los parámetros iniciales:
  - unos 34 px con la mira normal,
  - unos 21 px con la mira al mínimo y el zoom máximo.
- **Color:** **texto** con la mira normal, que pasa de forma continua a **acento** según el progreso de apuntado.
- **Desestabilización:** la mira se dibuja desplazada según el desvío de `vista`.
- **Aturdimiento:** la mira se dibuja como un círculo de trazo discontinuo (8 px de trazo y 6 px de hueco) con el punto central, sin marcas ni anillo de disparo, y opacidad al 40 %.

### Radar (abajo a la izquierda)
- Círculo de 150 px de radio con centro en (210, 870). Fondo **fondo-panel** y borde **borde-panel**.
- **Anillos:** a un tercio y dos tercios del radio, rotulados con su distancia (400 y 800 u). El borde corresponde a 1200 u.
- **Estación:** cruz **acento** de 10 px en el centro.
- **Campo de visión:** sector **acento** al 10 % que se abre hacia arriba con el ángulo del campo de visión actual. Se estrecha con el zoom.
- **Contactos:**
  - Forma según el tipo: círculo (sin efecto especial), triángulo (desestabilizador), rombo (aturdidor).
  - Tamaño según el tamaño del enemigo: 8, 12 o 16 px.
- **Altura:** un pequeño triángulo de 6 px junto al contacto. Apunta hacia arriba si el enemigo está por encima de la cámara y hacia abajo si está por debajo. No se dibuja si está a la misma altura.
- **Dentro del campo de visión:** contacto opaco con contorno de 1 px **texto**.
- **Fuera:** contacto al 70 % de opacidad.
- **Aviso de disparo:** el contacto del enemigo parpadea dos veces por segundo mientras dura el aviso.

### Oleada (arriba en el centro)
- Panel de 360 × 80 px centrado a 32 px del borde superior.
- `OLEADA 12 / 50` en cifras del HUD y, debajo, `7 ENEMIGOS RESTANTES` en etiqueta.

### Estado de la estación (abajo a la derecha)
- Panel de 432 × 120 px anclado al margen inferior derecho.
- **Integridad:** barra de color integridad-alta, aviso o peligro según el porcentaje.
- **Energía:** barra **acento**, con una marca vertical cada «coste de un disparo», para leer de un vistazo cuántos disparos quedan.
- **Nivel:** etiqueta `NIVEL 3` encima del panel, alineada a la derecha.

### Transmisión (arriba a la izquierda)
- Panel de 520 px de ancho, con la cabecera `◉ TRANSMISIÓN · MANDO DE LA RED` en etiqueta **acento** y el texto en Inter.
- El texto aparece letra a letra a 40 caracteres por segundo.
- En partida, el panel se oculta a los 6 s con un fundido de 0,5 s.

### Avisos
- **Sin energía:** la barra de energía parpadea en **aviso** tres veces en 0,6 s, y aparece `SIN ENERGÍA` sobre ella durante 1 s.
- **Aturdimiento:**
  - Cartel de 520 × 56 px bajo el panel de oleada: borde **enemigo-aturdidor** y texto `SISTEMAS ATURDIDOS · 1,2 s`, con la cuenta atrás.
  - Viñeta **enemigo-aturdidor** al 30 % en los bordes de la pantalla.
- **Daño recibido:** viñeta **peligro** al 40 % en los bordes, que se desvanece en 0,3 s. La dibuja `escena`.

### Elementos que no cambian con el entorno
El radar, los paneles y los avisos se dibujan encima de la niebla y de los destellos, con su aspecto normal.

## 7. Pantallas

### Menú principal (`01-menuPrincipal.svg`)
- **Fondo:** la escena espacial del fondo 1, girando muy despacio, sin HUD.
- **Título:** `ATALAYA` en título del juego, a la izquierda (x = 160, y = 380). Debajo, `ÚLTIMA GUARDIA DE LA RED` en etiqueta **acento**.
- **Opciones:** `JUGAR`, `MANUAL` y `SALIR DEL JUEGO`, en una columna de 480 px de ancho desde y = 520. `JUGAR` aparece seleccionada.
- **Ayudas:** `↑↓ Navegar · Intro Confirmar`.
- La versión del juego aparece en texto-secundario en la esquina inferior derecha.

### Selección de nivel (`02-seleccionNivel.svg`)
- Panel centrado de 720 × 440 px con el título `NIVEL DE DIFICULTAD`.
- **Selector:** `‹ 3 ›` con la cifra a 96 px. Las flechas se atenúan cuando no se puede bajar o subir más.
- **Información del nivel elegido:**
  - `Resistencia de los enemigos ×1,50`,
  - `Descanso entre oleadas 15,8 s`,
  - `Nivel más alto desbloqueado: 3`.
- **Ayudas:** `←→ Cambiar nivel · Intro Empezar · Esc Volver`.

### Pantalla de mejoras (`06-mejoras.svg`)
- Panel centrado de 1280 × 760 px sobre la escena del descanso.
- **Cabecera:** `OLEADA 14 SUPERADA` a la izquierda. A la derecha, `SIGUIENTE OLEADA EN` con la cuenta atrás en cifras de 48 px, que pasa a **aviso** con 5 s o menos.
- **Columna izquierda (480 px):**
  - la transmisión de radio,
  - el resultado de la oleada (`Tiempo 01:12 · Referencia 01:00 · +2 puntos`),
  - los puntos disponibles en cifras de 72 px,
  - la barra de integridad.
- **Columna derecha:** las opciones `REPARAR`, `BLINDAJE`, `BATERÍA`, `GENERADOR` y `CONTINUAR`. Cada mejora muestra su efecto, su coste en puntos y su indicador de niveles. `REPARAR` muestra `+20 integridad · 1 punto`.
- Si no hay puntos o la opción está al máximo, la opción aparece como no disponible y su coste se sustituye por `SIN PUNTOS` o `COMPLETO`.
- **Ayudas:** `↑↓ Navegar · Intro Comprar · Esc Pausa`.

### Pausa (`07-pausa.svg`)
- La escena queda congelada con el velo de pausa.
- Panel centrado de 560 × 440 px con el título `PAUSA` y las opciones `CONTINUAR`, `MANUAL`, `ABANDONAR PARTIDA` y `SALIR DEL JUEGO`.
- **Confirmación:** panel centrado de 640 × 260 px, encima del de pausa.
  - Pregunta: `¿ABANDONAR LA PARTIDA?` o `¿SALIR DEL JUEGO?`.
  - Debajo, en texto-secundario: `Se perderán los puntos y las mejoras de esta partida.`
  - Opciones `NO` y `SÍ` en una fila; `NO` aparece seleccionada. Se cambia con ←→ o ↑↓.
- **Ayudas:** `↑↓ Navegar · Intro Confirmar · Esc Continuar`.

### Manual (`08-manual.svg`)
- Panel centrado de 1440 × 840 px.
- **Pestañas:** `CONTROLES`, `ENEMIGOS`, `TAMAÑOS`, `ENTORNOS` y `MEJORAS` en una fila. La actual está subrayada en **acento**. A la derecha, la posición, por ejemplo `2 / 5`.
- **Contenido de cada sección:**
  - **Controles:** tabla de teclas y acciones.
  - **Enemigos:** tres tarjetas con el símbolo del radar, el nombre, el daño, la recarga y el efecto.
  - **Tamaños:** tres tarjetas con vida, velocidad y dificultad para acertar.
  - **Entornos:** niebla y destellos, con una frase cada uno.
  - **Mejoras:** tabla con efecto, coste y niveles.
- **Ayudas:** `←→ Sección · Esc Volver`.

### Fin de partida (`09-victoria.svg`)
- Velo de pausa sobre la escena y contenido centrado, sin panel.
- **Victoria:**
  - Título `VICTORIA` a 96 px en **acento**, con un brillo suave.
  - Debajo, la frase `La ruta hacia las colonias sigue abierta.`
  - Datos: `Oleadas superadas 50 / 50`, `Nivel 3`, `Nivel 4 desbloqueado`.
  - Opciones: `SUBIR A NIVEL 4`, `VOLVER A JUGAR (NIVEL 3)` y `MENÚ PRINCIPAL`.
- **Derrota:**
  - Título `ESTACIÓN PERDIDA` en **peligro**.
  - Debajo, la frase `La Atalaya ha caído.`
  - Datos: `Oleadas superadas 23 / 50` y `Nivel 3`.
  - Opciones: `VOLVER A JUGAR` y `MENÚ PRINCIPAL`.

## 8. Movimiento

- Las pantallas de menú aparecen con un fundido y un desplazamiento vertical de 16 px en 200 ms, y desaparecen con un fundido de 150 ms.
- Al abrir la pausa, el velo se oscurece en 150 ms.
- Ninguna animación bloquea la entrada: el jugador puede actuar mientras dura.

## 9. Accesibilidad

- Contraste mínimo de 4,5 : 1 entre texto y fondo del panel.
- Los tipos de enemigo se distinguen por forma además de por color.
- Ningún aviso depende solo del sonido o solo del color: cada uno combina al menos dos de imagen, texto y sonido.
- Los destellos no producen más de tres cambios bruscos de brillo por segundo.
