#!/usr/bin/env python3
"""Compara los tres métodos finales en la base sintética oficial, con k=3."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import adjusted_rand_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.segmentacion import (  # noqa: E402
    CATEGORICAS_BASE_FINAL,
    comparar_clusterizaciones,
)

NUMERICAS_MODELO_FINAL = [
    "edad", "personas_hogar", "personas_a_cargo", "ingreso_per_capita_cop",
    "ratio_gastos_ingreso", "ratio_deuda_ingreso", "cobertura_ahorro_meses",
    "meses_historial_crediticio", "moras_ultimos_12_meses", "monto_solicitado_cop",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--gower-train-size", type=int, default=1800)
    parser.add_argument("--evaluation-size", type=int, default=800)
    parser.add_argument("--pam-starts", type=int, default=20)
    parser.add_argument("--pam-max-iter", type=int, default=50)
    parser.add_argument("--tag", default="", help="sufijo opcional para experimentos separados")
    parser.add_argument(
        "--input", type=Path,
        default=ROOT / "data/processed/perfiles_crediticios_procesados.csv",
    )
    args = parser.parse_args()
    if not args.input.exists():
        parser.error(f"No se encontró la base final procesada: {args.input}")
    if args.tag and not re.fullmatch(r"[A-Za-z0-9_-]+", args.tag):
        parser.error("--tag solo puede tener letras, números, guion o guion bajo")

    perfiles = pd.read_csv(args.input)
    metricas, etiquetas, elegido, labels_by_model = comparar_clusterizaciones(
        perfiles,
        k_values=(3,),
        seed=args.seed,
        gower_train_size=args.gower_train_size,
        evaluation_size=args.evaluation_size,
        pam_starts=args.pam_starts,
        pam_max_iter=args.pam_max_iter,
        columnas_categoricas=CATEGORICAS_BASE_FINAL,
        columnas_numericas=NUMERICAS_MODELO_FINAL,
        estrategia_faltantes="pairwise",
    )
    reference_path = ROOT / "data/processed/referencia_arquetipos_sinteticos.csv"
    metricas["ari_vs_arquetipo_referencia"] = pd.NA
    if reference_path.exists():
        reference = pd.read_csv(reference_path)
        if not reference["id_persona"].equals(perfiles["id_persona"]):
            parser.error("Los IDs de la referencia no coinciden con la base procesada.")
        for row_index, row in metricas.iterrows():
            key = (row["algoritmo"], int(row["k"]))
            metricas.loc[row_index, "ari_vs_arquetipo_referencia"] = adjusted_rand_score(
                reference["arquetipo_referencia"], labels_by_model[key]
            )
    metricas["variables_numericas"] = ", ".join(NUMERICAS_MODELO_FINAL)
    metricas["variables_categoricas"] = ", ".join(CATEGORICAS_BASE_FINAL)
    metricas["semilla"] = args.seed
    metricas["muestra_evaluacion"] = min(args.evaluation_size, max(50, int(len(perfiles) * 0.20)))
    metricas["muestra_PAM"] = args.gower_train_size

    output = ROOT / "data/processed"
    output.mkdir(parents=True, exist_ok=True)
    suffix = f"_{args.tag}" if args.tag else ""
    metrics_path = output / f"comparacion_clusterizaciones{suffix}.csv"
    assignments_path = output / f"perfiles_clusterizados{suffix}.csv"
    metricas.to_csv(metrics_path, index=False, encoding="utf-8-sig")

    result = perfiles.copy()
    result["cluster"] = etiquetas.to_numpy()
    result["algoritmo_seleccionado"] = elegido[0]
    result["k_seleccionado"] = elegido[1]
    result["cluster_k_prototypes"] = labels_by_model[("K-Prototypes", 3)]
    result["cluster_one_hot_kmeans"] = labels_by_model[("One-Hot + K-Means", 3)]
    result["cluster_gower_k_medoids"] = labels_by_model[("Gower + K-Medoids (muestra)", 3)]
    result.to_csv(assignments_path, index=False, encoding="utf-8-sig")

    print(f"Métricas: {metrics_path}")
    print(f"Etiquetas sobre los {len(perfiles):,} perfiles: {assignments_path}")
    print("Resultados k=3, Silhouette Gower:")
    print(metricas[["algoritmo", "k", "silhouette_gower", "menor_cluster_pct", "mayor_cluster_pct"]].to_string(index=False))
    print(f"Mayor Silhouette observado: {elegido[0]}, k={elegido[1]}")


if __name__ == "__main__":
    main()
