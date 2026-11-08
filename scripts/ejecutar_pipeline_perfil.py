#!/usr/bin/env python3
"""Aplica las transformaciones del perfil y genera un CSV procesado."""
import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline.perfil_financiero import calcular_variables_derivadas  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path,
        default=ROOT / "data/raw/perfiles_crediticios_sinteticos.csv",
        help="CSV con campos de entrada del cliente",
    )
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "data/processed/perfiles_crediticios_procesados.csv",
        help="ruta de salida con las variables derivadas",
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.input.open("r", newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            parser.error(f"El archivo de entrada no tiene encabezados: {args.input}")
        output_fields = list(reader.fieldnames) + [
            "nivel_educacion_financiera",
            "gastos_esenciales_mensuales_cop",
            "flujo_mensual_disponible_cop",
        ]
        with args.output.open("w", newline="", encoding="utf-8-sig") as destination:
            writer = csv.DictWriter(destination, fieldnames=output_fields)
            writer.writeheader()
            count = 0
            for row in reader:
                derived = calcular_variables_derivadas(row)
                writer.writerow({**row, **derived})
                count += 1

    print(f"Pipeline aplicado a {count:,} perfiles. Archivo procesado: {args.output}")


if __name__ == "__main__":
    main()
