---
title: Inclusión Crediticia UdeM · API académica
emoji: 🧭
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
short_description: API didáctica para explorar tres clusters en perfiles sintéticos.
---

# Modelo de Inclusión Crediticia Estudiantes UdeM

API académica de **Gower + K-Medoids (k=3)**, ajustada sobre perfiles sintéticos. Permite consultar la documentación interactiva y enviar un perfil de ejemplo para observar las variables derivadas y el cluster asignado.

## Uso

- Documentación interactiva: `/docs`
- Estado del servicio: `/health`
- Descripción del modelo y perfiles: `/v1/modelo`
- Clasificar un perfil sintético: `POST /v1/clusterizar`

La respuesta es exploratoria. Los clusters no son puntajes, decisiones de crédito, recomendaciones de montos ni aprobaciones. Use únicamente datos sintéticos en esta demostración.

## Resumen interpretativo de los clusters

| Cluster | Proporción | Perfil descriptivo | Lectura académica |
|---|---:|---|---|
| 0 | 31,1 % | Historial extenso, crédito formal, flujo mensual mediano negativo. | Trayectoria crediticia estable con presión sobre el flujo disponible. |
| 1 | 27,4 % | Ingreso y flujo medianos mayores; también predomina el historial formal. | Perfil con más recursos disponibles; se solapa con el cluster 0 en experiencia. |
| 2 | 41,6 % | Sin historial crediticio en la mediana; mayor presencia de estudiantes. | Grupo descriptivo de poca experiencia observada; esto no demuestra baja capacidad ni conocimientos financieros. |

La separación y estabilidad de los grupos son limitadas (silhouette Gower ≈ 0,113; ARI de referencia ≈ 0,26). Los porcentajes de educación financiera son un proxy derivado del historial y no una medición independiente.
