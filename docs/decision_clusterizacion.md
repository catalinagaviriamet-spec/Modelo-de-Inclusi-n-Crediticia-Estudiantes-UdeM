# Decisión de modelado: candidato de clusterización

**Fecha:** 8 de noviembre de 2026  
**Estado:** provisional; sujeto a validación de estabilidad e interpretación  
**Etapa:** exploración no supervisada

## Decisión

Se continuará la exploración con **Gower + K-Medoids, k=3** como candidato de referencia. Es una selección para investigar y mejorar; todavía no se puede considerar un modelo ganador estable, de producción ni una regla de otorgamiento de crédito.

## Evidencia de la comparación

Los tres métodos se evaluaron sobre los mismos 800 perfiles de evaluación, usando distancia Gower para calcular silhouette. Se probaron valores de k entre 3 y 6.

| Método | k con mayor silhouette | Silhouette Gower | Tamaño menor | Tamaño mayor |
|---|---:|---:|---:|---:|
| Gower + K-Medoids (ajuste en muestra) | 3 | 0,115 | 25,3 % | 42,6 % |
| One-Hot + K-Means | 4 | 0,113 | 9,1 % | 37,9 % |
| K-Prototypes | 3 | 0,109 | 20,6 % | 41,0 % |

Gower + K-Medoids obtuvo el mayor silhouette y produjo grupos de tamaños razonables. La diferencia frente a One-Hot + K-Means es pequeña (0,002); por tanto, la puntuación sola no demuestra una superioridad clara. Los silhouettes son bajos en general y sugieren separación limitada entre perfiles.

## Alcance y limitaciones

- La base contiene perfiles sintéticos y no representa estudiantes observados ni clientes reales.
- K-Medoids se ajustó sobre una muestra de 1.800 perfiles por el coste cuadrático de la matriz de distancias. Los demás perfiles se asignaron al medoide más cercano.
- Se excluyeron identificadores y variables redundantes o derivadas de otras entradas; el flujo disponible y el proxy de educación financiera se reservan para describir los grupos.
- Las etiquetas de cluster no expresan riesgo, solvencia ni aprobación. No se traducirán a rutas de crédito sin criterios adicionales, revisión humana y validación con datos apropiados.

## Siguiente paso

Medir la **estabilidad ante remuestreo**: fijar el mismo conjunto de evaluación y separar dos fuentes de variación. Primero, cambiar las muestras de entrenamiento conservando la inicialización de PAM; segundo, conservar la misma muestra y variar la inicialización de PAM. Comparar las asignaciones con Adjusted Rand Index (ARI) y revisar silhouette y tamaños de cluster. El ARI mide consistencia entre particiones; no demuestra validez financiera ni capacidad de predecir resultados.

El análisis se ejecuta con:

```bash
uv run python scripts/analizar_estabilidad_cluster.py --seed 42 --repetitions 10
```

Los resultados por repetición se guardan en `data/processed/estabilidad_gower_kmedoids_k3.csv`. Tras revisar estabilidad, se describirán los clusters con sus variables financieras y sociodemográficas, sin convertir las etiquetas automáticamente en decisiones de crédito.

### Resultado de estabilidad — 10 repeticiones

Con un conjunto de evaluación fijo de 800 perfiles y muestras de entrenamiento de 1.800, las asignaciones variaron bastante entre la referencia y las corridas:

| Variación evaluada | ARI promedio vs. referencia | Rango (sin referencia) |
|---|---:|---:|
| Cambiar la muestra de entrenamiento | 0,268 | 0,164–0,360 |
| Cambiar la inicialización de PAM, con la misma muestra | 0,287 | 0,160–0,548 |

El silhouette Gower promedio fue **0,088** (rango **0,058–0,106**). Los tamaños se mantuvieron razonablemente repartidos, pero los ARI muestran que cambia qué personas quedan juntas. Por esto Gower + K-Medoids, k=3 sigue como **candidato para depuración**, no como elección final. La siguiente tarea es revisar la sensibilidad del algoritmo de búsqueda PAM y probar si una inicialización/optimización más robusta mejora la consistencia antes de interpretar los grupos como segmentos.

## Artefactos relacionados

- Comparación completa: [`notebooks/02_segmentacion_perfiles_sinteticos.ipynb`](../notebooks/02_segmentacion_perfiles_sinteticos.ipynb).
- Métricas comparativas: [`data/processed/comparacion_clusterizaciones.csv`](../data/processed/comparacion_clusterizaciones.csv).
- Implementación: [`src/models/segmentacion.py`](../src/models/segmentacion.py).
