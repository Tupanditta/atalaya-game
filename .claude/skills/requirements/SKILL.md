---
name: requirements
description: Formato, identificadores y criterios de calidad para requisitos funcionales (RF), no funcionales (RNF) y reglas de negocio (RN). Usar al crear, modificar o revisar software/requisitos.md o software/reglasNegocio.md.
---
# Requisitos y reglas de negocio

## Tipos
- **Requisito funcional (RF):** un servicio o función que el sistema ofrece. Archivo: `software/requisitos.md`, sección `## Requisitos funcionales`.
- **Requisito no funcional (RNF):** un límite o cualidad del sistema o del proceso de desarrollo. Archivo: `software/requisitos.md`, sección `## Requisitos no funcionales`.
- **Regla de negocio (RN):** una política o condición del dominio que el sistema debe respetar, independiente de la tecnología (p. ej. "un pedido no puede superar 10 artículos"). Archivo: `software/reglasNegocio.md`.

Si algo limita cómo se construye o distribuye el sistema (tecnología impuesta, plataforma, plazos), es una restricción: ver la skill `restrictions`.

## Características de un buen requisito funcional
- Describe el problema, no la solución.
- Usa lenguaje de negocio, no técnico.
- Es concreto y verificable: debe poder escribirse una prueba o criterio de aceptación que diga si se cumple.
- Es atómico: un requisito, una necesidad. Si lleva "y" o "o", probablemente son dos.
- No es ambiguo: evita "rápido", "fácil", "intuitivo", "etc." sin una medida.

No sobreespecifiques: fijar demasiados detalles al principio alarga el descubrimiento de requisitos sin aportar valor.

## Categorías habituales de RNF
Rendimiento, seguridad, disponibilidad, usabilidad y accesibilidad, compatibilidad, integración, mantenibilidad, soporte técnico, ubicación física. Cada RNF debe ser medible (p. ej. "responde en menos de 2 s con 100 usuarios concurrentes", no "es rápido").

## Identificadores
- Formato `RF-01`, `RNF-01`, `RN-01`, correlativos con dos dígitos (tres si se superan 99).
- Un identificador nunca se reutiliza ni se renumera, aunque el requisito se elimine (márcalo como `Eliminado`).
- Fuera de su archivo, un requisito o regla se cita solo por su identificador.

## Formato de cada entrada
```markdown
### RF-01. Título breve
- **Descripción:** El sistema debe permitir que <actor> <acción> para <beneficio>.
- **Prioridad:** Alta | Media | Baja
- **Origen:** <usuario, documento o sección de contexto.md>
- **Estado:** Propuesto | Confirmado | Eliminado
```
Para RNF, añade **Medida:** con el criterio cuantificable. Para RN, sustituye "El sistema debe…" por la regla del dominio.
