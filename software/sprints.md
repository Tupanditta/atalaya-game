# Plan de sprints

Este documento divide la implementación del primer prototipo en 10 sprints, del S0 al S9. Detalla el plan de construcción por fases de `design.md` (sección 11). Cada sprint define su alcance, su entregable y las pruebas que demuestran que está terminado.

## Correspondencia con las fases de `design.md`

| Fase | Sprints | Al cerrar la fase |
|---|---|---|
| 1. Núcleo jugable | S0, S1, S2, S3 | Partida jugable con un tipo de enemigo, radar e integridad |
| 2. Combate completo | S4, S5, S6 | Tres tipos y tamaños, descanso con mejoras, menús, pausa y manual |
| 3. Partida completa | S7, S8 | 50 oleadas, victoria, niveles, progreso, historia y entornos |
| 4. Acabado | S9 | Sonido y música completos, efectos finales, ajuste y ejecutable |

## Convenciones de las pruebas

- **Identificadores:**
  - `S<n>-T<nn>`: prueba automática.
  - `S<n>-M<nn>`: comprobación manual.
- **Trazabilidad:** la descripción de cada prueba empieza por su identificador y el CU, RF, RN o RNF que comprueba (`design.md`, sección 10).
- **Ubicación:**
  - Pruebas de cada módulo lógico: `implementacion/pruebas/<modulo>/`.
  - Pruebas de arquitectura: `implementacion/pruebas/arquitectura/`.
  - Pruebas de integración: `implementacion/pruebas/integracion/`.
- **Valores esperados:** las pruebas leen los valores de juego de `parametros`. Las cifras de este documento se calculan con los «Parámetros iniciales» de `reglasNegocio.md` y sirven de referencia. Si se ajusta un parámetro, la prueba sigue siendo válida.
- **Tiempo:** las pruebas avanzan el núcleo en pasos de 1/60 s. Una tolerancia de «±1 paso» significa ±1/60 s.
- **Azar:** todas las pruebas usan una semilla fija.
- **Pruebas lentas:** las simulaciones de partidas largas llevan la marca `lenta`. Se ejecutan al cerrar el sprint, no en cada cambio.
- **Jugador automático:** utilidad de pruebas que juega sin teclado. En cada paso gira con los ejes de giro hacia el enemigo más cercano y suelta la barra espaciadora cuando la mira está sobre él. Solo usa las mismas acciones que el jugador.
- **Regresión:** las pruebas de los sprints anteriores siguen en verde en todos los sprints.

## Definición de terminado

Un sprint está terminado cuando se cumplen todas estas condiciones:

1. Todas las pruebas automáticas del sprint y de los anteriores pasan, incluidas las lentas.
2. La cobertura de la capa lógica es del 90 % o más.
3. `ruff` no da avisos y `mypy` en modo estricto no da errores en la capa lógica.
4. Desde S1, el juego arranca con el punto de entrada `atalaya.arranque`.
5. Todas las comprobaciones manuales del sprint se han hecho y su resultado está anotado.
6. Los eventos que se usan coinciden con el catálogo de `modulos/README.md`.
7. Al cerrar una fase (S3, S6, S8 y S9), se mide RNF-01 en el equipo de referencia con PStats.

Comandos de verificación, desde la raíz del repositorio:

```
.\implementacion\.venv\Scripts\python.exe -m pytest implementacion/pruebas --cov=atalaya.logica --cov-fail-under=90
.\implementacion\.venv\Scripts\python.exe -m ruff check implementacion
.\implementacion\.venv\Scripts\python.exe -m ruff format --check implementacion
.\implementacion\.venv\Scripts\python.exe -m mypy --strict implementacion/atalaya/logica
```

---

## Sprint 0. Base del proyecto

**Objetivo:** tener la estructura, las herramientas y los dos módulos de los que dependen todos los demás.

**Alcance:**
- Estructura de carpetas de `design.md` (sección 9) y entorno virtual `implementacion/.venv`.
- `requirements.txt` (Panda3D, platformdirs) y `requirements-dev.txt` (pytest, pytest-cov, ruff, mypy), con versiones fijadas.
- Configuración de ruff, mypy y pytest (marca `lenta`).
- Módulo `nucleo`: bucle a paso fijo, reloj pausable, bus de eventos y azar con semilla.
- Todas las clases de evento del catálogo, inmutables.
- Módulo `parametros` y archivo `datos/parametros.json`.

**Entregable:** paquete instalable sin ventana. Las pruebas se ejecutan.

### Pruebas automáticas

