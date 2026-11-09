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
| Gower + K-Medoids (ajuste en muestra) | 3 | 0,112973 | 26,9 % | 42,8 % |
| One-Hot + K-Means | 4 | 0,113 | 9,1 % | 37,9 % |
| K-Prototypes | 3 | 0,109 | 20,6 % | 41,0 % |

La búsqueda PAM se reforzó con **20 inicios aleatorios**, evaluación de todos los posibles reemplazos en cada swap y hasta 50 iteraciones, deteniéndose antes si no hay mejora. Entre los inicios se conserva el de menor suma de distancias. Gower + K-Medoids obtuvo el mayor silhouette, pero la diferencia frente a One-Hot + K-Means es de solo **0,00035**; no demuestra una superioridad clara. Los silhouettes son bajos en general y sugieren separación limitada entre perfiles.

## Alcance y limitaciones

- La base contiene perfiles sintéticos y no representa estudiantes observados ni clientes reales.
- K-Medoids se ajustó sobre una muestra de 1.800 perfiles por el coste cuadrático de la matriz de distancias. Los demás perfiles se asignaron al medoide más cercano.
- Se excluyeron identificadores y variables redundantes o derivadas de otras entradas; el flujo disponible y el proxy de educación financiera se reservan para describir los grupos.
- Las etiquetas de cluster no expresan riesgo, solvencia ni aprobación. No se traducirán a rutas de crédito sin criterios adicionales, revisión humana y validación con datos apropiados.

## Validación de estabilidad y siguiente paso

Se midió la **estabilidad ante remuestreo** con el mismo conjunto de evaluación de 800 perfiles. Para cada ajuste se usaron muestras de 1.800 perfiles y la búsqueda PAM de 20 inicios. El análisis separa variación por muestra y por inicialización; compara las asignaciones mediante Adjusted Rand Index (ARI) y revisa silhouette y tamaños de cluster. El ARI mide consistencia entre particiones; no demuestra validez financiera ni capacidad de predecir resultados.

El análisis se ejecuta con:

```bash
uv run python scripts/analizar_estabilidad_cluster.py --seed 42 --repetitions 10 --pam-starts 20 --pam-max-iter 50
```

Los resultados por repetición se guardan en `data/processed/estabilidad_gower_kmedoids_k3.csv`. Tras revisar estabilidad, se describirán los clusters con sus variables financieras y sociodemográficas, sin convertir las etiquetas automáticamente en decisiones de crédito.

### Resultado de estabilidad con la búsqueda reforzada — 10 repeticiones

Con un conjunto de evaluación fijo de 800 perfiles y muestras de entrenamiento de 1.800, las asignaciones variaron bastante entre la referencia y las corridas:

| Variación evaluada | ARI promedio vs. referencia | Rango (sin referencia) |
|---|---:|---:|
| Cambiar la muestra de entrenamiento | 0,260 | 0,098–0,361 |
| Cambiar la inicialización de PAM, con la misma muestra | 1,000 | 1,000 |

La búsqueda reforzada eliminó la variación de inicialización en esta evaluación: los 20 inicios produjeron la misma partición para una muestra fija (ARI 1,000). Sin embargo, al cambiar la muestra, el ARI promedio sigue bajo, **0,260**. El silhouette Gower promedio fue **0,089** (rango **0,057–0,110**). Así que la búsqueda ya es consistente respecto a la inicialización, pero la pertenencia de las personas a cada cluster sigue siendo sensible a la muestra. Gower + K-Medoids, k=3 permanece como **candidato de exploración**, no elección final.

El siguiente paso será repetir con muestras de entrenamiento más grandes (por ejemplo, 3.000) y comprobar si la estabilidad mejora. Si persiste la variación, revisar las variables/datos sintéticos o reconsiderar la segmentación antes de asignar nombres a los grupos.

## Artefactos relacionados

- Comparación completa: [`notebooks/02_segmentacion_perfiles_sinteticos.ipynb`](../notebooks/02_segmentacion_perfiles_sinteticos.ipynb).
- Métricas comparativas: [`data/processed/comparacion_clusterizaciones.csv`](../data/processed/comparacion_clusterizaciones.csv).
- Implementación: [`src/models/segmentacion.py`](../src/models/segmentacion.py).
