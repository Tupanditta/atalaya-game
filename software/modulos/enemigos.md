# Módulo enemigos

- **Capa:** lógica
- **Cubre:** CU-04 (impacto), CU-06; RF-09, RF-13; RN-06, RN-07, RN-14, RN-29, RN-30, RN-31, RN-32, RN-33, RN-34, RN-35, RN-36, RN-42

## Responsabilidad
Mantener los enemigos y sus proyectiles: crearlos, moverlos, hacerlos atacar y resolver los disparos del jugador contra ellos.

## Estado que gestiona
- Para cada enemigo activo:
  - identificador, tipo, tamaño,
  - vida actual,
  - posición, velocidad,
  - fase de ataque (acercándose, en recarga o en aviso) y tiempo restante de esa fase.
- Para cada proyectil en vuelo: tipo del enemigo que lo disparó, posición y velocidad.

## Comportamiento de un enemigo
1. **Aparición:** al recibir SolicitudAparicion, crea el enemigo en una dirección al azar, a la distancia de aparición (RN-32). Empieza en fase de acercamiento.
2. **Movimiento con inercia (RN-33):**
   - Cada enemigo tiene un punto de destino. Lo persigue con una aceleración limitada y sin pasar de su velocidad máxima, así que describe curvas.
   - Cuando llega cerca del destino, elige otro al azar. Los destinos combinan cambios de dirección horizontales y verticales (RN-29) y de distancia (RN-30).
   - Los destinos siempre están entre la distancia mínima y la máxima. Si un enemigo se acerca al límite, se le frena y se le desvía de forma gradual (RN-31).
3. **Ataque:**
   - Fuera del alcance de disparo, el destino se elige dentro del alcance (RN-42).
   - Dentro del alcance y con la recarga terminada, pasa a fase de aviso y publica AvisoDisparo (RN-34).
   - Al terminar el aviso, lanza un proyectil hacia la estación (RN-35), publica ProyectilLanzado y pasa a fase de recarga, con el tiempo de recarga de su tipo (RN-14).
4. **Proyectiles:**
   - Avanzan en línea recta hacia la estación a velocidad constante.
   - Al llegar, publican ProyectilImpacta y desaparecen.
   - Un proyectil no desaparece aunque su enemigo sea destruido (RN-36).

## Resolución del disparo del jugador
Al recibir DisparoRealizado:
1. Busca el enemigo más cercano cuya zona de impacto (una esfera con el radio de su tamaño) corte la línea del disparo.
2. Si lo hay, le resta el daño del disparo.
   - Si su vida llega a cero, lo elimina, cancela su aviso si lo tenía y publica EnemigoDestruido (RN-07, RN-34).
   - Si no, publica EnemigoAlcanzado.

## Operaciones
- **Actualizar:** mueve enemigos y proyectiles y avanza sus fases.
- **Consultar:** lista de enemigos activos (id, tipo, tamaño, posición, fase); lista de proyectiles.

## Eventos
- Publica: EnemigoAparecido, AvisoDisparo, ProyectilLanzado, ProyectilImpacta, EnemigoAlcanzado, EnemigoDestruido.
- Escucha:
  - SolicitudAparicion, DisparoRealizado,
  - PartidaIniciada, PartidaAbandonada y EstacionDestruida, que eliminan todos los enemigos y proyectiles.

## Depende de
nucleo (azar con semilla), parametros.

## No hace
- No decide cuántos enemigos aparecen ni cuándo: eso lo hace `oleadas`.
- No aplica el daño a la estación: publica ProyectilImpacta y `estacion` lo aplica.
- No sabe si un enemigo se ve en pantalla: la niebla y los destellos no cambian su comportamiento (RN-44).