| ID | Comprueba | Escenario | Resultado esperado |
|---|---|---|---|
| S0-T01 | nucleo, paso fijo | Avanzar 1/60 s | Se ejecuta 1 paso |
| S0-T02 | nucleo, acumulador | Avanzar 0,05 s; después avanzar 0,01 s dos veces | 3 pasos; después 0 pasos y 1 paso |
| S0-T03 | nucleo, límite de pasos | Avanzar 1 s; después avanzar 0 s | 5 pasos; el resto se descarta y después hay 0 pasos |
| S0-T04 | RN-50 | Pausar el reloj y avanzar 1 s; reanudar y avanzar 1/60 s | 0 pasos y el tiempo acumulado no cambia; después 1 paso |
| S0-T05 | Orden de actualización | Registrar módulos falsos que anotan su llamada | Se llaman en el orden de `modulos/README.md` |
| S0-T06 | Bus de eventos | Publicar A y B; un suscriptor de A publica C | Los suscriptores reciben A, B y C en el mismo paso y en orden de publicación |
| S0-T07 | Eventos inmutables | Cambiar un campo de un evento publicado | Se lanza un error |
| S0-T08 | Azar con semilla | Dos generadores con la misma semilla; uno con otra semilla | La misma semilla da la misma secuencia; la otra da una secuencia distinta |
| S0-T09 | parametros, carga | Cargar `parametros.json` | Carga sin errores y los grupos de valores son de solo lectura |
| S0-T10 | parametros, valor ausente | Archivo sin el coste del disparo | Error que nombra el valor que falta |
| S0-T11 | parametros, tipo | Un valor numérico escrito como texto | Error que nombra el valor |
| S0-T12 | parametros, relaciones | Distancia mínima 800 (≥ alcance de disparo 700); alcance ≥ distancia máxima; distancia máxima ≥ alcance del radar; mira mínima ≥ mira normal | Cada caso da un error que nombra la relación que falla |
| S0-T13 | RN-22, vida | Vida por tamaño y nivel | Pequeño en nivel 1: 10; pequeño en nivel 3: 15; grande en nivel 5: 80 |
| S0-T14 | RN-18, RN-22, descanso | Descanso por nivel | Nivel 1: 20 s; nivel 2: 17,75 s; nivel 3: 15,8375 s; baja con cada nivel y siempre es mayor que 5 s |
| S0-T15 | RN-16, composición | Enemigos y tipos por oleada | Oleada 1: 3; 2: 4; 5: 5; 10: 8; 50: 28. El número nunca baja de una oleada a la siguiente. Oleadas 1 a 4: solo sin efecto especial; 5 a 9: también desestabilizadores; desde la 10: los tres tipos. Máximo de enemigos con efecto: parte entera de un tercio de la oleada |
| S0-T16 | RN-44, entorno de la oleada | Entorno por número de oleada | 14: ninguno; 15: niebla; 16: ninguno; 18: destellos; 21: niebla; 45: niebla; 48: destellos; 50: ninguno |
| S0-T17 | Coherencia de datos | Comparar `parametros.json` con las tablas de «Parámetros iniciales» de `reglasNegocio.md` | Todos los valores coinciden |
| S0-T18 | Arquitectura, capas | Analizar las importaciones de `atalaya.logica` | Ningún módulo lógico importa Panda3D ni `atalaya.presentacion` |
| S0-T19 | Arquitectura, dependencias | Analizar las importaciones entre módulos lógicos | Solo existen las de la tabla de dependencias, más `nucleo` y `parametros` |
| S0-T20 | Tiempo y azar del núcleo | Buscar en la capa lógica usos del reloj del sistema y del azar global | Ningún módulo salvo `nucleo` usa `time`, `datetime.now` ni `random` |
| S0-T21 | Catálogo de eventos | Comparar las clases de evento con el catálogo | Existe una clase por evento, con los datos del catálogo |

### Comprobaciones manuales

- **S0-M01:** el entorno virtual se crea desde cero e instala `requirements.txt` y `requirements-dev.txt` sin errores.
- **S0-M02:** `ruff` y `mypy` se ejecutan con la configuración del proyecto.

---

## Sprint 1. Vista y ventana

**Objetivo:** abrir el juego y girar la vista en el espacio.

**Alcance:**
- Módulo `vista`: orientación con cuaterniones, giro sobre los ejes de la cámara, flechas opuestas, giro más lento con zoom y campo de visión según el apuntado. El desvío por desestabilización y el bloqueo por aturdimiento quedan para S4.
- Módulo `entrada`: teclado y acciones.
- `flujo` mínimo: una sola pantalla de oleada en curso que entrega los ejes de giro a `vista`.
- `escena` mínima: ventana a pantalla completa, cámara y fondo 1.
- `arranque`: crea los módulos, inyecta sus dependencias, ejecuta el bucle e interpola la orientación entre pasos.

**Entregable:** el juego abre una ventana con el fondo espacial y la vista gira con las flechas.

### Pruebas automáticas

| ID | Comprueba | Escenario | Resultado esperado |
|---|---|---|---|
| S1-T01 | RF-02 | Flecha derecha durante 60 pasos | El eje «adelante» coincide con el eje «derecha» inicial (giro de 90°) |
| S1-T02 | RF-03 | Flecha arriba durante 60 pasos | El eje «adelante» coincide con el eje «arriba» inicial |
| S1-T03 | RN-26 | Izquierda y derecha; arriba, izquierda y derecha; las cuatro flechas | No gira; solo gira hacia arriba; no gira |
| S1-T04 | RF-21 | Arriba y derecha a la vez | Gira en los dos ejes en el mismo paso |
| S1-T05 | RN-41 | Flecha arriba durante 120 pasos (180°); después flecha derecha durante 60 pasos | Tras la media vuelta, el eje «arriba» de la cámara es el contrario del inicial. Después, «adelante» coincide con el eje «derecha» que tenía la cámara antes del giro lateral |
| S1-T06 | RN-41, vuelta completa | Flecha arriba durante 240 pasos (360°) | La orientación vuelve a la inicial, sin bloqueo de ejes |
| S1-T07 | Estabilidad numérica | 100 000 pasos de giro combinado | El cuaternión tiene norma 1 (±1e-9) y los ejes son ortonormales |
| S1-T08 | RN-40 | Publicar ApuntadoCambiado con progreso 1 y girar 1 paso | El ángulo girado es 1,5° × 25/70 ≈ 0,536° |
| S1-T09 | RN-39, RF-33 | ApuntadoCambiado con progreso 0, 0,5 y 1 | Campo de visión de 70°, uno estrictamente entre 25° y 70°, y 25° |
| S1-T10 | RNF-04 | Flecha derecha durante 120 pasos | Cada paso gira exactamente 1,5°, sin aceleraciones ni saltos |
| S1-T11 | PartidaIniciada | Girar y cambiar el zoom; publicar PartidaIniciada | Orientación inicial y campo de visión de 70° |
| S1-T12 | entrada | Fuente de teclado falsa: pulsar, mantener y soltar una tecla | Estados «recién pulsada», «mantenida» y «recién soltada» en los pasos correctos |
| S1-T13 | entrada, foco | Teclas pulsadas y la ventana pierde el foco | Todas las acciones se informan como sueltas |
| S1-T14 | Interpolación | Interpolar entre dos orientaciones con factor 0,5 | Resultado a medio camino en ángulo y con norma 1 |

