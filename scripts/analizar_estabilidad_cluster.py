#!/usr/bin/env python3
"""Evalúa la estabilidad de Gower + K-Medoids con k=3 ante remuestreo."""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.segmentacion import analizar_estabilidad_gower_kmedoids  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--gower-train-size", type=int, default=1800)
    parser.add_argument("--evaluation-size", type=int, default=800)
    parser.add_argument(
        "--input", type=Path,
        default=ROOT / "data/processed/perfiles_crediticios_procesados.csv",
    )
    args = parser.parse_args()
    if not args.input.exists():
        parser.error(f"No se encontró la base procesada: {args.input}")

    perfiles = pd.read_csv(args.input)
    resultados = analizar_estabilidad_gower_kmedoids(
        perfiles,
        k=3,
        seed=args.seed,
        repeticiones=args.repetitions,
        gower_train_size=args.gower_train_size,
        evaluation_size=args.evaluation_size,
    )
    salida = ROOT / "data/processed/estabilidad_gower_kmedoids_k3.csv"
    salida.parent.mkdir(parents=True, exist_ok=True)
    resultados.to_csv(salida, index=False, encoding="utf-8-sig")
    print("Resultados por repetición:")
    print(resultados.round(3).to_string(index=False))
    ari_columnas = [
        "ari_remuestreo_vs_referencia",
        "ari_inicializacion_vs_referencia",
    ]
    print("\nResumen de ARI (sin contar la repetición de referencia):")
    print(resultados[ari_columnas].iloc[1:].describe().round(3).to_string())
    print("\nArchivo guardado en:", salida)


if __name__ == "__main__":
    main()
