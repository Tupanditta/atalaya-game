# Shaders del paisaje — plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans (sin subagentes:
> lo prohíbe `.claude/CLAUDE.md`). Pasos con casillas (`- [ ]`).

**Goal:** planetas, asteroides, estrellas y sol con shaders GLSL 1.30 y respaldo al aspecto
actual, sin posproceso.

**Architecture:** `sombreado.py` compila los programas una vez contra el GSG y devuelve
`None` en los que fallan; `Paisaje`, el cielo y el sol eligen su camino según eso. Las
texturas siguen generándose con numpy en un proceso aparte y van a la caché (versión 2).

**Tech Stack:** Python 3.11, Panda3D 1.10.16, numpy, pytest. Comandos desde `implementacion/`.

**Spec:** `docs/superpowers/specs/2026-11-27-shaders-paisaje-design.md`

## Global Constraints

- GLSL `#version 130`; los programas, como cadenas en módulos Python (sin datos de paquete).
- Los shaders multiplican el color final por `p3d_ColorScale` (el salto apaga `espacio`).
- `planetas.VERSION = 2`, `cielo.VERSION = 2`.
- Fluidez: mediana ≤ 1,9 ms, p99 ≤ 8 ms; generación en frío del fondo 1 ≤ 1,5 × la actual.
- Sin commits (los hace el propietario); sin subagentes; `software/design.md` §6 y
  `software/modulos/escena.md` al día; `.md` de la raíz intactos.
- Pruebas: `.venv/Scripts/python.exe -m pytest -q`; además `ruff check` y `mypy atalaya`.

## Review Focus

1. Sin GLSL o con un shader que no compila → aspecto actual, sin excepción (prueba en
   tarea 1 y en cada tarea con `Sombreado(None)`).
2. Caché v1 presente → se ignora y se regenera v2 (prueba en tarea 2: archivo v1 no se lee).
3. El salto apaga el paisaje con `alpha_scale`/`color_scale` → los shaders lo respetan
   (revisión visual en la captura del salto, tarea 7).
4. Estrellas brillantes quitadas del cubo → se ven también en el respaldo (prueba en tarea 5).
5. Fondos sin sol (2 y 5) → sin deslumbramiento (prueba en tarea 6).

---

### Task 1: Infraestructura de shaders

**Files:** Create `atalaya/presentacion/escena/sombreado.py`; Test
`pruebas/escena/test_sombreado.py`.

**Interfaces — Produces:**
- `class Sombreado: __init__(self, gsg: GraphicsStateGuardianBase | None)`;
  `programa(self, nombre: str) -> Shader | None`; `activo: bool` (hay GLSL ≥ 1.30).
- `PROGRAMAS: dict[str, tuple[str, str]]` (vértice, fragmento), que rellenan las tareas
  siguientes desde sus módulos (`planetas_glsl.py`, etc.).
- Compilación: `Shader.make(Shader.SL_GLSL, v, f)` y `shader.prepare_now(gsg.prepared_objects, gsg)`;
  `None` del contexto = fallo, se anota con `notify` y se devuelve `None`.

- [ ] Pruebas: `Sombreado(None).programa("planeta") is None`; con GSG fuera de pantalla
  (se omite si no hay GLSL) un programa válido compila y uno roto devuelve `None`.
- [ ] Implementar; pasar las pruebas.

### Task 2: Texturas de planetas v2

**Files:** Modify `planetas.py`, `fondo.py`; Test `pruebas/escena/test_paisaje.py`,
`test_fondo.py`.

**Interfaces — Produces:** `texturas_planeta(planeta, divisor) -> TexturasPlaneta` con
`TexturasPlaneta = tuple[color RGBA (alto, ancho, 4), emisivo RGB | None, nubes (alto/2, ancho/2) gris | None]`;
`Planeta.nubes: float = 0.0` (cobertura; 0 = sin nubes). Altura en A, 0–255.
Caché: claves `color{i}`, `emisivo{i}`, `nubes{i}`. `Fondos.texturas_planetas` devuelve
`list[tuple[Texture, Texture | None, Texture | None]]`.

