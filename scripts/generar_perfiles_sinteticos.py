#!/usr/bin/env python3
"""Genera perfiles financieros sintéticos reproducibles para el proyecto UdeM."""
import argparse
import csv
from pathlib import Path


class RNG:
    """Generador xorshift32 para resultados reproducibles con la misma semilla."""
    def __init__(self, seed):
        self.state = seed & 0xFFFFFFFF or 1

    def random(self):
        x = self.state
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= x >> 17
        x ^= (x << 5) & 0xFFFFFFFF
        self.state = x & 0xFFFFFFFF
        return self.state / 4294967296

    def integer(self, low, high):
        return low + int(self.random() * (high - low + 1))

    def choice(self, values, weights=None):
        if weights is None:
            return values[self.integer(0, len(values) - 1)]
        point = self.random() * sum(weights)
        total = 0
        for value, weight in zip(values, weights):
            total += weight
            if point < total:
                return value
        return values[-1]

    def chance(self, probability):
        return self.random() < probability


def make_row(i, rng):
    age = rng.integer(18, 40)
    hogar = rng.choice(
        ["vive_solo", "comparte_vivienda", "vive_con_familia", "vive_con_pareja", "otro"],
        [10, 18, 42, 24, 6],
    )
    n_hogar = rng.choice([1, 2, 3, 4, 5, 6, 7], [12, 20, 25, 20, 13, 7, 3])
    dependientes = rng.integer(0, min(5, n_hogar - 1))
    estudio = rng.choice(
        ["secundaria", "tecnico_tecnologico", "universitario_en_curso", "universitario_completo", "posgrado"],
        [13, 23, 39, 20, 5],
    )
    empleo = rng.choice(
        ["estudia", "empleo_formal", "empleo_informal", "independiente", "desempleado", "estudia_y_trabaja"],
        [24, 24, 15, 14, 8, 15],
    )
    tipo_ingreso = rng.choice(
        ["sin_ingresos", "salario_fijo", "ingreso_variable", "informal", "apoyo_familiar"],
        [8, 37, 22, 17, 16],
    )
    rangos = {
        "sin_ingresos": (0, 0), "salario_fijo": (900_000, 8_000_000),
        "ingreso_variable": (450_000, 7_000_000), "informal": (300_000, 5_500_000),
        "apoyo_familiar": (200_000, 3_000_000),
    }
    low, high = rangos[tipo_ingreso]
    ingreso = rng.integer(low, high)
    vivienda = int(rng.chance(0.17 if age < 25 else (0.30 if age < 33 else 0.43)))
    vehiculo = int(rng.chance(0.12 if ingreso < 1_500_000 else (0.34 if ingreso < 4_000_000 else 0.58)))
    servicios = 0 if hogar == "comparte_vivienda" and rng.chance(0.30) else rng.integer(70_000, 750_000)
    celular = rng.choice(["sin_linea", "prepago", "pospago"], [3, 41 if ingreso < 1_500_000 else 24, 56 if ingreso < 1_500_000 else 73])
    experiencia = rng.choice(
        ["sin_experiencia", "credito_formal", "credito_informal", "tarjeta_credito", "microcredito"],
        [30, 30, 11, 20, 9],
    )
    historial = experiencia != "sin_experiencia"
    meses = rng.integer(1, 180) if historial else 0
    deuda = 0 if not historial or rng.chance(0.24) else rng.integer(40_000, max(50_000, min(2_500_000, ingreso // 2 + 50_000)))
    ahorro = 0 if rng.chance(0.27) else rng.integer(20_000, max(50_000, min(12_000_000, ingreso * 4 + 100_000)))
    educacion_financiera = rng.integer(0, 10)
    moras = 0 if not historial else rng.choice([0, 1, 2, 3, 4], [61, 20, 11, 5, 3])
    solicitado = rng.integer(200_000, 8_000_000)
    cuota_estimada = int(solicitado / rng.choice([6, 12, 18, 24, 36]))
    carga = round((deuda + cuota_estimada) / max(ingreso, 1), 4) if ingreso else 9.9999

    # Etiqueta de referencia sintética; no es una recomendación de crédito real.
    if educacion_financiera <= 3 or (ingreso == 0 and ahorro < 500_000):
        ruta = "educacion_financiera"
    elif (not historial or moras >= 2 or carga > 0.35
          or tipo_ingreso in {"ingreso_variable", "informal", "apoyo_familiar"}):
        ruta = "microcredito_con_acompanamiento"
    else:
        ruta = "credito_mayor_capacidad"

    return {
        "id_persona": f"SYN-{i:06d}", "edad": age, "tipo_hogar": hogar,
        "personas_hogar": n_hogar, "personas_a_cargo": dependientes,
        "nivel_estudio": estudio, "situacion_laboral": empleo, "tipo_ingreso": tipo_ingreso,
        "ingreso_mensual_cop": ingreso, "tiene_ingresos": int(ingreso > 0),
        "tiene_vivienda_propia": vivienda, "tiene_vehiculo": vehiculo,
        "pago_servicios_publicos_cop": servicios, "tipo_plan_celular": celular,
        "experiencia_crediticia": experiencia, "meses_historial_crediticio": meses,
        "deuda_mensual_cop": deuda, "ahorro_disponible_cop": ahorro,
        "puntaje_educacion_financiera_0_10": educacion_financiera,
        "moras_ultimos_12_meses": moras, "monto_solicitado_cop": solicitado,
        "carga_financiera_proyectada": carga, "ruta_referencia_sintetica": ruta,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=30_000, help="cantidad de perfiles")
    parser.add_argument("--seed", type=int, default=20261108, help="semilla reproducible")
    parser.add_argument("--out", type=Path, default=Path("data/raw/perfiles_crediticios_sinteticos.csv"))
    args = parser.parse_args()
    if args.n <= 0:
        parser.error("--n debe ser mayor que cero")
    rng = RNG(args.seed)
    first = make_row(1, rng)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(first))
        writer.writeheader()
        writer.writerow(first)
        for i in range(2, args.n + 1):
            writer.writerow(make_row(i, rng))
    print(f"Generados {args.n:,} perfiles en {args.out} (seed={args.seed}).")


if __name__ == "__main__":
    main()
