# Modelo de Inclusión Crediticia Estudiantes UdeM

Proyecto de aprendizaje automático en la nube — Especialización en Ciencia de Datos e IA, Universidad de Medellín.

## Integrantes

- [Carolina Tirado Osorio](https://github.com/Caro-Tirado)
- [Yerlith Zabala](https://github.com/Yerlith)
- [Ana Catalina Gaviria](https://github.com/catalinagaviriamet-spec)

El proyecto explora cómo orientar a cada persona hacia educación financiera, un crédito pequeño con acompañamiento o un crédito de mayor monto según su perfil y capacidad de pago.

Como punto de partida se creó una base de 30.000 perfiles financieros sintéticos, con edades de 18 a 74 años y el campo `rango_edad`. No contiene información de personas reales ni representa una muestra de estudiantes UdeM. Esta versión incluye variables de perfil; las métricas y rutas de atención se definirán más adelante. Ver [la ficha de datos, sus límites y el diccionario de campos](docs/datos_sinteticos.md).

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

La API es una demostración sencilla para que el equipo y el profesor inspeccionen el modelo con perfiles sintéticos. No guarda las solicitudes ni devuelve recomendaciones, montos o aprobaciones de crédito.

```bash
uv run python scripts/entrenar_modelo_api.py
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Al iniciar, abre `http://127.0.0.1:8000/docs` para probar `POST /v1/clusterizar`. `GET /v1/modelo` muestra el método, sus parámetros y el resumen de los tres clusters. El esquema de entrada y la respuesta se describen en OpenAPI. La síntesis interpretativa está en [`docs/perfiles_clusters_api.md`](docs/perfiles_clusters_api.md). Ingresen únicamente datos sintéticos de prueba; la demo no está pensada para datos personales reales.

### Publicar en Render

La configuración `render.yaml` define un servicio web Docker gratuito que toma este repositorio como fuente y comprueba su estado en `/health`. Para desplegarlo, inicia sesión en Render, elige **New > Blueprint**, conecta este repositorio y confirma el servicio `modelo-inclusion-crediticia-api`. Una vez terminado el despliegue, abre `/docs` en la URL asignada por Render.

**API pública:** <https://modelo-inclusion-crediticia-api.onrender.com> · [Documentación interactiva](https://modelo-inclusion-crediticia-api.onrender.com/docs) · [Estado](https://modelo-inclusion-crediticia-api.onrender.com/health). En `/docs`, usa **POST /v1/clusterizar → Try it out → Execute**; la ficha sintética de ejemplo ya viene cargada.

El servicio gratuito se duerme tras 15 minutos sin tráfico y puede tardar alrededor de un minuto o más en responder al primer acceso. Es una opción para la demostración académica; no se ofrece como servicio de producción. El contenedor incluye la API, el código del modelo y su artefacto, no los CSV. Usa únicamente perfiles sintéticos.

Como el servicio se conectó mediante la URL pública del repositorio, después de subir cambios a GitHub hay que publicarlos desde Render con **Manual Deploy > Deploy latest commit**.
