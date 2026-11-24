# Decisión del modelo ganador: K-Prototypes

## Decisión

El modelo ganador para el ejercicio académico es **K-Prototypes, k=3**.

## Evidencia

| Criterio | K-Prototypes | One-Hot + K-Means | Lectura |
|---|---:|---:|---|
| Silhouette Gower | **0,4165418** | **0,4165418** | Empate en el criterio principal |
| Cluster menor–mayor | 25,75%–38,25% | 25,75%–38,25% | Mismo balance |
| ARI vs. arquetipos sintéticos | 1,0000 | 1,0000 | Ambos recuperan el diseño sintético |
| Tiempo de ajuste en la corrida guardada | **0,88 s** | 1,22 s | Menor tiempo observado para K-Prototypes |

## Razones del desempate

1. Los dos candidatos con mayor Silhouette Gower empataron; ninguno supera al otro en la métrica principal.
2. K-Prototypes combina las variables numéricas y categóricas directamente. One-Hot + K-Means necesita transformar las categorías en columnas indicadoras.
3. En la corrida comparativa guardada, K-Prototypes ajustó más rápido. El tiempo proviene de una sola ejecución y se considera un apoyo operativo, no una ventaja universal demostrada.
4. Como ambos recuperaron exactamente los arquetipos sintéticos diseñados (ARI 1,0000), elegir K-Prototypes mantiene la mejor separación observada y simplifica el tratamiento de datos mixtos.

## Texto breve para una diapositiva

> **Elegimos K-Prototypes:** obtuvo el máximo Silhouette Gower (0,4165), empatado con One-Hot + K-Means. El desempate favorece a K-Prototypes porque integra datos numéricos y categóricos de forma directa y tuvo menor tiempo de ajuste en la comparación. Ambos recuperaron los arquetipos sintéticos; esto no valida el resultado en clientes reales.

## Alcance

La decisión describe el mejor candidato dentro de esta comparación académica sobre una base sintética diseñada con tres arquetipos. No demuestra que las mismas separaciones existan en datos reales, ni convierte los clusters en puntajes de riesgo o decisiones de crédito.
