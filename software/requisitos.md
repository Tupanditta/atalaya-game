# Requisitos

Servicios que el juego ofrece (requisitos funcionales) y cualidades que debe cumplir (requisitos no funcionales). Las reglas del juego están en `reglasNegocio.md`.

## Requisitos funcionales

### Partida

### RF-01. Iniciar partida
- **Descripción:** El sistema debe permitir que el jugador inicie una partida.
- **Prioridad:** Alta
- **Origen:** Propuesta derivada de contexto.md
- **Estado:** Confirmado

### RF-19. Mostrar resumen de fin de partida
- **Descripción:** El sistema debe mostrar al jugador, al terminar la partida, el número de oleadas superadas.
- **Prioridad:** Media
- **Origen:** Propuesta derivada de contexto.md
- **Estado:** Propuesto

### RF-20. Volver a jugar
- **Descripción:** El sistema debe permitir que el jugador empiece una partida nueva desde el resumen de fin de partida.
- **Prioridad:** Media
- **Origen:** Propuesta derivada de contexto.md
- **Estado:** Propuesto

### RF-24. Mostrar victoria
- **Descripción:** El sistema debe indicar al jugador que ha ganado la partida cuando supera la oleada final.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RF-25. Subir el nivel de dificultad
- **Descripción:** El sistema debe permitir que el jugador, tras ganar una partida, empiece una partida nueva en el siguiente nivel de dificultad.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RF-26. Guardar el nivel desbloqueado
- **Descripción:** El sistema debe guardar el nivel de dificultad más alto desbloqueado, para que el jugador lo conserve al cerrar y volver a abrir el juego.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RF-27. Elegir el nivel de dificultad
- **Descripción:** El sistema debe permitir que el jugador elija, al empezar una partida, el nivel de dificultad entre los niveles desbloqueados.
- **Prioridad:** Media
- **Origen:** Decisión delegada por el usuario
- **Estado:** Confirmado

### Controles

### RF-02. Girar la vista horizontalmente
- **Descripción:** El sistema debe permitir que el jugador gire la vista a izquierda y derecha con las flechas izquierda y derecha, hasta dar la vuelta completa, para vigilar todas las direcciones.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Mecánica principal»
- **Estado:** Confirmado

### RF-03. Girar la vista verticalmente
- **Descripción:** El sistema debe permitir que el jugador gire la vista hacia arriba y hacia abajo con las flechas arriba y abajo, hasta dar la vuelta completa, para vigilar también por encima y por debajo de la estación.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RF-21. Combinar giros
- **Descripción:** El sistema debe permitir que el jugador gire la vista en horizontal y en vertical a la vez, pulsando una flecha lateral y una vertical al mismo tiempo (por ejemplo, arriba y derecha).
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RF-04. Mover la mira
- **Descripción:** El sistema debe permitir que el jugador mueva la mira por la pantalla con el ratón.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Mecánica principal»
- **Estado:** Eliminado. Sustituido por RF-28: la mira está fija y se apunta girando la vista.

### RF-28. Mira fija en el centro
- **Descripción:** El sistema debe mostrar la mira fija en el centro de la pantalla, de modo que el jugador apunte girando la vista con las flechas.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RF-05. Disparar
- **Descripción:** El sistema debe permitir que el jugador dispare hacia la mira pulsando la barra espaciadora.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Mecánica principal»
- **Estado:** Confirmado

### Información en pantalla

### RF-06. Mostrar energía
- **Descripción:** El sistema debe mostrar al jugador, durante la partida, la energía disponible para disparar.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Elementos de la interfaz»
- **Estado:** Confirmado

### RF-07. Mostrar radar
- **Descripción:** El sistema debe mostrar al jugador, durante la partida, la posición de los enemigos a su alrededor, incluidos los que están fuera de la vista.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Elementos de la interfaz»
- **Estado:** Confirmado

### RF-22. Distinguir el tipo en el radar
- **Descripción:** El sistema debe mostrar en el radar el tipo de cada enemigo (sin efecto especial, desestabilizador o aturdidor).
- **Prioridad:** Media
- **Origen:** Usuario
- **Estado:** Confirmado

### RF-23. Distinguir el tamaño en el radar
- **Descripción:** El sistema debe mostrar en el radar el tamaño de cada enemigo.
- **Prioridad:** Media
- **Origen:** Usuario
- **Estado:** Confirmado

### RF-08. Mostrar integridad de la estación
- **Descripción:** El sistema debe mostrar al jugador, durante la partida, cuánto daño puede aguantar aún la estación.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Elementos de la interfaz»
- **Estado:** Confirmado

