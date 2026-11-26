# CU-11. Mejorar y reparar la estación

## Identificación
- **Actor principal:** ACT-01
- **Actores secundarios:** ninguno
- **Objetivo:** Gastar los puntos de mejora en reparar la estación o en mejorarla antes de la siguiente oleada.
- **Requisitos relacionados:** RF-16, RF-40, RF-41, RF-42, RF-43, RF-44, RNF-03, RN-18, RN-45, RN-46, RN-47, RN-48, RN-49, RES-04, RES-05, RES-06

## Precondiciones
- Ha terminado una oleada que no es la final y ha empezado el descanso (CU-07).

## Disparador
El sistema abre la pantalla de mejoras al empezar el descanso.

## Flujo principal
1. El sistema muestra la pantalla de mejoras con:
   - la transmisión de radio,
   - el tiempo de la oleada y los puntos obtenidos,
   - los puntos disponibles,
   - la integridad actual y la máxima,
   - las opciones «Reparar», «Blindaje», «Batería», «Generador» y «Continuar», cada una con su coste y, en las mejoras, su nivel actual y máximo,
   - la cuenta atrás del descanso.
2. El jugador selecciona «Reparar» con las flechas arriba y abajo y pulsa Intro.
3. El sistema descuenta el coste de la reparación de los puntos disponibles y devuelve integridad a la estación, sin superar la máxima.
4. El sistema actualiza los puntos disponibles y la integridad.
5. El jugador repite los pasos 2 a 4 mientras le queden puntos, o elige otra opción.

## Flujos alternativos y excepciones
### A1. Mejorar una característica (desde el paso 2)
1. El jugador selecciona «Blindaje», «Batería» o «Generador» y pulsa Intro.
2. El sistema descuenta el coste de la mejora, sube un nivel esa característica y aplica su efecto a la estación.
3. Vuelve al paso 4.

### A2. Puntos insuficientes (desde el paso 2 o desde A1)
1. Los puntos disponibles no cubren el coste de la opción elegida.
2. El sistema no aplica nada y avisa con un sonido de error. La opción se muestra como no disponible.
3. Vuelve al paso 5.

### A3. Integridad al máximo (desde el paso 2)
1. La integridad de la estación ya está al máximo.
2. El sistema muestra «Reparar» como no disponible y no gasta puntos.
3. Vuelve al paso 5.

### A4. Mejora al nivel máximo (desde A1)
1. La característica elegida ya está en su nivel máximo.
2. El sistema la muestra como completa y no gasta puntos.
3. Vuelve al paso 5.

### A5. Continuar (desde el paso 5)
1. El jugador elige «Continuar».
2. El sistema termina el descanso y cierra la pantalla. Los puntos no gastados se conservan. Deriva al paso 7 de CU-07.

### A6. Fin de la cuenta atrás (en cualquier paso)
1. La cuenta atrás llega a cero.
2. El sistema cierra la pantalla. Los puntos no gastados se conservan. Deriva al paso 7 de CU-07.

### A7. Pausa (en cualquier paso)
1. El jugador pulsa Esc.
2. Deriva a CU-09. La cuenta atrás se detiene mientras dura la pausa.

## Reglas de presentación
- La pantalla de mejoras es simple: una lista vertical de opciones y un bloque de información.
- La cuenta atrás está siempre visible y destaca cuando quedan 5 segundos o menos.
- Las opciones que no se pueden elegir se muestran atenuadas.

## Postcondiciones
- Los puntos gastados quedan descontados.
- La integridad y las características de la estación reflejan las reparaciones y mejoras hechas.

## Criterios de aceptación
- La pantalla de mejoras solo aparece durante el descanso entre oleadas.
- Reparar cuesta 1 punto y devuelve 20 de integridad, sin superar la máxima.
- Cada nivel de mejora cuesta 2 puntos y no se puede pasar del nivel máximo.
- Con puntos insuficientes no se aplica nada.
- Subir el blindaje aumenta la integridad máxima y la actual en 10.
- Subir la batería aumenta la energía máxima en 10.
- Subir el generador aumenta la recarga en 1 por segundo.
- Los puntos no gastados siguen disponibles en el siguiente descanso.
- Al terminar la cuenta atrás, la pantalla se cierra y empieza la siguiente oleada aunque el jugador no haya elegido nada.
