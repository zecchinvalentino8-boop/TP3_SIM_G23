# TP3 Simulación - Parqueando (Montecarlo)
**Universidad Tecnológica Nacional - Facultad Regional Córdoba (UTN FRC)**<br>
**Carrera:** Ingeniería en Sistemas de Información<br>
**Materia:** Simulación (2026)<br>
**Grupo:** 23

## Integrantes del Grupo
* Aybar, Laura - Legajo: 92472
* Correa, M. Valentina - Legajo: 400655
* Giampieri, Lucia - Legajo: 96505
* Mendez Carranza, Pedro - Legajo: 94214
* Paez, Maria Candela - Legajo: 95256
* Tito Yelma, Luz Melanie - Legajo: 94465
* Zecchin, Valentino - Legajo: 94444

## Descripción del Proyecto
Este proyecto implementa la simulación de Montecarlo para analizar el flujo y la demora de vehículos en el sistema de estacionamiento de un aeropuerto ("Parqueando"). El sistema simula el trayecto desde el ingreso hasta los distintos sectores (Cercano, Intermedio y Alejado) considerando probabilidades de ruteo, detenciones para validación (Distribución Normal), demoras por tráfico/bloqueos, y tiempos de circulación (Distribución Uniforme).

## Características Técnicas y Restricciones
Para cumplir con los requerimientos de la cátedra, el simulador cuenta con las siguientes características:
* **Gestión de Memoria Optimizada:** Se utiliza un Vector de Estado de solo 2 filas en memoria para procesar los datos, permitiendo simular $N \ge 100.000$ iteraciones sin desbordamiento.
* **Interfaz Gráfica (Frontend):** Desarrollada con `Tkinter`. Permite la parametrización de todas las variables, probabilidades y distribuciones.
* **Visualización Selectiva:** Solo se renderiza en pantalla un rango específico de iteraciones (desde la fila $i$ hasta la $i+200$) y la fila final $N$, garantizando el rendimiento de la UI.

## Instalación y Ejecución
El proyecto está desarrollado enteramente en Python y utiliza librerías estándar, por lo que no requiere instalaciones complejas.

### Prerrequisitos
* Python 3.8 o superior.
* Librería `tkinter` (usualmente incluida por defecto en la instalación de Python).

### Pasos para ejecutar
1. Clonar el repositorio:
   ```bash
   git clone [https://github.com/tu-usuario/simulacion-tp3-parqueando.git](https://github.com/tu-usuario/simulacion-tp3-parqueando.git)