### RF-15. Indicar aturdimiento
- **Descripción:** El sistema debe indicar al jugador que está aturdido mientras dura el aturdimiento.
- **Prioridad:** Media
- **Origen:** Propuesta derivada de contexto.md, «Estabilidad de la pantalla»
- **Estado:** Propuesto

### Enemigos

### RF-09. Generar oleadas
- **Descripción:** El sistema debe generar enemigos en oleadas que lleguen desde distintas direcciones alrededor del jugador.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Enemigos y progresión»
- **Estado:** Confirmado

### RF-10. Localizar enemigos por el sonido
- **Descripción:** El sistema debe permitir que el jugador identifique por el sonido la dirección de un enemigo que está fuera de la vista.
- **Prioridad:** Media
- **Origen:** contexto.md, «Ambientación audiovisual»
- **Estado:** Confirmado

### Efectos

### RF-11. Avisar de energía insuficiente
- **Descripción:** El sistema debe avisar al jugador, con un efecto visual y sonoro, cuando intenta disparar sin energía suficiente.
- **Prioridad:** Media
- **Origen:** contexto.md, «Ambientación audiovisual»
- **Estado:** Confirmado

### RF-12. Efecto de disparo
- **Descripción:** El sistema debe acompañar cada disparo del jugador con un efecto visual y sonoro.
- **Prioridad:** Media
- **Origen:** contexto.md, «Ambientación audiovisual»
- **Estado:** Confirmado

### RF-13. Efecto de destrucción
- **Descripción:** El sistema debe mostrar una explosión, con su sonido, cuando un enemigo queda destruido.
- **Prioridad:** Media
- **Origen:** contexto.md, «Ambientación audiovisual»
- **Estado:** Confirmado

### RF-14. Efecto de daño recibido
- **Descripción:** El sistema debe avisar al jugador, con un temblor breve de la pantalla y una alarma, cuando la estación recibe daño.
- **Prioridad:** Media
- **Origen:** contexto.md, «Ambientación audiovisual»
- **Estado:** Confirmado

### Historia y ambientación

### RF-16. Transmisiones de radio
- **Descripción:** El sistema debe presentar al jugador transmisiones de radio que cuenten la historia al empezar la partida y entre oleadas.
- **Prioridad:** Media
- **Origen:** contexto.md, «Historia»
- **Estado:** Confirmado

### RF-17. Cambiar el fondo espacial
- **Descripción:** El sistema debe cambiar el fondo espacial a lo largo de la partida para reflejar el avance del jugador.
- **Prioridad:** Media
- **Origen:** contexto.md, «Ambientación audiovisual»
- **Estado:** Confirmado

### RF-18. Música según la tensión
- **Descripción:** El sistema debe reproducir música que acompañe la intensidad de cada momento de la partida.
- **Prioridad:** Baja
- **Origen:** contexto.md, «Ambientación audiovisual»
- **Estado:** Propuesto

## Requisitos no funcionales

### RNF-01. Fluidez
- **Descripción:** El juego debe mantenerse fluido durante las oleadas.
- **Medida:** Al menos 60 fotogramas por segundo de media, y nunca menos de 30, durante una oleada en el equipo de referencia (por definir).
- **Prioridad:** Media
- **Origen:** Propuesta
- **Estado:** Propuesto

### RNF-02. Respuesta de los controles
- **Descripción:** Los giros y los disparos deben reflejarse en pantalla sin retraso perceptible.
- **Medida:** Tiempo entre la acción del jugador y su efecto en pantalla menor o igual a 50 ms.
- **Prioridad:** Alta
- **Origen:** Propuesta
- **Estado:** Propuesto

### RNF-03. Controles reducidos
- **Descripción:** Durante la partida, el jugador debe poder jugar solo con las flechas y la barra espaciadora.
- **Medida:** Ninguna acción de la partida requiere teclas distintas de las cuatro flechas y la barra espaciadora. Ninguna acción requiere ratón.
- **Prioridad:** Alta
- **Origen:** contexto.md, «Pilares del diseño»
- **Estado:** Confirmado

### RNF-04. Giro fluido
- **Descripción:** El giro de la vista debe ser continuo, sin saltos ni pausas, también al combinar un giro horizontal y uno vertical.
- **Medida:** Mientras una flecha está pulsada, la orientación cambia en todos los fotogramas a velocidad constante. El giro combinado no se detiene ni salta al pulsar o soltar la segunda flecha.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RNF-05. Disparo fluido
- **Descripción:** El disparo y su efecto deben aparecer sin retraso respecto a la pulsación de la tecla de disparo.
- **Medida:** El rayo del disparo y su impacto se muestran en el primer fotograma tras la pulsación.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado
