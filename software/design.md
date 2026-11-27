# Diseño técnico

Este documento fija los lenguajes, herramientas, métodos y protocolos con los que se implementa lo especificado en `software/`. No contiene código. Si una decisión de este documento contradice una regla, un requisito o una restricción, prevalece la especificación y este documento debe corregirse.

## 1. Lenguaje

- **Python 3.11** (RES-05).
  - Está instalado en el equipo de desarrollo.
  - Es compatible con todas las bibliotecas elegidas.
  - Su rendimiento basta para la lógica del juego si el dibujo lo hace el motor.
- Se usan anotaciones de tipo en todo el código. La capa lógica pasa la comprobación de tipos estricta.

## 2. Motor y bibliotecas

| Necesidad | Elección | Motivo |
|---|---|---|
| Gráficos 3D, ventana y teclado | **Panda3D 1.10** | Motor 3D maduro y pensado para Python. Funciona con gráficos integrados (RNF-01). Trae cuaterniones, niebla, partículas, interfaz 2D y un medidor de rendimiento. |
| Sonido posicional y música | Audio de Panda3D con OpenAL | Sonido 3D respecto al oyente (RF-10) sin bibliotecas extra. |
| Carpeta de datos de usuario | **platformdirs** | Da la carpeta correcta de cada sistema, `%APPDATA%` en Windows, para `progreso.json`. |
| Cálculo de texturas y sonidos | **numpy** | Genera por código los fondos y los sonidos con operaciones vectorizadas, sin recorrer píxeles ni muestras en Python. |
| Lectura de datos | `json` y `dataclasses` de la biblioteca estándar | Sin dependencias adicionales para parámetros, historia y progreso. |

Alternativas descartadas:
- **pygame:** es 2D y su sonido solo se reparte entre izquierda y derecha.
- **Ursina:** es una capa sobre Panda3D que da menos control sobre el bucle y el rendimiento.
- **Godot y Unity:** no usan Python.

Las versiones exactas se fijan en `implementacion/requirements.txt` (y `requirements-dev.txt` para desarrollo). Solo se usan versiones publicadas hace al menos dos semanas.

## 3. Arquitectura

- **Capas y módulos** según `modulos/README.md`:
  - La capa lógica es Python puro y no importa Panda3D.
  - La capa de presentación (`entrada`, `escena`, `hud`, `audio`) es la única que usa el motor.
- **Bus de eventos síncrono** del núcleo. Los eventos son objetos inmutables con los datos del catálogo. Se entregan en el mismo paso y en orden de publicación.
- **Inyección de dependencias en el arranque:** cada módulo recibe en su creación los módulos que puede consultar. No hay variables globales compartidas.
- **Puertos para el exterior:** el acceso a disco de `progreso` pasa por un puerto (lectura y escritura atómica). En pruebas se sustituye por una versión en memoria.

## 4. Bucle del juego

- **Simulación a paso fijo de 1/60 s** con acumulador de tiempo. Se ejecutan como máximo 5 pasos por fotograma.
  - Garantiza que la lógica se comporte igual en cualquier equipo.
  - Hace las pruebas reproducibles.
- **Dibujo a la frecuencia de la pantalla**, con sincronización vertical activada. Posiciones y orientación se interpolan entre los dos últimos pasos de simulación.
- **El teclado se lee al principio de cada paso**, y el resultado se dibuja en ese mismo fotograma.
  - El retraso máximo es de un paso más un fotograma, unos 33 ms a 60 Hz, dentro de los 50 ms de RNF-02.
  - El disparo aparece en el primer fotograma tras soltar la barra (RNF-05).
- **Pausa:** el núcleo deja de ejecutar los pasos de la partida. Los menús siguen respondiendo (RN-50).

## 5. Matemáticas del juego

- **Orientación con cuaterniones** (RN-41).
  - Cada giro se aplica sobre los ejes locales de la cámara: lateral sobre su eje vertical, vertical sobre su eje horizontal.
  - El cuaternión se normaliza en cada paso para evitar errores acumulados.
  - No se usan ángulos de Euler, que fallan al dar la vuelta vertical completa.
