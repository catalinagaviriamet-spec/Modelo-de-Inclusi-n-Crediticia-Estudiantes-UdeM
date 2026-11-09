# Síntesis académica de los clusters

La API usa un ajuste final de **Gower + K-Medoids, k=3**, con 20 inicios PAM, una muestra de ajuste de 1.800 perfiles y semilla 42. Los porcentajes de esta tabla se calcularon al asignar los 30.000 perfiles sintéticos a los medoides guardados en `models/gower_kmedoids_k3.joblib`.

| Cluster | Tamaño | Perfil descriptivo (medianas) | Señales frecuentes | Comprensibilidad académica |
|---|---:|---|---|---|
| 0 | 9.321 (31,1 %) | 48 años; ingreso neto $2,34 M; gastos esenciales $1,82 M; deuda vigente $333 mil; flujo disponible **−$117 mil**; historial 96 meses. | Empleo formal, salario fijo y crédito formal son las categorías más frecuentes. El proxy derivado marca 61 % alto y 36 % medio. | **Media-alta:** se reconoce una trayectoria crediticia estable, pero el flujo mediano es deficitario. Conviene explicar esa combinación y evitar resumirla como “buen pagador”. |
| 1 | 8.211 (27,4 %) | 48 años; ingreso neto $3,67 M; gastos esenciales $1,97 M; deuda vigente $571 mil; flujo disponible $647 mil; historial 91 meses. | Estudia y trabaja, salario fijo y crédito formal son las categorías más frecuentes. El proxy marca 51 % alto y 48 % medio. | **Media:** se distingue por ingreso y flujo disponibles mayores, aunque comparte historial formal con el cluster 0. |
| 2 | 12.468 (41,6 %) | 43 años; ingreso neto $2,53 M; gastos esenciales $1,95 M; deuda vigente mediana $0; flujo disponible $448 mil; historial mediano 0 meses. | Estudia, salario fijo y sin experiencia crediticia son las categorías más frecuentes. El proxy marca 70 % bajo. | **Alta como descripción, limitada como conclusión:** la falta de historial separa el grupo, pero no demuestra falta de conocimientos financieros ni incapacidad de pago. |

Los montos se expresan en COP y se redondean para facilitar la lectura. Las categorías “más frecuentes” son modas del grupo, no describen a todas las personas del cluster.

## Lectura global

Los perfiles se pueden describir con señales reconocibles —historial y deuda, ingreso y flujo, experiencia crediticia—, pero **no quedan suficientemente separados ni estables para convertirlos en rutas de crédito**. En la comparación exploratoria, silhouette Gower fue aproximadamente 0,113; al variar la muestra, el ARI promedio frente a la referencia fue 0,26. La base es sintética y el nivel de educación financiera es un proxy derivado del historial, por lo que sus porcentajes son circulares y no una medición independiente.

La API devuelve `cluster_id` como etiqueta técnica y distancia al medoide. No transforma esas salidas en recomendación, aprobación, monto ni rechazo. Para inspeccionar el resumen programáticamente, consultar `GET /v1/modelo`.
