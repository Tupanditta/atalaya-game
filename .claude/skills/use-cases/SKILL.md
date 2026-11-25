---
name: use-cases
description: Estructura del catálogo de casos de uso, actores, especificación de cada CU y matriz de trazabilidad en software/casosUso/ y software/matrizTrazabilidad.md. Usar al crear, modificar o revisar casos de uso o la matriz de trazabilidad.
---
# Casos de uso

## Archivos
- `software/casosUso/catalogoCU.md`: actores y lista de casos de uso.
- `software/casosUso/especificacionesCU/especificacionCUXX.md`: un archivo por caso de uso (p. ej. `especificacionCU01.md`).
- `software/matrizTrazabilidad.md`: relación entre requisitos, reglas de negocio, restricciones y casos de uso.

## Conceptos
**Actor:** rol que adopta una entidad al interactuar con el sistema. No tiene por qué ser humano (puede ser un sistema externo). Nombre descriptivo e identificador `ACT-01`, `ACT-02`…

**Caso de uso (CU):** comportamiento externo del sistema visto desde los actores.
- Describe todos los escenarios en que los actores usan una funcionalidad concreta; un escenario es una instancia del CU.
- Lo inicia siempre un actor; después pueden intervenir otros.
- Su título es una locución verbal con el objetivo del actor ("Registrar pedido", no "Pedidos").

## Catálogo
Arriba, la tabla de actores; debajo, la tabla de casos de uso.

```markdown
## Actores
| ID | Nombre | Descripción |
|---|---|---|
| ACT-01 | Cliente | Persona que compra en la tienda |

## Casos de uso
| ID | Título | Actores | Objetivo |
|---|---|---|---|
| CU-01 | Registrar pedido | ACT-01 | Que el cliente confirme una compra |
```
Identificadores `CU-01`, `CU-02`… correlativos, sin renumerar ni reutilizar.

## Especificación de cada caso de uso
Nombre del archivo: `especificacionCUXX.md` (camelCase, p. ej. `especificacionCU01.md`). Si falta información, escribe `[por definir]` y no inventes detalles.

```markdown
# CU-XX. <Título>

## Identificación
- **Actor principal:** ACT-XX
- **Actores secundarios:** ACT-YY | ninguno
- **Objetivo:** <resultado que el actor quiere alcanzar>
- **Requisitos relacionados:** RF-XX, RNF-XX, RN-XX, RES-XX

## Precondiciones
- <condición necesaria para empezar> | No se requieren precondiciones.

## Disparador
<evento que inicia el caso de uso>

## Flujo principal
1. El actor <acción>.
2. El sistema <respuesta observable>.
3. …hasta alcanzar el objetivo.

## Flujos alternativos y excepciones
### A1. <Nombre> (desde el paso N)
1. <acción o condición>
2. El sistema <respuesta>.
3. <Vuelve al paso M | Finaliza | Deriva a CU-YY>.

(Si no hay: "No se identifican flujos alternativos o excepciones.")

## Reglas de presentación
- <qué información se muestra y cómo; accesibilidad; lo que el sistema no debe hacer>
(Solo reglas propias de este CU; no repitas pasos del flujo.)

## Postcondiciones
- <estado o datos que quedan tras terminar con éxito> | No modifica el estado del sistema.

## Criterios de aceptación
- <condición observable y comprobable del flujo principal>
- <condición para cada alternativa o excepción relevante>
```

Distingue siempre las acciones del actor de las respuestas del sistema. Los criterios de aceptación son la base de las pruebas: deben ser comprobables, no objetivos vagos.

## Matriz de trazabilidad
Una fila por cada requisito (RF, RNF), regla de negocio (RN) y restricción (RES); marca con `X` los casos de uso con los que se relaciona.

```markdown
| Elemento | CU-01 | CU-02 | CU-03 |
|---|---|---|---|
| RF-01 | X | | |
| RNF-01 | | X | X |
| RN-01 | X | | |
| RES-01 | | | X |
```
- Todo RF, RNF, RN y RES debe relacionarse con al menos un CU (puede relacionarse con varios).
- Todo CU debe relacionarse con al menos un elemento (puede relacionarse con varios).
- Si alguno queda sin relacionar, indícalo al terminar.
