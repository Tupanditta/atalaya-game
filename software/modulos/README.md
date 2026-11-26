# Módulos

El juego se divide en módulos con una responsabilidad cada uno. El objetivo es que cada módulo se pueda entender, probar y cambiar sin tocar los demás.

## Principios

1. **Dos capas.**
   - La **capa lógica** contiene las reglas del juego. No conoce el motor gráfico, el teclado ni el sonido, y se puede probar sin abrir una ventana.
   - La **capa de presentación** contiene los adaptadores del motor. Lee el teclado, dibuja la escena y la interfaz, y reproduce el sonido.
2. **La lógica no depende de la presentación.** Ningún módulo lógico conoce a un módulo de presentación. La presentación sí consulta el estado de la lógica.
3. **Comunicación por eventos.** Los módulos se avisan de lo que ocurre publicando eventos en el bus del núcleo. Quien publica un evento no sabe quién lo escucha.
4. **Consultas de solo lectura.** Cuando un módulo necesita el estado de otro, lo consulta, pero no lo modifica. Las únicas consultas permitidas son las de la tabla de dependencias.
5. **Parámetros fuera del código.** Todos los valores de la sección «Parámetros iniciales» de `reglasNegocio.md` se leen del módulo `parametros`. Ningún módulo tiene valores de juego escritos a mano.
6. **Tiempo del núcleo.** Ningún módulo lógico lee el reloj del sistema. Todos reciben el paso de tiempo del núcleo, de modo que la pausa (RN-50) los detiene a todos a la vez.

## Lista de módulos

| Módulo | Capa | Responsabilidad | Archivo |
|---|---|---|---|
| nucleo | lógica | Bucle a paso fijo, reloj pausable, bus de eventos, azar con semilla | [nucleo.md](nucleo.md) |
| parametros | lógica | Cargar y validar los parámetros del juego | [parametros.md](parametros.md) |
| flujo | lógica | Pantallas y estados del juego; reparte las acciones del jugador | [flujo.md](flujo.md) |
| vista | lógica | Orientación de la cámara, giro, zoom y desvío por temblor | [vista.md](vista.md) |
| armamento | lógica | Energía, mira de precisión y disparo | [armamento.md](armamento.md) |
| estacion | lógica | Integridad, aturdimiento, desestabilización y valores mejorados | [estacion.md](estacion.md) |
| enemigos | lógica | Enemigos, movimiento, ataques, proyectiles e impactos | [enemigos.md](enemigos.md) |
| oleadas | lógica | Composición, aparición, fin de oleada, descanso y victoria | [oleadas.md](oleadas.md) |
| mejoras | lógica | Puntos de mejora, reparación y mejoras | [mejoras.md](mejoras.md) |
| entorno | lógica | Fondo espacial y entornos de baja visibilidad | [entorno.md](entorno.md) |
| radar | lógica | Contactos del radar respecto a la cámara | [radar.md](radar.md) |
| historia | lógica | Transmisiones de radio | [historia.md](historia.md) |
| progreso | lógica | Guardar y leer el nivel desbloqueado | [progreso.md](progreso.md) |
| entrada | presentación | Teclado y acciones del jugador | [entrada.md](entrada.md) |
| escena | presentación | Escena 3D, efectos visuales y cámara | [escena.md](escena.md) |
| hud | presentación | Mira, radar, indicadores, menús y pantallas | [hud.md](hud.md) |
| audio | presentación | Efectos, sonido posicional, radio y música | [audio.md](audio.md) |

El **arranque** no es un módulo: es el punto de entrada del programa. Crea los módulos en orden, les pasa sus dependencias y arranca el bucle del núcleo. Es el único sitio donde se conocen todos los módulos.

## Dependencias permitidas

Todos los módulos pueden usar `nucleo` y `parametros`. Además, solo se permiten estas consultas:

| Módulo | Consulta a |
|---|---|
| flujo | entrada (acciones), vista, armamento, mejoras, oleadas, progreso |
| armamento | vista (dirección de la mira) |
| radar | vista (orientación), enemigos (posiciones) |
| escena | vista, enemigos, entorno, armamento |
| hud | vista (posición de la mira), radar, armamento, estacion, oleadas, mejoras, historia, flujo, progreso, parametros |
| audio | vista (oyente), enemigos (posiciones), flujo (sonidos de los menús) |