### Comprobaciones manuales

- **S1-M01:** la ventana abre a pantalla completa en 1920 × 1080 con el fondo espacial.
- **S1-M02:** cada flecha gira la vista en su sentido en pantalla, también tras una media vuelta vertical.
- **S1-M03:** el giro es suave y sin tirones (RNF-04) y responde al instante al pulsar y soltar (RNF-02).

---

## Sprint 2. Disparo y primeros enemigos

**Objetivo:** apuntar, disparar y destruir enemigos que se mueven.

**Alcance:**
- Módulo `armamento` completo, salvo el aturdimiento (S4) y las mejoras (S5).
- Módulo `enemigos`: aparición, movimiento con inercia, límites de distancia y resolución del disparo. Solo tipo sin efecto especial y tamaño mediano. Los enemigos todavía no atacan.
- Módulo `oleadas`: solo la aparición (ritmo y máximo de enemigos activos) para la composición de la oleada en curso.
- `hud`: mira y barra de energía con parpadeo sin energía.
- `escena`: modelo de enemigo, rayo del disparo, destello de impacto y explosión básica.

**Entregable:** aparecen enemigos que se mueven en curvas. El jugador los apunta con zoom y los destruye.

### Pruebas automáticas

| ID | Comprueba | Escenario | Resultado esperado |
|---|---|---|---|
| S2-T01 | RN-02 | PartidaIniciada | Energía 100 de 100 |
| S2-T02 | RN-03, RF-05 | Pulsar y soltar la barra | DisparoRealizado y EnergiaCambiada; energía 90 |
| S2-T03 | RN-05, RF-11 | 10 disparos seguidos en 20 pasos; un disparo más | El undécimo publica DisparoSinEnergia, no publica DisparoRealizado y la energía no cambia |
| S2-T04 | RN-04 | Energía 90 y esperar 1 s; esperar 1 s más | 98; después 100, sin superar la máxima |
| S2-T05 | RN-04 | Recarga con la barra pulsada | La energía sube igual que sin apuntar |
| S2-T06 | RN-38, RF-32 | Barra pulsada 0,75 s, 1,5 s y 3 s | Progreso de apuntado 0,5; 1; 1. Mira de 3° con progreso 0 y de 0,5° con progreso 1; nunca menor |
| S2-T07 | RN-38 | Soltar la barra con progreso 1 | A los 0,1 s el progreso está entre 0 y 1; a los 0,2 s es 0 |
| S2-T08 | RN-39 | Apuntar 1,5 s con `armamento` y `vista` conectados | `vista` recibe ApuntadoCambiado y su campo de visión es 25° |
| S2-T09 | RN-37 | 10 000 disparos con la mira normal y semilla fija | Todos dentro de 3° de la dirección de la mira. Ángulo medio de 2° (±0,05°). Un 25 % (±1,5 %) dentro de 1,5° |
| S2-T10 | RN-37 | 10 000 disparos con la mira mínima | Todos dentro de 0,5° |
| S2-T11 | RN-23, RNF-05 | Soltar la barra en el paso N | DisparoRealizado se publica en el paso N |
| S2-T12 | Cancelar el apuntado | Cancelar con la barra pulsada y soltar; pulsar y soltar otra vez | El primer suelte no dispara y el progreso vuelve a 0; el segundo dispara |
| S2-T13 | RN-32 | 1000 apariciones con semilla fija | Distancia entre 900 y 1000 u; hay apariciones en los 8 octantes |
| S2-T14 | Aparición | SolicitudAparicion de un enemigo mediano con vida 20 | EnemigoAparecido con su id, tipo y tamaño; vida 20 |
| S2-T15 | RN-30, RN-31 | 6 enemigos durante 300 s simulados | En todos los pasos, la distancia de cada enemigo está entre 150 y 1000 u |
| S2-T16 | RN-33 | 6 enemigos durante 300 s simulados | Velocidad ≤ 70 u/s. Entre dos pasos, el cambio de velocidad no supera 35 u/s² × 1/60 s ≈ 0,583 u/s. Desde parado, llega a la velocidad máxima en 2 s (±1 paso) |
| S2-T17 | RN-33, llegada | Enemigo con un destino fijo en línea recta | Frena de forma gradual al acercarse. Al quedar a menos de 50 u del destino, elige otro destino |
| S2-T18 | RN-29 | 6 enemigos durante 300 s simulados | Cada enemigo cambia de dirección en horizontal y en vertical |
| S2-T19 | RN-07 | Enemigo mediano a 500 u justo delante; dos disparos en la dirección exacta | EnemigoAlcanzado con vida 10; después EnemigoDestruido con su posición, y deja de estar en la lista |
| S2-T20 | Impacto, el más cercano | Dos enemigos alineados a 300 y 600 u | Solo se daña el de 300 u |
| S2-T21 | Impacto, esfera | Enemigo a 500 u desplazado 11 u y 13 u del eje del disparo (radio 12 u) | Con 11 u hay impacto; con 13 u no |
| S2-T22 | Impacto, sentido | Enemigo justo detrás de la estación | El disparo no lo alcanza |
| S2-T23 | Limpieza | PartidaIniciada o PartidaAbandonada con enemigos activos | No quedan enemigos |
| S2-T24 | RN-43, RF-09 | Oleada 10 (8 enemigos) sin destruir ninguno | Nunca hay más de una SolicitudAparicion cada 2 s. A los 12 s hay 6 activos y 2 pendientes |
| S2-T25 | RN-43 | En el escenario anterior, destruir un enemigo | En 2 s o menos vuelve a haber 6 activos |

