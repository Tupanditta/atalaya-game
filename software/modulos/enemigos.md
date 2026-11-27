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
  - maniobra (ataque, retirada o espera), destino actual y puntos de paso que le quedan,
  - fase de ataque (acercándose, en recarga o en aviso) y tiempo restante de esa fase.
- Para cada proyectil en vuelo: tipo del enemigo que lo disparó, posición y velocidad.

## Comportamiento de un enemigo
1. **Aparición:** al recibir SolicitudAparicion, crea el enemigo en una dirección al azar, a la distancia de aparición (RN-32). Empieza atacando, en fase de acercamiento.
2. **Movimiento con inercia (RN-33):** cada enemigo persigue su destino con una aceleración limitada y sin pasar de su velocidad máxima, así que describe curvas. Si se acerca a la distancia máxima, se le frena de forma gradual. Si va a pasar a menos de la distancia mínima, también (RN-31); si pasa de lado, no.
3. **Maniobras, en bucle (RN-30):**
   - **Ataque:** elige un punto de pasada de lado junto a la estación, a la distancia de pasada más el radio de su zona de impacto, y se lanza hacia él sin frenar. Al cruzar el plano de ese punto, perpendicular a su rumbo, ha sobrepasado la estación y empieza la retirada.
   - **Retirada:** sigue a toda velocidad dos puntos de paso, cada uno más lejos y girado entre 20° y 45° respecto al anterior (RN-29). Un punto de paso que ya queda detrás cuenta como alcanzado. Después sigue hacia un tercer punto y, al llegar a la distancia de aparición, empieza a esperar.
   - **Espera:** durante la duración de la espera patrulla de lado alrededor de la estación, a media velocidad, hacia puntos girados 25° y desviados hasta 50° del sentido de la marcha. Corrige poco a poco su distancia hacia una distancia de espera al azar entre la de aparición mínima y 50 u menos que la máxima. Después vuelve a atacar.
4. **Ataque:**
   - Solo durante la maniobra de ataque, dentro del alcance de disparo y con la recarga terminada, pasa a fase de aviso y publica AvisoDisparo (RN-34, RN-42).
   - Al terminar el aviso, lanza un proyectil hacia la estación (RN-35), publica ProyectilLanzado y pasa a fase de recarga, con el tiempo de recarga de su tipo (RN-14).
5. **Proyectiles:**
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
- **Consultar:** lista de enemigos activos (id, tipo, tamaño, posición, fase, maniobra); lista de proyectiles.

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
