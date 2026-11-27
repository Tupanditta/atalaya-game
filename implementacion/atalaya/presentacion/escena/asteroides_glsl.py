"""Programa GLSL de las rocas de los asteroides (`sombreado.py`).

Luz por píxel con las normales suaves de la roca y el color de cada vértice (que ya
oscurece las hendiduras). Un contorno tenue en el lado de la sombra separa las rocas del
fondo. Todo en el espacio de la vista.

Entradas, puestas en el nodo del paisaje: `luz_dir` (hacia el sol, en el mundo) y
`luz_color`.
"""

_VERTICE = """
#version 130
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrix;
uniform mat3 p3d_NormalMatrix;
uniform mat4 p3d_ViewMatrix;
uniform vec3 luz_dir;
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec4 p3d_Color;
out vec3 v_normal;
out vec3 v_vista;
out vec3 v_luz;
out vec4 v_color;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    v_normal = p3d_NormalMatrix * p3d_Normal;
    v_vista = -(p3d_ModelViewMatrix * p3d_Vertex).xyz;
    v_luz = mat3(p3d_ViewMatrix) * luz_dir;
    v_color = p3d_Color;
}
"""

_FRAGMENTO = """
#version 130
uniform vec3 luz_color;
uniform vec4 p3d_ColorScale;
in vec3 v_normal;
in vec3 v_vista;
in vec3 v_luz;
in vec4 v_color;
out vec4 color_final;

void main() {
    vec3 n = normalize(v_normal);
    vec3 v = normalize(v_vista);
    vec3 l = normalize(v_luz);
    vec3 base = v_color.rgb * p3d_ColorScale.rgb;
    float difusa = max(dot(n, l), 0.0);
    // Roca polvorienta: algo de brillo rasante cuando la luz llega de frente.
    float rasante = pow(max(dot(reflect(-l, n), v), 0.0), 6.0) * 0.12;
    vec3 color = base * luz_color * (difusa + rasante);
    // Contorno: la luz del sol bordea la roca vista a contraluz.
    float borde = pow(1.0 - max(dot(n, v), 0.0), 4.0);
    float contraluz = max(dot(-v, l), 0.0);
    color += luz_color * base * borde * (0.12 + 0.5 * contraluz);
    // Cara de sombra: apenas se adivina.
    color += base * 0.025;
    color_final = vec4(color, p3d_ColorScale.a);
}
"""

PROGRAMAS: dict[str, tuple[str, str]] = {"roca": (_VERTICE, _FRAGMENTO)}
