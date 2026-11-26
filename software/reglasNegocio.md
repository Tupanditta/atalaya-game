# Reglas de negocio

Reglas del juego que el sistema debe respetar, independientes de la tecnología. Los valores numéricos (cantidades, tiempos, velocidades) están en la sección «Parámetros iniciales», al final del documento.

## Posición y giro

### RN-01. Posición fija
- **Regla:** La estación no se desplaza. El jugador solo puede girar sobre su propio eje.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Mecánica principal»
- **Estado:** Confirmado

### RN-26. Flechas opuestas
- **Regla:** Si en un mismo eje están pulsadas a la vez las dos flechas opuestas (izquierda y derecha, o arriba y abajo), la vista no gira en ese eje. El otro eje no se ve afectado: con arriba, izquierda y derecha pulsadas, la vista solo gira hacia arriba; con las cuatro flechas pulsadas, la vista no gira.
- **Prioridad:** Media
- **Origen:** Usuario
- **Estado:** Confirmado

### RN-40. Giro más lento con zoom
- **Regla:** La velocidad de giro es proporcional al campo de visión: cuanto mayor es el zoom, más lento gira la vista, para poder apuntar con precisión.
- **Prioridad:** Media
- **Origen:** Decisión delegada por el usuario
- **Estado:** Confirmado

### RN-41. Giro respecto a la cámara
- **Regla:** Los giros se hacen respecto a la propia cámara. Las flechas laterales giran la vista alrededor del eje vertical de la cámara, y las flechas arriba y abajo alrededor de su eje horizontal. No existe un «arriba» fijo del espacio: tras media vuelta vertical, el espacio se ve invertido respecto al inicio, pero cada flecha sigue girando la vista en el mismo sentido en pantalla. «Arriba» y «abajo» se refieren siempre a la cámara, también en el radar.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

## Estado inicial

### RN-02. Inicio con recursos al máximo
- **Regla:** Al empezar una partida, la energía y la integridad de la estación están al máximo, y la estación no tiene mejoras ni puntos de mejora (RN-49).
- **Prioridad:** Media
- **Origen:** Propuesta derivada de contexto.md
- **Estado:** Confirmado

## Energía

### RN-03. Coste del disparo
- **Regla:** Cada disparo consume energía.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Mecánica principal»
- **Estado:** Confirmado

### RN-04. Recarga automática
- **Regla:** La energía se recarga sola con el paso del tiempo, hasta su valor máximo. La recarga continúa mientras el jugador apunta o está aturdido, y se detiene durante la pausa (RN-50).
- **Prioridad:** Alta
- **Origen:** contexto.md, «Mecánica principal»
- **Estado:** Confirmado

### RN-05. Disparo bloqueado sin energía
- **Regla:** Si la energía disponible es menor que el coste de un disparo, el jugador no puede disparar.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Mecánica principal»
- **Estado:** Confirmado

## Enemigos

### RN-06. Tamaño, vida y velocidad
- **Regla:** El tamaño de un enemigo determina su vida, su velocidad y su zona de impacto. A mayor tamaño, más vida, menos velocidad y una zona de impacto mayor. A menor tamaño, menos vida, más velocidad y una zona de impacto menor.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Tamaño, vida y velocidad»
- **Estado:** Confirmado

### RN-07. Destrucción de un enemigo
- **Regla:** Un enemigo queda destruido cuando su vida llega a cero.
- **Prioridad:** Alta
- **Origen:** Propuesta derivada de contexto.md
- **Estado:** Confirmado

### RN-08. Visibilidad variable
- **Regla:** Existen enemigos de baja visibilidad, más difíciles de distinguir contra el fondo o de seguir con la vista.
- **Prioridad:** Media
- **Origen:** contexto.md, «Visibilidad»
- **Estado:** Eliminado. Sustituido por RN-44: la baja visibilidad es del entorno, no de los enemigos.

### RN-09. Radar completo
- **Regla:** Todo enemigo activo aparece en el radar, sea cual sea la visibilidad del entorno.
- **Prioridad:** Media
- **Origen:** Propuesta derivada de contexto.md, «Visibilidad»
- **Estado:** Confirmado

