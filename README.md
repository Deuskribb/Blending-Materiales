
```markdown

## Tema 
- Mezcla de minerales (Blending)

## Estructura del Proyecto
El proyecto está organizado según las exigencias de la pauta:

```text
Trabajo_TIO/
│
├── README.md                   <-- Manual de instrucciones y documentación
│
├── data/
│   └── TIO_DataSet.csv         <-- Archivo con datos de minas, costos y leyes
│
├── fuente/
│   └── model.py               <-- Script principal con el modelo de optimización (PuLP)
│
└── resultados/                 <-- Archivos generados automáticamente
    ├── solucion_variables.csv  <-- Toneladas extraídas y costos reducidos
    ├── analisis_restricciones.csv <-- Precios sombra (duales) y holguras
    ├── rangos_validez.csv       <-- Evaluación de sensibilidad e impacto de norma Pb
    ├── analisis_parametrico.csv <-- Datos tabulados de variación del parámetro Pb
    └── analisis_parametrico_plomo.png <-- Gráfico de sensibilidad del plomo
```

## Dependencias (Requisitos)

Para ejecutar este proyecto necesitas Python 3.8+ e instalar las siguientes librerías:

```bash
pip install pulp pandas matplotlib 

```

## Instrucciones de Ejecución

Para correr el modelo, realizar la verificación de factibilidad y generar los resultados y gráficos, abre la terminal en la raíz de la carpeta (`Trabajo_TIO`) y ejecuta:

```bash
python fuente/modelo.py

```

*(En macOS o Linux utiliza `python3 fuente/modelo.py` si es necesario)*.

## Resultados Generados

Al ejecutar el código, se exportarán automáticamente los siguientes archivos en la carpeta `resultados/`:

* `solucion_variables.csv`: Plan de extracción óptimo y costos reducidos ($d_j$).
* `analisis_restricciones.csv`: Estado de cada restricción, holguras y precios sombra ($\pi_i$).
* `analisis_parametrico_plomo.png`: Gráficos con la evolución del costo y la extracción ante variaciones en la tolerancia de Plomo.

## Declaración sobre el uso de Asistentes de Inteligencia Artificial (IA)

En cumplimiento con los requerimientos éticos de la asignatura, se declara que se utilizó asistencia de Inteligencia Artificial (Gemini / ChatGPT) como herramienta de apoyo para:

* Estructuración de la sintaxis en la librería `PuLP`.
* Formateo de exportación de datos con `pandas` y generación de gráficos en `matplotlib`.
* Corrección y optimización del código.

La formulación matemática del problema, la validación de factibilidad y la interpretación económica de los resultados (precios sombra y costos reducidos) fueron desarrolladas de manera autónoma por el grupo.

```

```