Cualquier otra relación entre módulos se hace con eventos. Una consulta nueva debe añadirse antes a esta tabla.

## Orden de actualización

En cada paso de simulación (60 por segundo), el núcleo actualiza los módulos en este orden:

1. `entrada` toma el estado del teclado.
2. `flujo` reparte las acciones según la pantalla actual.
3. `vista` aplica el giro, el zoom y el temblor.
4. `armamento` actualiza la energía y la mira, y resuelve el disparo.
5. `enemigos` mueve enemigos y proyectiles, y resuelve impactos.
6. `oleadas` gestiona apariciones, el cronómetro y el descanso.
7. `estacion` actualiza la duración del aturdimiento y la desestabilización.
8. `entorno` actualiza la niebla y los destellos.

`mejoras`, `historia` y `progreso` solo reaccionan a eventos. `escena`, `hud` y `audio` se actualizan una vez por fotograma, después de la simulación.

Con la partida en pausa, los pasos 3 a 8 no se ejecutan.

## Catálogo de eventos

| Evento | Datos | Publica | Escuchan |
|---|---|---|---|
| PartidaIniciada | nivel | flujo | vista, armamento, estacion, enemigos, oleadas, mejoras, entorno, historia, escena, hud, audio |
| PartidaAbandonada | — | flujo | enemigos, oleadas, entorno, escena, audio |
| PausaCambiada | activa | flujo | escena, hud, audio |
| ApuntadoCambiado | progreso (0 = mira normal, 1 = mira mínima) | armamento | vista, hud, audio |
| DisparoRealizado | origen, dirección | armamento | enemigos, escena, audio |
| DisparoSinEnergia | — | armamento | hud, audio |
| EnergiaCambiada | actual, máxima | armamento | hud |
| EnemigoAparecido | id, tipo, tamaño | enemigos | escena, audio |
| AvisoDisparo | id del enemigo | enemigos | escena, audio |
| ProyectilLanzado | id, tipo de enemigo | enemigos | escena, audio |
| ProyectilImpacta | tipo de enemigo | enemigos | estacion |
| EnemigoAlcanzado | id, vida restante | enemigos | escena, audio |
| EnemigoDestruido | id, posición | enemigos | oleadas, escena, audio |
| EstacionDanada | cantidad, integridad, máxima | estacion | escena, hud, audio |
| IntegridadCambiada | actual, máxima | estacion | mejoras, hud |
| DesestabilizacionIniciada / DesestabilizacionTerminada | duración | estacion | vista, escena, hud |
| AturdimientoIniciado / AturdimientoTerminado | duración | estacion | vista, armamento, hud, audio |
| EstacionDestruida | oleadas superadas | estacion | flujo, enemigos, oleadas, entorno, escena, audio, historia |
| OleadaIniciada | número, entorno | oleadas | entorno, hud, audio |
| SolicitudAparicion | tipo, tamaño, vida | oleadas | enemigos |
| OleadaSuperada | número, tiempo, enemigos | oleadas | mejoras, entorno, historia, flujo, audio |
| DescansoIniciado | duración, siguiente oleada | oleadas | flujo, mejoras, hud |
| DescansoTerminado | — | oleadas | flujo, mejoras |
| TerminarDescansoSolicitado | — | flujo | oleadas |
| PartidaGanada | nivel | oleadas | flujo, progreso, historia, audio |
| PuntosObtenidos | obtenidos, disponibles, tiempo, tiempo de referencia | mejoras | hud |
| ReparacionAplicada | cantidad | mejoras | estacion |
| MejoraAplicada | mejora, nivel | mejoras | estacion, armamento, hud |
| FondoCambiado | índice del fondo | entorno | escena |
| EntornoCambiado | ninguno, niebla o destellos | entorno | escena, audio |
| DestelloAviso / DestelloInicio / DestelloFin | — | entorno | escena, audio |
| TransmisionDisponible | texto | historia | hud, audio |

Los eventos se entregan en el mismo paso en que se publican, en el orden en que se publican.