### RN-29. Trayectoria en tres dimensiones
- **Regla:** Los enemigos se mueven y cambian de dirección en horizontal y en vertical mientras se acercan, de modo que seguirlos puede exigir giros altos o combinados.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RN-30. Distancia variable
- **Regla:** Los enemigos pueden acercarse a la estación y alejarse de ella durante la oleada, siempre entre la distancia mínima y la distancia máxima. Como aparecen dentro del alcance del radar y la distancia máxima es menor que ese alcance, un enemigo nunca sale del radar.
- **Prioridad:** Media
- **Origen:** Usuario
- **Estado:** Confirmado

### RN-31. Sin colisiones
- **Regla:** Los enemigos nunca chocan con la estación ni se acercan más que la distancia mínima. Solo la dañan con sus disparos.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RN-32. Aparición lejana
- **Regla:** Todo enemigo aparece lejos de la estación, dentro de la distancia de aparición fijada en los parámetros. Nunca aparece cerca del jugador.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RN-33. Movimiento con inercia
- **Regla:** Los enemigos cambian de dirección y de velocidad de forma gradual, describiendo curvas. Nunca cambian de dirección de golpe ni se teletransportan.
- **Prioridad:** Alta
- **Origen:** Propuesta, para combinar fluidez y realismo
- **Estado:** Confirmado

### RN-42. Alcance de disparo enemigo
- **Regla:** Un enemigo solo dispara cuando está a una distancia de la estación menor o igual que su alcance de disparo. Mientras está más lejos, se acerca.
- **Prioridad:** Alta
- **Origen:** Decisión delegada por el usuario
- **Estado:** Confirmado

### RN-43. Enemigos activos a la vez
- **Regla:** En cada momento hay como máximo un número fijo de enemigos activos. El resto de enemigos de la oleada aparece a medida que se destruyen los activos.
- **Prioridad:** Alta
- **Origen:** Decisión delegada por el usuario, para que el juego sea ganable
- **Estado:** Confirmado

## Ataques enemigos

### RN-10. Daño a la estación
- **Regla:** Cada disparo enemigo que alcanza la estación reduce su integridad.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Elementos de la interfaz»
- **Estado:** Confirmado

### RN-11. Daño reducido del desestabilizador
- **Regla:** Los ataques de un enemigo desestabilizador causan menos daño que los de un enemigo sin efecto especial.
- **Prioridad:** Media
- **Origen:** contexto.md, «Estabilidad de la pantalla»
- **Estado:** Confirmado

### RN-12. Temblor por desestabilización
- **Regla:** Un ataque desestabilizador hace temblar la pantalla y la mira durante un tiempo limitado. Mientras dura, la mira se desvía del centro y el disparo va hacia donde apunta la mira desviada.
- **Prioridad:** Media
- **Origen:** contexto.md, «Estabilidad de la pantalla»
- **Estado:** Confirmado

### RN-13. Aturdimiento
- **Regla:** Un ataque aturdidor aturde al jugador durante un tiempo limitado. Mientras dura el aturdimiento, el jugador no puede girar ni disparar.
- **Prioridad:** Media
- **Origen:** contexto.md, «Estabilidad de la pantalla»; usuario
- **Estado:** Confirmado

### RN-14. Cadencia del aturdidor
- **Regla:** Un enemigo aturdidor tarda más en volver a atacar que un enemigo sin efecto especial.
- **Prioridad:** Media
- **Origen:** contexto.md, «Estabilidad de la pantalla»
- **Estado:** Confirmado

### RN-34. Aviso de disparo
- **Regla:** Antes de cada disparo, el enemigo muestra un aviso visible y audible durante un tiempo breve. Si el enemigo es destruido durante el aviso, no llega a disparar.
- **Prioridad:** Alta
- **Origen:** Propuesta, para que el jugador pueda reaccionar aunque no pueda esquivar
- **Estado:** Confirmado

### RN-35. Proyectiles enemigos
- **Regla:** Los disparos enemigos son proyectiles visibles que viajan a velocidad finita hacia la estación. Tardan más en llegar cuanto más lejos está el enemigo que los dispara.
- **Prioridad:** Alta
- **Origen:** Propuesta, para combinar fluidez y realismo
- **Estado:** Confirmado

### RN-36. Proyectil en vuelo
- **Regla:** Un proyectil ya lanzado siempre alcanza la estación, aunque el enemigo que lo disparó sea destruido. La estación no puede esquivar.
- **Prioridad:** Media
- **Origen:** Propuesta derivada de RN-01
- **Estado:** Confirmado

