# Portafolio de Modelos ML GPU Market Analytics

Parte nueva del proyecto agregada para la Evaluación Final Transversal
(SCY1101). Construye sobre el dataset final que genera `etl/pipeline.py`.

| Archivo | Modelo | Tipo | Target |
|---|---|---|---|
| `train_regression.py` | Predicción de precio | Supervisado (regresión) | `precio_venta_clp` |
| `train_classification.py` | Predicción de gama | Supervisado (clasificación) | `gama` |
| `train_clustering.py` | Segmentación de mercado | No supervisado |  |
| `model_utils.py` | Utilidades compartidas (split, preprocesamiento, guardado) |  |  |
| `evaluate.py` | Comparación de métricas + gráficos para informe y dashboard |  |  |

## Cómo correr (una vez implementado)

```bash
python -m models.train_regression
python -m models.train_classification
python -m models.train_clustering
python -m models.evaluate
```

Los modelos entrenados y sus métricas quedan en `models/artifacts/`,
que luego consumen `api/main.py` (nuevos endpoints `/predict/*`) y
`dashboards/app.py` (nueva sección de resultados de ML).

## Estado actual

Los 3 modelos están completos y entrenados contra el dataset real (120 GPUs). Resultados:

| Modelo | Métrica principal | Valor |
|---|---|---|
| Regresión (TDP) | R² / MAE | 0.87 / 24.3 W (Random Forest) |
| Clasificación (gama) | Accuracy / F1 macro | 0.75 / 0.74 (Logistic Regression) |
| Clustering (mercado) | Silhouette (K=2) | 0.53 |

Cada script documenta en su docstring decisiones de diseño importantes tomadas durante el desarrollo (ej. por qué se cambió el target de regresión de `precio_venta_clp` a `tdp_watts`, por qué `chip_gpu` se excluye de las features). Léelas antes de la presentación son buen material para responder preguntas del profesor.
