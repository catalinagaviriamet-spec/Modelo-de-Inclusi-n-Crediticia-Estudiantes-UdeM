# Modelo de Inclusión Crediticia Estudiantes UdeM

Proyecto de aprendizaje automático en la nube — Especialización en Ciencia de Datos e IA, Universidad de Medellín.

## Integrantes

- [Carolina Tirado Osorio](https://github.com/Caro-Tirado)
- [Yerlith Zabala](https://github.com/Yerlith)
- [Ana Catalina Gaviria](https://github.com/catalinagaviriamet-spec)

El proyecto explora cómo orientar a cada persona hacia educación financiera, un crédito pequeño con acompañamiento o un crédito de mayor monto según su perfil y capacidad de pago.

Como punto de partida se creó una base de 30.000 perfiles financieros sintéticos, con edades de 18 a 74 años y el campo `rango_edad`. No contiene información de personas reales ni representa una muestra de estudiantes UdeM. Esta versión incluye variables de perfil; las métricas y rutas de atención se definirán más adelante. Ver [la ficha de datos, sus límites y el diccionario de campos](docs/datos_sinteticos.md).

Para regenerar el CSV con la semilla usada en la versión inicial:

```bash
python scripts/generar_perfiles_sinteticos.py --n 30000 --seed 20261108
```

## Estructura

- `configs/`: configuración del proyecto.
- `data/`: datos separados por etapa; no incluir datos sensibles o identificables.
- `docs/`: decisiones, documentación y acuerdos del equipo.
- `models/`: artefactos de modelos.
- `notebooks/`: exploración y experimentos.
- `output/`: resultados generados.
- `scripts/`: utilidades ejecutables.
- `src/`: código fuente organizado por componente.
- `tests/`: pruebas.
