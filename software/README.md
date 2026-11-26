 # Especificación formal del proyecto
 Especificación formal y completa del producto. Es la única fuente de verdad para implementar: no quedan puntos «por definir».
 Esta carpeta no contiene código, el código va en la carpeta implementacion/

 ## Estructura de Archivos y Carpetas
 
 **basesDatos/**
 Esta carpeta especifica la base de datos del proyecto.

 **casosUso/**
 Contiene el catálogo de los casos de uso. Por cada caso de uso se muestra su nombre, los actores que participan en él y el objetivo del caso de uso

 Por otra parte contiene la carpeta especificacionesCU/
 Esta carpeta contiene un archivo.md por cada caso de uso del catálogo. 
    Se especifica precondiciones, disparador, flujo principal, flujos alternativos, casos de error, estados en caso de error y postcondiciones

**interfaz/**
Esta carpeta contiene imágenes que muestran cual es la interfaz deseada a implementar. 

**modulos/**
El proyecto debe tener una estructura modular bien planteada. Se especifica cada módulo a implementar en un archivo.md diferente dentro de la carpeta modulos/. El archivo modulos/README.md contiene la lista de módulos, las dependencias permitidas entre ellos, el orden de actualización y el catálogo de eventos con el que se comunican. Luego en la implementación se debe conseguir la mayor independencia posible de los módulos respecto al resto de módulos y código del proyecto

**Diseño técnico**
El archivo design.md especifica los lenguajes, herramientas, métodos y protocolos que se utilizan en la implementación para conseguir la mejor versión de lo especificado. No contiene código. Si contradice una regla, un requisito o una restricción, prevalece la especificación y design.md debe corregirse

**Contexto**
Contexto inicial del proyecto. En principio no es un archivo que se actualice. Es una idea base para empezar el proyecto. El proyecto final acabará teniendo muchos más conceptos que los especificados en el contexto. Es contexto sirve como punto de partida mínimo

**Reglas de Negocio**
Se especifican las reglas de negocio del proyecto. Al final del archivo, la sección «Parámetros iniciales» reúne todos los valores numéricos del juego (cantidades, tiempos, velocidades), que se ajustan durante las pruebas sin cambiar las reglas

**Requisitos**
Se especifican los requisitos del proyecto. Se diferencian los no funcionales y los funcionales

**Restricciones**
Se especifican las restricciones del proyecto 

**Matriz de Trazabilidad**
Contiene una matriz de trazabilidad para relacionar las restricciones, requisitos y reglas de negocio con cada caso de uso. Todo requisito, restricción y regla de negocio debe relacionarse con al menos un caso de uso, y puede relacionarse con más de un caso de uso. Un caso de uso debe relacionarse con un elemento mínimo, o restricción, o regla de negocio o requisito, y puede relacionarse con varios de estos. 