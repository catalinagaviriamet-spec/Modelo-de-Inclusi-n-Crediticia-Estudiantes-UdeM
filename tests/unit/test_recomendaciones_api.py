"""Pruebas de las rutas académicas que devuelve la API."""
import unittest

from api.main import construir_recomendacion


class RecomendacionesAcademicasTests(unittest.TestCase):
    def test_grupo_cero_orienta_a_revision_formal_sin_asignar_cupo(self):
        recomendacion = construir_recomendacion(cluster_id=0, flujo_disponible=-100_000)

        self.assertEqual(recomendacion.nombre_grupo, "Viabilidad estudio formal de crédito")
        self.assertEqual(recomendacion.tipo, "revision_formal")
        self.assertIsNone(recomendacion.cupo_simulado_cop)
        self.assertIn("siguiente sesión", recomendacion.mensaje)
        self.assertIn("no es positivo", recomendacion.fundamento)

    def test_grupo_uno_asigna_cupo_simulado_segun_flujo(self):
        casos = ((-1, 300_000), (0, 300_000), (1, 500_000))
        for flujo, cupo_esperado in casos:
            with self.subTest(flujo=flujo):
                recomendacion = construir_recomendacion(cluster_id=1, flujo_disponible=flujo)

                self.assertEqual(recomendacion.nombre_grupo, "Cuida tu historial crediticio")
                self.assertEqual(recomendacion.tipo, "cupo_simulado")
                self.assertEqual(recomendacion.cupo_simulado_cop, cupo_esperado)
                self.assertIn("simulación académica", recomendacion.mensaje)
                self.assertIn("no una oferta ni", recomendacion.aclaracion)

    def test_grupo_dos_orienta_a_educacion_financiera_sin_cupo(self):
        recomendacion = construir_recomendacion(cluster_id=2, flujo_disponible=500_000)

        self.assertEqual(recomendacion.nombre_grupo, "Iniciemos con educación financiera")
        self.assertEqual(recomendacion.tipo, "educacion_financiera")
        self.assertIsNone(recomendacion.cupo_simulado_cop)
        self.assertIn("curso corto e interactivo", recomendacion.mensaje)
        self.assertIn("no demuestra falta de conocimientos", recomendacion.aclaracion)


if __name__ == "__main__":
    unittest.main()
