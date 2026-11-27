"""Programa GLSL de la capa de estrellas que centellean (`estrellas.py`).

Cada punto es un cuadrado de pantalla con la textura de brillo. Las más débiles llenan
menos el cuadrado; todas oscilan un poco de intensidad, cada una a su ritmo (`fase`).
"""

_VERTICE = """
#version 130
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform float tiempo;
in vec4 p3d_Vertex;
in vec4 p3d_Color;
in vec2 fase;
out vec3 v_color;
out float v_nitidez;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    float brillo = max(max(p3d_Color.r, p3d_Color.g), p3d_Color.b);
    // Dos senos de ritmos distintos: el centelleo no se ve periódico.
    float onda = sin(tiempo * fase.y + fase.x) * 0.6
        + sin(tiempo * fase.y * 2.7 + fase.x * 1.3) * 0.4;
    v_color = p3d_Color.rgb * (1.0 + 0.22 * onda);
    // Las débiles, más pequeñas: el brillo cae antes hacia el borde del punto.
    v_nitidez = mix(9.0, 3.0, brillo);
}
"""

_FRAGMENTO = """
#version 130
uniform vec4 p3d_ColorScale;
in vec3 v_color;
in float v_nitidez;
out vec4 color_final;

void main() {
    vec2 p = gl_PointCoord * 2.0 - 1.0;
    float r2 = dot(p, p);
    float luz = exp(-r2 * v_nitidez) + 0.25 * exp(-r2 * v_nitidez * 0.25) * step(r2, 1.0);
    color_final = vec4(v_color * luz, 1.0) * p3d_ColorScale;
}
"""

PROGRAMAS: dict[str, tuple[str, str]] = {"estrellas": (_VERTICE, _FRAGMENTO)}
