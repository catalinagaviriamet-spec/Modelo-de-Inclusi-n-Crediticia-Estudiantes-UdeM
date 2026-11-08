# Perfiles financieros sintéticos

## Propósito y límites

`data/raw/perfiles_crediticios_sinteticos.csv` contiene 30.000 perfiles completamente ficticios para explorar el flujo de una ficha y desarrollar prototipos. No proviene de clientes, estudiantes, entidades financieras ni encuestas; no representa una muestra estadística de Colombia o de la Universidad de Medellín.

Esta versión contiene variables de perfil de entrada y una categoría derivada llamada `nivel_educacion_financiera`. En esta fase se calcula a partir del historial crediticio como un proxy solicitado para el ejercicio, no a partir de una prueba de conocimientos. La capacidad de pago y las rutas de atención se definirán más adelante; no se incluyen como columnas en el CSV.

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
| `nivel_educacion_financiera` | Proxy categórico derivado del historial: `bajo`, `medio` o `alto`, según la regla abajo. No mide conocimientos financieros directamente. |
| `deuda_mensual_cop` | Obligaciones mensuales actuales sintéticas en COP. |
| `ahorro_disponible_cop` | Ahorro disponible sintético en COP. |
| `moras_ultimos_12_meses` | Número sintético de moras recientes; cero si no tiene historial. |
| `monto_solicitado_cop` | Monto solicitado sintético en COP. |

## Regla del proxy de educación financiera

- `bajo`: no tiene experiencia crediticia o tiene cero meses de historial.
- `medio`: tiene historial, pero dura menos de 12 meses o registra una o más moras en los últimos 12 meses.
- `alto`: tiene al menos 12 meses de historial y ninguna mora registrada en los últimos 12 meses.

La regla sirve para producir una categoría antes de probar la clasificación, pero **historial crediticio y educación financiera no son equivalentes**. No tener historial puede deberse a barreras de acceso, no a falta de conocimientos. Para una evaluación válida de educación financiera harían falta preguntas o ejercicios que midan conocimientos y comportamientos directamente. Si se usa esta categoría como objetivo de una clasificación, no se deben incluir sus variables de origen (`experiencia_crediticia`, `meses_historial_crediticio` y `moras_ultimos_12_meses`) entre los predictores; hacerlo filtraría la respuesta al modelo.

## Capacidad de pago: definición pendiente

El CSV **no tiene actualmente una variable calculada de capacidad de pago**. Incluye algunos insumos —ingreso mensual, deuda mensual, pago de servicios, personas a cargo, ahorro y monto solicitado—, pero faltan gastos esenciales del hogar (por ejemplo, vivienda, alimentación, transporte, salud y educación), la confirmación de si el ingreso es neto, y el plazo y la tasa del crédito solicitado.

Una definición operativa a validar sería:

`flujo_libre_mensual = ingreso_neto_mensual - gastos_esenciales_mensuales - cuotas_deudas_vigentes`

`cuota_nueva_estimada = cuota del monto solicitado, calculada con plazo, tasa, frecuencia y cargos del producto`

Se compararía la cuota nueva con el flujo libre y se reportaría, como indicador complementario, la carga financiera total: `(cuotas vigentes + cuota nueva estimada) / ingreso neto mensual`. Si el ingreso neto es cero o desconocido, el indicador se marca como no calculable, no como cero ni como una capacidad positiva. Los servicios públicos deben contarse dentro de los gastos esenciales una sola vez.

La Superintendencia Financiera describe el análisis de capacidad de pago con flujos de ingresos y egresos, flujo de caja, endeudamiento y características financieras del crédito. La fórmula anterior es una propuesta de trabajo para este proyecto; no es un umbral regulatorio ni debe convertirse en una decisión automática sin validación. [Referencia de la SFC](https://www.superfinanciera.gov.co/publicaciones/10096970/normativanormativa-generalboletin-juridico-superintendencia-financieraboletin-juridico-numero-credito-deudor-solidario-analisis-de-endeudamiento-10096970/).
