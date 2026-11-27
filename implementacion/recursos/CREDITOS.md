# Créditos de recursos

Cada recurso externo se anota con su autor, origen y licencia (`design.md`, sección 14).

| Recurso | Autor | Origen | Licencia |
|---|---|---|---|
| Fuente Rajdhani SemiBold y Bold (`fuentes/`) | Indian Type Foundry | Google Fonts, repositorio `google/fonts`, carpeta `ofl/rajdhani` | SIL Open Font License 1.1 (`fuentes/OFL.txt`) |
| Disparo láser «BlasterOutgoing6abox» (`sonidos/177023__zimbot__blasteroutgoing6abox.wav`) | zimbot | freesound.org, sonido 177023 | Creative Commons Reconocimiento 4.0 (CC BY 4.0) |
| Explosión «Deep Boom» (`sonidos/539968__za-games__deep-boom.wav`) | Za-Games | freesound.org, sonido 539968 | Creative Commons 0 (CC0 1.0) |

Los cielos, planetas, efectos visuales y el resto de sonidos no son recursos externos: se generan por código al arrancar (`presentacion/escena/cielo.py`, `planetas.py` y `presentacion/audio/sintesis.py`). Qué sonidos se sustituyen por archivos de `sonidos/` lo dice `sonidos/sonidos.json`.
