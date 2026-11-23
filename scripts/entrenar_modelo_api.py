#!/usr/bin/env python3
"""Ajusta y guarda el artefacto académico que consume la API."""
import sys
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.segmentacion import (  # noqa: E402
    CATEGORICAS_BASE_FINAL,
    NUMERICAS_BASE_FINAL,
    ajustar_gower_kmedoids,
)
from src.pipeline.perfil_financiero import calcular_variables_derivadas  # noqa: E402


def cargar_perfiles() -> pd.DataFrame:
    procesado = ROOT / "data/processed/perfiles_crediticios_procesados.csv"
    if procesado.exists():
        return pd.read_csv(procesado)
    crudo = pd.read_csv(ROOT / "data/raw/perfiles_crediticios_sinteticos.csv")
    derivadas = pd.DataFrame(
        [calcular_variables_derivadas(registro) for registro in crudo.to_dict("records")]
    )
    return pd.concat([crudo, derivadas], axis=1)


def main() -> None:
    perfiles = cargar_perfiles()
    modelo = ajustar_gower_kmedoids(
        perfiles,
        k=3,
        seed=42,
        train_sample_size=1800,
        n_starts=20,
        max_iter=50,
        columnas_numericas=NUMERICAS_BASE_FINAL,
        columnas_categoricas=CATEGORICAS_BASE_FINAL,
        transformacion_relativas="winsor99_log1p",
    )
    modelo.dataset_size = len(perfiles)
    por_cluster = {p["cluster_id"]: p["medianas"] for p in modelo.cluster_profiles}
    educacion = min(por_cluster, key=lambda c: por_cluster[c]["meses_historial_crediticio"])
    viabilidad = max(
        (c for c in por_cluster if c != educacion),
        key=lambda c: (
            por_cluster[c]["meses_historial_crediticio"],
            por_cluster[c]["flujo_mensual_disponible_cop"],
        ),
    )
    cuidar = next(c for c in por_cluster if c not in {educacion, viabilidad})
    modelo.cluster_routes = {
        str(educacion): "educacion_financiera",
        str(viabilidad): "viabilidad_formal",
        str(cuidar): "cuidar_historial",
    }
    salida = ROOT / "models/gower_kmedoids_k3.joblib"
    salida.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, salida)
    print("Artefacto académico guardado en:", salida)
    print("Tamaño de la base sintética:", modelo.dataset_size)
    print("Muestra usada para ajustar medoids:", modelo.train_sample_size)
    print("Perfiles por cluster:")
    for perfil in modelo.cluster_profiles:
        print(perfil["cluster_id"], perfil["perfiles"], f"({perfil['porcentaje']}%)")


if __name__ == "__main__":
    main()
