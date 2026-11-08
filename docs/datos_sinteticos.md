# Perfiles financieros sintéticos

## Propósito y límites

`data/raw/perfiles_crediticios_sinteticos.csv` contiene 30.000 perfiles completamente ficticios para explorar el flujo de una ficha y desarrollar prototipos. No proviene de clientes, estudiantes, entidades financieras ni encuestas; no representa una muestra estadística de Colombia o de la Universidad de Medellín.

El CSV de `data/raw/` contiene los campos de entrada que podría entregar una persona. El pipeline genera `nivel_educacion_financiera`, `gastos_esenciales_mensuales_cop` y `flujo_mensual_disponible_cop`; la salida se guarda en `data/processed/`. Así, la categoría y el flujo se calculan con el mismo código durante el prototipado y en una futura integración de producción.

## Tamaño y reproducibilidad

- Registros: 30.000 (se puede cambiar con `--n`).
- El CSV de entrada contiene 28 campos; el procesamiento añade 3 variables derivadas y genera 31 campos.
- Semilla inicial: `20261108`.
- Moneda de referencia: pesos colombianos (COP).
- Generación reproducible: `python scripts/generar_perfiles_sinteticos.py`.
- Para regenerar: `python scripts/generar_perfiles_sinteticos.py --n 30000 --seed 20261108`.
- Para procesar los campos de entrada: `python scripts/ejecutar_pipeline_perfil.py`.
- Salida procesada predeterminada: `data/processed/perfiles_crediticios_procesados.csv`.

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
| `ingreso_mensual_cop` | Ingreso mensual reportado sintético en COP. |
| `tiene_ingresos` | Indicador 1/0 derivado de ingreso mensual mayor que cero. |
| `ingreso_neto_mensual_cop` | Ingreso neto mensual que usa el cálculo del flujo disponible. En una ficha real debe ingresarlo o confirmarlo el cliente. |
| `tiene_vivienda_propia` | Indicador sintético 1/0. |
| `tiene_vehiculo` | Indicador sintético 1/0. |
| `gasto_vivienda_mensual_cop` | Gasto mensual de vivienda del cliente/hogar en COP. |
| `gasto_alimentacion_mensual_cop` | Gasto mensual de alimentación en COP. |
| `gasto_transporte_mensual_cop` | Gasto mensual de transporte en COP. |
| `gasto_salud_mensual_cop` | Gasto mensual de salud en COP. |
| `gasto_educacion_mensual_cop` | Gasto mensual de educación en COP. |
| `pago_servicios_publicos_cop` | Pago mensual sintético de servicios del hogar en COP. |
| `otros_gastos_esenciales_mensuales_cop` | Otros gastos esenciales mensuales en COP. |
| `tipo_plan_celular` | Sin línea, prepago o pospago. |
| `experiencia_crediticia` | Sin experiencia, crédito formal o informal, tarjeta o microcrédito. |
| `meses_historial_crediticio` | Meses sintéticos de historial; cero si no tiene experiencia. |
| `cuotas_deudas_vigentes_cop` | Suma mensual sintética de las cuotas de deudas vigentes en COP. |
| `ahorro_disponible_cop` | Ahorro disponible sintético en COP. |
| `moras_ultimos_12_meses` | Número sintético de moras recientes; cero si no tiene historial. |
| `monto_solicitado_cop` | Monto solicitado sintético en COP. |
| `nivel_educacion_financiera` | Campo derivado por el pipeline (`bajo`, `medio`, `alto`). Es un proxy del historial y no está en el CSV crudo. |
| `gastos_esenciales_mensuales_cop` | Campo derivado por el pipeline: suma de vivienda, alimentación, transporte, salud, educación, servicios públicos y otros esenciales. |
| `flujo_mensual_disponible_cop` | Campo derivado por el pipeline: ingreso neto menos gastos esenciales y cuotas de deudas vigentes. Puede ser negativo. |

## Regla del proxy de educación financiera

- `bajo`: no tiene experiencia crediticia o tiene cero meses de historial.
- `medio`: tiene historial, pero dura menos de 12 meses o registra una o más moras en los últimos 12 meses.
- `alto`: tiene al menos 12 meses de historial y ninguna mora registrada en los últimos 12 meses.

La regla se aplica dentro de `src/pipeline/perfil_financiero.py` antes de la clasificación. Sirve para producir la categoría operativa solicitada, pero **historial crediticio y educación financiera no son equivalentes**. No tener historial puede deberse a barreras de acceso, no a falta de conocimientos. Para una evaluación válida harían falta preguntas o ejercicios que midan conocimientos y comportamientos directamente. Si se usa esta categoría como objetivo de una clasificación, no se deben incluir sus variables de origen (`experiencia_crediticia`, `meses_historial_crediticio` y `moras_ultimos_12_meses`) entre los predictores; hacerlo filtraría la respuesta al modelo.

## Flujo mensual disponible en el pipeline

La función `calcular_variables_derivadas(perfil)` requiere ingreso neto, los siete rubros de gastos esenciales y las cuotas de deudas vigentes. Si falta un dato, no lo asume como cero: devuelve un error para que el formulario solicite la información. Los montos deben ser finitos, no negativos y expresados en pesos enteros. El resultado puede ser negativo y se conserva como señal de déficit.

El cálculo implementado es:

`gastos_esenciales_mensuales_cop = vivienda + alimentación + transporte + salud + educación + servicios públicos + otros esenciales`

`flujo_mensual_disponible_cop = ingreso_neto_mensual_cop - gastos_esenciales_mensuales_cop - cuotas_deudas_vigentes_cop`

Este flujo es un insumo de capacidad de pago, no un monto de crédito aprobado ni una decisión final. Para comparar con una nueva cuota se necesitan además monto, plazo, tasa, frecuencia y cargos del producto. Los servicios públicos se suman una sola vez dentro de los gastos esenciales.

La Superintendencia Financiera describe el análisis de capacidad de pago con flujos de ingresos y egresos, flujo de caja, endeudamiento y características financieras del crédito. Este cálculo es un insumo del proyecto, no un umbral regulatorio ni una decisión automática de otorgamiento. [Referencia de la SFC](https://www.superfinanciera.gov.co/publicaciones/10096970/normativanormativa-generalboletin-juridico-superintendencia-financieraboletin-juridico-numero-credito-deudor-solidario-analisis-de-endeudamiento-10096970/).