## Disparo del jugador

### RN-23. Disparo instantáneo
- **Regla:** El disparo sale al soltar la barra espaciadora y no tiene tiempo de viaje: alcanza al instante el punto del centro de la mira (RN-37).
- **Prioridad:** Alta
- **Origen:** Decisión delegada por el usuario, para que el disparo sea lo más fluido posible
- **Estado:** Confirmado

### RN-27. Fijado de objetivo
- **Regla:** Un enemigo queda fijado cuando el jugador lo mantiene bajo la mira, con la barra espaciadora pulsada, durante un tiempo continuo.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Eliminado. Sustituido por RN-37, RN-38 y RN-39.

### RN-28. Disparo fijado
- **Regla:** Una vez fijado, el enemigo sigue fijado hasta que el jugador suelta la barra espaciadora.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Eliminado. El fijado ya no existe.

### RN-37. Disparo al centro de la mira
- **Regla:** El disparo va exactamente hacia el centro de la mira, sin dispersión al azar. Reducir la mira y el zoom (RN-38, RN-39) ayudan a apuntar con precisión, pero no cambian hacia dónde va el disparo.
- **Prioridad:** Alta
- **Origen:** Usuario. Sustituye a la dispersión al azar dentro de la mira, que hacía fallar disparos con el enemigo justo en el centro.
- **Estado:** Confirmado

### RN-38. Reducción de la mira
- **Regla:** Mientras el jugador mantiene pulsada la barra espaciadora, la mira se reduce de forma continua hasta un tamaño mínimo, y no puede ser más pequeña. Al disparar, al pausar la partida o si el jugador queda aturdido, la mira vuelve a su tamaño normal.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RN-39. Zoom proporcional
- **Regla:** El zoom aumenta a la vez que la mira se reduce. Es máximo cuando la mira tiene su tamaño mínimo, y vuelve a su estado normal cuando la mira vuelve a su tamaño normal.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

## Progresión

### RN-15. Fin de oleada
- **Regla:** Una oleada termina cuando todos sus enemigos han sido destruidos. Después del descanso (RN-18) empieza la siguiente oleada.
- **Prioridad:** Alta
- **Origen:** Propuesta derivada de contexto.md, «Enemigos y progresión»
- **Estado:** Confirmado

### RN-16. Dificultad creciente
- **Regla:** La dificultad de cada oleada es mayor o igual que la de la anterior, en número o tipo de enemigos.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Enemigos y progresión»
- **Estado:** Confirmado

### RN-17. Fin de partida
- **Regla:** La partida termina cuando la integridad de la estación llega a cero.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Enemigos y progresión»
- **Estado:** Confirmado

### RN-18. Descanso entre oleadas
- **Regla:** Entre el fin de una oleada y el inicio de la siguiente hay un tiempo de descanso sin enemigos. Durante el descanso está abierta la pantalla de mejoras (RN-48). El jugador puede terminar el descanso antes de tiempo.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RN-19. Oleada final
- **Regla:** Una partida tiene 50 oleadas. Superar la oleada 50 es ganar la partida.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RN-20. Cambio de fondo
- **Regla:** El fondo espacial cambia cada 5 oleadas superadas.
- **Prioridad:** Media
- **Origen:** Usuario
- **Estado:** Confirmado

## Entorno

### RN-44. Entornos de baja visibilidad
- **Regla:** Algunas oleadas se juegan en un entorno de baja visibilidad. Hay dos tipos. En la **niebla**, una nube de polvo cósmico difumina los enemigos y los proyectiles según su distancia, hasta ocultarlos. En los **destellos**, una estrella cercana lanza llamaradas que deslumbran la pantalla durante unos segundos, con un breve aviso previo. Los enemigos no cambian; solo cambia cuánto se ve. El radar y los indicadores de pantalla no se ven afectados.
- **Prioridad:** Media
- **Origen:** Usuario; los dos tipos de entorno son decisión delegada
- **Estado:** Confirmado

## Mejoras y reparación

