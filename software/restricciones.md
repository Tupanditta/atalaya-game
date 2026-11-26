# Restricciones

Límites de alcance y condiciones que deben respetarse en el diseño, la implementación y la organización del proyecto.

## Alcance

- **RES-01. Un solo jugador:** El juego es para un solo jugador. El modo multijugador queda fuera de alcance.
- **RES-02. Sin desplazamiento:** Queda fuera de alcance cualquier desplazamiento del jugador por el escenario (ver RN-01).
- **RES-03. Gráficos sencillos:** No se exigen modelos 3D de calidad profesional. La calidad de la experiencia se apoya en el sonido, los efectos especiales y los cambios de fondo.

## Restricciones técnicas

- **RES-04. Plataforma:** El juego se ejecuta en un ordenador y se controla con el teclado. El ratón solo se usa durante una oleada, para mover la mira (RF-46) y para disparar con el botón izquierdo como alternativa a la barra espaciadora. Los mandos y las pantallas táctiles quedan fuera de alcance.
- **RES-05. Lenguaje:** El código se implementa en Python. Las dependencias se instalan en el entorno virtual `implementacion/.venv`.

## Restricciones de datos y privacidad

- **RES-07. Datos solo en el equipo:** Los datos guardados se almacenan solo en el equipo del jugador. No se envían a ningún servidor ni servicio externo.

## Restricciones de organización de archivos

- **RES-06. Separación de especificación y código:** La especificación se guarda en `software/` y no contiene código. El código se guarda en `implementacion/`.
