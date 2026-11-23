"""Pipeline de transformaciones de entrada para un perfil financiero.

Calcula los campos derivados usados por la base final. ``id_persona`` se
conserva como metadato y ``segmento_generador`` se infiere desde el perfil.
"""
from decimal import Decimal, InvalidOperation, ROUND_FLOOR, ROUND_HALF_UP
from typing import Any, Mapping


GASTOS_ESENCIALES = (
    "gasto_vivienda_mensual_cop",
    "gasto_alimentacion_mensual_cop",
    "gasto_transporte_mensual_cop",
    "gasto_salud_mensual_cop",
    "gasto_educacion_mensual_cop",
    "pago_servicios_publicos_cop",
    "otros_gastos_esenciales_mensuales_cop",
)

EXPERIENCIAS_CREDITICIAS = {
    "sin_experiencia",
    "credito_formal",
    "credito_informal",
    "tarjeta_credito",
    "microcredito",
}


def _monto_no_negativo(perfil: Mapping[str, Any], campo: str) -> int:
    if campo not in perfil or perfil[campo] is None or str(perfil[campo]).strip() == "":
        raise ValueError(f"Falta el dato requerido '{campo}'. No se puede calcular el flujo.")
    try:
        valor = Decimal(str(perfil[campo]))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"'{campo}' debe ser un monto numérico en COP.") from exc
    if not valor.is_finite() or valor < 0:
        raise ValueError(f"'{campo}' debe ser un monto finito y no negativo.")
    if valor != valor.to_integral_value():
        raise ValueError(f"'{campo}' debe expresarse en pesos enteros (COP).")
    return int(valor)


def _entero_no_negativo(perfil: Mapping[str, Any], campo: str) -> int:
    if campo not in perfil or perfil[campo] is None or str(perfil[campo]).strip() == "":
        raise ValueError(f"Falta el dato requerido '{campo}'.")
    try:
        valor = Decimal(str(perfil[campo]))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"'{campo}' debe ser un entero no negativo.") from exc
    if not valor.is_finite() or valor < 0 or valor != valor.to_integral_value():
        raise ValueError(f"'{campo}' debe ser un entero no negativo.")
    return int(valor)


def _nivel_educacion_financiera(perfil: Mapping[str, Any]) -> str:
    experiencia = str(perfil.get("experiencia_crediticia", "")).strip().lower()
    if experiencia not in EXPERIENCIAS_CREDITICIAS:
        raise ValueError(
            "'experiencia_crediticia' debe ser una de estas categorías: "
            + ", ".join(sorted(EXPERIENCIAS_CREDITICIAS))
        )
    meses = _entero_no_negativo(perfil, "meses_historial_crediticio")
    moras = _entero_no_negativo(perfil, "moras_ultimos_12_meses")
    sin_historial = experiencia == "sin_experiencia"
    if sin_historial and (meses != 0 or moras != 0):
        raise ValueError("Sin experiencia crediticia, meses de historial y moras deben ser cero.")
    if not sin_historial and meses == 0:
        raise ValueError("Con experiencia crediticia, meses_historial_crediticio debe ser mayor que cero.")
    if sin_historial:
        return "bajo"
    if meses >= 12 and moras == 0:
        return "alto"
    return "medio"


def _segmento_generador(
    perfil: Mapping[str, Any],
    ingreso_neto: int,
    gastos_esenciales: int,
    flujo_disponible: int,
    deudas_vigentes: int,
    ahorro: int,
) -> str:
    """Asigna un segmento único mediante reglas ordenadas y explícitas."""
    experiencia = str(perfil.get("experiencia_crediticia", "")).strip().lower()
    tipo_ingreso = str(perfil.get("tipo_ingreso", "")).strip().lower()
    situacion = str(perfil.get("situacion_laboral", "")).strip().lower()
    moras = _entero_no_negativo(perfil, "moras_ultimos_12_meses")

    # La secuencia establece precedencia cuando un perfil cumple más de una regla.
    if ingreso_neto == 0 and experiencia == "sin_experiencia":
        return "sin_ingresos_sin_historial"
    if ingreso_neto > 0 and deudas_vigentes / ingreso_neto > 0.50:
        return "sobreendeudado"
    if gastos_esenciales > 0 and ahorro >= 3 * gastos_esenciales:
        return "ahorrador_con_respaldo"
    if tipo_ingreso == "informal" or situacion == "empleo_informal":
        return "informal_vulnerable"
    if situacion == "independiente":
        if flujo_disponible < 0 or moras > 0:
            return "informal_vulnerable"
        return "independiente_estable"
    if tipo_ingreso == "salario_fijo":
        return "formal_estable"
    # Perfiles sin salario fijo ni actividad independiente se agrupan aquí por
    # vulnerabilidad o inestabilidad del ingreso (p. ej. apoyo familiar).
    return "informal_vulnerable"