### RN-45. Puntos de mejora
- **Regla:** Al superar una oleada, el jugador obtiene puntos de mejora según el tiempo que ha tardado en destruir todos sus enemigos: cuanto más rápido, más puntos. Siempre obtiene al menos un punto. Los puntos no gastados se acumulan para los siguientes descansos.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RN-46. Reparación
- **Regla:** Gastar puntos en reparar devuelve integridad a la estación, sin superar la integridad máxima.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RN-47. Mejoras de la estación
- **Regla:** Gastar puntos en una mejora sube un nivel una característica de la estación: blindaje (integridad máxima), batería (energía máxima) o generador (velocidad de recarga). Cada mejora tiene un número máximo de niveles.
- **Prioridad:** Alta
- **Origen:** Usuario; el catálogo de mejoras es decisión delegada
- **Estado:** Confirmado

### RN-48. Mejoras solo entre oleadas
- **Regla:** Las reparaciones y las mejoras solo pueden hacerse en la pantalla de mejoras, que está abierta durante el descanso entre oleadas. Durante una oleada no se puede reparar ni mejorar.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RN-49. Mejoras solo para la partida
- **Regla:** Los puntos y las mejoras solo duran la partida en curso. Una partida nueva empieza sin puntos ni mejoras, y no se guardan al cerrar el juego.
- **Prioridad:** Media
- **Origen:** Decisión delegada por el usuario
- **Estado:** Confirmado

## Nivel de dificultad

### RN-21. Desbloqueo del siguiente nivel
- **Regla:** Ganar una partida desbloquea el siguiente nivel de dificultad. No hay un nivel máximo.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RN-22. Efecto del nivel de dificultad
- **Regla:** Cada nivel de dificultad aumenta la resistencia de todos los enemigos y reduce el tiempo de descanso entre oleadas respecto al nivel anterior. El nivel no cambia nada más.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RN-24. Nivel inicial
- **Regla:** Al empezar una partida, el jugador puede elegir cualquier nivel entre el 1 y el más alto desbloqueado. Por defecto se propone el más alto. Mientras no se haya ganado ninguna partida, solo existe el nivel 1. Volver a jugar mantiene el nivel de la partida anterior.
- **Prioridad:** Media
- **Origen:** Decisión delegada por el usuario
- **Estado:** Confirmado

### RN-25. Nivel desbloqueado permanente
- **Regla:** El nivel de dificultad más alto desbloqueado se conserva aunque se cierre el juego. Nunca disminuye.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

## Pausa

### RN-50. Tiempo detenido en pausa
- **Regla:** Mientras la partida está en pausa, el tiempo del juego se detiene: los enemigos, los proyectiles, la recarga de energía, los efectos, el cronómetro de la oleada y la cuenta atrás del descanso. Al reanudar, todo continúa exactamente donde se detuvo.
- **Prioridad:** Alta
- **Origen:** Usuario; el comportamiento de la pausa es decisión delegada
- **Estado:** Confirmado

## Parámetros iniciales

Valores de partida para implementar el juego y ajustarlo durante las pruebas. Cambiar un valor no cambia las reglas. Unidades: s (segundos), u (unidades de distancia del mundo), ° (grados).

### Jugador y estación

| Parámetro | Valor | Regla |
|---|---|---|
| Energía máxima | 100 | RN-02 |
| Coste de un disparo | 10 | RN-03 |
| Recarga de energía | 8 por segundo | RN-04 |
| Integridad máxima | 100 | RN-02 |
| Daño de un disparo del jugador | 10 puntos de vida | RN-07 |
| Velocidad de giro sin zoom | 90 °/s en cada eje | RN-40 |
| Campo de visión sin zoom | 70° | RN-39 |
| Campo de visión con zoom máximo | 25° | RN-39 |
| Tamaño normal de la mira (radio del círculo) | 2,5° | RN-38 |
| Tamaño mínimo de la mira | 0,5° | RN-38 |
| Tiempo para llegar al tamaño mínimo | 1 s | RN-38 |
| Tiempo de vuelta de la mira y el zoom a su estado normal | 0,2 s | RN-38 |

### Enemigos por tamaño

| Tamaño | Vida en nivel 1 | Velocidad máxima | Aceleración máxima | Radio de la zona de impacto |
|---|---|---|---|---|
| Pequeño | 10 | 110 u/s | 55 u/s² | 10 u |
| Mediano | 20 | 70 u/s | 35 u/s² | 18 u |
| Grande | 40 | 40 u/s | 20 u/s² | 32 u |

