# Modelo de Inclusión Crediticia Estudiantes UdeM

Proyecto de aprendizaje automático en la nube — Especialización en Ciencia de Datos e IA, Universidad de Medellín.

## Integrantes

- [Carolina Tirado Osorio](https://github.com/Caro-Tirado)
- [Yerlith Zabala](https://github.com/Yerlith)
- [Ana Catalina Gaviria](https://github.com/catalinagaviriamet-spec)

El proyecto explora cómo orientar a cada persona hacia educación financiera, un crédito pequeño con acompañamiento o un crédito de mayor monto según su perfil y capacidad de pago.

Como punto de partida se creó una base de 30.000 perfiles financieros sintéticos, con edades de 18 a 74 años y el campo `rango_edad`. No contiene información de personas reales ni representa una muestra de estudiantes UdeM. El proyecto explora clusters y rutas académicas ilustrativas; sus métricas y limitaciones están documentadas y no se deben interpretar como decisiones de crédito reales. Ver [la ficha de datos, sus límites y el diccionario de campos](docs/datos_sinteticos.md).

Para regenerar el CSV con la semilla usada en la versión inicial:

```bash
python scripts/generar_perfiles_sinteticos.py --n 30000 --seed 20261108
python scripts/ejecutar_pipeline_perfil.py
```

El pipeline calcula el nivel de educación financiera proxy, suma los gastos esenciales y calcula el flujo mensual disponible a partir de los campos de entrada. La salida procesada queda en `data/processed/perfiles_crediticios_procesados.csv`.

## Estructura

- `configs/`: configuración del proyecto.
- `data/`: datos separados por etapa; no incluir datos sensibles o identificables.
- `docs/`: decisiones, documentación y acuerdos del equipo.
- `models/`: artefactos de modelos.
- `notebooks/`: exploración y experimentos.
- `output/`: resultados generados.
- `scripts/`: utilidades ejecutables.
- `src/`: código fuente organizado por componente.
- `tests/`: pruebas.

## Análisis exploratorio

El primer EDA está en [`notebooks/01_eda_perfiles_sinteticos.ipynb`](notebooks/01_eda_perfiles_sinteticos.ipynb). Presenta la estructura, los grupos de variables, distribuciones, relaciones descriptivas y controles de calidad de la base sintética.

La comparación exploratoria de segmentación no supervisada está en [`notebooks/02_segmentacion_perfiles_sinteticos.ipynb`](notebooks/02_segmentacion_perfiles_sinteticos.ipynb). Se puede repetir con `python scripts/entrenar_clusterizaciones.py`.

Para instalar las dependencias con Python 3.12 y ejecutar la comparación:

```bash
uv sync
uv run python scripts/entrenar_clusterizaciones.py --seed 42 --k-values 3,4,5,6 --gower-train-size 1800 --pam-starts 20 --pam-max-iter 50
```

El script compara K-Prototypes, One-Hot + K-Means y Gower + K-Medoids para varios valores de `k`, y guarda las métricas en `data/processed/comparacion_clusterizaciones.csv` y los perfiles etiquetados en `data/processed/perfiles_clusterizados.csv`. El mayor silhouette Gower observado es una referencia inicial, no una decisión automática de producto. K-Medoids se ajusta en una muestra de 1.800 de los 30.000 perfiles por el coste de las distancias por pares; usa 20 inicios, evalúa todos los swaps posibles y asigna después los demás perfiles al medoide más cercano.

La decisión provisional de continuar con **Gower + K-Medoids, k=3**, su evidencia y sus limitaciones se documentan en [`docs/decision_clusterizacion.md`](docs/decision_clusterizacion.md). La búsqueda PAM usa 20 inicios, evalúa todos los swaps posibles y termina si converge o al llegar a 50 iteraciones. El análisis revisa la estabilidad ante remuestreo:

```bash
uv run python scripts/analizar_estabilidad_cluster.py --seed 42 --repetitions 10 --gower-train-size 1800 --pam-starts 20 --pam-max-iter 50
```

Los resultados por repetición se guardan en `data/processed/estabilidad_gower_kmedoids_k3.csv`.

## API académica

La API es una demostración sencilla para que el equipo y el profesor inspeccionen el modelo con perfiles sintéticos. Además del cluster y las variables calculadas, devuelve una ruta académica ilustrativa. Los cupos que aparecen son ficticios y la salida no es una oferta, aprobación ni evaluación de una solicitud real. La API no guarda las solicitudes.

```bash
uv run python scripts/entrenar_modelo_api.py
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Al iniciar, abre `http://127.0.0.1:8000/docs` para probar `POST /v1/clusterizar`. `GET /v1/modelo` muestra el método, sus parámetros y el resumen de los tres clusters. El esquema de entrada y la respuesta se describen en OpenAPI. La síntesis interpretativa y las reglas didácticas de las rutas están en [`docs/perfiles_clusters_api.md`](docs/perfiles_clusters_api.md). Ingresen únicamente datos sintéticos de prueba; la demo no está pensada para datos personales reales.

### Publicar en Render

La configuración `render.yaml` define un servicio web Docker gratuito que toma este repositorio como fuente y comprueba su estado en `/health`. Para desplegarlo, inicia sesión en Render, elige **New > Blueprint**, conecta este repositorio y confirma el servicio `modelo-inclusion-crediticia-api`. Una vez terminado el despliegue, abre `/docs` en la URL asignada por Render.

**API pública:** <https://modelo-inclusion-crediticia-api.onrender.com> · [Documentación interactiva](https://modelo-inclusion-crediticia-api.onrender.com/docs) · [Estado](https://modelo-inclusion-crediticia-api.onrender.com/health). En `/docs`, usa **POST /v1/clusterizar → Try it out → Execute**; la ficha sintética de ejemplo ya viene cargada.

#### Perfiles de ejemplo para la demostración

En Swagger, abre **POST /v1/clusterizar**, pulsa **Try it out**, reemplaza el contenido del cuerpo por uno de estos perfiles y selecciona **Execute**. En la respuesta, revisa `cluster_id` y `recomendacion`.

**Grupo 0 — Viabilidad estudio formal de crédito**

```json
{
  "edad": 46,
  "tipo_hogar": "vive_con_familia",
  "personas_hogar": 3,
  "personas_a_cargo": 0,
  "nivel_estudio": "universitario_completo",
  "situacion_laboral": "empleo_formal",
  "tipo_ingreso": "salario_fijo",
  "ingreso_neto_mensual_cop": 1222411,
  "tiene_vivienda_propia": 1,
  "tiene_vehiculo": 0,
  "gasto_vivienda_mensual_cop": 246885,
  "gasto_alimentacion_mensual_cop": 499587,
  "gasto_transporte_mensual_cop": 366590,
  "gasto_salud_mensual_cop": 27346,
  "gasto_educacion_mensual_cop": 125197,
  "pago_servicios_publicos_cop": 532475,
  "otros_gastos_esenciales_mensuales_cop": 177036,
  "tipo_plan_celular": "pospago",
  "experiencia_crediticia": "credito_formal",
  "meses_historial_crediticio": 118,
  "cuotas_deudas_vigentes_cop": 550457,
  "ahorro_disponible_cop": 2456903,
  "moras_ultimos_12_meses": 0,
  "monto_solicitado_cop": 3209459
}
```

**Grupo 1 — Cuida tu historial crediticio** (flujo negativo; cupo simulado de $300.000 COP)

```json
{
  "edad": 45,
  "tipo_hogar": "otro",
  "personas_hogar": 2,
  "personas_a_cargo": 0,
  "nivel_estudio": "universitario_en_curso",
  "situacion_laboral": "estudia_y_trabaja",
  "tipo_ingreso": "salario_fijo",
  "ingreso_neto_mensual_cop": 967590,
  "tiene_vivienda_propia": 0,
  "tiene_vehiculo": 0,
  "gasto_vivienda_mensual_cop": 1276605,
  "gasto_alimentacion_mensual_cop": 520893,
  "gasto_transporte_mensual_cop": 444023,
  "gasto_salud_mensual_cop": 218938,
  "gasto_educacion_mensual_cop": 327684,
  "pago_servicios_publicos_cop": 151711,
  "otros_gastos_esenciales_mensuales_cop": 296791,
  "tipo_plan_celular": "prepago",
  "experiencia_crediticia": "tarjeta_credito",
  "meses_historial_crediticio": 121,
  "cuotas_deudas_vigentes_cop": 300326,
  "ahorro_disponible_cop": 3277018,
  "moras_ultimos_12_meses": 2,
  "monto_solicitado_cop": 1442447
}
```

**Grupo 2 — Iniciemos con educación financiera**

```json
{
  "edad": 34,
  "tipo_hogar": "vive_con_familia",
  "personas_hogar": 3,
  "personas_a_cargo": 1,
  "nivel_estudio": "universitario_en_curso",
  "situacion_laboral": "estudia_y_trabaja",
  "tipo_ingreso": "salario_fijo",
  "ingreso_neto_mensual_cop": 1800000,
  "tiene_vivienda_propia": 0,
  "tiene_vehiculo": 0,
  "gasto_vivienda_mensual_cop": 400000,
  "gasto_alimentacion_mensual_cop": 450000,
  "gasto_transporte_mensual_cop": 150000,
  "gasto_salud_mensual_cop": 50000,
  "gasto_educacion_mensual_cop": 200000,
  "pago_servicios_publicos_cop": 120000,
  "otros_gastos_esenciales_mensuales_cop": 100000,
  "tipo_plan_celular": "prepago",
  "experiencia_crediticia": "sin_experiencia",
  "meses_historial_crediticio": 0,
  "cuotas_deudas_vigentes_cop": 0,
  "ahorro_disponible_cop": 200000,
  "moras_ultimos_12_meses": 0,
  "monto_solicitado_cop": 500000
}
```

El servicio gratuito se duerme tras 15 minutos sin tráfico y puede tardar alrededor de un minuto o más en responder al primer acceso. Es una opción para la demostración académica; no se ofrece como servicio de producción. El contenedor incluye la API, el código del modelo y su artefacto, no los CSV. Usa únicamente perfiles sintéticos.

Como el servicio se conectó mediante la URL pública del repositorio, después de subir cambios a GitHub hay que publicarlos desde Render con **Manual Deploy > Deploy latest commit**.