### Comprobaciones manuales

- **S2-M01:** al mantener la barra, la mira se reduce y el zoom aumenta a la vez, como en `interfaz/04-apuntando.svg`.
- **S2-M02:** al soltar la barra, el rayo se ve y se desvanece en 0,1 s; al acertar hay un destello; al destruir hay una explosión.
- **S2-M03:** los enemigos describen curvas y nunca cambian de dirección de golpe.
- **S2-M04:** la barra de energía baja con cada disparo, se recarga y parpadea al disparar sin energía.

---

## Sprint 3. Ataque, radar e integridad

Cierra la fase 1.

**Objetivo:** partida jugable de principio a derrota con un tipo de enemigo.

**Alcance:**
- `enemigos`: ataque del tipo sin efecto especial (aviso, proyectil y recarga).
- Módulo `estacion`: integridad y destrucción. Los efectos especiales quedan para S4.
- Módulo `radar`.
- `oleadas`: cronómetro, fin de oleada y paso directo a la siguiente oleada, sin descanso (el descanso llega en S5).
- `hud`: radar, barra de integridad, número de oleada, enemigos restantes y resumen mínimo de derrota.
- `escena`: proyectiles, destello de aviso, temblor de 0,3 s y tinte rojo al recibir daño.
- `audio` mínimo, sin posición: disparo, aviso, impacto, explosión, falta de energía y alarma de daño.
- La partida empieza directamente en la oleada 1 al abrir el juego (CU-01 sin menús).

**Entregable:** el jugador defiende la estación oleada tras oleada hasta que la integridad llega a cero.

### Pruebas automáticas

| ID | Comprueba | Escenario | Resultado esperado |
|---|---|---|---|
| S3-T01 | RN-42 | Enemigo a 800 u con la recarga terminada | No publica AvisoDisparo mientras está a más de 700 u. En 30 s simulados entra en el alcance y publica AvisoDisparo |
| S3-T02 | RN-34 | Enemigo dentro del alcance publica AvisoDisparo | ProyectilLanzado 1 s después (±1 paso) |
| S3-T03 | RN-34 | Destruir el enemigo durante el aviso | No publica ProyectilLanzado |
| S3-T04 | RN-14 | Enemigo sin efecto que sigue dentro del alcance | Entre un ProyectilLanzado y el siguiente AvisoDisparo pasan 4 s (±1 paso) |
| S3-T05 | RN-35 | Proyectil lanzado desde 600 u | Avanza en línea recta hacia el centro a 300 u/s. ProyectilImpacta a los (600 − 5)/300 ≈ 1,983 s (±1 paso) |
| S3-T06 | RN-36 | Destruir el enemigo con su proyectil en vuelo | El proyectil sigue y publica ProyectilImpacta |
| S3-T07 | RN-10 | ProyectilImpacta de tipo sin efecto | Integridad 97. EstacionDanada (3, 97, 100) e IntegridadCambiada (97, 100) |
| S3-T08 | RN-17 | 35 impactos sin efecto | El impacto 34 deja la integridad en 0, sin valores negativos. EstacionDestruida se publica una sola vez; el impacto 35 no cambia nada |
| S3-T09 | EstacionDestruida | Estación destruida con enemigos y proyectiles activos | `enemigos` queda vacío y `oleadas` no publica más SolicitudAparicion |
| S3-T10 | RF-07, radar, ángulo | Enemigo delante, a la derecha, detrás y a la izquierda | Ángulo de 0°, 90°, 180° y 270°, medido en sentido horario desde «adelante» |
| S3-T11 | RF-31 | Enemigo a 600 u y a 1200 u | Distancia relativa 0,5 y 1 |
| S3-T12 | Radar, altura | Enemigo 20° por encima, 10° por encima, exactamente 15° y 20° por debajo del plano de la cámara | «Por encima», «a la misma altura», «por encima» y «por debajo» |
| S3-T13 | RN-41 | Girar la cámara 90° a la derecha con un enemigo a la derecha | El enemigo pasa a 0° |
| S3-T14 | RN-41 | Media vuelta vertical con un enemigo en el «arriba» inicial | El enemigo pasa a «por debajo» |
| S3-T15 | Campo de visión | Enemigo a 20° del centro, sin zoom y con zoom máximo | Dentro del campo de visión sin zoom; fuera con zoom |
| S3-T16 | RN-09 | 6 enemigos activos | El radar devuelve 6 contactos |
| S3-T17 | RN-15 | Destruir los 3 enemigos de la oleada 1 | Una sola OleadaSuperada (1, tiempo, 3) y después OleadaIniciada (2) |
| S3-T18 | Cronómetro | El último enemigo se destruye 20 s después de aparecer el primero | OleadaSuperada con tiempo de 20 s (±1 paso) |
| S3-T19 | Integración (lenta) | Jugador automático, semilla fija, desde el inicio de la partida | Supera las oleadas 1 a 5 sin que la estación sea destruida |

### Comprobaciones manuales

- **S3-M01:** el radar coincide con `interfaz/03-oleada.svg`. Un enemigo a la derecha de la vista aparece a la derecha del radar.
- **S3-M02:** el aviso de disparo se ve y se oye 1 s antes de que salga el proyectil.
- **S3-M03:** al recibir daño, la cámara tiembla, los bordes se tiñen de rojo y suena la alarma.
- **S3-M04:** la integridad, el número de oleada y los enemigos restantes se actualizan en pantalla.
- **S3-M05:** al llegar la integridad a cero aparece el resumen de derrota.
- **S3-M06:** medición de RNF-01 con 6 enemigos y proyectiles activos (cierre de fase 1).

---

## Sprint 4. Tipos, tamaños y efectos

