# TP3 Simulacion - Parqueando (Montecarlo)

**Universidad Tecnologica Nacional - Facultad Regional Cordoba (UTN FRC)**  
**Carrera:** Ingenieria en Sistemas de Informacion  
**Materia:** Simulacion (2026)  
**Grupo:** 23

## Integrantes del grupo

* Aybar, Laura - Legajo: 92472
* Correa, M. Valentina - Legajo: 400655
* Giampieri, Lucia - Legajo: 96505
* Mendez Carranza, Pedro - Legajo: 94214
* Paez, Maria Candela - Legajo: 95256
* Tito Yelma, Luz Melanie - Legajo: 94465
* Zecchin, Valentino - Legajo: 94444

## Objetivo del proyecto

El programa implementa una simulacion de Montecarlo para estimar el tiempo que tarda un vehiculo en completar el proceso de estacionamiento en el sistema "Parqueando".

Cada iteracion representa una jornada o caso simulado. En cada jornada se generan numeros aleatorios para decidir:

* a que sector se dirige el vehiculo;
* cuanto tarda en recorrer la cuadra base;
* si se detiene en un panel o cartel informativo;
* si hay bloqueo de cuadra;
* si ocurre una parada extra de pago o validacion;
* cual es el tiempo total final de estacionamiento.

Luego, con los resultados de todas las jornadas, el sistema calcula indicadores estadisticos y muestra una tabla de simulacion junto con graficos.

## Archivos principales

### `main.py`

Contiene toda la logica del proyecto:

* definicion de parametros por defecto;
* funciones de simulacion;
* calculo de indicadores;
* interfaz grafica en Tkinter;
* tabla de resultados;
* graficos con Matplotlib.

### `README.md`

Documento explicativo del funcionamiento del codigo y de la forma de ejecucion.

## Librerias utilizadas

El programa usa las siguientes librerias:

* `tkinter`: construye la interfaz grafica.
* `ttk` y `messagebox`: agregan componentes visuales y mensajes de alerta.
* `numpy`: genera numeros aleatorios y aplica formulas matematicas.
* `pandas`: arma un `DataFrame` con los resultados visibles para facilitar los graficos.
* `matplotlib`: genera los graficos estadisticos.
* `FigureCanvasTkAgg`: permite incrustar graficos de Matplotlib dentro de Tkinter.

## Parametros por defecto

El archivo comienza definiendo constantes que representan el escenario base de la simulacion.

### Sector de estacionamiento

Se usa una distribucion discreta empirica:

| Sector | Probabilidad | Distancia aproximada |
| --- | ---: | --- |
| Cercano | 0.35 | 1 a 2 cuadras |
| Intermedio | 0.40 | 2 a 3 cuadras |
| Lejano | 0.25 | 3 a 5 cuadras |

Las probabilidades deben sumar 1.

### Detencion en panel/cartel

La detencion en panel o cartel informativo se modela como una distribucion Bernoulli:

* probabilidad de detenerse: `0.45`;
* si ocurre la detencion, la demora se genera con una distribucion Normal;
* media de la demora: `60` segundos;
* desvio estandar: `20` segundos.

Para generar la Normal se usa el metodo de Box-Muller.

### Bloqueo de cuadra

El bloqueo solo puede ocurrir en los sectores `Cercano` y `Lejano`.

* probabilidad de bloqueo: `0.40`;
* factor de incremento: `1.80`;
* si hay bloqueo, el tiempo de circulacion se multiplica por `1.80`.

### Tiempo de recorrido base

El tiempo base de circulacion se genera con una distribucion Uniforme:

```text
Uniforme(30, 45)
```

Es decir, cada jornada toma un valor entre 30 y 45 segundos.

### Parada extra

La parada extra representa una demora adicional, por ejemplo en pago o validacion.

* probabilidad: `60 / 250 = 0.24`;
* si ocurre, la demora se genera con una distribucion Exponencial;
* media de la demora: `80` segundos.

La formula usada es:

```text
t_extra = -media_extra * ln(1 - rnd)
```

## Funcion `sector_cuadras_local`

Esta funcion recibe un numero aleatorio `rnd` entre 0 y 1 y lo transforma en un sector.

Funcionamiento:

1. Si `rnd < p_cercano`, devuelve `Cercano`.
2. Si `rnd` esta entre `p_cercano` y `p_cercano + p_intermedio`, devuelve `Intermedio`.
3. En cualquier otro caso, devuelve `Lejano`.

Ejemplo con los parametros por defecto:

| Rango del RND | Sector asignado |
| --- | --- |
| `0.00 <= rnd < 0.35` | Cercano |
| `0.35 <= rnd < 0.75` | Intermedio |
| `0.75 <= rnd <= 1.00` | Lejano |

