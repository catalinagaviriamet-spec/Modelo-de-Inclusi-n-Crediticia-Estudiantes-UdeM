# Perfiles financieros sintéticos

## Propósito y límites

`data/raw/perfiles_crediticios_sinteticos.csv` contiene 30.000 perfiles completamente ficticios para explorar el flujo de una ficha y desarrollar prototipos. No proviene de clientes, estudiantes, entidades financieras ni encuestas; no representa una muestra estadística de Colombia o de la Universidad de Medellín.

Esta versión contiene variables de perfil de entrada. Las métricas derivadas y las rutas de atención se definirán más adelante en el proyecto; por eso no se incluyen como columnas en el CSV.

## Tamaño y reproducibilidad

- Registros: 30.000 (se puede cambiar con `--n`).
- Semilla inicial: `20261108`.
- Moneda de referencia: pesos colombianos (COP).
- Generación reproducible: `python scripts/generar_perfiles_sinteticos.py`.
- Para regenerar: `python scripts/generar_perfiles_sinteticos.py --n 30000 --seed 20261108`.

El generador crea valores variados y relaciones plausibles para demostración; las distribuciones no se calibraron con evidencia poblacional. La base puede compartirse porque no contiene datos personales reales.

## Diccionario de campos

| Campo | Descripción |
|---|---|
| `id_persona` | Identificador ficticio, sin relación con una persona real. |
| `edad` | Edad sintética entre 18 y 74 años. |
| `rango_edad` | Categoría derivada de la edad: `18-25`, `26-40`, `41-60` o `61-74`. |
| `tipo_hogar` | Vive solo, comparte vivienda, vive con familia, con pareja u otro. |
| `personas_hogar` | Número de personas en el hogar. |
| `personas_a_cargo` | Personas dependientes económicamente dentro del hogar. |
| `nivel_estudio` | Nivel educativo sintético. |
| `situacion_laboral` | Situación laboral sintética. |
| `tipo_ingreso` | Sin ingresos, salario fijo, ingreso variable, informal o apoyo familiar. |
| `ingreso_mensual_cop` | Ingreso mensual sintético en COP. |
| `tiene_ingresos` | Indicador 1/0 derivado de ingreso mensual mayor que cero. |
| `tiene_vivienda_propia` | Indicador sintético 1/0. |
| `tiene_vehiculo` | Indicador sintético 1/0. |
| `pago_servicios_publicos_cop` | Pago mensual sintético de servicios del hogar en COP. |
| `tipo_plan_celular` | Sin línea, prepago o pospago. |
| `experiencia_crediticia` | Sin experiencia, crédito formal o informal, tarjeta o microcrédito. |
| `meses_historial_crediticio` | Meses sintéticos de historial; cero si no tiene experiencia. |
| `deuda_mensual_cop` | Obligaciones mensuales actuales sintéticas en COP. |
| `ahorro_disponible_cop` | Ahorro disponible sintético en COP. |
| `moras_ultimos_12_meses` | Número sintético de moras recientes; cero si no tiene historial. |
| `monto_solicitado_cop` | Monto solicitado sintético en COP. |