**Objetivo:** combate completo con los tres tipos y los tres tamaños de enemigo.

**Alcance:**
- `enemigos` y `oleadas`: tamaños pequeño, mediano y grande; tipos desestabilizador y aturdidor; composición completa de las oleadas.
- `estacion`: desestabilización y aturdimiento.
- `vista`: desvío de la mira y bloqueo del giro por aturdimiento.
- `armamento`: bloqueo del disparo y cancelación del apuntado por aturdimiento.
- `hud`: aviso de aturdimiento, mira desviada, símbolo y color de cada tipo y tamaño en el radar.
- `escena`: modelo y color de emisión por tipo, escala por tamaño y temblor continuo de la imagen.
- `audio`: sonido de aturdimiento.

**Entregable:** las oleadas mezclan tipos y tamaños, y cada tipo tiene su efecto sobre el jugador.

### Pruebas automáticas

| ID | Comprueba | Escenario | Resultado esperado |
|---|---|---|---|
| S4-T01 | RN-06, RN-33 | Simular un enemigo de cada tamaño durante 300 s | Velocidad máxima observada ≤ 110, 70 y 40 u/s. Cambio de velocidad por paso ≤ 55, 35 y 20 u/s² × 1/60 s |
| S4-T02 | RN-06, zona de impacto | Enemigo a 500 u desplazado del eje del disparo: pequeño a 5 y 7 u; grande a 23 y 25 u | Pequeño: impacto con 5 u y fallo con 7 u. Grande: impacto con 23 u y fallo con 25 u |
| S4-T03 | RN-06, vida | Disparos exactos en nivel 1 | Pequeño: 1 disparo; mediano: 2; grande: 4 |
| S4-T04 | RN-11 | ProyectilImpacta de cada tipo con integridad 100 | Sin efecto: 97; desestabilizador: 99; aturdidor: 98 |
| S4-T05 | RN-12 | Impacto desestabilizador | DesestabilizacionIniciada (3 s) y DesestabilizacionTerminada 3 s después (±1 paso) |
| S4-T06 | RN-12, renovación | Segundo impacto desestabilizador a los 2 s | Una sola DesestabilizacionTerminada, a los 5 s del primero |
| S4-T07 | RN-12, desvío | Simular 3 s de desestabilización | La dirección de la mira se separa del centro, sin superar 2°. Entre dos pasos, el desvío cambia como máximo 30 °/s × 1/60 s = 0,5°. Al terminar, el desvío vuelve a 0 |
| S4-T08 | RN-12, disparo desviado | 1000 disparos durante la desestabilización | Cada dirección cae dentro del cono de la mira alrededor de la dirección desviada |
| S4-T09 | RN-13, giro | Impacto aturdidor y flecha derecha pulsada 1,5 s | La orientación no cambia durante el aturdimiento; vuelve a girar después de AturdimientoTerminado |
| S4-T10 | RN-13, disparo | Soltar la barra durante el aturdimiento | No hay DisparoRealizado ni DisparoSinEnergia |
| S4-T11 | RN-38 | Aturdimiento con la barra pulsada | El progreso de apuntado vuelve a 0. Tras el aturdimiento, con la barra aún pulsada, no se apunta ni se dispara hasta soltarla y pulsarla otra vez |
| S4-T12 | RN-04 | Aturdimiento de 1,5 s con energía 50 | La energía sube a 62 |
| S4-T13 | RN-13, renovación | Segundo impacto aturdidor a los 1 s | Un solo AturdimientoTerminado, a los 2,5 s del primero |
| S4-T14 | RN-14 | Enemigo de cada tipo que sigue dentro del alcance | Recarga entre disparos: sin efecto 4 s; desestabilizador 3 s; aturdidor 8 s |
| S4-T15 | RN-16 | Generar con semilla fija 100 partidas de 50 oleadas | Oleadas 1 a 4: solo sin efecto. 5 a 9: sin aturdidores. En todas, enemigos con efecto ≤ parte entera de un tercio de la oleada. En la oleada 1 aparecen los tres tamaños a lo largo de las 100 partidas |
| S4-T16 | RN-22 | SolicitudAparicion en nivel 1 | La vida coincide con la de su tamaño |

### Comprobaciones manuales

- **S4-M01:** el aviso de aturdimiento se ve como en `interfaz/05-aturdido.svg` y suena el sonido de aturdimiento.
- **S4-M02:** durante la desestabilización, la imagen tiembla y la mira se desvía de la misma forma.
- **S4-M03:** cada tipo y tamaño se distingue en la escena y en el radar (RF-22, RF-23).
- **S4-M04:** los enemigos pequeños se mueven claramente más rápido que los grandes.

---

## Sprint 5. Descanso y mejoras

**Objetivo:** descanso entre oleadas con la pantalla de mejoras.

**Alcance:**
- `oleadas`: descanso, cuenta atrás y fin anticipado.
- Módulo `mejoras`.
- `estacion`: reparación y blindaje.
- `armamento`: batería y generador.
- `flujo`: pantalla de descanso, selección de opciones y Continuar.
- `hud`: pantalla de mejoras con resultado de la oleada, puntos, opciones, costes, niveles y cuenta atrás. El hueco de la transmisión queda vacío hasta S8.

**Entregable:** tras cada oleada se abre la pantalla de mejoras. El jugador repara o mejora y continúa.

### Pruebas automáticas