- [ ] Pruebas: forma RGBA y alfa con rango > 100 niveles; nubes solo donde `nubes > 0` y no
  en el gaseoso; meridiano sin costura también en nubes; la caché v2 se relee igual.
- [ ] Implementar (altura = la misma señal que hoy hunde cráteres/grietas/dunas).

### Task 3: Shaders de planeta, atmósfera y anillos

**Files:** Create `atalaya/presentacion/escena/planetas_glsl.py`; Modify `paisaje.py`,
`escena.py` (pasa `Sombreado`, calienta); Test `test_paisaje.py`.

**Interfaces:** `Paisaje(padre, brillo, sombreado: Sombreado | None = None)`. Entradas
del shader del planeta: `color`, `emisivo`, `nubes` (texturas), `luz_dir` (mundo),
`luz_color`, `atmosfera` (vec4, a = 0 si no tiene), `anillos` (vec3: interior, exterior,
hay), `textura_anillos`, `tiempo_nubes`, `hielo` (float). Atmósfera: esfera a 1,04 con
`set_two_sided`/caras traseras y aditiva. El camino de respaldo es el código actual.

- [ ] Pruebas: con `sombreado=None` la estructura actual (lava, tarjeta de halo) no cambia;
  con un `Sombreado` falso que devuelve `Shader` sin compilar, hay `atmosfera` como esfera,
  no hay nodo `lava` y cada superficie lleva shader y su propia textura.
- [ ] Implementar; capturas `despues/` y comparar con `antes/`; validar con el propietario.

### Task 4: Asteroides

**Files:** Modify `paisaje.py`; Create `asteroides_glsl.py`; Test `test_paisaje.py`.

**Interfaces:** `_roca(semilla: int) -> GeomNode` con formato v3n3c4, subdivisión 3,
desplazamiento `ruido.fractal`, normales suaves; `_VARIANTES_ROCA = 8`.

- [ ] Pruebas: normales unitarias, sin triángulos degenerados, color por vértice variado;
  número de grupos aplanados igual que hoy (6).
- [ ] Implementar; capturas; validar.

### Task 5: Estrellas y nebulosas

**Files:** Modify `cielo.py`, `fondo.py`, `escena.py`; Create `estrellas_glsl.py`; Test
`test_fondo.py`.

**Interfaces:** `cielo.brillantes(indice: int, n: int = 1500) -> tuple[dirs (n,3), colores (n,3), brillo (n,)]`,
deterministas y excluidas del cubo; `capa_estrellas(indice, sombreado) -> NodePath`
(puntos, bin `background` tras el cubo). Colores por temperatura; `_LADO_NUBES = 512`.

- [ ] Medir antes el tiempo de `cielo.generar(1)` en frío.
- [ ] Pruebas: `brillantes` determinista; capa con `n` puntos con y sin shader; tonos con
  azuladas y rojizas.
- [ ] Implementar; tiempo ≤ 1,5 ×; capturas; validar.

### Task 6: Sol

**Files:** Create `sol.py` (+ GLSL); Modify `escena.py`; Test `pruebas/escena/test_sol.py`.

**Interfaces:** `class Sol: __init__(espacio, render2d, sombreado)`;
`mostrar(indice: int)`; `avanzar(camara: NodePath, lente: Lens)`. Sin sol en el tema → oculto.

- [ ] Pruebas: fondos 2 y 5 sin deslumbramiento; sol detrás de un planeta → atenuado;
  sol fuera de campo → destellos ocultos.
- [ ] Implementar; capturas; validar.

### Task 7: Medición y documentación

- [ ] Medición método F7 (fuera de pantalla, escena + HUD + audio reales): mediana, p99,
  picos; comparar con 1,4 / 6,5–7 ms.
- [ ] Captura durante el salto (respeta `color_scale`).
- [ ] `software/design.md` §6 y `software/modulos/escena.md`.
- [ ] Suite completa, `ruff`, `mypy`.