## Funcion `simular`

Es la funcion principal del modelo de Montecarlo. Recibe la cantidad de jornadas a simular y todos los parametros configurables desde la interfaz.

Devuelve tres elementos:

* `filas_rango`: filas visibles desde la jornada indicada hasta 200 jornadas posteriores;
* `ultima_fila`: ultima jornada simulada;
* `estadisticas`: diccionario con los KPIs calculados.

### Flujo de una jornada simulada

En cada iteracion del ciclo `for`, el programa realiza los siguientes pasos:

1. **Genera el sector**
   * Se obtiene `RND_Sector`.
   * Se llama a `sector_cuadras_local`.
   * Se decide si el vehiculo va al sector `Cercano`, `Intermedio` o `Lejano`.

2. **Calcula el tiempo base de recorrido**
   * Se obtiene `RND_T_Cuadra`.
   * Se transforma el numero aleatorio usando una distribucion Uniforme entre 30 y 45 segundos.

3. **Evalua la detencion en panel/cartel**
   * Se obtiene `RND_Detencion`.
   * Si el valor es menor a la probabilidad de detencion, ocurre la parada.
   * Cuando ocurre, se generan `RND1_Normal` y `RND2_Normal`.
   * Con Box-Muller se calcula una demora Normal.
   * Si la Normal da un valor negativo, se reemplaza por `0`.

4. **Calcula el tiempo de circulacion**
   * Se suma el tiempo base mas la demora del panel/cartel.

5. **Evalua bloqueo de cuadra**
   * Solo aplica si el sector es `Cercano` o `Lejano`.
   * Si ocurre bloqueo, el tiempo de circulacion se multiplica por el factor configurado.
   * Si no ocurre bloqueo, el tiempo queda igual.

6. **Evalua parada extra**
   * Se obtiene `RND_Parada_Extra`.
   * Si el valor es menor a la probabilidad configurada, ocurre la parada extra.
   * En ese caso se genera `RND_Exp` y se calcula la demora exponencial.

7. **Calcula el tiempo total**
   * El tiempo total de la jornada es:

```text
T_Total = tiempo_circulacion_con_o_sin_bloqueo + tiempo_extra
```

8. **Actualiza acumuladores**
   * Suma el tiempo total acumulado.
   * Actualiza maximo y minimo.
   * Cuenta eventos de interes.
   * Cuenta cuantas jornadas caen en cada sector.
   * Acumula tiempos por sector.

9. **Guarda filas para mostrar**
   * No se guardan todas las jornadas en la tabla.
   * Se guarda el rango solicitado por el usuario, desde `fila_inicio` hasta `fila_inicio + 200`.
   * Tambien se guarda la ultima jornada `N`.

## KPIs calculados

La simulacion calcula los siguientes indicadores:

| KPI | Descripcion |
| --- | --- |
| `t_promedio` | Tiempo promedio de estacionamiento. |
| `pct_cartel_y_extra` | Porcentaje de jornadas con detencion en panel y parada extra. |
| `cnt_sin_cartel_sin_extra` | Cantidad de jornadas sin detencion en panel, sin bloqueo y sin parada extra. |
| `tiempo_max` | Mayor tiempo total registrado. |
| `tiempo_min` | Menor tiempo total registrado. |
| `pct_bloqueo` | Porcentaje de jornadas con bloqueo. |
| `t_prom_cercano` | Tiempo promedio en sector Cercano. |
| `t_prom_lejano` | Tiempo promedio en sector Lejano. |
| `pct_sector_cercano` | Porcentaje de jornadas asignadas al sector Cercano. |
| `pct_sector_intermedio` | Porcentaje de jornadas asignadas al sector Intermedio. |
| `pct_sector_lejano` | Porcentaje de jornadas asignadas al sector Lejano. |

## Clase `App`

La clase `App` construye y controla la interfaz grafica.

Al iniciar, crea una ventana de Tkinter con cuatro pestañas:

1. **Configuracion**
   * Permite cargar cantidad de jornadas, semilla, fila inicial y parametros de probabilidad.
   * Tiene botones para ejecutar la simulacion y restablecer valores por defecto.

2. **Tabla de Simulacion**
   * Muestra el vector de estado visible.
   * Incluye las jornadas desde la fila inicial hasta 200 filas posteriores.
   * Tambien muestra la ultima jornada simulada.

3. **Resultados / KPIs**
   * Presenta los indicadores requeridos por la consigna.
   * Tambien muestra indicadores adicionales propuestos por el grupo.
   * Incluye una leyenda con el significado de las columnas principales.

4. **Graficos**
   * Muestra tres graficos:
     * distribucion porcentual de sectores;
     * composicion promedio del tiempo total;
     * porcentaje de ocurrencia de eventos clave.

