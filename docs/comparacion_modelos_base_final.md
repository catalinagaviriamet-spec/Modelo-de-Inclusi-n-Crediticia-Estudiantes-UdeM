# Comparación de modelos sobre la base final

## Protocolo

Se compararon K-Prototypes, One-Hot + K-Means y Gower + K-Medoids (PAM), con `k=3`, sobre los mismos 800 perfiles de evaluación. Se emplearon las 10 variables numéricas relativas y seis categóricas documentadas en [`datos_sinteticos.md`](datos_sinteticos.md). Las razones sin definir para perfiles con ingreso cero se omiten por pares al calcular Gower. K-Prototypes y One-Hot + K-Means usan imputación mediana solo en sus matrices numéricas. En PAM se ajusta una muestra de 1.800 registros, con semilla 42, 20 inicios y máximo 50 iteraciones; las etiquetas se asignan al conjunto completo por medoide más cercano.

Silhouette Gower se calcula en la muestra común y permite contrastar separación geométrica en la distancia definida. ARI frente al arquetipo de referencia mide recuperación de las clases deliberadamente diseñadas; no es validación externa.

## Resultados

| Modelo | k | Silhouette Gower | Cluster menor en evaluación | Cluster mayor en evaluación | ARI vs. arquetipo diseñado |
|---|---:|---:|---:|---:|---:|
| K-Prototypes | 3 | **0,4165** | 25,8% | 38,3% | **1,0000** |
| One-Hot + K-Means | 3 | **0,4165** | 25,8% | 38,3% | **1,0000** |
| Gower + K-Medoids | 3 | 0,4131 | 26,3% | 38,3% | 0,9722 |

K-Prototypes y One-Hot + K-Means empatan al redondear a cuatro decimales; ambos recuperan exactamente la misma partición que los arquetipos de diseño (ARI=1; los números de cluster pueden permutarse). Gower + K-Medoids queda muy cerca, con ARI=0,972. Sus 30.000 asignaciones tienen tamaños 29,7%, 39,9% y 30,4%; los IDs son arbitrarios y la correspondencia con las narrativas está en `data/processed/distribucion_arquetipos_clusters.csv`.

## Interpretación académica

Las métricas son sustancialmente mayores que en la base exploratoria previa porque los campos financieros de esta base se generaron con diferencias más marcadas entre los tres arquetipos. Es una prueba controlada de que los algoritmos pueden recuperar esas estructuras. No demuestra que los perfiles existan con esa separación en personas reales ni que los grupos predigan capacidad de pago o resultados crediticios. Las proporciones 40/30/30 también son decisiones de diseño, no prevalencias estimadas.

La referencia `arquetipo_referencia` se conserva aparte para auditoría y nunca entra en la matriz de clustering. No confundirla con `segmento_generador`, que calcula el pipeline usando reglas distintas.

## Reproducción

El pipeline convierte los campos de entrada en la salida procesada:

```bash
uv run python scripts/ejecutar_pipeline_perfil.py
```

La comparación final se reproduce con:

```bash
uv run python scripts/entrenar_modelos_finales.py
```

Los resultados quedan en `data/processed/comparacion_clusterizaciones.csv` y las asignaciones del modelo con mayor Silhouette en `data/processed/perfiles_clusterizados.csv`.

## Punto pendiente para la API

La API y el artefacto `models/gower_kmedoids_k3.joblib` aún corresponden a una versión previa: usan un conjunto distinto de variables y asignan las rutas a IDs de cluster anteriores. Antes de desplegar esta base se debe volver a entrenar Gower con las variables finales, guardar y revisar el mapa entre clusters y recomendaciones, actualizar los ejemplos/documentación de la API y verificar sus respuestas. La comparación de tres modelos no sustituye ese paso.
