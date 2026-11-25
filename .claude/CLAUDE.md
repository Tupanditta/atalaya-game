# Reglas de Entorno y Permisos
- Tienes permiso para instalar las librerías necesarias.
- Realiza siempre las instalaciones directamente en el entorno virtual activo:
  - Windows: `.\implementacion\.venv\Scripts\pip.exe install <paquete>`
- Nunca ejecutes `pip install` sin apuntar al entorno virtual.

## Identidad de Git

1. Nunca configures Claude como autor o committer, ni cambies `git config user.name` o `git config user.email`.
2. No crees commits. El propietario del repositorio crea y sube todos los commits.
3. No modifiques autores existentes ni reescribas el historial.
4. No cambien el branch actual, a menos que yo te lo pida expresamente

## Datos personales y secretos

1. Nunca escribas datos personales ni credenciales reales en ningún archivo del repositorio, incluidos pruebas, datos semilla, documentación y mensajes.
2. Usa datos inventados ("Jane Doe", "user@example.com", "fake-api-key-123").
3. Los secretos se leen de variables de entorno o de archivos ignorados por Git.
4. Si un archivo ya contiene datos reales o credenciales, no los copies: avisa.

## Forma de trabajo

- No uses subagentes salvo que el propietario lo pida.
- Una tarea por sesión (salvo que yo te pida otra cosa). Lee solo los archivos que la tarea necesita.

## Documentación

- Solo debes actualizar los archivos.md de la raíz cuando yo te lo pida