# Modelo de Inclusión Crediticia Estudiantes UdeM

Proyecto de aprendizaje automático en la nube — Especialización en Ciencia de Datos e IA, Universidad de Medellín.

## Integrantes

- [Carolina Tirado Osorio](https://github.com/Caro-Tirado)
- [Yerlith Zabala](https://github.com/Yerlith)
- [Ana Catalina Gaviria](https://github.com/catalinagaviriamet-spec)

El proyecto explora cómo orientar a cada persona hacia educación financiera, un crédito pequeño con acompañamiento o un crédito de mayor monto según su perfil y capacidad de pago.

Como punto de partida se creó una base de 30.000 perfiles financieros sintéticos, con edades de 18 a 74 años y el campo `rango_edad`. No contiene información de personas reales ni representa una muestra de estudiantes UdeM. El proyecto explora clusters y rutas académicas ilustrativas; sus métricas y limitaciones están documentadas y no se deben interpretar como decisiones de crédito reales. Ver [la ficha de datos, sus límites y el diccionario de campos](docs/datos_sinteticos.md).

La base final del proyecto es una copia sintética controlada de 30.000 perfiles, guardada en `data/raw/perfiles_crediticios_sinteticos.csv`. No representa clientes reales. Para recalcular todos sus campos derivados:

```bash
uv run python scripts/ejecutar_pipeline_perfil.py
```

El pipeline calcula los proxies crediticios, los gastos esenciales, el flujo disponible, ratios, ingreso per cápita, cobertura de ahorro, capacidad de cuota referencial y `segmento_generador`. La salida final queda en `data/processed/perfiles_crediticios_procesados.csv`. Las definiciones y límites están en [`docs/datos_sinteticos.md`](docs/datos_sinteticos.md).

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

El EDA de la base final está en [`notebooks/03_eda_base_final.ipynb`](notebooks/03_eda_base_final.ipynb). Revisa calidad, vuelve a calcular los derivados con el pipeline, presenta las distribuciones de la base sintética y compara los tres modelos en k=3.

Los tres modelos —K-Prototypes, One-Hot + K-Means y Gower + K-Medoids— se comparan en k=3 con `uv run python scripts/entrenar_modelos_finales.py`. Las métricas y las etiquetas del mejor resultado quedan en `data/processed/comparacion_clusterizaciones.csv` y `data/processed/perfiles_clusterizados.csv`. La interpretación y las limitaciones académicas están en [`docs/comparacion_modelos_base_final.md`](docs/comparacion_modelos_base_final.md).

El ganador final es **K-Prototypes**: empató por el mayor Silhouette Gower (0,4165) y se prefirió como desempate por su tratamiento directo de variables mixtas y menor tiempo observado en la corrida comparativa. La justificación lista para llevar a la presentación está en [`docs/decision_modelo_ganador.md`](docs/decision_modelo_ganador.md).

Para instalar las dependencias con Python 3.12 y ejecutar la comparación de la base final:

```bash
uv sync
uv run python scripts/entrenar_modelos_finales.py
```

El protocolo, la comparación de modelos y sus limitaciones están en [`docs/comparacion_modelos_base_final.md`](docs/comparacion_modelos_base_final.md); el desempate y las razones para la presentación, en [`docs/decision_modelo_ganador.md`](docs/decision_modelo_ganador.md).

## Validación de comportamientos clave

Las pruebas unitarias comprueban el proxy de educación financiera, el flujo mensual disponible (incluidos déficits) y las tres rutas académicas que devuelve la API. También se ejecutan automáticamente en GitHub Actions al subir cambios a `main` o abrir un pull request dirigido a esa rama. Para correrlas localmente desde la raíz del repositorio:

```bash
uv run python -m unittest discover -s tests/unit -v
```

El alcance y las reglas que se validan están documentados en [`docs/validacion_comportamientos_clave.md`](docs/validacion_comportamientos_clave.md).

## API académica

La API local usa el modelo ganador K-Prototypes, vuelve a calcular los 10 campos derivados del pipeline y devuelve una ruta académica. En el artefacto actual, el mapa es cluster 0 → viabilidad formal, cluster 1 → educación financiera y cluster 2 → cuidar historial. Los IDs pueden cambiar al volver a entrenar; consulta `GET /v1/modelo` para ver el mapa guardado en el artefacto.

Para entrenar el artefacto y ejecutar la API local:

```bash
uv run python scripts/entrenar_modelo_api.py
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Abre `http://127.0.0.1:8000/docs`, usa **POST /v1/clusterizar → Try it out** y selecciona uno de los tres ejemplos sintéticos que Swagger ofrece: un perfil representativo de cada ruta. `GET /v1/modelo` muestra las variables de entrada, los clusters, el mapa de rutas y el criterio usado para elegir K-Prototypes. La API genera los mismos cálculos del pipeline antes de clusterizar.

**Render:** el código actualizado está en `main`, pero la última consulta al servicio público todavía devolvió Gower + K-Medoids 0.1.0. En el panel de Render del servicio `modelo-inclusion-crediticia-api`, ejecuta **Manual Deploy → Deploy latest commit**. Confirma el cambio cuando `GET /v1/modelo` responda **K-Prototypes 0.3.0**; luego valida `/health` y los tres ejemplos de `/docs` antes de usar la URL pública en la sustentación. Los grupos y cupos son simulaciones didácticas y no representan evaluaciones ni ofertas de crédito reales.

La composición y lectura de los clusters está en [`docs/perfiles_clusters_api.md`](docs/perfiles_clusters_api.md); la comparación completa de modelos está en [`docs/comparacion_modelos_base_final.md`](docs/comparacion_modelos_base_final.md).
