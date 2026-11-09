#!/usr/bin/env python3
"""Exporta los archivos mínimos para publicar la API en un Hugging Face Space.

Ejemplo: uv run python scripts/preparar_space.py C:/ruta/space
La carpeta destino debe ser un repositorio Space independiente.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANTILLA = ROOT / "deploy/huggingface"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Uso: uv run python scripts/preparar_space.py <carpeta-del-space>")
    destino = Path(sys.argv[1]).expanduser().resolve()
    if destino == ROOT or ROOT in destino.parents:
        raise SystemExit("El destino debe quedar fuera del repositorio del proyecto.")
    modelo = ROOT / "models/gower_kmedoids_k3.joblib"
    if not modelo.is_file():
        raise SystemExit(f"No se encontró el artefacto del modelo: {modelo}")

    destino.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "deploy/container/Dockerfile", destino / "Dockerfile")
    shutil.copy2(PLANTILLA / "README.md", destino / "README.md")
    for archivo in ("pyproject.toml", "uv.lock"):
        shutil.copy2(ROOT / archivo, destino / archivo)
    for carpeta in ("api", "src"):
        shutil.copytree(ROOT / carpeta, destino / carpeta, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (destino / "models").mkdir(exist_ok=True)
    shutil.copy2(modelo, destino / "models/gower_kmedoids_k3.joblib")
    print(f"Archivos listos para Space en: {destino}")


if __name__ == "__main__":
    main()
