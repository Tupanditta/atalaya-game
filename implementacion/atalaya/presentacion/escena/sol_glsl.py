"""Programa GLSL del deslumbramiento del sol (`sol.py`).

Se dibuja en una tarjeta enfrentada a la cámara, centrada en el sol. Coordenadas de la
tarjeta de −1 a 1. Núcleo muy brillante, halo amplio y seis rayos finos que se apagan
hacia fuera. `visible` atenúa todo si un planeta tapa el sol.
"""

_VERTICE = """
#version 130
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
out vec2 v_p;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    v_p = p3d_MultiTexCoord0 * 2.0 - 1.0;
}
"""

_FRAGMENTO = """
#version 130
uniform vec3 sol_color;
uniform float visible;
uniform float tiempo;
uniform vec4 p3d_ColorScale;
in vec2 v_p;
out vec4 color_final;

void main() {
    float r = length(v_p);
    float angulo = atan(v_p.y, v_p.x);
    float nucleo = exp(-r * 38.0) * 2.2;
    float halo = exp(-r * 7.0) * 0.35 + exp(-r * 2.6) * 0.08;
    // Seis rayos finos, de largos algo distintos, que vibran muy despacio.
    float rayos = pow(abs(cos(angulo * 3.0 + 0.3)), 90.0) * exp(-r * 4.5) * 0.55;
    rayos += pow(abs(cos(angulo * 3.0 + 0.3 + 1.0472 * 0.5)), 140.0) * exp(-r * 8.0) * 0.3;
    rayos *= 0.9 + 0.1 * sin(tiempo * 1.3 + angulo * 4.0);
    float luz = (nucleo + halo + rayos) * visible * smoothstep(1.0, 0.85, r);
    color_final = vec4(sol_color * luz, 1.0) * p3d_ColorScale;
}
"""

PROGRAMAS: dict[str, tuple[str, str]] = {"sol": (_VERTICE, _FRAGMENTO)}