Con estos radios, un enemigo grande se acierta siempre con un disparo rápido bien centrado a media distancia, y un mediano, unas dos de cada tres veces. Un enemigo pequeño lejano exige reducir la mira.

Con estas aceleraciones, cada enemigo tarda 2 s en pasar de parado a su velocidad máxima (RN-33). A velocidad máxima, su giro más cerrado tiene un radio de 220 u (pequeño), 140 u (mediano) y 80 u (grande). El enemigo empieza a frenar cuando la distancia a su destino es igual a la que necesita para detenerse con su aceleración máxima.

### Enemigos por tipo

| Tipo | Daño a la integridad | Tiempo de recarga | Efecto |
|---|---|---|---|
| Sin efecto especial | 3 | 4 s | ninguno |
| Desestabilizador | 1 | 3 s | temblor durante 3 s |
| Aturdidor | 2 | 8 s | aturdimiento durante 1,5 s |

### Ataques y distancias

| Parámetro | Valor | Regla |
|---|---|---|
| Duración del aviso de disparo | 1 s | RN-34 |
| Velocidad de los proyectiles enemigos | 300 u/s | RN-35 |
| Distancia de aparición | entre 900 y 1000 u | RN-32 |
| Distancia máxima | 1000 u | RN-30 |
| Alcance de disparo enemigo | 700 u | RN-42 |
| Distancia mínima | 150 u | RN-31 |
| Alcance del radar | 1200 u | RF-07 |
| Distancia de llegada al destino (a menos de esta distancia, el enemigo elige otro destino) | 50 u | RN-33 |
| Desestabilización: desvío máximo de la mira respecto al centro | 2° | RN-12 |
| Desestabilización: velocidad máxima del desvío | 30 °/s | RN-12 |
| Enemigos activos a la vez | como máximo 6 | RN-43 |
| Ritmo de aparición | un enemigo cada 2 s, mientras haya hueco | RF-09 |

### Composición de las oleadas

n es el número de la oleada (de 1 a 50).

| Parámetro | Valor | Regla |
|---|---|---|
| Enemigos por oleada | 3 + parte entera de n / 2 | RN-16 |
| Tamaños | mezcla al azar de los tres tamaños desde la oleada 1 | RN-06 |
| Desestabilizadores | desde la oleada 5 | RN-16 |
| Aturdidores | desde la oleada 10 | RN-16 |
| Enemigos con efecto especial | como máximo un tercio de la oleada | RN-16 |
| Fondos distintos | 10, uno por cada tramo de 5 oleadas | RN-20 |

### Entornos de baja visibilidad

| Parámetro | Valor | Regla |
|---|---|---|
| Oleadas con entorno | desde la oleada 15, una de cada tres (15, 18, 21…), alternando niebla y destellos, empezando por la niebla | RN-44 |
| Niebla: visibilidad completa | hasta 250 u | RN-44 |
| Niebla: invisible | desde 700 u | RN-44 |
| Destellos: intervalo | uno cada 12 a 20 s, al azar | RN-44 |
| Destellos: aviso previo | 1 s de resplandor creciente | RN-44 |
| Destellos: deslumbramiento | 1,5 s | RN-44 |

### Mejoras y reparación

| Parámetro | Valor | Regla |
|---|---|---|
| Tiempo de referencia de una oleada | 10 s + 5 s × número de enemigos de la oleada | RN-45 |
| Puntos por oleada | 3 si el tiempo es menor o igual que el de referencia; 2 si es menor o igual que el doble; 1 en otro caso | RN-45 |
| Reparación | 1 punto devuelve 20 de integridad | RN-46 |

| Mejora | Efecto por nivel | Niveles máximos | Coste por nivel |
|---|---|---|---|
| Blindaje | +10 de integridad máxima, y +10 de integridad actual | 5 | 2 puntos |
| Batería | +10 de energía máxima | 5 | 2 puntos |
| Generador | +1 de recarga de energía por segundo | 5 | 2 puntos |

### Nivel de dificultad

| Parámetro | Valor | Regla |
|---|---|---|
| Vida de los enemigos | vida en nivel 1 × (1 + 0,25 × (nivel − 1)) | RN-22 |
| Descanso entre oleadas | 5 s + 15 s × 0,85^(nivel − 1) | RN-18, RN-22 |
