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

Plantilla de exportación de la API académica de **K-Prototypes (k=3)**, ganador de la comparación con Silhouette Gower 0,4165. El despliegue académico vigente se gestiona en Render; esta carpeta solo conserva una plantilla opcional para Spaces.

## Uso

- Documentación interactiva: `/docs`
- Estado del servicio: `/health`
- Descripción del modelo y perfiles: `/v1/modelo`
- Clasificar un perfil sintético: `POST /v1/clusterizar`

La respuesta es exploratoria. Los clusters no son puntajes, decisiones de crédito, recomendaciones de montos ni aprobaciones. Use únicamente datos sintéticos en esta demostración.

## Resumen interpretativo de los clusters

| Cluster | Proporción | Perfil descriptivo | Lectura académica |
|---|---:|---|---|
| 0 | 40,0 % | Historial mediano de 180 meses, ingreso formal, flujo mediano positivo. | Viabilidad estudio formal de crédito. |
| 1 | 30,0 % | Sin historial crediticio en la mediana; predomina estudio y apoyo familiar. | Iniciemos con educación financiera. |
| 2 | 30,0 % | Historial mediano de 30 meses, cuotas altas y flujo mediano negativo. | Cuida tu historial crediticio. |

El desempate entre K-Prototypes y One-Hot + K-Means se basa en el tratamiento directo de variables mixtas y en menor tiempo observado para K-Prototypes en una sola corrida. Consulta `GET /v1/modelo` para ver el mapa vigente, ya que los IDs pueden cambiar al reentrenar. Las clases y métricas provienen de datos sintéticos diseñados y no representan separación demostrada en personas reales.