def calcular_variables_derivadas(
    perfil: Mapping[str, Any],
) -> dict[str, int | float | str | None]:
    """Calcula campos derivados a partir de los datos que entrega el cliente.

    El flujo puede ser negativo. No se recorta a cero, porque el déficit también
    es información relevante. Si falta un gasto, el pipeline falla de forma
    explícita en lugar de asumir que ese gasto es cero.
    """
    ingreso_neto = _monto_no_negativo(perfil, "ingreso_neto_mensual_cop")
    gastos_esenciales = sum(_monto_no_negativo(perfil, campo) for campo in GASTOS_ESENCIALES)
    deudas_vigentes = _monto_no_negativo(perfil, "cuotas_deudas_vigentes_cop")
    ahorro = _monto_no_negativo(perfil, "ahorro_disponible_cop")
    personas_hogar = _entero_no_negativo(perfil, "personas_hogar")
    if personas_hogar < 1:
        raise ValueError("'personas_hogar' debe ser al menos 1.")
    nivel_educacion = _nivel_educacion_financiera(perfil)
    flujo_disponible = ingreso_neto - gastos_esenciales - deudas_vigentes

    # Las razones no están definidas si no hay ingreso. Se serializan como
    # campos vacíos en CSV, en lugar de disfrazar ese caso como una razón 0.
    ratio_deuda = round(deudas_vigentes / ingreso_neto, 4) if ingreso_neto else None
    ratio_gastos = round(gastos_esenciales / ingreso_neto, 4) if ingreso_neto else None
    ingreso_per_capita = int(
        (Decimal(ingreso_neto) / Decimal(personas_hogar)).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )
    cobertura_ahorro = (
        round(ahorro / gastos_esenciales, 2) if gastos_esenciales else None
    )
    # Regla referencial acordada: máximo 70% del flujo disponible y,
    # simultáneamente, máximo 20% del ingreso neto menos las cuotas vigentes.
    capacidad_referencial = max(
        Decimal(0),
        min(
            Decimal("0.70") * Decimal(flujo_disponible),
            Decimal("0.20") * Decimal(ingreso_neto) - Decimal(deudas_vigentes),
        ),
    ).to_integral_value(rounding=ROUND_FLOOR)

    experiencia = str(perfil.get("experiencia_crediticia", "")).strip().lower()
    meses_historial = _entero_no_negativo(perfil, "meses_historial_crediticio")
    moras = _entero_no_negativo(perfil, "moras_ultimos_12_meses")
    nivel_experiencia = (
        "sin_experiencia"
        if experiencia == "sin_experiencia"
        else "consolidada"
        if meses_historial >= 12 and moras == 0
        else "en_desarrollo"
    )
    segmento = _segmento_generador(
        perfil,
        ingreso_neto,
        gastos_esenciales,
        flujo_disponible,
        deudas_vigentes,
        ahorro,
    )

    return {
        "nivel_educacion_financiera": nivel_educacion,
        "gastos_esenciales_mensuales_cop": gastos_esenciales,
        "flujo_mensual_disponible_cop": flujo_disponible,
        "ratio_deuda_ingreso": ratio_deuda,
        "ratio_gastos_ingreso": ratio_gastos,
        "ingreso_per_capita_cop": ingreso_per_capita,
        "cobertura_ahorro_meses": cobertura_ahorro,
        "capacidad_cuota_referencial_cop": int(capacidad_referencial),
        "nivel_experiencia_crediticia_proxy": nivel_experiencia,
        "segmento_generador": segmento,
    }
