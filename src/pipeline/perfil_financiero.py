"""Pipeline de transformaciones de entrada para un perfil financiero.

La función opera sobre un registro de entrada y devuelve variables derivadas
que puede consumir el modelo: nivel educativo financiero proxy, gastos
esenciales agregados y flujo mensual disponible.
"""
from decimal import Decimal, InvalidOperation
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


def calcular_variables_derivadas(perfil: Mapping[str, Any]) -> dict[str, int | str]:
    """Calcula campos derivados a partir de los datos que entrega el cliente.

    El flujo puede ser negativo. No se recorta a cero, porque el déficit también
    es información relevante. Si falta un gasto, el pipeline falla de forma
    explícita en lugar de asumir que ese gasto es cero.
    """
    ingreso_neto = _monto_no_negativo(perfil, "ingreso_neto_mensual_cop")
    gastos_esenciales = sum(_monto_no_negativo(perfil, campo) for campo in GASTOS_ESENCIALES)
    deudas_vigentes = _monto_no_negativo(perfil, "cuotas_deudas_vigentes_cop")
    nivel_educacion = _nivel_educacion_financiera(perfil)
    flujo_disponible = ingreso_neto - gastos_esenciales - deudas_vigentes

    return {
        "nivel_educacion_financiera": nivel_educacion,
        "gastos_esenciales_mensuales_cop": gastos_esenciales,
        "flujo_mensual_disponible_cop": flujo_disponible,
    }