- **Giro:** ángulo por paso = velocidad sin zoom × (campo de visión actual ÷ campo normal) × duración del paso (RN-40).
- **Dirección del disparo** (RN-37): la dirección de la mira que da `vista`, sin dispersión. Incluye el desvío por desestabilización (RN-12).
- **Impacto:** se calcula de forma exacta la intersección de la línea del disparo con la esfera de impacto de cada enemigo, y gana la más cercana. Con 6 enemigos activos como máximo, el coste es despreciable.
- **Movimiento de los enemigos** (RN-33): comportamiento de persecución con aceleración y velocidad máximas, y frenado al acercarse al destino. Se limita a la capa entre la distancia mínima y la máxima.
- **Proyectiles enemigos:** movimiento rectilíneo uniforme hacia el centro de la estación. Impactan al entrar en un radio de 5 u.
- **Azar:** un generador con semilla por partida, que da el núcleo. Las pruebas usan semillas fijas.

## 6. Gráficos

- **Modelos (RES-03):** geometría sencilla de pocos polígonos, con un color de emisión por tipo de enemigo. Se generan por código a partir de primitivas o se cargan en formato glTF. Si se usa glTF, se añade el complemento `panda3d-gltf`.
- **Fondos:** un cubo de cielo (seis imágenes) por cada uno de los 5 fondos, generado por código con **numpy** (estrellas, nebulosas y polvo galáctico) y guardado en la caché de usuario para que los arranques siguientes sean inmediatos. El fondo 1 se prepara al arrancar; los demás se generan en un proceso aparte para no restar fluidez.
- **Paisaje de cada fondo:** planetas y lunas (esferas con texturas generadas con numpy y guardadas en la misma caché), anillos, cinturones de asteroides de pocos polígonos y polvo cercano. Los asteroides lejanos se unen en pocas geometrías para dibujarlos de una vez. El paisaje del fondo de destino se construye y se sube a la tarjeta gráfica en el descanso previo al salto. El paso de un fondo al siguiente es un salto hiperespacial animado.
- **Niebla:**
  - El color de enemigos y proyectiles se mezcla con el del fondo según la visibilidad que calcula `entorno` para su distancia.
  - Se aplica objeto a objeto, para que el radar y la interfaz no se vean afectados.
- **Destellos:** un velo blanco a pantalla completa con transparencia animada.
- **Efectos:**
  - Disparo: haz bláster que vuela del cañón al impacto en 0,1 s como mucho.
  - Explosiones y chispas: partículas propias. Las chispas de cada efecto son una sola geometría de puntos con textura, así que cuestan un único dibujo.
  - Salto hiperespacial: estelas cuyos vértices se escriben con numpy en cada fotograma y un túnel con textura que se desplaza.
  - Las texturas y estados de los efectos se suben a la tarjeta gráfica en el menú, para que el primer uso no dé tirones.
  - Temblor: desplazamiento de la cámara con ruido suave.
- **Resolución:** pantalla completa con la resolución nativa de la pantalla; 1920 × 1080 si el sistema no la informa. El campo de visión vertical es fijo y el horizontal se calcula con la proporción de la pantalla, para que la imagen no se deforme. La interfaz se escala según la altura de la ventana.
- **Medición:** el medidor PStats de Panda3D se usa para comprobar RNF-01 en el equipo de referencia.

## 7. Sonido

- **Origen y formato:** los sonidos se generan por código con numpy (recursos propios) y se guardan como WAV mono de 16 bits a 44,1 kHz en la caché de usuario. Desde el segundo arranque se cargan al momento. Cualquiera se puede sustituir por un archivo WAV u OGG de `implementacion/recursos/sonidos/`, indicado en `sonidos.json`, con su autor y licencia en `CREDITOS.md`.
- **Sonidos posicionales:** se colocan en la posición de cada enemigo (motor, aviso de disparo, disparos y explosión). El oyente se coloca en la cámara en cada fotograma.
- **Registro:** todos los sonidos son graves; las pruebas comprueban que el centro de su espectro queda por debajo de 2 kHz.
- **Sonido de fondo:** sin música. El fondo de la oleada es la suma de los motores de las naves, más graves y fuertes cuanto más cerca, sobre un zumbido provisional de la estación, según `modulos/audio.md`. Los bucles son periódicos de forma exacta y no tienen saltos al repetirse.

## 8. Datos

Todos los archivos son JSON en UTF-8 con un campo `version`.

| Archivo | Dónde | Contenido |
|---|---|---|
| `parametros.json` | datos del juego, junto al código | Valores de «Parámetros iniciales» de `reglasNegocio.md` |
| `historia.json` | datos del juego, junto al código | Textos de las transmisiones de radio |
| `progreso.json` | carpeta de datos de usuario | Nivel desbloqueado, según `basesDatos/especificacion.md` |

