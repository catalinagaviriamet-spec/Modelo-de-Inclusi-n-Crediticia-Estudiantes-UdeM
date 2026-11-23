"""Pruebas de las rutas académicas que devuelve la API."""
import unittest
from types import SimpleNamespace

import joblib

from api.main import (
    ARTIFACT,
    EJEMPLO_PERFIL_SINTETICO,
    EJEMPLOS_PERFILES_BASE_FINAL,
    PerfilEntrada,
    clusterizar,
    construir_recomendacion,
    informacion_modelo,
)


class RecomendacionesAcademicasTests(unittest.TestCase):
    def test_grupo_cero_orienta_a_revision_formal_sin_asignar_cupo(self):
        recomendacion = construir_recomendacion(ruta="viabilidad_formal", flujo_disponible=-100_000)

        self.assertEqual(recomendacion.nombre_grupo, "Viabilidad estudio formal de crédito")
        self.assertEqual(recomendacion.tipo, "revision_formal")
        self.assertIsNone(recomendacion.cupo_simulado_cop)
        self.assertIn("siguiente sesión", recomendacion.mensaje)
        self.assertIn("no es positivo", recomendacion.fundamento)

    def test_grupo_uno_asigna_cupo_simulado_segun_flujo(self):
        casos = ((-1, 300_000), (0, 300_000), (1, 500_000))
        for flujo, cupo_esperado in casos:
            with self.subTest(flujo=flujo):
                recomendacion = construir_recomendacion(ruta="cuidar_historial", flujo_disponible=flujo)

                self.assertEqual(recomendacion.nombre_grupo, "Cuida tu historial crediticio")
                self.assertEqual(recomendacion.tipo, "cupo_simulado")
                self.assertEqual(recomendacion.cupo_simulado_cop, cupo_esperado)
                self.assertIn("simulación académica", recomendacion.mensaje)
                self.assertIn("no una oferta ni", recomendacion.aclaracion)

    def test_grupo_dos_orienta_a_educacion_financiera_sin_cupo(self):
        recomendacion = construir_recomendacion(ruta="educacion_financiera", flujo_disponible=500_000)

        self.assertEqual(recomendacion.nombre_grupo, "Iniciemos con educación financiera")
        self.assertEqual(recomendacion.tipo, "educacion_financiera")
        self.assertIsNone(recomendacion.cupo_simulado_cop)
        self.assertIn("curso corto e interactivo", recomendacion.mensaje)
        self.assertIn("no demuestra falta de conocimientos", recomendacion.aclaracion)

    def test_api_usa_el_artefacto_y_el_esquema_de_la_base_final(self):
        self.assertNotIn("nivel_estudio", EJEMPLO_PERFIL_SINTETICO)
        self.assertNotIn("tipo_plan_celular", EJEMPLO_PERFIL_SINTETICO)
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(
            modelo=joblib.load(ARTIFACT)
        )))
        info = informacion_modelo(request)
        self.assertEqual(info["variables_numericas"][3], "ingreso_per_capita_cop")
        self.assertEqual(set(info["mapa_rutas_por_cluster"].values()), {
            "educacion_financiera", "viabilidad_formal", "cuidar_historial"
        })
        respuesta = clusterizar(request, PerfilEntrada(**EJEMPLO_PERFIL_SINTETICO))
        self.assertEqual(respuesta.cluster_id, 2)
        self.assertEqual(
            respuesta.recomendacion.nombre_grupo,
            "Iniciemos con educación financiera",
        )

    def test_ejemplos_swagger_producen_las_tres_rutas(self):
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(
            modelo=joblib.load(ARTIFACT)
        )))
        esperadas = {
            "viabilidad_formal": "Viabilidad estudio formal de crédito",
            "cuidar_historial": "Cuida tu historial crediticio",
            "educacion_financiera": "Iniciemos con educación financiera",
        }
        for clave, esperado in esperadas.items():
            with self.subTest(clave=clave):
                perfil = PerfilEntrada(**EJEMPLOS_PERFILES_BASE_FINAL[clave]["value"])
                respuesta = clusterizar(request, perfil)
                self.assertEqual(respuesta.recomendacion.nombre_grupo, esperado)


if __name__ == "__main__":
    unittest.main()
