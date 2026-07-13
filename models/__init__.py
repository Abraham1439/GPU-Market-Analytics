"""
Paquete de Machine Learning de GPU Market Analytics.

Contiene el portafolio de modelos entrenados sobre el dataset final
generado por el pipeline ETL (etl/pipeline.py):

- train_regression.py     -> Predicción de precio_venta_clp (supervisado, regresión)
- train_classification.py -> Predicción de gama (supervisado, clasificación)
- train_clustering.py     -> Segmentación de mercado (no supervisado)
- model_utils.py           -> Utilidades compartidas (split, preprocesamiento, guardado)
- evaluate.py               -> Comparación de métricas y generación de gráficos

Los modelos entrenados y sus métricas se guardan en models/artifacts/.
"""
