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
- **Estado:** Confirmado

### RF-20. Volver a jugar
- **Descripción:** El sistema debe permitir que el jugador empiece una partida nueva desde el resumen de fin de partida.
- **Prioridad:** Media
- **Origen:** Propuesta derivada de contexto.md
- **Estado:** Confirmado

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

### RF-29. Fijar objetivo
- **Descripción:** El sistema debe permitir que el jugador fije un enemigo manteniendo pulsada la barra espaciadora mientras lo mantiene bajo la mira, para que el disparo lo alcance aunque se mueva.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Eliminado. Sustituido por RF-32 y RF-33.

### RF-30. Indicar objetivo fijado
- **Descripción:** El sistema debe mostrar la mira en verde mientras hay un objetivo fijado.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Eliminado. El fijado ya no existe.

### RF-32. Mira de precisión
- **Descripción:** El sistema debe permitir que el jugador reduzca el tamaño de la mira manteniendo pulsada la barra espaciadora, para disparar con más precisión.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RF-33. Zoom
- **Descripción:** El sistema debe acercar la imagen a medida que la mira se reduce, para que el jugador vea más lejos.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RF-05. Disparar
- **Descripción:** El sistema debe permitir que el jugador dispare hacia la mira con la barra espaciadora. El disparo sale al soltar la tecla.
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

### RF-31. Mostrar la distancia en el radar
- **Descripción:** El sistema debe mostrar en el radar a qué distancia de la estación está cada enemigo.
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
- **Estado:** Confirmado

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
- **Estado:** Confirmado

### RF-45. Entornos de baja visibilidad
- **Descripción:** El sistema debe presentar, en las oleadas que corresponda, un entorno de niebla o de destellos que reduzca lo que el jugador ve del espacio.
- **Prioridad:** Media
- **Origen:** Usuario
- **Estado:** Confirmado

### Menús

### RF-34. Menú principal
- **Descripción:** El sistema debe mostrar, al abrir el juego, un menú principal desde el que el jugador pueda empezar a jugar, consultar el manual o salir del juego.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RF-35. Pausar la partida
- **Descripción:** El sistema debe permitir que el jugador pause la partida en cualquier momento con la tecla Esc.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RF-36. Reanudar la partida
- **Descripción:** El sistema debe permitir que el jugador reanude la partida pausada en el mismo punto en que la dejó.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RF-37. Abandonar la partida
- **Descripción:** El sistema debe permitir que el jugador abandone la partida en curso desde la pausa y vuelva al menú principal.
- **Prioridad:** Media
- **Origen:** Usuario
- **Estado:** Confirmado

### RF-38. Salir del juego
- **Descripción:** El sistema debe permitir que el jugador cierre el juego desde el menú principal o desde la pausa.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RF-39. Consultar el manual
- **Descripción:** El sistema debe permitir que el jugador consulte, desde el menú principal o desde la pausa, un manual con los controles, los tipos y tamaños de enemigos con sus características, los entornos de baja visibilidad y las mejoras.
- **Prioridad:** Media
- **Origen:** Usuario
- **Estado:** Confirmado

### Mejoras y reparación

### RF-40. Pantalla de mejoras
- **Descripción:** El sistema debe mostrar una pantalla de mejoras durante el descanso entre oleadas.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RF-41. Reparar la estación
- **Descripción:** El sistema debe permitir que el jugador gaste puntos de mejora en reparar la estación desde la pantalla de mejoras.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RF-42. Mejorar la estación
- **Descripción:** El sistema debe permitir que el jugador gaste puntos de mejora en subir de nivel el blindaje, la batería o el generador de la estación desde la pantalla de mejoras.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado

### RF-43. Mostrar el resultado de la oleada
- **Descripción:** El sistema debe mostrar en la pantalla de mejoras el tiempo que el jugador ha tardado en superar la oleada, los puntos obtenidos y los puntos disponibles.
- **Prioridad:** Media
- **Origen:** Usuario
- **Estado:** Confirmado

### RF-44. Terminar el descanso antes de tiempo
- **Descripción:** El sistema debe permitir que el jugador cierre la pantalla de mejoras y empiece la siguiente oleada sin esperar a que acabe el descanso.
- **Prioridad:** Baja
- **Origen:** Decisión delegada por el usuario
- **Estado:** Confirmado

## Requisitos no funcionales

### RNF-01. Fluidez
- **Descripción:** El juego debe mantenerse fluido durante las oleadas.
- **Medida:** Al menos 60 fotogramas por segundo de media, y nunca menos de 30, durante una oleada en el equipo de referencia: procesador de 4 núcleos, 8 GB de RAM, gráficos integrados y resolución de 1920 × 1080.
- **Prioridad:** Media
- **Origen:** Propuesta
- **Estado:** Confirmado

### RNF-02. Respuesta de los controles
- **Descripción:** Los giros y los disparos deben reflejarse en pantalla sin retraso perceptible.
- **Medida:** Tiempo entre la acción del jugador y su efecto en pantalla menor o igual a 50 ms.
- **Prioridad:** Alta
- **Origen:** Propuesta
- **Estado:** Confirmado

### RNF-03. Controles reducidos
- **Descripción:** El juego debe manejarse solo con el teclado y con muy pocas teclas.
- **Medida:** Durante una oleada solo se usan las cuatro flechas, la barra espaciadora y Esc (pausa). En los menús y pantallas solo se usan las flechas, Intro (confirmar) y Esc (volver). Ninguna acción requiere ratón.
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
- **Descripción:** El disparo y su efecto deben aparecer sin retraso al soltar la tecla de disparo.
- **Medida:** El rayo del disparo y su impacto se muestran en el primer fotograma tras soltar la barra espaciadora.
- **Prioridad:** Alta
- **Origen:** Usuario
- **Estado:** Confirmado
