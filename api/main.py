"""API académica para explorar el cluster Gower + K-Medoids."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import Body, FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.models.segmentacion import GowerKMedoidsPredictor
from src.pipeline.perfil_financiero import calcular_variables_derivadas


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "models/gower_kmedoids_k3.joblib"
EJEMPLO_PERFIL_SINTETICO = {
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
    "monto_solicitado_cop": 500000,
}


class PerfilEntrada(BaseModel):
    """Datos mínimos de una ficha para la demostración académica."""

    model_config = ConfigDict(extra="forbid")

    edad: int = Field(ge=18, le=74, description="Edad entre 18 y 74 años.")
    tipo_hogar: Literal[
        "vive_solo", "comparte_vivienda", "vive_con_familia", "vive_con_pareja", "otro"
    ]
    personas_hogar: int = Field(ge=1, le=7)
    personas_a_cargo: int = Field(ge=0, le=5)
    nivel_estudio: Literal[
        "secundaria", "tecnico_tecnologico", "universitario_en_curso",
        "universitario_completo", "posgrado",
    ]
    situacion_laboral: Literal[
        "estudia", "empleo_formal", "empleo_informal", "independiente",
        "desempleado", "estudia_y_trabaja",
    ]
    tipo_ingreso: Literal[
        "sin_ingresos", "salario_fijo", "ingreso_variable", "informal", "apoyo_familiar"
    ]
    ingreso_neto_mensual_cop: int = Field(ge=0, le=100_000_000)
    tiene_vivienda_propia: Literal[0, 1]
    tiene_vehiculo: Literal[0, 1]
    gasto_vivienda_mensual_cop: int = Field(ge=0, le=100_000_000)
    gasto_alimentacion_mensual_cop: int = Field(ge=0, le=100_000_000)
    gasto_transporte_mensual_cop: int = Field(ge=0, le=100_000_000)
    gasto_salud_mensual_cop: int = Field(ge=0, le=100_000_000)
    gasto_educacion_mensual_cop: int = Field(ge=0, le=100_000_000)
    pago_servicios_publicos_cop: int = Field(ge=0, le=100_000_000)
    otros_gastos_esenciales_mensuales_cop: int = Field(ge=0, le=100_000_000)
    tipo_plan_celular: Literal["sin_linea", "prepago", "pospago"]
    experiencia_crediticia: Literal[
        "sin_experiencia", "credito_formal", "credito_informal",
        "tarjeta_credito", "microcredito",
    ]
    meses_historial_crediticio: int = Field(ge=0, le=600)
    cuotas_deudas_vigentes_cop: int = Field(ge=0, le=100_000_000)
    ahorro_disponible_cop: int = Field(ge=0, le=100_000_000)
    moras_ultimos_12_meses: int = Field(ge=0, le=12)
    monto_solicitado_cop: int = Field(ge=0, le=100_000_000)

    @model_validator(mode="after")
    def validar_coherencia_basica(self):
        if self.personas_a_cargo >= self.personas_hogar:
            raise ValueError("Personas a cargo debe ser menor que el tamaño del hogar.")
        if self.tipo_ingreso == "sin_ingresos" and self.ingreso_neto_mensual_cop != 0:
            raise ValueError("Con tipo_ingreso='sin_ingresos', el ingreso neto debe ser cero.")
        if self.tipo_ingreso != "sin_ingresos" and self.ingreso_neto_mensual_cop == 0:
            raise ValueError("Indica 'sin_ingresos' si el ingreso neto es cero.")
        return self


class VariablesDerivadas(BaseModel):
    nivel_educacion_financiera: str
    gastos_esenciales_mensuales_cop: int
    flujo_mensual_disponible_cop: int


class RecomendacionAcademica(BaseModel):
    nombre_grupo: str
    tipo: Literal["revision_formal", "cupo_simulado", "educacion_financiera"]
    mensaje: str
    cupo_simulado_cop: int | None = None
    fundamento: str
    aclaracion: str


class ResultadoCluster(BaseModel):
    cluster_id: int
    distancia_gower_al_medoid: float
    variables_derivadas: VariablesDerivadas
    recomendacion: RecomendacionAcademica
    nota: str


def construir_recomendacion(cluster_id: int, flujo_disponible: int) -> RecomendacionAcademica:
    """Construye una ruta demostrativa; no representa una decisión crediticia real."""
    if cluster_id == 0:
        fundamento = (
            "El perfil quedó en el grupo exploratorio asociado a experiencia crediticia. "
            "El flujo disponible es positivo." if flujo_disponible > 0 else
            "El perfil quedó en el grupo exploratorio asociado a experiencia crediticia. "
            "El flujo disponible no es positivo y debe revisarse antes de evaluar cualquier monto."
        )
        return RecomendacionAcademica(
            nombre_grupo="Viabilidad estudio formal de crédito",
            tipo="revision_formal",
            mensaje=(
                "Dirígete a la siguiente sesión y completa la información para revisar "
                "el crédito que más se acomode a tus necesidades."
            ),
            fundamento=fundamento,
            aclaracion=(
                "Esta ruta solo indica continuar una evaluación académica. No significa "
                "que el crédito sea viable, esté preaprobado o vaya a ser otorgado."
            ),
        )
    if cluster_id == 1:
        cupo = 500_000 if flujo_disponible > 0 else 300_000
        cupo_formateado = f"{cupo:,}".replace(",", ".")
        if flujo_disponible > 0:
            fundamento = "En este ejercicio, el flujo mensual disponible calculado es positivo."
        else:
            fundamento = (
                "En este ejercicio, el flujo mensual disponible calculado es cero o negativo; "
                "por eso se muestra el cupo simulado menor."
            )
        return RecomendacionAcademica(
            nombre_grupo="Cuida tu historial crediticio",
            tipo="cupo_simulado",
            mensaje=(
                f"Para esta simulación académica se muestra un cupo de ${cupo_formateado} COP. "
                "Continúa cuidando tu historial y revisa tu presupuesto."
            ),
            cupo_simulado_cop=cupo,
            fundamento=fundamento,
            aclaracion=(
                "El cupo es un valor ficticio definido para el ejercicio, no una oferta ni "
                "una recomendación de endeudamiento. Si el flujo es cero o negativo, revisa "
                "ingresos, gastos y deudas antes de considerar una obligación real."
            ),
        )
    return RecomendacionAcademica(
        nombre_grupo="Iniciemos con educación financiera",
        tipo="educacion_financiera",
        mensaje=(
            "Continúa a la siguiente sesión, donde encontrarás un curso corto e interactivo "
            "de educación financiera que te preparará para tomar buenas decisiones con tu primer crédito."
        ),
        fundamento=(
            "Este grupo exploratorio reúne principalmente perfiles sin experiencia crediticia "
            "reportada en la ficha sintética."
        ),
        aclaracion=(
            "La falta de historial no demuestra falta de conocimientos financieros. "
            "El nivel de educación financiera del proyecto es un proxy derivado del historial."
        ),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not ARTIFACT.exists():
        raise RuntimeError(
            "Falta el modelo académico. Ejecuta primero: "
            "uv run python scripts/entrenar_modelo_api.py"
        )
    app.state.modelo = joblib.load(ARTIFACT)
    yield


app = FastAPI(
    title="API académica de inclusión crediticia",
    description=(
        "Demostración con perfiles sintéticos. Calcula variables financieras "
        "derivadas, asigna un cluster exploratorio y presenta una ruta académica simulada. "
        "No evalúa solicitudes reales ni aprueba créditos."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/", tags=["Información"])
def inicio():
    return {
        "mensaje": "API académica de clusterización de perfiles sintéticos",
        "documentacion": "/docs",
        "estado": "/health",
    }


@app.get("/health", tags=["Información"])
def health(request: Request):
    return {"estado": "disponible", "modelo_cargado": hasattr(request.app.state, "modelo")}


@app.get("/v1/modelo", tags=["Información"])
def informacion_modelo(request: Request):
    modelo: GowerKMedoidsPredictor = request.app.state.modelo
    return {
        "nombre": "Gower + K-Medoids",
        "version": "0.1.0-academica",
        "k": modelo.k,
        "tamano_muestra_ajuste": modelo.train_sample_size,
        "inicios_pam": modelo.n_starts,
        "max_iteraciones_pam": modelo.max_iter,
        "semilla": modelo.seed,
        "perfiles_en_base_sintetica": modelo.dataset_size,
        "clusters": modelo.cluster_profiles,
        "evidencia_seleccion": {
            "silhouette_gower_candidato_1800": 0.112973,
            "alternativa_muy_cercana": "One-Hot + K-Means (k=4): 0.112625",
            "ari_promedio_referencial_10_corridas": 0.260,
            "nota": "Métricas de evaluación comparativa; no son probabilidades ni garantías del perfil consultado.",
        },
        "limitacion": (
            "Las etiquetas describen grupos exploratorios de una base sintética; "
            "las rutas mostradas por la API son reglas académicas ilustrativas, no "
            "puntajes de riesgo, ofertas ni decisiones de crédito."
        ),
    }


@app.post("/v1/clusterizar", response_model=ResultadoCluster, tags=["Clusterización"])
def clusterizar(
    request: Request,
    perfil: PerfilEntrada = Body(
        openapi_examples={
            "perfil_sintetico": {
                "summary": "Perfil sintético de ejemplo",
                "description": "Ejemplo válido para probar la documentación interactiva.",
                "value": EJEMPLO_PERFIL_SINTETICO,
            }
        }
    ),
):
    datos = perfil.model_dump()
    try:
        derivadas = calcular_variables_derivadas(datos)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    fila = {**datos, **derivadas}
    modelo: GowerKMedoidsPredictor = request.app.state.modelo
    etiquetas, distancias = modelo.predict(pd.DataFrame([fila]))
    cluster_id = int(etiquetas[0])
    return ResultadoCluster(
        cluster_id=cluster_id,
        distancia_gower_al_medoid=round(float(distancias[0]), 4),
        variables_derivadas=derivadas,
        recomendacion=construir_recomendacion(
            cluster_id, derivadas["flujo_mensual_disponible_cop"]
        ),
        nota=(
            "Resultado académico con datos sintéticos. La ruta y, cuando aplica, el cupo "
            "son simulaciones didácticas; no determinan elegibilidad, monto ni aprobación "
            "de un crédito real."
        ),
    )
