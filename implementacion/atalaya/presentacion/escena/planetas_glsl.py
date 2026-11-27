"""Programas GLSL de los planetas: superficie, atmósfera y anillos (`sombreado.py`).

Todo se calcula en el espacio del objeto, donde el planeta es una esfera de radio 1 y los
anillos están en el plano z = 0 (el ecuador). La luz y la vista se pasan a ese espacio en
el programa de vértices.

Entradas comunes, puestas en el nodo del planeta:

- `luz_dir`: dirección hacia el sol, en el mundo. `luz_color`: color del sol.
- `atmosfera`: color de la atmósfera; `a` es su fuerza (0 si no tiene).
- `anillos`: radios interior y exterior de los anillos y, en `z`, 1 si los tiene.
- `tex_anillos`: densidad de los anillos (canal alfa), de dentro a fuera.
- `tiempo`: segundos de paisaje, para mover las nubes.
"""

_VERTICE = """
#version 130
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
uniform mat4 p3d_ModelViewMatrix;
uniform vec3 luz_dir;
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
out vec3 v_pos;
out vec3 v_luz;
out vec3 v_vista;
out vec2 v_uv;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    v_pos = p3d_Vertex.xyz;
    v_uv = p3d_MultiTexCoord0;
    // Con escala uniforme, la traspuesta lleva direcciones al espacio del objeto.
    v_luz = transpose(mat3(p3d_ModelMatrix)) * luz_dir;
    vec3 ojo = (p3d_ModelViewMatrix * p3d_Vertex).xyz;
    v_vista = transpose(mat3(p3d_ModelViewMatrix)) * -ojo;
}
"""

#: Funciones comunes: sombra de los anillos sobre un punto y de la esfera sobre otro.
_COMUN = """
uniform vec3 anillos;
uniform sampler2D tex_anillos;

float densidad_anillos(float r) {
    if (anillos.z < 0.5 || r < anillos.x || r > anillos.y) return 0.0;
    return texture(tex_anillos, vec2((r - anillos.x) / (anillos.y - anillos.x), 0.5)).a;
}

// Luz que llega a `p` tras cruzar los anillos en dirección a `l`.
float paso_anillos(vec3 p, vec3 l) {
    if (anillos.z < 0.5 || abs(l.z) < 1e-4) return 1.0;
    float t = -p.z / l.z;
    if (t <= 0.0) return 1.0;
    vec3 cruce = p + l * t;
    return 1.0 - 0.9 * densidad_anillos(length(cruce.xy));
}
"""

_SUPERFICIE = (
    """
#version 130
uniform sampler2D tex_color;
uniform sampler2D tex_emisivo;
uniform sampler2D tex_nubes;
uniform vec3 luz_color;
uniform vec4 atmosfera;
uniform vec4 nubes;
uniform float hielo;
uniform float emisivo;
uniform float relieve;
uniform float tiempo;
uniform vec4 p3d_ColorScale;
in vec3 v_pos;
in vec3 v_luz;
in vec3 v_vista;
in vec2 v_uv;
out vec4 color_final;
"""
    + _COMUN
    + """
float altura(vec2 uv) { return texture(tex_color, uv).a; }

void main() {
    vec3 n = normalize(v_pos);
    vec3 l = normalize(v_luz);
    vec3 v = normalize(v_vista);
    // Relieve: la pendiente de la altura inclina la normal hacia el este y el norte.
    vec3 este = normalize(vec3(-n.y, n.x, 0.0) + vec3(1e-5, 0.0, 0.0));
    vec3 norte = cross(n, este);
    vec2 paso = 1.0 / vec2(textureSize(tex_color, 0));
    float de = altura(v_uv + vec2(paso.x, 0.0)) - altura(v_uv - vec2(paso.x, 0.0));
    float dn = altura(v_uv + vec2(0.0, paso.y)) - altura(v_uv - vec2(0.0, paso.y));
    vec3 normal = normalize(n - relieve * (de * este + dn * norte));

    vec3 base = texture(tex_color, v_uv).rgb;
    float geometrica = dot(n, l);
    // Paso suave del día a la noche: la luz se apaga antes de la sombra geométrica.
    float dia = smoothstep(-0.12, 0.18, geometrica);
    float difusa = max(dot(normal, l), 0.0) * dia;
    difusa *= paso_anillos(n, l);

    // Nubes: giran más deprisa que el suelo y le dan sombra hacia el lado contrario al sol.
    float cubierta = 0.0;
    float sombra_nubes = 0.0;
    if (nubes.a > 0.0) {
        vec2 deriva = vec2(tiempo * 0.0006, 0.0);
        cubierta = texture(tex_nubes, v_uv + deriva).r * nubes.a;
        vec2 hacia_sol = vec2(dot(l, este), dot(l, norte)) * 0.006;
        sombra_nubes = texture(tex_nubes, v_uv + deriva - hacia_sol).r * nubes.a;
    }
    vec3 suelo = base * luz_color * difusa * (1.0 - 0.55 * sombra_nubes);
    float luz_nubes = max(geometrica, 0.0) * dia * paso_anillos(n, l);
    vec3 color = mix(suelo, nubes.rgb * luz_color * luz_nubes, cubierta);

    // Brillo del hielo bajo el sol.
    vec3 medio = normalize(l + v);
    float brillo = pow(max(dot(normal, medio), 0.0), 48.0) * hielo * dia * (1.0 - cubierta);
    color += luz_color * brillo * 0.45;

    // Atmósfera: tiñe la línea de sombra y aclara el borde del disco.
    float frente = max(dot(n, v), 0.0);
    if (atmosfera.a > 0.0) {
        float ocaso = exp(-pow(geometrica / 0.16, 2.0));
        color += atmosfera.rgb * vec3(1.0, 0.62, 0.42) * ocaso * 0.18 * atmosfera.a;
        float borde = pow(1.0 - frente, 3.0);
        color += atmosfera.rgb * luz_color * borde * dia * 0.25 * atmosfera.a;
    }
    // Oscurecimiento hacia el borde, más marcado con atmósfera densa.
    color *= mix(0.62, 1.0, pow(frente, 0.35));
    // Lava: brilla en todo el planeta, más visible en la cara de noche.
    if (emisivo > 0.0) {
        vec3 lava = texture(tex_emisivo, v_uv).rgb;
        // Solo brillan con fuerza las grietas más calientes.
        lava = lava * lava * 1.6;
        color += lava * (0.3 + 0.5 * (1.0 - dia)) * (1.0 - 0.7 * cubierta);
    }
    // La cara de noche se adivina.
    color += base * 0.012;
    color_final = vec4(color, 1.0) * p3d_ColorScale;
}
"""
)