| ID | Comprueba | Escenario | Resultado esperado |
|---|---|---|---|
| S5-T01 | RN-18 | Superar la oleada 1 en nivel 1 | OleadaSuperada y después DescansoIniciado (20 s, oleada 2). Durante el descanso no hay SolicitudAparicion. A los 20 s, DescansoTerminado y OleadaIniciada (2) |
| S5-T02 | RF-44 | TerminarDescansoSolicitado a los 5 s del descanso | DescansoTerminado en ese mismo paso |
| S5-T03 | RN-45 | Oleada 1 (3 enemigos, referencia 25 s) superada en 25 s, 25,01 s, 50 s, 50,01 s y 500 s | 3, 2, 2, 1 y 1 puntos |
| S5-T04 | RF-43 | Superar una oleada | PuntosObtenidos con puntos obtenidos, disponibles, tiempo y tiempo de referencia |
| S5-T05 | RN-45, acumulación | Obtener 3 puntos y después 2 sin gastar | 5 puntos disponibles |
| S5-T06 | RN-48 | Reparar y mejorar durante una oleada | No hay evento. Motivo: fuera del descanso |
| S5-T07 | RN-46, RF-41 | Integridad 70 de 100 con 3 puntos; reparar tres veces | 90; 100; la tercera no hace nada (motivo: integridad al máximo). Queda 1 punto |
| S5-T08 | Reparar sin puntos | Integridad 70 y 0 puntos | No hace nada. Motivo: sin puntos |
| S5-T09 | RN-47, blindaje | Integridad 80 de 100; comprar blindaje | Nivel 1; integridad 90 de 110; cuesta 2 puntos |
| S5-T10 | RN-47, nivel máximo | Comprar blindaje 6 veces con puntos de sobra | 5 niveles. La sexta compra no hace nada (motivo: nivel máximo) |
| S5-T11 | RN-47, batería | Comprar batería | Energía máxima 110 |
| S5-T12 | RN-47, generador | Comprar generador y recargar 1 s desde 0 | Energía 9 |
| S5-T13 | Puntos insuficientes | 1 punto y comprar una mejora | No hace nada. Motivo: sin puntos |
| S5-T14 | RN-49, RN-02 | Partida con mejoras y puntos; PartidaIniciada | 0 puntos, mejoras a nivel 0, energía 100 de 100, integridad 100 de 100, recarga 8 por segundo |
| S5-T15 | Opciones disponibles | Consultar con distintos puntos, niveles e integridad | Solo se marcan disponibles las opciones que se pueden comprar |
| S5-T16 | flujo | DescansoIniciado; Continuar; DescansoTerminado | Pantalla de descanso; TerminarDescansoSolicitado; oleada en curso |
| S5-T17 | flujo | Flechas pulsadas en la pantalla de mejoras | Mueven la selección; la orientación de `vista` no cambia |

### Comprobaciones manuales

- **S5-M01:** la pantalla de mejoras coincide con `interfaz/06-mejoras.svg`: resultado de la oleada, puntos, opciones, costes, niveles y cuenta atrás.
- **S5-M02:** una opción no disponible se ve deshabilitada y al elegirla suena el sonido de error.
- **S5-M03:** Continuar empieza la siguiente oleada sin esperar a la cuenta atrás.

---

## Sprint 6. Menús, pausa y manual

Cierra la fase 2.

**Objetivo:** juego completo de pantallas, salvo la selección de nivel y la victoria.

**Alcance:**
- `flujo` completo: menú principal, pausa, confirmación, manual, resumen de derrota y salida.
- `hud`: menú principal, pausa, confirmaciones y manual con valores de `parametros`.
- `escena` y `audio`: escena congelada y oscurecida, y sonidos detenidos durante la pausa; sonidos de menú.

**Entregable:** el juego empieza en el menú principal. Se puede pausar, consultar el manual, abandonar y salir.

### Pruebas automáticas

| ID | Comprueba | Escenario | Resultado esperado |
|---|---|---|---|
| S6-T01 | CU-01, RF-34 | Jugar en el menú principal con solo el nivel 1 | Oleada en curso y PartidaIniciada (1), sin pantalla de selección |
| S6-T02 | CU-10, RF-39 | Manual en el menú principal; Esc | Pantalla de manual; vuelve al menú principal |
| S6-T03 | CU-12, RF-38 | Salir del juego en el menú principal | `flujo` indica que se debe cerrar el juego |
| S6-T04 | CU-09, RF-35 | Esc durante una oleada | Pantalla de pausa; PausaCambiada (activa); el reloj está en pausa |
| S6-T05 | RN-50 | Dos simulaciones con la misma semilla y entradas. Una se pausa 10 s en el paso 600 | Tras el mismo número de pasos de partida, el estado de enemigos, proyectiles, energía, cronómetro, aviso, aturdimiento y desestabilización es idéntico en las dos |
| S6-T06 | RN-50 | Pausa 10 s durante el descanso | La cuenta atrás no cambia |
| S6-T07 | RF-36 | Continuar o Esc en la pausa, desde una oleada y desde el descanso | Vuelve a la pantalla anterior; PausaCambiada (inactiva); el reloj continúa |
| S6-T08 | RN-38 | Pausar con la barra pulsada; reanudar y soltar | El apuntado se cancela al pausar; al soltar no dispara |
| S6-T09 | Pausa y giro | Flechas pulsadas durante la pausa | La orientación no cambia |
| S6-T10 | Manual desde la pausa | Manual en la pausa; Esc | Manual; vuelve a la pausa |
| S6-T11 | RF-37 | Abandonar; No; Abandonar; Esc; Abandonar; Sí | Confirmación; pausa; confirmación; pausa; confirmación; menú principal con PartidaAbandonada, sin enemigos y con las oleadas detenidas |
| S6-T12 | CU-12 | Salir del juego en la pausa; Sí | Confirmación; `flujo` indica que se debe cerrar el juego |
| S6-T13 | Navegación | Flecha abajo e Intro en el menú principal | La selección pasa a la siguiente opción e Intro ejecuta la seleccionada |
| S6-T14 | RF-19, RF-20 | EstacionDestruida; Volver a jugar | Resumen de fin de partida; PartidaIniciada con el mismo nivel |
| S6-T15 | Resumen | EstacionDestruida; Menú principal | Menú principal |

