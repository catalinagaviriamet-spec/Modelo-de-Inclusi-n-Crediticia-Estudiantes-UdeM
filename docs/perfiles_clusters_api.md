# Perfiles Gower de la base final y correspondencia de rutas

## Estado

La asignación corresponde al artefacto local `models/gower_kmedoids_k3.joblib`, reentrenado con la base final y las variables relativas. Los IDs se vinculan a rutas por el perfil mediano de cada grupo: menor historial para educación, mayor historial y flujo para viabilidad formal, y el grupo restante para cuidado del historial. Los IDs son propios de esta corrida y pueden cambiar al reentrenar.

## Perfiles de Gower + K-Medoids

| Cluster nuevo | Tamaño en 30.000 | Medianas principales | Arquetipo que recupera |
|---:|---:|---|---|
| 0 | 12.002 (40,0%) | Ingreso mensual $5,00 M; gastos esenciales $2,03 M; cuotas $262 mil; historial 180 meses; flujo +$2,66 M; proxy alto 100%. | Viabilidad estudio formal de crédito |
| 1 | 9.131 (30,4%) | Ingreso mensual $1,47 M; gastos esenciales $1,22 M; cuotas $874 mil; historial 30 meses; flujo −$628 mil; proxy medio 89%. | Cuida tu historial crediticio |
| 2 | 8.867 (29,6%) | Ingreso mensual $1,03 M; gastos esenciales $793 mil; sin cuotas ni historial; flujo +$358 mil; proxy bajo 95%. | Iniciemos con educación financiera |

Los IDs de cluster son etiquetas internas arbitrarias y pueden cambiar al reentrenar. La comparación controlada del estudio obtuvo ARI 0,972 para Gower + K-Medoids, pero el artefacto de API se ajusta en una muestra de 1.800 y produce esta asignación final. La base es sintética y fue construida para separar perfiles; no se interpreta como riesgo, solvencia ni probabilidad de aprobación.

## Rutas académicas propuestas

| Cluster de la base final | Ruta | Mensaje académico |
|---:|---|---|
| 0 | **Viabilidad estudio formal de crédito** | Invita a completar información en una siguiente sesión para revisar qué alternativa podría ajustarse a sus necesidades; no implica aprobación. |
| 1 | **Cuida tu historial crediticio** | Muestra el cupo didáctico de $300.000 si el flujo es cero o negativo y $500.000 si es positivo. No es oferta ni recomendación de endeudamiento. |
| 2 | **Iniciemos con educación financiera** | Invita a completar un curso corto antes de decidir sobre un primer crédito. La falta de historial no prueba falta de conocimientos financieros. |

En el artefacto regenerado, el mapa reportado por `GET /v1/modelo` es `0 → viabilidad_formal`, `1 → cuidar_historial`, `2 → educacion_financiera`. La API calcula los 10 campos derivados del pipeline y utiliza las seis variables categóricas y las diez numéricas descritas en la documentación de la base final. La API pública de Render requiere un despliegue posterior para recibir estos cambios.
