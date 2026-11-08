# Perfiles financieros sintéticos

## Propósito y límites

`data/raw/perfiles_crediticios_sinteticos.csv` contiene 30.000 perfiles completamente ficticios para explorar el flujo de una ficha y desarrollar prototipos. No proviene de clientes, estudiantes, entidades financieras ni encuestas; no representa una muestra estadística de Colombia o de la Universidad de Medellín.

La columna `ruta_referencia_sintetica` se asigna mediante reglas transparentes del generador para tener ejemplos de las tres salidas. Es una etiqueta artificial para practicar el flujo y comparar enfoques; no es una decisión experta ni una verdad observada. Un modelo entrenado para reproducirla aprendería esas mismas reglas. Antes de proponer decisiones para personas reales se necesitarían datos autorizados y validados, criterios de capacidad de pago, revisión de sesgos y evaluación con responsables del programa.

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
| `edad` | Edad sintética entre 18 y 40 años. |
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
| `puntaje_educacion_financiera_0_10` | Puntaje sintético de 0 a 10; no proviene de una prueba aplicada. |
| `moras_ultimos_12_meses` | Número sintético de moras recientes; cero si no tiene historial. |
| `monto_solicitado_cop` | Monto solicitado sintético en COP. |
| `carga_financiera_proyectada` | Deuda actual más cuota estimada dividida por ingreso; valor alto si no hay ingreso. |
| `ruta_referencia_sintetica` | Etiqueta demostrativa: `educacion_financiera`, `microcredito_con_acompanamiento` o `credito_mayor_capacidad`. |

## Criterio de las etiquetas de demostración

- Educación financiera: puntaje sintético bajo (0–3), o no tiene ingresos y cuenta con ahorro bajo.
- Microcrédito con acompañamiento: no tiene historial, registra al menos dos moras, la carga financiera proyectada supera 35%, o sus ingresos son variables/informales o dependen de apoyo familiar.
- Crédito de mayor capacidad: los demás perfiles.

Estas reglas solo buscan producir rutas diversas en el conjunto sintético. Deben revisarse y reemplazarse antes de cualquier uso fuera de un ejercicio académico.