- Los parámetros se validan al arrancar según `modulos/parametros.md`.
- `parametros.json` y la tabla de `reglasNegocio.md` deben coincidir. Una prueba automática compara ambos.

## 9. Organización del código

Todo vive en `implementacion/` (RES-06):

| Ruta | Contenido |
|---|---|
| `implementacion/.venv/` | entorno virtual (no se sube al repositorio) |
| `implementacion/atalaya/logica/` | un subpaquete por módulo lógico |
| `implementacion/atalaya/presentacion/` | un subpaquete por módulo de presentación |
| `implementacion/atalaya/arranque` | punto de entrada |
| `implementacion/datos/` | `parametros.json` e `historia.json` |
| `implementacion/recursos/` | modelos, texturas, sonidos y fuentes, con `CREDITOS.md` |
| `implementacion/pruebas/` | pruebas automáticas, con la misma estructura que la capa lógica |
| `implementacion/requirements.txt` y `requirements-dev.txt` | dependencias con versiones fijadas |

- **Nombres:** paquetes y módulos en minúsculas sin acentos; clases en `PascalCase`; funciones y variables en `snake_case`.
- **Idioma:** los nombres del dominio van en español, igual que en la especificación (estacion, oleada, mira).

## 10. Calidad y pruebas

- **pytest** para las pruebas automáticas y **pytest-cov** para la cobertura.
  - Cada criterio de aceptación de los casos de uso que dependa de la lógica tiene al menos una prueba.
  - Cada prueba indica en su nombre o descripción el CU, RF o RN que comprueba.
  - Objetivo de cobertura de la capa lógica: 90 %.
- **ruff** para el estilo y el formato; **mypy** en modo estricto para la capa lógica.
- **Desarrollo guiado por pruebas** en la capa lógica: se escribe la prueba del criterio de aceptación y después el código.
- **Pruebas manuales** de la capa de presentación, con una lista de comprobación por caso de uso.
- **Rendimiento:** antes de cerrar cada fase se mide RNF-01 en el equipo de referencia con PStats.

## 11. Plan de construcción

Se construye por fases. Cada fase termina con un juego ejecutable y sus pruebas en verde.

1. **Núcleo jugable:**
   - giro, mira de precisión, disparo y energía,
   - enemigo sin efecto especial,
   - radar e integridad,
   - 5 oleadas sin descanso,
   - sonido mínimo.
2. **Combate completo:**
   - los tres tipos y tamaños de enemigo,
   - aviso y proyectiles,
   - desestabilización y aturdimiento,
   - descanso con pantalla de mejoras,
   - pausa, menú principal y manual.
3. **Partida completa:**
   - 50 oleadas y victoria,
   - niveles de dificultad y progreso guardado,
   - historia,
   - 5 fondos y salto hiperespacial,
   - niebla y destellos.
4. **Acabado:**
   - sonido posicional completo y música,
   - efectos visuales finales,
   - ajuste de parámetros jugando,
   - empaquetado.

## 12. Distribución

- Ejecutable para Windows generado con la herramienta de empaquetado de Panda3D (`build_apps`). Incluye el intérprete, el motor, los datos y los recursos.
- Sin instalador en el primer prototipo: una carpeta comprimida que se descomprime y se ejecuta.

## 13. Protocolos y convenciones

- **Sin red:** el juego no abre conexiones ni envía datos (RES-07).
- **Contrato interno:** el catálogo de eventos de `modulos/README.md` es el contrato entre módulos. Un evento nuevo o un cambio en sus datos se añade primero al catálogo.
- **Formato de archivos:** JSON UTF-8 con campo `version`. Un cambio de formato sube la versión y el código acepta las versiones anteriores.
- **Versiones del juego:** versionado semántico (mayor.menor.corrección).
- **Control de versiones:** Git. Los commits los crea el propietario del repositorio.
- **Registro de errores:** módulo `logging` de la biblioteca estándar, con un archivo de registro en la carpeta de datos de usuario. No guarda datos personales.

## 14. Recursos y licencias

- Solo se usan recursos propios o con licencia CC0 o compatible, por ejemplo de Kenney, OpenGameArt o Freesound filtrando por CC0.
- Cada recurso externo se anota en `implementacion/recursos/CREDITOS.md` con su autor, origen y licencia.
- Las dependencias de código deben tener licencia libre compatible con la distribución: Panda3D usa BSD modificada, platformdirs usa MIT y numpy usa BSD.