## Metodos principales de la interfaz

### `_build_config_tab`

Construye la pestaña de configuracion. Crea campos de entrada para:

* cantidad de jornadas;
* semilla aleatoria;
* fila inicial a visualizar;
* probabilidades de sector;
* parametros de la detencion en cartel;
* parametros de bloqueo;
* tiempos minimo y maximo por cuadra;
* parametros de parada extra.

### `_build_tabla_tab`

Crea la tabla de resultados usando `ttk.Treeview` y agrega barras de desplazamiento vertical y horizontal.

### `_cargar_tabla`

Limpia la tabla y carga las filas generadas por la simulacion.

Si la ultima jornada no esta dentro del rango visible, agrega una fila separadora con `...` y despues muestra la jornada final.

### `_build_kpi_tab`

Construye la pestaña de KPIs. Define etiquetas que luego se actualizan al ejecutar la simulacion.

### `_build_graficos_tab`

Crea la figura de Matplotlib y la incrusta dentro de Tkinter.

### `_actualizar_graficos`

Actualiza los tres graficos despues de cada simulacion:

* grafico de barras para sectores;
* grafico de torta para composicion del tiempo;
* grafico de barras para eventos principales.

### `ejecutar`

Es el metodo que se dispara al presionar el boton **Ejecutar Simulacion**.

Realiza estas tareas:

1. Lee los valores ingresados por el usuario.
2. Valida que las probabilidades de sector sumen 1.
3. Valida que la fila inicial este dentro del rango permitido.
4. Valida que `N` sea mayor o igual a 1.
5. Fija la semilla aleatoria con `np.random.seed`.
6. Llama a la funcion `simular`.
7. Carga la tabla de resultados.
8. Actualiza los KPIs.
9. Actualiza los graficos.
10. Cambia automaticamente a la pestaña de tabla.
11. Muestra un mensaje indicando que la simulacion finalizo.

### `restablecer`

Vuelve a cargar todos los parametros por defecto definidos al inicio del archivo.

## Columnas de la tabla

| Columna | Significado |
| --- | --- |
| `Jornada` | Numero de iteracion simulada. |
| `RND_Sector` | Numero aleatorio usado para asignar sector. |
| `Sector` | Sector asignado. |
| `RND_T_Cuadra` | Numero aleatorio usado para el tiempo base. |
| `T_Base_Cuadras(s)` | Tiempo base calculado con Uniforme(30,45). |
| `RND_Detencion` | Numero aleatorio usado para decidir detencion en panel. |
| `Detencion` | Indica si hubo detencion en panel/cartel. |
| `RND1_Normal` | Primer numero aleatorio usado por Box-Muller. |
| `RND2_Normal` | Segundo numero aleatorio usado por Box-Muller. |
| `T_Detencion(s)` | Tiempo generado para la detencion. |
| `T_Circulacion(s)` | Tiempo base mas detencion. |
| `RND_Bloqueo` | Numero aleatorio usado para decidir bloqueo. |
| `Hay_Bloqueo` | Indica si hubo bloqueo o si no aplicaba. |
| `T_Bloqueo_Extra(s)` | Tiempo de circulacion luego de aplicar el factor de bloqueo. |
| `RND_Parada_Extra` | Numero aleatorio usado para decidir parada extra. |
| `Parada_Extra` | Indica si hubo parada extra. |
| `RND_Exp` | Numero aleatorio usado para la distribucion Exponencial. |
| `T_Extra(s)` | Tiempo adicional por parada extra. |
| `T_Total(s)` | Tiempo total de la jornada. |
| `T_Acum(s)` | Tiempo acumulado hasta la jornada actual. |
| `T_Prom_Acum(s)` | Promedio acumulado hasta la jornada actual. |

## Ejecucion

Desde la carpeta del proyecto:

```bash
python main.py
```

O desde la carpeta padre:

```bash
python .\TP3_SIM_G23\main.py
```

Si faltan dependencias, instalarlas con:

```bash
pip install numpy pandas matplotlib
```

## Observaciones sobre el codigo

* La semilla permite repetir resultados si se usan los mismos parametros.
* La tabla no muestra necesariamente todas las jornadas simuladas, sino un rango elegido y la ultima fila.
* Los KPIs se calculan con todas las jornadas, no solo con las visibles.
* Los graficos usan el `DataFrame` armado con las filas visibles, por lo que la composicion promedio graficada puede representar el rango mostrado y no necesariamente todo `N`.
* La Normal se trunca en cero para evitar tiempos negativos.
* El bloqueo se aplica solo a `Cercano` y `Lejano`, tal como indica la logica del codigo.

