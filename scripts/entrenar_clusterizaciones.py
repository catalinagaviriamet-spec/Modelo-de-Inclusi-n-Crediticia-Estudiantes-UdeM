#!/usr/bin/env python3
"""Ajusta tres métodos de clusterización mixta y guarda su comparación."""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.segmentacion import comparar_clusterizaciones  # noqa: E402
from src.pipeline.perfil_financiero import calcular_variables_derivadas  # noqa: E402


def cargar_perfiles(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    raw_path = ROOT / "data/raw/perfiles_crediticios_sinteticos.csv"
    raw = pd.read_csv(raw_path)
    derivadas = pd.DataFrame(
        [calcular_variables_derivadas(row) for row in raw.to_dict(orient="records")]
    )
    return pd.concat([raw, derivadas], axis=1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k-values", default="3,4,5,6", help="valores de k separados por coma")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--gower-train-size", type=int, default=1800)
    parser.add_argument("--evaluation-size", type=int, default=800)
    parser.add_argument(
        "--input", type=Path,
        default=ROOT / "data/processed/perfiles_crediticios_procesados.csv",
    )
    args = parser.parse_args()
    k_values = tuple(int(value.strip()) for value in args.k_values.split(",") if value.strip())
    if not k_values or any(k < 2 for k in k_values):
        parser.error("--k-values debe contener enteros mayores o iguales a 2")

    perfiles = cargar_perfiles(args.input)
    metricas, etiquetas, elegido, _ = comparar_clusterizaciones(
        perfiles,
        k_values=k_values,
        seed=args.seed,
        gower_train_size=args.gower_train_size,
        evaluation_size=args.evaluation_size,
    )

    salida = ROOT / "data/processed"
    salida.mkdir(parents=True, exist_ok=True)
    metricas_path = salida / "comparacion_clusterizaciones.csv"
    perfiles_path = salida / "perfiles_clusterizados.csv"
    metricas.to_csv(metricas_path, index=False, encoding="utf-8-sig")
    resultado = perfiles.copy()
    resultado["cluster"] = etiquetas.to_numpy()
    resultado["algoritmo_seleccionado"] = elegido[0]
    resultado["k_seleccionado"] = elegido[1]
    resultado.to_csv(perfiles_path, index=False, encoding="utf-8-sig")

    print("Comparación guardada en:", metricas_path)
    print("Perfiles con cluster guardados en:", perfiles_path)
    print("Mejor silhouette Gower para inspección inicial:", elegido)
    print(metricas.to_string(index=False))


if __name__ == "__main__":
    main()