### Comprobaciones manuales

- **S6-M01:** el menú principal coincide con `interfaz/01-menuPrincipal.svg`.
- **S6-M02:** la pausa coincide con `interfaz/07-pausa.svg`. La escena queda congelada y oscurecida, los sonidos se detienen y la música baja.
- **S6-M03:** el manual coincide con `interfaz/08-manual.svg`. Si se cambia un valor en `parametros.json`, el manual muestra el nuevo valor.
- **S6-M04:** Salir del juego cierra la ventana sin errores en el registro.
- **S6-M05:** medición de RNF-01 (cierre de fase 2).

---

## Sprint 7. Partida completa y niveles

**Objetivo:** ganar una partida de 50 oleadas y desbloquear el siguiente nivel.

**Alcance:**
- `oleadas`: oleada 50 y victoria.
- Nivel de dificultad aplicado a la vida y al descanso.
- Módulo `progreso` y su puerto de almacenamiento en disco (platformdirs, escritura atómica).
- `flujo` y `hud`: selección de nivel y resumen de victoria con Subir nivel.

**Entregable:** el jugador elige nivel, gana la partida, sube de nivel y el nivel se conserva al cerrar el juego.

### Pruebas automáticas

| ID | Comprueba | Escenario | Resultado esperado |
|---|---|---|---|
| S7-T01 | RN-19, RF-24 | Superar la oleada 49 y después la 50 | Tras la 49: OleadaSuperada y DescansoIniciado. Tras la 50: PartidaGanada (nivel), sin OleadaSuperada ni DescansoIniciado |
| S7-T02 | RN-22 | Partida en nivel 3 | Vida de un pequeño: 15; descanso: 15,8375 s. Daño, velocidades, recargas y composición iguales que en nivel 1 |
| S7-T03 | Progreso, sin archivo | Puerto en memoria vacío | Nivel desbloqueado 1; no se escribe ningún archivo |
| S7-T04 | CU-01 A4 | Contenido que no es JSON | Nivel 1; el contenido no se borra |
| S7-T05 | CU-01 A4 | `nivel_desbloqueado` con 0, −1, "3", 2,5 o ausente | Nivel 1 en todos los casos |
| S7-T06 | Lectura válida | `{"version": 1, "nivel_desbloqueado": 3}` | Nivel 3 |
| S7-T07 | RN-21, RF-26 | Nivel guardado 3; PartidaGanada (3) | Se escribe `{"version": 1, "nivel_desbloqueado": 4}` |
| S7-T08 | RN-25 | Nivel guardado 4; PartidaGanada (1) | No se escribe; el nivel sigue en 4 |
| S7-T09 | Fallo de escritura | Puerto que falla al escribir; PartidaGanada (1) | Nivel 2 en memoria; se registra el error; no se lanza ninguna excepción |
| S7-T10 | Escritura atómica | Puerto real en una carpeta temporal; forzar un fallo al renombrar | Se escribe primero un archivo temporal en la misma carpeta. Si el renombrado falla, el `progreso.json` anterior queda intacto |
| S7-T11 | RES-07 | Analizar las importaciones de `atalaya` | Ningún módulo importa `socket`, `http`, `urllib` ni bibliotecas de red |
| S7-T12 | RN-24, RF-27 | Nivel desbloqueado 3; Jugar | Selección de nivel con el 3 propuesto. Elegir el 2 e Intro: PartidaIniciada (2). Esc: menú principal |
| S7-T13 | RF-25, CU-08 | Tras PartidaGanada (2): Subir nivel; tras otra victoria: Volver a jugar | PartidaIniciada (3); PartidaIniciada con el mismo nivel |
| S7-T14 | CU-08 | Resumen tras EstacionDestruida | No ofrece Subir nivel |
| S7-T15 | Integración (lenta) | Jugador automático, nivel 1, semilla fija | Gana la partida y el nivel desbloqueado pasa a 2 |

### Comprobaciones manuales

- **S7-M01:** la selección de nivel coincide con `interfaz/02-seleccionNivel.svg`.
- **S7-M02:** la pantalla de victoria coincide con `interfaz/09-victoria.svg`.
- **S7-M03:** tras ganar, cerrar y abrir el juego, el nivel desbloqueado se conserva en `%APPDATA%\Atalaya\progreso.json`.
- **S7-M04:** con `progreso.json` borrado o dañado a mano, el juego arranca en nivel 1 sin mostrar errores.

---

## Sprint 8. Entorno e historia

Cierra la fase 3.

**Objetivo:** los 10 fondos, la niebla, los destellos y las transmisiones de radio.

**Alcance:**
- Módulo `entorno`.
- Módulo `historia` y archivo `datos/historia.json`, con textos provisionales.
- `escena`: 10 fondos con fundido de 2 s, niebla aplicada a cada enemigo y proyectil, velo de los destellos.
- `hud`: transmisión de inicio (6 s) y transmisión en la pantalla de mejoras.
- `audio`: sonido de radio y sonidos de los destellos.

**Entregable:** partida completa con su ambientación.

### Pruebas automáticas