_ATMOSFERA = """
#version 130
uniform vec3 luz_color;
uniform vec4 atmosfera;
uniform float alcance;
uniform vec4 p3d_ColorScale;
in vec3 v_pos;
in vec3 v_luz;
in vec3 v_vista;
out vec4 color_final;

void main() {
    // Cáscara de radio `alcance` (en radios del planeta) vista desde fuera.
    vec3 p = normalize(v_pos) * alcance;
    vec3 v = normalize(v_vista);
    vec3 l = normalize(v_luz);
    vec3 d = -v;
    // Tramo del rayo de vista dentro de la cáscara, hasta el suelo o hasta volver a salir.
    float b = dot(p, d);
    float c = dot(p, p) - alcance * alcance;
    float salida = -b + sqrt(max(b * b - c, 0.0));
    float suelo = b * b - (dot(p, p) - 1.0);
    float largo = salida;
    if (suelo > 0.0 && -b - sqrt(suelo) > 0.0) largo = -b - sqrt(suelo);
    vec3 medio = p + d * (largo * 0.5);
    float iluminado = smoothstep(-0.25, 0.35, dot(normalize(medio), l));
    float densidad = (1.0 - exp(-largo * 5.0)) * 0.8;
    // Más rojiza donde la luz roza el planeta, como en un ocaso.
    float roce = exp(-pow(dot(normalize(medio), l) / 0.22, 2.0));
    vec3 ocaso = atmosfera.rgb * vec3(1.0, 0.55, 0.35) + vec3(0.12, 0.03, 0.0);
    vec3 tono = mix(atmosfera.rgb, ocaso, roce);
    // Mirando hacia el sol, la luz atraviesa el borde y se ve más.
    float contraluz = 1.0 + 1.6 * pow(max(dot(d, l), 0.0), 6.0);
    vec3 color = tono * luz_color * densidad * iluminado * contraluz * atmosfera.a;
    color_final = vec4(color, 1.0) * p3d_ColorScale;
}
"""

_ANILLOS = (
    """
#version 130
uniform vec3 luz_color;
uniform vec4 p3d_ColorScale;
in vec3 v_pos;
in vec3 v_luz;
in vec3 v_vista;
out vec4 color_final;
"""
    + _COMUN
    + """
void main() {
    vec3 l = normalize(v_luz);
    vec3 v = normalize(v_vista);
    float r = length(v_pos.xy);
    vec4 muestra = texture(tex_anillos, vec2((r - anillos.x) / (anillos.y - anillos.x), 0.5));
    float densidad = muestra.a;
    // Sombra del planeta: el rayo hacia el sol corta la esfera de radio 1.
    float b = dot(v_pos, l);
    float c = dot(v_pos, v_pos) - 1.0;
    float corte = b * b - c;
    float sombra = (b < 0.0) ? smoothstep(-0.02, 0.06, corte) : 0.0;
    float luz = 1.0 - 0.95 * sombra;
    // Vistos desde el lado de la sombra, solo pasa la luz por las zonas finas.
    bool contraluz = sign(v.z) != sign(l.z);
    float a_traves = contraluz ? (1.0 - densidad) * 1.4 + 0.15 : 1.0;
    float rasante = 0.35 + 0.65 * abs(l.z);
    vec3 color = muestra.rgb * luz_color * luz * a_traves * rasante;
    color_final = vec4(color, densidad) * p3d_ColorScale;
}
"""
)

PROGRAMAS: dict[str, tuple[str, str]] = {
    "planeta": (_VERTICE, _SUPERFICIE),
    "atmosfera": (_VERTICE, _ATMOSFERA),
    "anillos": (_VERTICE, _ANILLOS),
}
