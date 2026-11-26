# CU-05. Localizar enemigos

## Identificación
- **Actor principal:** ACT-01
- **Actores secundarios:** ninguno
- **Objetivo:** Saber dónde están los enemigos, incluidos los que están fuera de la vista.
- **Requisitos relacionados:** RF-07, RF-10, RF-22, RF-23, RF-31, RF-45, RN-09, RN-29, RN-30, RN-41, RN-44, RES-05, RES-06

## Precondiciones
- Hay una partida en curso con al menos un enemigo activo.

## Disparador
El jugador quiere saber hacia dónde mirar.

## Flujo principal
1. El jugador consulta el radar.
2. El sistema muestra en el radar la posición, la distancia, el tipo y el tamaño de cada enemigo activo respecto a la orientación del jugador.
3. El sistema emite el sonido de cada enemigo de modo que se perciba la dirección de la que viene.
4. El jugador identifica la dirección de un enemigo y gira hacia él (CU-02).

## Flujos alternativos y excepciones
### A1. Entorno de baja visibilidad (desde el paso 2)
1. La oleada se juega con niebla o con destellos, y hay enemigos que no se ven en pantalla.
2. El sistema los sigue mostrando en el radar igual que en un entorno normal. El radar no se ve afectado por la niebla ni por los destellos.
3. Vuelve al paso 3.

## Reglas de presentación
- El radar se actualiza de forma continua mientras haya enemigos activos.
- El radar es circular. La estación está en el centro y la dirección en la que mira el jugador apunta hacia arriba.
- La dirección horizontal de cada enemigo es su ángulo en el radar. Su distancia a la estación es su distancia al centro del radar; el borde corresponde al alcance del radar.
- La altura de cada enemigo respecto a la vista se indica junto a su símbolo: por encima, a la misma altura o por debajo.
- El tipo de enemigo se distingue por la forma y el color del símbolo: círculo para el enemigo sin efecto especial, triángulo para el desestabilizador y rombo para el aturdidor.
- El tamaño del enemigo se distingue por el tamaño del símbolo, con tres tamaños.
- El radar muestra el campo de visión actual como un sector. Los enemigos dentro de ese sector se ven resaltados.
- La forma, el color y la posición exactos se especifican en `interfaz/`.

## Postcondiciones
- No modifica el estado del sistema.

## Criterios de aceptación
- Todo enemigo activo aparece en el radar en la dirección correcta respecto a la vista del jugador.
- Con niebla o destellos, todos los enemigos activos siguen apareciendo en el radar.
- Un enemigo que ha aparecido en el radar no sale de él hasta ser destruido.
- En el radar se distinguen los tres tipos de enemigo y sus tamaños.
- En el radar se distingue qué enemigos están más cerca y cuáles más lejos, y el cambio se ve cuando un enemigo se acerca o se aleja.
- En el radar se distingue si cada enemigo está por encima, a la misma altura o por debajo de la vista.
- Los enemigos dentro del campo de visión aparecen resaltados en el radar.
- Un enemigo situado a un lado del jugador se oye por ese lado.
