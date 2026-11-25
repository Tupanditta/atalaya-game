---
name: restrictions
description: Crear, modificar o analizar las restricciones del proyecto (RES-XX) en software/restricciones.md. Usar cuando se pida definir límites de alcance, tecnología, plataforma o distribución.
---
# Restricciones del proyecto

## Propósito
Crear, modificar y analizar las restricciones respetando el alcance y las decisiones ya documentadas en `software/restricciones.md`.

## Fuentes de referencia
Consulta solo las necesarias para la tarea:
- `software/restricciones.md`: restricciones vigentes.
- `software/contexto.md`: lo que el usuario quiere del producto.
- `software/requisitos.md` (RF y RNF).
- `software/reglasNegocio.md`.
- `software/casosUso/especificacionesCU/`, cuando la restricción afecte a un flujo concreto.

No introduzcas decisiones que contradigan estos documentos. Si hay una contradicción, indica qué documentos afecta; no la resuelvas inventando una regla.

## Qué es una restricción
Una restricción delimita el alcance o impone una condición que debe respetarse en el diseño, la implementación o la distribución (p. ej. "debe funcionar sin conexión", "solo se usarán dependencias con licencia MIT", "fuera de alcance: pagos").
- No conviertas requisitos funcionales, detalles de interfaz o ideas futuras en restricciones.
- Redacta cada restricción como una regla concreta, clara y comprobable.
- No añadas tecnologías, servicios ni plataformas salvo que el usuario los pida o los documentos lo justifiquen.
- No dupliques: si una regla pertenece a otro documento, referencia su ID.

## Estructura del documento
1. Título y una breve introducción.
2. Secciones temáticas. Usa solo las que tengan contenido; las habituales son:
   - Alcance (incluido y excluido)
   - Restricciones técnicas (lenguaje, plataforma, dependencias)
   - Restricciones de datos y privacidad
   - Restricciones de conectividad
   - Restricciones de distribución y despliegue
   - Restricciones de organización de archivos
3. Cada regla en una línea:

`- **RES-01. Nombre breve:** Regla concreta.`

## Crear
1. Comprueba si la regla ya está cubierta.
2. Identifica qué límite o decisión protege.
3. Asigna el siguiente `RES-XX` libre. Nunca renumeres ni reutilices identificadores.
4. Ubícala en su sección y comprueba que no contradiga requisitos ni alcance.

## Modificar
1. Conserva el identificador mientras represente la misma decisión.
2. Cambia solo lo necesario y revisa las referencias en requisitos y casos de uso.
3. Si otra regla queda duplicada o contradictoria, indícalo y modifícala solo si es imprescindible para la coherencia.

## Analizar
- Señala contradicciones, duplicados, ambigüedades y reglas imposibles de comprobar, citando su `RES-XX`.
- Distingue entre restricción, RF, RNF, regla de negocio y decisión de interfaz.
- No presentes como defecto una ausencia que el proyecto haya excluido expresamente.
- Prioriza hallazgos concretos; no propongas cambios de redacción que no aporten claridad.
