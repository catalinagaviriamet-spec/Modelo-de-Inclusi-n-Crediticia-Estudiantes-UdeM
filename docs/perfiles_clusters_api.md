# Perfiles K-Prototypes y rutas de la API

## Estado

La API utiliza el artefacto `models/kprototypes_k3.joblib`, ajustado con la base final procesada de 30.000 perfiles. La ruta se asigna según el perfil mediano de cada grupo. Los IDs son etiquetas internas del ajuste y pueden cambiar si se reentrena; `GET /v1/modelo` devuelve el mapa almacenado junto con el artefacto.

## Perfiles del artefacto actual

| Cluster | Tamaño | Medianas y rasgos principales | Ruta académica |
|---:|---:|---|---|
| 0 | 12.000 (40,0%) | Ingreso $5,00 M; gastos esenciales $2,03 M; cuotas $262 mil; historial 180 meses; flujo +$2,66 M; proxy alto 100%. Predomina empleo formal y salario fijo. | **Viabilidad estudio formal de crédito** |
| 1 | 9.000 (30,0%) | Ingreso $1,03 M; gastos esenciales $791 mil; sin cuotas ni historial; flujo +$358 mil; proxy bajo 94,8%. Predomina estudio y apoyo familiar. | **Iniciemos con educación financiera** |
| 2 | 9.000 (30,0%) | Ingreso $1,48 M; gastos esenciales $1,23 M; cuotas $885 mil; historial 30 meses; flujo −$631 mil; proxy medio 89,3%. Predomina ingreso informal e independiente. | **Cuida tu historial crediticio** |

Las cifras describen el ajuste reproducido el 23 de noviembre de 2026; el mapa no debe suponerse permanente tras volver a entrenar.

## Recomendaciones de la demostración

| Ruta | Respuesta académica |
|---|---|
| Viabilidad estudio formal | Invita a completar información en una siguiente sesión. No implica aprobación del crédito. |
| Cuida tu historial crediticio | Muestra un cupo simulado de $300.000 si el flujo disponible es cero o negativo, y $500.000 si es positivo. Es un valor ficticio, no una oferta. |
| Educación financiera | Invita a completar un curso corto e interactivo. La falta de historial no demuestra falta de conocimientos financieros. |

La API recalcula las 10 variables derivadas desde los campos de entrada, luego estima el cluster mediante K-Prototypes. La distancia al prototipo es una medida interna del algoritmo, no una probabilidad ni una calificación crediticia.

Todos los perfiles son sintéticos. Los clusters no representan riesgo, solvencia ni probabilidad de aprobación y las recomendaciones son ilustrativas.
