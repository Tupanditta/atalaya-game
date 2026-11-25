# Reglas de negocio

Reglas del juego que el sistema debe respetar, independientes de la tecnología. Los valores numéricos concretos (cantidades, tiempos, velocidades) se fijarán más adelante.

## Posición del jugador

### RN-01. Posición fija
- **Regla:** La estación no se desplaza. El jugador solo puede girar sobre su propio eje.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Mecánica principal»
- **Estado:** Confirmado

## Estado inicial

### RN-02. Inicio con recursos al máximo
- **Regla:** Al empezar una partida, la energía y la integridad de la estación están al máximo.
- **Prioridad:** Media
- **Origen:** Propuesta derivada de contexto.md
- **Estado:** Propuesto

## Energía

### RN-03. Coste del disparo
- **Regla:** Cada disparo consume energía.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Mecánica principal»
- **Estado:** Confirmado

### RN-04. Recarga automática
- **Regla:** La energía se recarga sola con el paso del tiempo, hasta su valor máximo.
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
- **Regla:** El tamaño de un enemigo determina su vida y su velocidad. A mayor tamaño, más vida y menos velocidad. A menor tamaño, menos vida y más velocidad.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Tamaño, vida y velocidad»
- **Estado:** Confirmado

### RN-07. Destrucción de un enemigo
- **Regla:** Un enemigo queda destruido cuando su vida llega a cero.
- **Prioridad:** Alta
- **Origen:** Propuesta derivada de contexto.md
- **Estado:** Propuesto

### RN-08. Visibilidad variable
- **Regla:** Existen enemigos de baja visibilidad, más difíciles de distinguir contra el fondo o de seguir con la vista.
- **Prioridad:** Media
- **Origen:** contexto.md, «Visibilidad»
- **Estado:** Confirmado

### RN-09. Radar completo
- **Regla:** Todo enemigo activo aparece en el radar, sea cual sea su visibilidad en pantalla.
- **Prioridad:** Media
- **Origen:** Propuesta derivada de contexto.md, «Visibilidad»
- **Estado:** Propuesto

## Ataques enemigos

### RN-10. Daño a la estación
- **Regla:** Cada ataque enemigo que alcanza la estación reduce su integridad.
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

## Progresión

### RN-15. Fin de oleada
- **Regla:** Una oleada termina cuando todos sus enemigos han sido destruidos. Después del descanso (RN-18) empieza la siguiente oleada.
- **Prioridad:** Alta
- **Origen:** Propuesta derivada de contexto.md, «Enemigos y progresión»
- **Estado:** Propuesto

### RN-16. Dificultad creciente
- **Regla:** La dificultad de cada oleada es mayor o igual que la de la anterior, en número, tipo o velocidad de los enemigos.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Enemigos y progresión»
- **Estado:** Confirmado

### RN-17. Fin de partida
- **Regla:** La partida termina cuando la integridad de la estación llega a cero.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Enemigos y progresión»
- **Estado:** Confirmado

### RN-18. Descanso entre oleadas
- **Regla:** Entre el fin de una oleada y el inicio de la siguiente hay un tiempo de descanso sin enemigos.
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

## Disparo

### RN-23. Disparo instantáneo
- **Regla:** El disparo no tiene tiempo de viaje: alcanza al instante el punto que marca la mira en el momento de disparar.
- **Prioridad:** Alta
- **Origen:** Decisión delegada por el usuario, para que el disparo sea lo más fluido posible
- **Estado:** Confirmado

## Nivel de dificultad (continuación)

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

## Giro de la vista

### RN-26. Flechas opuestas
- **Regla:** Si en un mismo eje están pulsadas a la vez las dos flechas opuestas (izquierda y derecha, o arriba y abajo), la vista no gira en ese eje. El otro eje no se ve afectado: con arriba, izquierda y derecha pulsadas, la vista solo gira hacia arriba; con las cuatro flechas pulsadas, la vista no gira.
- **Prioridad:** Media
- **Origen:** Usuario
- **Estado:** Confirmado
