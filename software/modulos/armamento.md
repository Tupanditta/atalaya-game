# Módulo armamento

- **Capa:** lógica
- **Cubre:** CU-04; RF-05, RF-06, RF-11, RF-32; RNF-05; RN-03, RN-04, RN-05, RN-23, RN-37, RN-38, RN-47 (batería y generador)

## Responsabilidad
Gestionar la energía, la mira de precisión y el momento del disparo.

## Estado que gestiona
- La energía actual, la energía máxima y la velocidad de recarga, incluidas las mejoras de batería y generador.
- El progreso de apuntado, de 0 (mira normal) a 1 (mira mínima), y el tamaño de mira que le corresponde.
- Si la barra espaciadora está pulsada y si el apuntado se ha cancelado (por aturdimiento o pausa) hasta que se suelte la barra.
- Si el jugador está aturdido.

## Operaciones
- **Recibir el estado de la barra espaciadora** (pulsada o no) desde `flujo`.
- **Actualizar:**
  - Recarga la energía (RN-04).
  - Mientras la barra está pulsada y el apuntado no está cancelado, aumenta el progreso de apuntado hasta 1 en el tiempo fijado. Al soltar o cancelar, lo devuelve a 0 en el tiempo de vuelta.
  - Al pasar la barra de pulsada a suelta:
    - Si el jugador está aturdido o el apuntado estaba cancelado, no dispara.
    - Si la energía no llega al coste del disparo, publica DisparoSinEnergia (RN-05).
    - En otro caso, descuenta el coste, elige un punto al azar uniforme dentro del círculo de la mira (RN-37) alrededor de la dirección de la mira de `vista`, y publica DisparoRealizado.
- **Cancelar el apuntado:** lo usa `flujo` al pausar.
- **Consultar:** energía actual y máxima, progreso de apuntado y tamaño de la mira.

## Eventos
- Publica: ApuntadoCambiado, DisparoRealizado, DisparoSinEnergia, EnergiaCambiada.
- Escucha:
  - AturdimientoIniciado, que cancela el apuntado y bloquea el disparo,
  - AturdimientoTerminado,
  - MejoraAplicada (batería y generador),
  - PartidaIniciada, que deja la energía al máximo base y quita las mejoras.

## Depende de
nucleo, parametros, vista (dirección de la mira).

## No hace
- No decide si el disparo acierta: `enemigos` resuelve el impacto al recibir DisparoRealizado.
- No dibuja la mira ni el rayo.
