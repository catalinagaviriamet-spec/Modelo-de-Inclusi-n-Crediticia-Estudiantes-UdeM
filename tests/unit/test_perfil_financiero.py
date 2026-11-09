"""Pruebas unitarias de los cálculos derivados del perfil financiero."""
import unittest

from src.pipeline.perfil_financiero import calcular_variables_derivadas


class CalculoVariablesDerivadasTests(unittest.TestCase):
    def perfil_base(self):
        return {
            "ingreso_neto_mensual_cop": 1_000_000,
            "gasto_vivienda_mensual_cop": 0,
            "gasto_alimentacion_mensual_cop": 0,
            "gasto_transporte_mensual_cop": 0,
            "gasto_salud_mensual_cop": 0,
            "gasto_educacion_mensual_cop": 0,
            "pago_servicios_publicos_cop": 0,
            "otros_gastos_esenciales_mensuales_cop": 0,
            "cuotas_deudas_vigentes_cop": 0,
            "experiencia_crediticia": "sin_experiencia",
            "meses_historial_crediticio": 0,
            "moras_ultimos_12_meses": 0,
        }

    def test_calcula_gastos_esenciales_y_flujo_mensual(self):
        perfil = self.perfil_base()
        perfil.update(
            {
                "gasto_vivienda_mensual_cop": 100_000,
                "gasto_alimentacion_mensual_cop": 200_000,
                "gasto_transporte_mensual_cop": 50_000,
                "gasto_salud_mensual_cop": 20_000,
                "gasto_educacion_mensual_cop": 30_000,
                "pago_servicios_publicos_cop": 40_000,
                "otros_gastos_esenciales_mensuales_cop": 10_000,
                "cuotas_deudas_vigentes_cop": 150_000,
            }
        )

        resultado = calcular_variables_derivadas(perfil)

        self.assertEqual(resultado["gastos_esenciales_mensuales_cop"], 450_000)
        self.assertEqual(resultado["flujo_mensual_disponible_cop"], 400_000)

    def test_conserva_el_flujo_negativo(self):
        perfil = self.perfil_base()
        perfil.update(
            {
                "ingreso_neto_mensual_cop": 500_000,
                "gasto_vivienda_mensual_cop": 200_000,
                "gasto_alimentacion_mensual_cop": 250_000,
                "gasto_transporte_mensual_cop": 50_000,
                "gasto_salud_mensual_cop": 20_000,
                "gasto_educacion_mensual_cop": 30_000,
                "pago_servicios_publicos_cop": 30_000,
                "otros_gastos_esenciales_mensuales_cop": 20_000,
                "cuotas_deudas_vigentes_cop": 100_000,
            }
        )

        resultado = calcular_variables_derivadas(perfil)

        self.assertEqual(resultado["flujo_mensual_disponible_cop"], -200_000)

    def test_asigna_nivel_proxy_segun_historial_crediticio(self):
        casos = (
            ("sin_experiencia", 0, 0, "bajo"),
            ("credito_formal", 11, 0, "medio"),
            ("credito_formal", 12, 1, "medio"),
            ("credito_formal", 12, 0, "alto"),
        )
        for experiencia, meses, moras, nivel_esperado in casos:
            with self.subTest(experiencia=experiencia, meses=meses, moras=moras):
                perfil = self.perfil_base()
                perfil.update(
                    {
                        "experiencia_crediticia": experiencia,
                        "meses_historial_crediticio": meses,
                        "moras_ultimos_12_meses": moras,
                    }
                )
                resultado = calcular_variables_derivadas(perfil)
                self.assertEqual(resultado["nivel_educacion_financiera"], nivel_esperado)

    def test_falla_si_falta_un_gasto_esencial(self):
        perfil = self.perfil_base()
        del perfil["pago_servicios_publicos_cop"]

        with self.assertRaisesRegex(ValueError, "pago_servicios_publicos_cop"):
            calcular_variables_derivadas(perfil)


if __name__ == "__main__":
    unittest.main()
