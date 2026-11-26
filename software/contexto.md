# Contexto del proyecto

> Título provisional: **Atalaya**

Este documento es el punto de partida del proyecto. Describe la idea general del juego. No entra en detalles de implementación. Los detalles se concretan en requisitos, reglas de negocio, restricciones y casos de uso.

## Idea general

Atalaya es un juego de disparos en primera persona ambientado en el espacio. El jugador ocupa un puesto fijo: no se desplaza, solo gira sobre su propio eje para mirar a su alrededor. Los enemigos se acercan desde cualquier dirección y el jugador debe detectarlos, girar hacia ellos, apuntar y disparar antes de que lleguen.

El reto del juego no está en moverse, sino en vigilar, decidir hacia dónde mirar y administrar una energía limitada.

## Historia

En los confines de un sistema estelar, la humanidad mantiene una red de estaciones que protegen las rutas hacia sus colonias. Una de ellas, la Atalaya, es una plataforma de defensa anclada a un asteroide en un punto estratégico.

Algo ha atacado la red. Las demás estaciones han dejado de responder. El jugador es el último artillero que sigue operativo en la Atalaya. La plataforma no puede moverse y su reactor está dañado: genera energía a un ritmo lento, insuficiente para disparar sin pausa.

Mientras la Atalaya resista, la ruta hacia las colonias sigue abierta. Oleada tras oleada, el jugador debe aguantar en su puesto y, con el tiempo, descubrir qué hay detrás del ataque.

La historia se cuenta de forma ligera: mensajes de radio, transmisiones entre oleadas y cambios en el entorno que muestran que la situación evoluciona.

## Mecánica principal

- **Posición fija.** El jugador no se desplaza por el escenario. Solo rota sobre su eje.
- **Girar la vista.** Las flechas del teclado, o las teclas W, A, S y D, giran la vista del jugador.
- **Apuntar.** El jugador mueve la mira por la pantalla con el ratón y gira la vista con las flechas para buscar enemigos fuera de ella.
- **Disparar.** La barra espaciadora o el botón izquierdo del ratón disparan hacia la mira. Salvo la mira y el disparo, el juego se controla con el teclado.
- **Apuntar con precisión.** Mantener pulsada la tecla de disparo reduce la mira hasta un tamaño mínimo y acerca la imagen para ver más lejos. Cuanto más pequeña es la mira, más preciso es el disparo. El disparo sale al soltar la tecla.
- **Energía limitada.** Cada disparo consume energía. La energía se recarga sola con el tiempo. Si la barra está vacía, el jugador no puede disparar hasta que se recargue.

## Elementos de la interfaz

- **Mira.** Indica hacia dónde se dispara.
- **Mapa / radar.** Muestra la posición de los enemigos alrededor del jugador, incluidos los que están fuera de la vista. Permite decidir hacia dónde girar.
- **Barra de energía.** Muestra la energía disponible para disparar y cómo se va recargando.
- **Estado de la estación.** Indica cuánto daño puede aguantar aún la Atalaya antes de caer.

## Enemigos y progresión

- Los enemigos llegan en oleadas, desde distintas direcciones. Siempre aparecen lejos, nunca encima del jugador.
- Se mueven en todas direcciones mientras se acercan, y pueden acercarse y alejarse. Seguirlos puede exigir giros altos o diagonales.
- No chocan con la estación: la atacan disparando.
- Se mueven con inercia, en curvas, sin cambios bruscos. Avisan antes de disparar, y sus proyectiles se ven venir.
- La dificultad aumenta a medida que avanza la partida.

### Tamaño, vida y velocidad

Los enemigos se diferencian por su tamaño, y el tamaño marca su vida y su velocidad:

- **Grandes:** tienen más vida, pero son más lentos.
- **Pequeños:** tienen menos vida, pero son más rápidos.

### Visibilidad

Algunas oleadas se juegan en un entorno de poca visibilidad: niebla de polvo cósmico o destellos de una estrella cercana. En esos momentos el jugador tiene que apoyarse en el radar y en el sonido para encontrar a los enemigos.

### Mejoras entre oleadas

Entre oleadas se abre una pantalla sencilla para reparar y mejorar la estación. Cuanto más rápido acaba el jugador con una oleada, más puntos tiene para gastar. Durante las oleadas no se puede reparar ni mejorar.

### Menús

Un menú principal permite jugar, consultar el manual o salir. Durante la partida, Esc la pausa. El manual explica los controles, los enemigos y sus características, los entornos y las mejoras.

### Estabilidad de la pantalla

Algunos enemigos no buscan destruir la estación, sino dificultar el control del jugador:

- **Desestabilizadores:** sus disparos hacen menos daño, pero hacen temblar la pantalla y la mira. Apuntar se vuelve más difícil.
- **Aturdidores:** sus disparos aturden al jugador. Mientras dura el aturdimiento, el jugador no puede girar ni disparar. A cambio, tardan más en volver a disparar.
- La partida termina cuando la estación cae.

## Ambientación audiovisual

El juego no tiene desplazamiento y los modelos 3D serán sencillos. Esa limitación se compensa con la ambientación:

- **Sonido.** Disparos, impactos, explosiones, alarmas, mensajes de radio y música que acompañan la tensión del momento. El sonido también ayuda a localizar enemigos fuera de la vista.
- **Efectos especiales.** Destellos de disparo, explosiones, partículas, temblores de pantalla al recibir daño y avisos visuales cuando la energía se agota.
- **Cambio de fondo.** El fondo espacial cambia a lo largo de la partida (nebulosas, planetas, estrellas, eclipses, tormentas). Estos cambios refuerzan la sensación de progreso y acompañan la historia.

## Pilares del diseño

1. **Vigilar y decidir.** El jugador siempre debe elegir hacia dónde mirar.
2. **Administrar la energía.** Disparar sin control castiga. Apuntar bien recompensa.
3. **Sensación por encima del realismo.** Sonido, efectos y entorno dan vida a un escenario estático.
4. **Simplicidad.** Pocos controles, fáciles de aprender.
