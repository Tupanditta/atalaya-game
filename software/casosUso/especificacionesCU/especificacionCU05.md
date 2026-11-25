# CU-05. Localizar enemigos

## Identificación
- **Actor principal:** ACT-01
- **Actores secundarios:** ninguno
- **Objetivo:** Saber dónde están los enemigos, incluidos los que están fuera de la vista.
- **Requisitos relacionados:** RF-07, RF-10, RF-22, RF-23, RN-08, RN-09, RES-05, RES-06

## Precondiciones
- Hay una partida en curso con al menos un enemigo activo.

## Disparador
El jugador quiere saber hacia dónde mirar.

## Flujo principal
1. El jugador consulta el radar.
2. El sistema muestra en el radar la posición, el tipo y el tamaño de cada enemigo activo respecto a la orientación del jugador.
3. El sistema emite el sonido de cada enemigo de modo que se perciba la dirección de la que viene.
4. El jugador identifica la dirección de un enemigo y gira hacia él (CU-02).

## Flujos alternativos y excepciones
### A1. Enemigo de baja visibilidad (desde el paso 2)
1. Un enemigo es difícil de distinguir en pantalla.
2. El sistema lo muestra en el radar igual que al resto de enemigos.
3. Vuelve al paso 3.

## Reglas de presentación
- El radar se actualiza de forma continua mientras haya enemigos activos.
- Cómo se representan en el radar el tipo y el tamaño está [por definir].
- El radar representa las tres dimensiones, porque la vista gira en horizontal y en vertical. Cómo lo hace está [por definir].
- Si el radar distingue los enemigos que están dentro de la vista de los que están fuera está [por definir].

## Postcondiciones
- No modifica el estado del sistema.

## Criterios de aceptación
- Todo enemigo activo aparece en el radar en la dirección correcta respecto a la vista del jugador.
- Un enemigo de baja visibilidad aparece en el radar.
- En el radar se distinguen los tres tipos de enemigo y sus tamaños.
- Un enemigo situado a un lado del jugador se oye por ese lado.
