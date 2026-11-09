# Documentación y comprobación de comportamientos clave

La suite unitaria cubre tres comportamientos de la demostración académica. Se ejecuta desde la raíz del repositorio con:

```bash
uv run python -m unittest discover -s tests/unit -v
```

Las pruebas usan `unittest`, incluido en Python, y no llaman a la API pública ni dependen de datos personales.

## 1. Proxy de educación financiera

El campo `nivel_educacion_financiera` es una regla didáctica calculada a partir de la experiencia crediticia, los meses de historial y las moras reportadas en los últimos 12 meses:

| Condición | Nivel asignado |
|---|---|
| Sin experiencia, cero meses y cero moras | Bajo |
| Tiene experiencia, pero no cumple la regla de nivel alto | Medio |
| Al menos 12 meses de historial y cero moras recientes | Alto |

El proxy no mide directamente conocimientos financieros. Las pruebas verifican los tres niveles y un caso con mora que permanece en nivel medio.

## 2. Flujo mensual disponible

El pipeline suma los siete gastos esenciales y calcula:

```text
flujo mensual disponible = ingreso neto mensual − gastos esenciales − cuotas de deudas vigentes
```

El resultado puede ser negativo y no se recorta a cero. El pipeline también falla si falta un gasto esencial, en vez de asumir que su valor es cero. Las pruebas comprueban el cálculo con flujo positivo, el resultado negativo y el error por dato faltante.

## 3. Rutas académicas por cluster

La API asigna una salida ilustrativa según el cluster producido por el modelo:

| Cluster | Ruta | Regla comprobada |
|---|---|---|
| 0 | Viabilidad estudio formal de crédito | Invita a completar información en la siguiente sesión; no asigna cupo. Cuando el flujo no es positivo, la respuesta dice que debe revisarse antes de evaluar un monto. |
| 1 | Cuida tu historial crediticio | Cupo simulado de $300.000 COP cuando el flujo es cero o negativo y de $500.000 COP cuando es positivo. |
| 2 | Iniciemos con educación financiera | Invita al curso corto e interactivo; no asigna cupo. |

Los cupos y las rutas son salidas didácticas de un proyecto con perfiles sintéticos. No son ofertas, aprobaciones, rechazos ni recomendaciones aplicables a solicitudes reales.

## Archivos comprobados

- `src/pipeline/perfil_financiero.py`: calcula el proxy educativo, los gastos esenciales y el flujo.
- `api/main.py`: construye el mensaje académico según el cluster y, para el grupo 1, según el flujo.
- `tests/unit/test_perfil_financiero.py`: comprueba transformaciones y validaciones del pipeline.
- `tests/unit/test_recomendaciones_api.py`: comprueba nombres, mensajes y montos de las rutas.
