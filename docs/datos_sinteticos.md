# Base sintética final y pipeline

## Base oficial del proyecto

La entrada oficial es [`data/raw/perfiles_crediticios_sinteticos.csv`](../data/raw/perfiles_crediticios_sinteticos.csv), con 30.000 perfiles ficticios. Se construyó con distribuciones controladas para representar tres arquetipos académicos: viabilidad de estudio formal (40%), cuidado del historial (30%) e inicio en educación financiera (30%). Las proporciones y los patrones financieros se diseñaron para facilitar una comparación didáctica de clusters; no estiman prevalencias de clientes, estudiantes UdeM o población colombiana.

El archivo de referencia `data/processed/referencia_arquetipos_sinteticos.csv` conserva los arquetipos usados para auditar la recuperación de los grupos. No es un campo de entrada, no se une al dataset del modelo y no debe publicarse como etiqueta observable del cliente.

## Flujo para generar la base procesada

El CSV crudo contiene identificador y campos de entrada. Se recalculan todas las variables derivadas con el código compartido entre el pipeline por lotes y la API:

```bash
uv run python scripts/ejecutar_pipeline_perfil.py
```

La salida oficial es [`data/processed/perfiles_crediticios_procesados.csv`](../data/processed/perfiles_crediticios_procesados.csv), con 33 columnas. El pipeline debe terminar sin errores; exige montos enteros, finitos y no negativos, historial coherente con experiencia y al menos una persona por hogar.

## Variables de entrada

| Campo | Significado |
|---|---|
| `id_persona` | Identificador ficticio; no entra al modelo. |
| `edad` | Edad de 18 a 74 años; se conserva independiente del arquetipo. |
| `tipo_hogar`, `personas_hogar`, `personas_a_cargo` | Tipo y tamaño de hogar y dependientes; se conservan independientes del arquetipo. |
| `situacion_laboral`, `tipo_ingreso`, `ingreso_neto_mensual_cop` | Situación laboral, fuente de ingreso e ingreso neto mensual. |
| `tiene_vivienda_propia`, `tiene_vehiculo` | Indicadores 0/1 de activos. |
| `gasto_vivienda_mensual_cop`, `gasto_alimentacion_mensual_cop`, `gasto_transporte_mensual_cop`, `gasto_salud_mensual_cop`, `gasto_educacion_mensual_cop`, `pago_servicios_publicos_cop`, `otros_gastos_esenciales_mensuales_cop` | Rubros de gasto mensual en COP. |
| `experiencia_crediticia`, `meses_historial_crediticio`, `moras_ultimos_12_meses` | Tipo y duración de la experiencia y moras recientes. |
| `cuotas_deudas_vigentes_cop`, `ahorro_disponible_cop`, `monto_solicitado_cop` | Cuotas mensuales, ahorro y monto solicitado en COP. |

## Variables calculadas por el pipeline

| Campo | Regla |
|---|---|
| `nivel_educacion_financiera` | Proxy: bajo sin experiencia; alto con al menos 12 meses y cero moras; medio para los demás perfiles con historial. El historial no mide conocimientos reales. |
| `gastos_esenciales_mensuales_cop` | Suma de los siete rubros esenciales. |
| `flujo_mensual_disponible_cop` | Ingreso neto − gastos esenciales − cuotas vigentes. Puede ser negativo. |
| `ratio_deuda_ingreso` | Cuotas vigentes / ingreso neto, redondeado a 4 decimales. Vacío cuando no hay ingreso. |
| `ratio_gastos_ingreso` | Gastos esenciales / ingreso neto, redondeado a 4 decimales. Vacío cuando no hay ingreso. |
| `ingreso_per_capita_cop` | Ingreso neto / personas del hogar, redondeado al peso más cercano. |
| `cobertura_ahorro_meses` | Ahorro / gastos esenciales, redondeado a 2 decimales. |
| `capacidad_cuota_referencial_cop` | Máximo entre cero y el menor valor de 70% del flujo disponible o 20% del ingreso neto menos cuotas vigentes; redondeado hacia abajo. Es una regla didáctica inferida, no un estándar de crédito. |
| `nivel_experiencia_crediticia_proxy` | Sin experiencia; consolidada con 12+ meses y cero moras; en desarrollo en otro caso. |
| `segmento_generador` | Categoría determinística según las reglas de prioridad abajo. No se usa como predictor de cluster. |

### Prioridad de `segmento_generador`

Se aplica la primera regla que corresponda: (1) ingreso cero y sin experiencia; (2) deuda superior a 50% del ingreso; (3) ahorro para al menos tres meses de gastos; (4) ingreso o empleo informal, o independencia vulnerable; (5) independencia estable; (6) salario fijo; (7) categoría de respaldo informal/vulnerable. El orden evita etiquetas superpuestas y permite que el ahorro cubra meses futuros aunque el flujo del mes sea negativo.

## Variables que entran a la comparación de clustering

Se usan 10 variables numéricas: `edad`, `personas_hogar`, `personas_a_cargo`, `ingreso_per_capita_cop`, `ratio_gastos_ingreso`, `ratio_deuda_ingreso`, `cobertura_ahorro_meses`, `meses_historial_crediticio`, `moras_ultimos_12_meses` y `monto_solicitado_cop`.

Se usan seis categóricas: `tipo_hogar`, `situacion_laboral`, `tipo_ingreso`, `tiene_vivienda_propia`, `tiene_vehiculo` y `experiencia_crediticia`. No se incluyen `id_persona`, el arquetipo de referencia, `segmento_generador`, `nivel_educacion_financiera` ni los montos usados para construir los ratios. Si el ingreso es cero, Gower omite por pares los ratios no definidos; los otros métodos usan imputación mediana solo para poder operar con matrices numéricas.

## Límites de uso

La base final fue construida para que las diferencias entre los arquetipos sean más marcadas que en la base exploratoria anterior. Por ello, la Silhouette de aproximadamente 0,41 y el acuerdo con los arquetipos son resultados de un escenario sintético diseñado; no son validación en clientes reales ni garantía de generalización. Los grupos, proxies, capacidad referencial y rutas de la API son únicamente parte de una demostración académica.
