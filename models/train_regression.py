import logging

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline

from models.model_utils import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    TARGET_REGRESSION,
    build_preprocessor,
    load_final_dataset,
    save_metrics,
    save_model,
    train_test_split_gpu,
)

logging.basicConfig(level="INFO", format="%(asctime)s - %(levelname)s - %(message)s")


def evaluate_regressor(model, X_test, y_test) -> dict:
    """Calcula MAE, RMSE y R² sobre el set de test."""
    y_pred = model.predict(X_test)
    return {
        "mae_watts": round(mean_absolute_error(y_test, y_pred), 2),
        "rmse_watts": round(np.sqrt(mean_squared_error(y_test, y_pred)), 2),
        "r2": round(r2_score(y_test, y_pred), 4),
    }


def get_feature_importance(pipeline: Pipeline, target: str) -> dict:
    """
    Extrae importancia de features del modelo final (solo disponible
    para RandomForest/GradientBoosting, no para LinearRegression).
    """
    model = pipeline.named_steps["model"]
    if not hasattr(model, "feature_importances_"):
        return {}

    numeric_cols = [c for c in NUMERIC_FEATURES if c != target]
    categorical_cols = [c for c in CATEGORICAL_FEATURES if c != target]

    preprocessor = pipeline.named_steps["preprocessor"]
    cat_encoder = preprocessor.named_transformers_["cat"]
    cat_feature_names = cat_encoder.get_feature_names_out(categorical_cols)
    all_feature_names = numeric_cols + list(cat_feature_names)

    importances = dict(zip(all_feature_names, model.feature_importances_))
    # Top 10 features más importantes, ordenadas
    top_10 = dict(
        sorted(importances.items(), key=lambda x: x[1], reverse=True)[:10]
    )
    return {k: round(float(v), 4) for k, v in top_10.items()}


def main() -> None:
    logging.info("========== Entrenando modelos de REGRESIÓN (TDP) ==========")

    df = load_final_dataset()

    rows_before = len(df)
    df = df[df[TARGET_REGRESSION] > 0].reset_index(drop=True)
    logging.info(
        "Filtradas filas con tdp_watts=0 (dato faltante, no real): %s -> %s filas",
        rows_before, len(df)
    )

    X_train, X_test, y_train, y_test = train_test_split_gpu(df, TARGET_REGRESSION)

    preprocessor = build_preprocessor(target=TARGET_REGRESSION)

    candidates = {
        "linear_regression": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("model", LinearRegression()),
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("model", RandomForestRegressor(random_state=42)),
            ]
        ),
        "gradient_boosting": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("model", GradientBoostingRegressor(random_state=42)),
            ]
        ),
    }

    param_grids = {
        "random_forest": {
            "model__n_estimators": [100, 200],
            "model__max_depth": [None, 5, 10],
        },
        "gradient_boosting": {
            "model__n_estimators": [100, 200],
            "model__learning_rate": [0.05, 0.1],
            "model__max_depth": [3, 5],
        },
    }

    results = {}
    trained_pipelines = {}

    for name, pipeline in candidates.items():
        logging.info("Entrenando: %s", name)

        if name in param_grids:
            search = GridSearchCV(
                pipeline,
                param_grids[name],
                cv=3,
                scoring="neg_mean_absolute_error",
                n_jobs=-1,
            )
            search.fit(X_train, y_train)
            best_pipeline = search.best_estimator_
            best_params = search.best_params_
        else:
            pipeline.fit(X_train, y_train)
            best_pipeline = pipeline
            best_params = {}

        metrics = evaluate_regressor(best_pipeline, X_test, y_test)
        metrics["best_params"] = best_params

        results[name] = metrics
        trained_pipelines[name] = best_pipeline

        logging.info("%s -> MAE: %s W | RMSE: %s W | R2: %s",
                      name, metrics["mae_watts"], metrics["rmse_watts"], metrics["r2"])

    # Selecciona el mejor modelo según MAE (métrica de negocio más
    # interpretable: "en promedio nos equivocamos en X watts")
    best_model_name = min(results, key=lambda k: results[k]["mae_watts"])
    best_pipeline = trained_pipelines[best_model_name]

    logging.info("Mejor modelo: %s (MAE más bajo)", best_model_name)

    feature_importance = get_feature_importance(best_pipeline, TARGET_REGRESSION)

    final_report = {
        "target": TARGET_REGRESSION,
        "best_model": best_model_name,
        "comparison": results,
        "feature_importance_top10": feature_importance,
        "train_rows": len(X_train),
        "test_rows": len(X_test),
    }

    save_model(best_pipeline, "regression_model")
    save_metrics("regression", final_report)

    logging.info("========== Entrenamiento de REGRESIÓN finalizado ==========")


if __name__ == "__main__":
    main()