| ID | Comprueba | Escenario | Resultado esperado |
|---|---|---|---|
| S8-T01 | RN-20, RF-17 | PartidaIniciada; OleadaSuperada de las oleadas 4, 5 y 45 | Fondo 1; sigue en 1; FondoCambiado (2); FondoCambiado (10). Una partida recorre los 10 fondos |
| S8-T02 | RN-44, RF-45 | OleadaIniciada (15, niebla); OleadaSuperada (15) | EntornoCambiado (niebla); EntornoCambiado (ninguno) |
| S8-T03 | Niebla | Visibilidad a 0, 250, 475, 700 y 1000 u | 1; 1; entre 0 y 1; 0; 0. No sube con la distancia y cambia menos de 0,01 entre distancias separadas 1 u |
| S8-T04 | Sin entorno | Visibilidad sin niebla a cualquier distancia | 1 |
| S8-T05 | Destellos | 10 minutos simulados con semilla fija | Cada calma dura entre 12 y 20 s. DestelloAviso; 1 s después DestelloInicio; 1,5 s después DestelloFin |
| S8-T06 | Intensidad | Consultar el deslumbramiento en cada fase | 0 en calma; crece en el aviso sin llegar a 1; 1 durante el deslumbramiento |
| S8-T07 | RN-44, RN-09 | Dos simulaciones con la misma semilla, con niebla y sin entorno | Posiciones de enemigos y contactos del radar idénticos |
| S8-T08 | Limpieza | PartidaAbandonada o EstacionDestruida en una oleada con niebla | Entorno ninguno |
| S8-T09 | RN-50 | Pausa de 10 s durante un aviso de destello | La fase y su tiempo restante no cambian |
| S8-T10 | RF-16 | PartidaIniciada | TransmisionDisponible con el texto de inicio |
| S8-T11 | RF-16 | OleadaSuperada (14) | TransmisionDisponible con el texto del descanso 14, que avisa de la niebla |
| S8-T12 | RF-16 | PartidaGanada; EstacionDestruida | Texto de victoria; texto de derrota |
| S8-T13 | Texto genérico | Momento sin texto propio en el archivo | Se publica el texto genérico |
| S8-T14 | historia.json | Validar el archivo | UTF-8 con `version`. Tienen texto propio el inicio, la victoria, la derrota y los descansos previos a cada oleada con entorno (14, 17, 20… 47) |

### Comprobaciones manuales

- **S8-M01:** el fondo cambia con un fundido de 2 s tras las oleadas 5, 10, 15…
- **S8-M02:** la niebla difumina enemigos y proyectiles según su distancia; el radar y los indicadores no cambian.
- **S8-M03:** el destello tiene un resplandor previo de 1 s y deslumbra 1,5 s; el radar y los indicadores siguen legibles.
- **S8-M04:** la transmisión de inicio desaparece a los 6 s; la del descanso se ve en la pantalla de mejoras con su sonido de radio.
- **S8-M05:** medición de RNF-01 con niebla, destellos y 6 enemigos activos (cierre de fase 3).

---

## Sprint 9. Acabado

Cierra la fase 4.

**Objetivo:** prototipo terminado y distribuible.

**Alcance:**
- `audio` completo: sonidos posicionales (motor, aviso, proyectil y explosión) y música con tres pistas y fundidos de 2 s.
- Efectos visuales finales: partículas de las explosiones y estela de los proyectiles.
- Ajuste de parámetros jugando. Cada cambio se hace a la vez en `parametros.json` y en la tabla de `reglasNegocio.md`.
- Recursos definitivos y `recursos/CREDITOS.md`.
- Registro de errores en la carpeta de datos de usuario.
- Ejecutable para Windows con `build_apps`, en una carpeta comprimida.

**Entregable:** carpeta comprimida que se descomprime y se juega en un equipo con Windows sin Python instalado.

### Pruebas automáticas

| ID | Comprueba | Escenario | Resultado esperado |
|---|---|---|---|
| S9-T01 | RF-18 | Elegir la pista de música según pantalla e integridad | Calma en menús, descanso y pausa. Combate en oleada con integridad del 25 % o más. Crítica con integridad del 24 % |
| S9-T02 | Coherencia de datos | Repetir S0-T17 tras el ajuste de parámetros | `parametros.json` y `reglasNegocio.md` coinciden |
| S9-T03 | Licencias | Comparar los archivos de `recursos/` con `CREDITOS.md` | Cada recurso externo tiene autor, origen y licencia |
| S9-T04 | Registro de errores | Provocar un fallo de escritura del progreso | El error se anota en el archivo de registro de la carpeta de datos de usuario |
| S9-T05 | Regresión completa | Toda la batería, incluidas las pruebas lentas, con los parámetros ajustados | Todas pasan |

### Comprobaciones manuales

- **S9-M01:** un enemigo a la derecha se oye por la derecha, uno detrás se distingue de uno delante y el volumen baja con la distancia (RF-10).
- **S9-M02:** el aviso de disparo se oye igual con niebla y con destellos.
- **S9-M03:** la música cambia con fundidos de 2 s y pasa a la pista crítica por debajo del 25 % de integridad.
- **S9-M04:** el ejecutable se descomprime y se juega en un Windows sin Python.
- **S9-M05:** durante una partida, el juego no abre conexiones de red (RES-07), comprobado con el monitor de recursos de Windows.
- **S9-M06:** medición final de RNF-01, RNF-02 (50 ms como máximo) y RNF-05 en el equipo de referencia.
- **S9-M07:** una partida completa jugada a mano en nivel 1 confirma que el juego es ganable con los parámetros ajustados.

---

## Cobertura de los casos de uso

| Caso de uso | Sprints |
|---|---|
| CU-01 Iniciar partida | S3 (sin menús), S6, S7, S8 (transmisión de inicio) |
| CU-02 Girar la vista | S1, S4 (aturdimiento y desvío) |
| CU-03 Apuntar | Eliminado; integrado en CU-02 |
| CU-04 Disparar | S2, S4 |
| CU-05 Localizar enemigos | S3, S4, S9 (sonido posicional) |
| CU-06 Atacar la estación | S3, S4 |
| CU-07 Superar oleada | S3, S5, S7, S8 |
| CU-08 Subir el nivel de dificultad | S7 |
| CU-09 Pausar la partida | S6 |
| CU-10 Consultar el manual | S6 |
| CU-11 Mejorar y reparar la estación | S5 |
| CU-12 Salir del juego | S6 |
